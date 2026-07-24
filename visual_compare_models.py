#!/usr/bin/env python3
"""Cross-model visual comparison on the common eligible task intersection."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
import time
from typing import Any

from openai import OpenAI

_EVAL_ROOT = Path(__file__).resolve().parent
if str(_EVAL_ROOT) not in sys.path:
    sys.path.insert(0, str(_EVAL_ROOT))

import evaluate_api_model as eval_api  # noqa: E402
import visual_eval  # noqa: E402


DEFAULT_MODEL_SLUGS = [
    "deepseek__deepseek-chat-v3.1",
    "openai__gpt-4o-mini",
    "qwen__qwen3-30b-a3b-instruct-2507",
    "openai__gpt-5.4",
]


def _parse_args() -> argparse.Namespace:
    default_base_url = os.environ.get("OPENAI_BASE_URL") or visual_eval.DEFAULT_BASE_URL
    parser = argparse.ArgumentParser(
        description="Run visual comparison across multiple result folders on their common eligible tasks."
    )
    parser.add_argument("--results-dir", type=Path, default=visual_eval.DEFAULT_RESULTS_DIR)
    parser.add_argument(
        "--protocol-version",
        choices=["0.8", "0.9.1"],
        default=visual_eval.DEFAULT_PROTOCOL_VERSION,
        help="A2UI protocol stack (default 0.9.1). Selects render_check, "
        "default render URL, results subdir, and VLM copy.",
    )
    parser.add_argument("--model-slugs", nargs="+", default=DEFAULT_MODEL_SLUGS)
    parser.add_argument(
        "--render-url",
        type=str,
        default=None,
        help="Renderer base URL (default: 0.8→5173, 0.9.1→5174).",
    )
    parser.add_argument("--vlm-model", type=str, default=visual_eval.DEFAULT_VLM_MODEL)
    parser.add_argument("--vlm-base-url", type=str, default=default_base_url)
    parser.add_argument("--judge-api-key", type=str, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--viewport-width", type=int, default=520)
    parser.add_argument("--viewport-height", type=int, default=1600)
    parser.add_argument("--stage-width", type=int, default=320)
    parser.add_argument("--stage-max-height", type=int, default=2600)
    parser.add_argument("--screenshot-timeout-ms", type=int, default=20000)
    parser.add_argument("--limit-common-tasks", type=int, default=0)
    parser.add_argument("--max-workers", type=int, default=4)
    return parser.parse_args()


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _pearson(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) != len(ys) or len(xs) < 2:
        return None
    x_mean = _mean(xs)
    y_mean = _mean(ys)
    x_var = sum((x - x_mean) ** 2 for x in xs)
    y_var = sum((y - y_mean) ** 2 for y in ys)
    if x_var <= 0 or y_var <= 0:
        return None
    cov = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys))
    return cov / ((x_var ** 0.5) * (y_var ** 0.5))


def _load_existing_rows(output_dir: Path) -> list[dict[str, Any]]:
    results_path = output_dir / "results.json"
    if not results_path.exists():
        return []
    return json.loads(results_path.read_text(encoding="utf-8"))


def _load_existing_errors(output_dir: Path) -> list[dict[str, Any]]:
    errors_path = output_dir / "errors.json"
    if not errors_path.exists():
        return []
    return json.loads(errors_path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _pick_sample_target(
    eligible_by_model: dict[str, dict[str, visual_eval.VisualEvalTarget]],
    target_id: str,
) -> visual_eval.VisualEvalTarget:
    for rows in eligible_by_model.values():
        target = rows.get(target_id)
        if target is not None:
            return target
    raise KeyError(f"Missing common target: {target_id}")


def _build_summary(
    rows: list[dict[str, Any]],
    errors: list[dict[str, Any]],
    *,
    model_slugs: list[str],
    common_target_ids: list[str],
    scenario_by_target: dict[str, str],
    vlm_model: str,
    render_url: str,
    eligible_counts: dict[str, int],
    protocol_version: str,
) -> dict[str, Any]:
    per_model: dict[str, dict[str, Any]] = {}
    rows_by_model: dict[str, list[dict[str, Any]]] = defaultdict(list)
    errors_by_model: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        rows_by_model[row["model_slug"]].append(row)
    for err in errors:
        errors_by_model[err["model_slug"]].append(err)

    for model_slug in model_slugs:
        model_rows = rows_by_model.get(model_slug, [])
        issue_counter = Counter()
        for row in model_rows:
            issue_counter.update(row["visual_eval"].get("issues_detected", []))
        per_model[model_slug] = {
            "eligible_target_count": eligible_counts.get(model_slug, 0),
            "common_target_count": len(common_target_ids),
            "completed_count": len(model_rows),
            "error_count": len(errors_by_model.get(model_slug, [])),
            "avg_screenshot_seconds": _mean(
                [float(row["timing"]["screenshot_seconds"]) for row in model_rows if row.get("timing")]
            ),
            "avg_judge_seconds": _mean(
                [float(row["timing"]["judge_seconds"]) for row in model_rows if row.get("timing")]
            ),
            "avg_total_seconds": _mean(
                [float(row["timing"]["total_seconds"]) for row in model_rows if row.get("timing")]
            ),
            "avg_baseline_l2_mean": _mean([row["baseline_l2_mean"] for row in model_rows]),
            "avg_baseline_l3_mean": _mean([row["baseline_l3_mean"] for row in model_rows]),
            "avg_visual_mean": _mean([row["visual_eval"]["mean"] for row in model_rows]),
            "avg_visual_dims": {
                dim: _mean([row["visual_eval"]["scores"][dim] for row in model_rows])
                for dim in visual_eval.VISUAL_DIMS
            },
            "issue_rate": (
                sum(1 for row in model_rows if row["visual_eval"].get("issues_detected")) / len(model_rows)
                if model_rows
                else 0.0
            ),
            "top_issues": issue_counter.most_common(10),
            "visual_vs_l2_corr": _pearson(
                [row["visual_eval"]["mean"] for row in model_rows],
                [row["baseline_l2_mean"] for row in model_rows],
            ),
            "visual_vs_l3_corr": _pearson(
                [row["visual_eval"]["mean"] for row in model_rows],
                [row["baseline_l3_mean"] for row in model_rows],
            ),
        }

    scenario_distribution = Counter(
        scenario_by_target[target_id]
        for target_id in common_target_ids
        if scenario_by_target.get(target_id)
    )
    scenario_means: dict[str, dict[str, float]] = {}
    for scenario_id in sorted({value for value in scenario_by_target.values() if value}):
        scenario_rows = [row for row in rows if row["scenario_id"] == scenario_id]
        scenario_means[scenario_id] = {
            model_slug: _mean(
                [row["visual_eval"]["mean"] for row in scenario_rows if row["model_slug"] == model_slug]
            )
            for model_slug in model_slugs
        }

    return {
        "protocol_version": protocol_version,
        "vlm_model": vlm_model,
        "render_url": render_url,
        "model_slugs": model_slugs,
        "eligible_counts": eligible_counts,
        "common_target_count": len(common_target_ids),
        "scenario_distribution": dict(sorted(scenario_distribution.items())),
        "completed_rows": len(rows),
        "error_rows": len(errors),
        "avg_total_seconds": _mean(
            [float(row["timing"]["total_seconds"]) for row in rows if row.get("timing")]
        ),
        "per_model": per_model,
        "scenario_visual_means": scenario_means,
    }


def _run_single_visual_judgment(
    *,
    api_key: str,
    vlm_base_url: str,
    vlm_model: str,
    render_url: str,
    viewport_width: int,
    viewport_height: int,
    stage_width: int,
    stage_max_height: int,
    screenshot_timeout_ms: int,
    candidate: visual_eval.VisualEvalTarget,
    task: Any,
    screenshot_path: Path,
    protocol_version: str,
) -> dict[str, Any]:
    client = OpenAI(api_key=api_key, base_url=vlm_base_url)
    start = time.perf_counter()
    screenshot_start = start
    visual_eval._screenshot_rendered_ui(
        render_url,
        a2ui_messages=candidate.a2ui_messages,
        output_path=screenshot_path,
        viewport_width=viewport_width,
        viewport_height=viewport_height,
        stage_width=stage_width,
        stage_max_height=stage_max_height,
        timeout_ms=screenshot_timeout_ms,
    )
    screenshot_end = time.perf_counter()
    judged = visual_eval._judge_visual(
        client,
        vlm_model=vlm_model,
        task=task,
        target=candidate,
        text_response=candidate.text_response,
        screenshot_path=screenshot_path,
        protocol_version=protocol_version,
    )
    judge_end = time.perf_counter()
    visual = visual_eval._normalize_visual_result(judged)
    return {
        "task_id": candidate.task_id,
        "target_id": candidate.target_id,
        "scenario_id": candidate.scenario_id,
        "difficulty_level": candidate.difficulty_level,
        "model_slug": candidate.model_slug,
        "user_message": candidate.user_message,
        "dialogue_context": candidate.dialogue_context,
        "step_idx": candidate.step_idx,
        "step_count": candidate.step_count,
        "screenshot_path": str(screenshot_path),
        "baseline_l2_mean": candidate.baseline_l2_mean,
        "baseline_l3_mean": candidate.baseline_l3_mean,
        "visual_eval": visual,
        "text_response": candidate.text_response,
        "timing": {
            "screenshot_seconds": screenshot_end - screenshot_start,
            "judge_seconds": judge_end - screenshot_end,
            "total_seconds": judge_end - start,
        },
    }


def main() -> None:
    args = _parse_args()
    if not args.render_url:
        args.render_url = visual_eval.default_render_url_for_protocol(args.protocol_version)
    results_dir = eval_api.resolve_output_dir(Path(args.results_dir), args.protocol_version)
    visual_eval._setup_env()
    api_key = (
        args.judge_api_key
        or os.environ.get("OPENROUTER_API_KEY")
        or os.environ.get("OPENAI_API_KEY")
    )
    if not api_key:
        raise RuntimeError("Missing API key. Set OPENROUTER_API_KEY or OPENAI_API_KEY.")

    tasks_by_id = visual_eval._load_tasks_by_id(results_dir)
    eligible_by_model: dict[str, dict[str, visual_eval.VisualEvalTarget]] = {}
    for model_slug in args.model_slugs:
        eligible = visual_eval._load_candidates(
            results_dir,
            model_slug,
            tasks_by_id,
            protocol_version=args.protocol_version,
        )
        eligible_by_model[model_slug] = {row.target_id: row for row in eligible}
    common_target_ids = sorted(
        set.intersection(*(set(rows.keys()) for rows in eligible_by_model.values()))
    )
    if args.limit_common_tasks > 0:
        common_target_ids = common_target_ids[: args.limit_common_tasks]
    if not common_target_ids:
        raise RuntimeError("No common eligible tasks found across the selected models.")

    missing_tasks = [
        _pick_sample_target(eligible_by_model, target_id).task_id
        for target_id in common_target_ids
        if _pick_sample_target(eligible_by_model, target_id).task_id not in tasks_by_id
    ]
    if missing_tasks:
        raise RuntimeError(f"Missing tasks in manifest: {missing_tasks[:5]}")

    scenario_by_target = {
        target_id: _pick_sample_target(eligible_by_model, target_id).scenario_id
        for target_id in common_target_ids
    }
    eligible_counts = {model_slug: len(rows) for model_slug, rows in eligible_by_model.items()}
    common_task_ids = sorted({_pick_sample_target(eligible_by_model, target_id).task_id for target_id in common_target_ids})
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = args.output_dir or (results_dir / f"visual_compare_common{len(common_target_ids)}_{timestamp}")
    output_dir.mkdir(parents=True, exist_ok=True)
    screenshots_dir = output_dir / "screenshots"
    screenshots_dir.mkdir(exist_ok=True)

    metadata = {
        "results_dir": str(results_dir),
        "protocol_version": args.protocol_version,
        "model_slugs": args.model_slugs,
        "eligible_counts": eligible_counts,
        "common_target_count": len(common_target_ids),
        "common_task_count": len(common_task_ids),
        "common_target_ids": common_target_ids,
        "common_task_ids": common_task_ids,
        "scenario_by_target": scenario_by_target,
        "scenario_distribution": dict(sorted(Counter(scenario_by_target.values()).items())),
        "render_url": args.render_url,
        "vlm_model": args.vlm_model,
        "viewport_width": args.viewport_width,
        "viewport_height": args.viewport_height,
        "stage_width": args.stage_width,
        "stage_max_height": args.stage_max_height,
        "max_workers": args.max_workers,
    }
    _write_json(output_dir / "metadata.json", metadata)

    rows = _load_existing_rows(output_dir)
    errors = _load_existing_errors(output_dir)
    done_keys = {(row["model_slug"], row["target_id"]) for row in rows}
    done_keys.update((err["model_slug"], err["target_id"]) for err in errors)

    total = len(common_target_ids) * len(args.model_slugs)
    completed = len(done_keys)
    print(
        json.dumps(
            {
                "output_dir": str(output_dir),
                "protocol_version": args.protocol_version,
                "total_judgments": total,
                "already_completed": completed,
                "common_target_count": len(common_target_ids),
                "scenario_distribution": metadata["scenario_distribution"],
            },
            ensure_ascii=False,
        )
    )
    pending_jobs: list[dict[str, Any]] = []
    for target_idx, target_id in enumerate(common_target_ids, start=1):
        for model_slug in args.model_slugs:
            key = (model_slug, target_id)
            if key in done_keys:
                continue
            candidate = eligible_by_model[model_slug][target_id]
            task = tasks_by_id[candidate.task_id]
            screenshot_path = screenshots_dir / model_slug / f"{target_id}.png"
            pending_jobs.append(
                {
                    "key": key,
                    "target_id": target_id,
                    "target_idx": target_idx,
                    "candidate": candidate,
                    "task": task,
                    "screenshot_path": screenshot_path,
                }
            )

    print(
        json.dumps(
            {
                "pending_judgments": len(pending_jobs),
                "max_workers": args.max_workers,
            },
            ensure_ascii=False,
        )
    )

    with ThreadPoolExecutor(max_workers=max(1, args.max_workers)) as executor:
        future_to_job = {}
        for job in pending_jobs:
            candidate = job["candidate"]
            task = job["task"]
            print(
                f"[queue] {candidate.model_slug} {candidate.target_id} "
                f"(scenario={task.scenario_id}, common_target={job['target_idx']}/{len(common_target_ids)})"
            )
            future = executor.submit(
                _run_single_visual_judgment,
                api_key=api_key,
                vlm_base_url=args.vlm_base_url,
                vlm_model=args.vlm_model,
                render_url=args.render_url,
                viewport_width=args.viewport_width,
                viewport_height=args.viewport_height,
                stage_width=args.stage_width,
                stage_max_height=args.stage_max_height,
                screenshot_timeout_ms=args.screenshot_timeout_ms,
                candidate=candidate,
                task=task,
                screenshot_path=job["screenshot_path"],
                protocol_version=args.protocol_version,
            )
            future_to_job[future] = job

        for future in as_completed(future_to_job):
            job = future_to_job[future]
            key = job["key"]
            candidate = job["candidate"]
            task = job["task"]
            try:
                row = future.result()
                rows.append(row)
                _write_json(output_dir / "results.json", rows)
                timing = row.get("timing", {})
                print(
                    f"[done {completed + 1}/{total}] {candidate.model_slug} {candidate.target_id} "
                    f"total={timing.get('total_seconds', 0.0):.2f}s "
                    f"(shot={timing.get('screenshot_seconds', 0.0):.2f}s, "
                    f"judge={timing.get('judge_seconds', 0.0):.2f}s)"
                )
            except Exception as exc:
                errors.append(
                    {
                        "task_id": candidate.task_id,
                        "target_id": job["target_id"],
                        "scenario_id": task.scenario_id,
                        "model_slug": candidate.model_slug,
                        "error": str(exc),
                    }
                )
                _write_json(output_dir / "errors.json", errors)
                print(
                    f"[error {completed + 1}/{total}] {candidate.model_slug} {candidate.target_id}: {exc}"
                )
            completed += 1
            done_keys.add(key)
            summary = _build_summary(
                rows,
                errors,
                model_slugs=args.model_slugs,
                common_target_ids=common_target_ids,
                scenario_by_target=scenario_by_target,
                vlm_model=args.vlm_model,
                render_url=args.render_url,
                eligible_counts=eligible_counts,
                protocol_version=args.protocol_version,
            )
            _write_json(output_dir / "summary.json", summary)

    final_summary = _build_summary(
        rows,
        errors,
        model_slugs=args.model_slugs,
        common_target_ids=common_target_ids,
        scenario_by_target=scenario_by_target,
        vlm_model=args.vlm_model,
        render_url=args.render_url,
        eligible_counts=eligible_counts,
        protocol_version=args.protocol_version,
    )
    _write_json(output_dir / "summary.json", final_summary)
    if not (output_dir / "errors.json").exists():
        _write_json(output_dir / "errors.json", errors)
    if not (output_dir / "results.json").exists():
        _write_json(output_dir / "results.json", rows)
    print(json.dumps(final_summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
