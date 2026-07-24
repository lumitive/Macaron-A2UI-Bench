#!/usr/bin/env python3
"""Minimal render -> screenshot -> VLM visual evaluation for existing API results.

Example:
  python visual_eval.py \
    --results-dir ./results \
    --protocol-version 0.8 \
    --model-slug openai__gpt-4o-mini \
    --limit 5

Prerequisites:
  1. Start a compatible local render service and expose it at `--render-url`
     (default: 0.8 → `http://127.0.0.1:5173/`; 0.9.1 → `http://127.0.0.1:5174/`).
  2. Set `OPENROUTER_API_KEY` (or `OPENAI_API_KEY`) for the VLM judge.
"""

from __future__ import annotations

import argparse
import base64
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
import random
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from openai import OpenAI

_EVAL_ROOT = Path(__file__).resolve().parent
if str(_EVAL_ROOT) not in sys.path:
    sys.path.insert(0, str(_EVAL_ROOT))

import evaluate_api_model as eval_api  # noqa: E402
from protocol import get_protocol_stack  # noqa: E402

DEFAULT_RESULTS_DIR = Path(__file__).resolve().parent / "results"
DEFAULT_PROTOCOL_VERSION = "0.8"
DEFAULT_RENDER_URL = "http://127.0.0.1:5173/"
DEFAULT_VLM_MODEL = "qwen/qwen3-vl-235b-a22b-instruct"
DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"


def default_render_url_for_protocol(protocol_version: str) -> str:
    """Return the default local renderer URL for a protocol version."""
    if protocol_version == "0.9.1":
        return "http://127.0.0.1:5174/"
    if protocol_version == "0.8":
        return "http://127.0.0.1:5173/"
    raise ValueError(f"Unsupported protocol version: {protocol_version!r}")


def select_targets_with_stack_render_check(
    a2ui_messages: list[dict[str, Any]],
    *,
    protocol_version: str,
) -> tuple[bool, list[str]]:
    """Filter visual candidates via the active protocol stack's render_check.

    Never uses root ``render_check.py`` directly — 0.9.1 messages must go
    through ``get_protocol_stack(...).render_check``.
    """
    stack = get_protocol_stack(protocol_version)
    return stack.render_check(a2ui_messages)


def _iter_search_roots() -> list[Path]:
    roots: list[Path] = []
    seen: set[Path] = set()
    for base in (_EVAL_ROOT, *_EVAL_ROOT.parents):
        for candidate in (base, base.parent):
            candidate = candidate.resolve()
            if candidate not in seen:
                seen.add(candidate)
                roots.append(candidate)
    return roots

VISUAL_DIMS = {
    "V1": "Visual Integrity",
    "V2": "Task Alignment",
    "V3": "Action Clarity",
}


@dataclass
class VisualEvalTarget:
    model_slug: str
    task_id: str
    target_id: str
    scenario_id: str
    difficulty_level: str
    baseline_l2_mean: float
    baseline_l3_mean: float
    user_message: str
    dialogue_context: list[dict[str, str]]
    text_response: str
    a2ui_messages: list[dict[str, Any]]
    step_idx: int | None
    step_count: int
    raw_result: dict[str, Any]


def _parse_args() -> argparse.Namespace:
    default_base_url = os.environ.get("OPENAI_BASE_URL") or DEFAULT_BASE_URL
    parser = argparse.ArgumentParser(
        description="Minimal VLM-based visual evaluation over existing API result files."
    )
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument(
        "--protocol-version",
        choices=["0.8", "0.9.1"],
        default=DEFAULT_PROTOCOL_VERSION,
        help="A2UI protocol stack (default 0.8 until cutover). Selects render_check, "
        "default render URL, results subdir, and VLM copy.",
    )
    parser.add_argument("--model-slug", type=str, default="openai__gpt-4o-mini")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--selection", choices=["balanced", "random"], default="balanced")
    parser.add_argument(
        "--render-url",
        type=str,
        default=None,
        help="Renderer base URL (default: 0.8→5173, 0.9.1→5174).",
    )
    parser.add_argument("--vlm-model", type=str, default=DEFAULT_VLM_MODEL)
    parser.add_argument("--vlm-base-url", type=str, default=default_base_url)
    parser.add_argument("--judge-api-key", type=str, default=None)
    parser.add_argument("--skip-judge", action="store_true")
    parser.add_argument("--continue-on-judge-error", action="store_true")
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument(
        "--max-workers",
        type=int,
        default=max(1, int(os.environ.get("A2UI_VISUAL_MAX_WORKERS", "1"))),
    )
    parser.add_argument("--viewport-width", type=int, default=720)
    parser.add_argument("--viewport-height", type=int, default=1400)
    parser.add_argument("--stage-width", type=int, default=420)
    parser.add_argument("--stage-max-height", type=int, default=1600)
    parser.add_argument("--screenshot-timeout-ms", type=int, default=20000)
    return parser.parse_args()


def _load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def _setup_env() -> None:
    _load_env_file(_EVAL_ROOT / ".env")
    for root in _iter_search_roots()[:4]:
        _load_env_file(root / ".env")


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _score_mean(score_block: dict[str, Any]) -> float:
    return _mean([float(v) for v in score_block.get("scores", {}).values()])


def _build_target_id(task_id: str, step_idx: int | None) -> str:
    if step_idx is None:
        return task_id
    return f"{task_id}__step{step_idx + 1:02d}"


def _make_single_turn_target(
    *,
    row: dict[str, Any],
    model_slug: str,
    task: eval_api.TaskSample,
    protocol_version: str,
) -> VisualEvalTarget | None:
    model_output = row.get("model_output", {})
    hard_fail = row.get("hard_fail", {})
    if model_output.get("parse_error"):
        return None
    if not row.get("render_check", {}).get("pass", False):
        return None
    if hard_fail.get("any", False):
        return None
    a2ui_messages = model_output.get("a2ui_messages") or []
    if not a2ui_messages:
        return None
    # Re-run stack render_check to avoid trusting stale result files and to
    # avoid filtering 0.9.1 candidates through root 0.8 render_check.py.
    render_pass, _ = select_targets_with_stack_render_check(
        a2ui_messages, protocol_version=protocol_version
    )
    if not render_pass:
        return None
    return VisualEvalTarget(
        model_slug=model_slug,
        task_id=row["task_id"],
        target_id=_build_target_id(row["task_id"], None),
        scenario_id=row["scenario_id"],
        difficulty_level=row.get("difficulty_level", task.difficulty_level),
        baseline_l2_mean=_score_mean(row.get("l2", {})),
        baseline_l3_mean=_score_mean(row.get("l3", {})),
        user_message=task.user_message,
        dialogue_context=task.dialogue_context,
        text_response=model_output.get("text_response", ""),
        a2ui_messages=a2ui_messages,
        step_idx=None,
        step_count=1,
        raw_result=row,
    )


def _make_depth_step_targets(
    *,
    row: dict[str, Any],
    model_slug: str,
    task: eval_api.TaskSample,
    protocol_version: str,
) -> list[VisualEvalTarget]:
    model_output = row.get("model_output", {})
    steps = model_output.get("steps", []) or []
    episode_turns = task.episode_turns or []
    step_count = min(len(steps), len(episode_turns))
    targets: list[VisualEvalTarget] = []
    for step_idx in range(step_count):
        step = steps[step_idx]
        step_task = episode_turns[step_idx]
        step_output = step.get("model_output", {}) or {}
        a2ui_messages = step_output.get("a2ui_messages") or []
        if step_output.get("parse_error"):
            continue
        if not a2ui_messages:
            continue
        render_pass, _ = select_targets_with_stack_render_check(
            a2ui_messages, protocol_version=protocol_version
        )
        if not render_pass:
            continue
        targets.append(
            VisualEvalTarget(
                model_slug=model_slug,
                task_id=row["task_id"],
                target_id=_build_target_id(row["task_id"], step_idx),
                scenario_id=row["scenario_id"],
                difficulty_level=row.get("difficulty_level", task.difficulty_level),
                baseline_l2_mean=_score_mean(row.get("l2", {})),
                baseline_l3_mean=_score_mean(row.get("l3", {})),
                user_message=str(step_task.get("user_message", "")).strip(),
                dialogue_context=list(step_task.get("dialogue_context_before", []) or []),
                text_response=step_output.get("text_response", ""),
                a2ui_messages=a2ui_messages,
                step_idx=step_idx,
                step_count=step_count,
                raw_result=row,
            )
        )
    return targets


def _load_candidates(
    results_dir: Path,
    model_slug: str,
    tasks_by_id: dict[str, eval_api.TaskSample],
    *,
    protocol_version: str = DEFAULT_PROTOCOL_VERSION,
) -> list[VisualEvalTarget]:
    task_results = json.loads((results_dir / model_slug / "task_results.json").read_text(encoding="utf-8"))
    candidates: list[VisualEvalTarget] = []
    for row in task_results:
        task = tasks_by_id.get(row["task_id"])
        if task is None:
            continue
        if row.get("difficulty_level") == "depth":
            candidates.extend(
                _make_depth_step_targets(
                    row=row,
                    model_slug=model_slug,
                    task=task,
                    protocol_version=protocol_version,
                )
            )
            continue
        target = _make_single_turn_target(
            row=row,
            model_slug=model_slug,
            task=task,
            protocol_version=protocol_version,
        )
        if target is not None:
            candidates.append(target)
    return candidates


def _infer_sources_from_manifest(manifest: dict[str, Any]) -> list[str]:
    task_source = str(manifest.get("task_source", "")).strip()
    if task_source == "eval_data":
        return []
    if manifest.get("sources"):
        return list(manifest["sources"])
    selected_task_ids = manifest.get("selected_task_ids", []) or []
    inferred = []
    for task_id in selected_task_ids:
        parts = str(task_id).split("_", 2)
        if len(parts) >= 2 and parts[1] not in inferred:
            inferred.append(parts[1])
    return inferred


def _resolve_eval_data_path(results_dir: Path, manifest: dict[str, Any]) -> Path | None:
    eval_data = str(manifest.get("eval_data", "")).strip()
    if not eval_data:
        return None
    eval_path = Path(eval_data)
    if eval_path.exists():
        return eval_path
    fallback_paths = [
        results_dir / eval_path.name,
    ]
    for root in _iter_search_roots():
        fallback_paths.extend(
            [
                root / "results" / "0325_shiqi_food" / eval_path.name,
                root / "results" / eval_path.name,
                root / "data_generation_v3" / eval_path.name,
            ]
        )
    for candidate in fallback_paths:
        if candidate.exists():
            return candidate
    return None


def _resolve_task_manifest(results_dir: Path) -> tuple[Path | None, list[str], dict[str, Any]]:
    manifest = json.loads((results_dir / "task_sample_manifest.json").read_text(encoding="utf-8"))
    if str(manifest.get("task_source", "")).strip() == "eval_data":
        return _resolve_eval_data_path(results_dir, manifest), [], manifest
    task_dir = Path(manifest["task_dir"])
    candidates = [task_dir] if task_dir.is_absolute() else [results_dir / task_dir, _EVAL_ROOT / task_dir]
    for root in _iter_search_roots():
        candidates.extend([root / task_dir, root / "a2ui_tasks" / "eval" / task_dir.name])
    for candidate in candidates:
        if candidate.exists():
            task_dir = candidate
            break
    sources = _infer_sources_from_manifest(manifest)
    return task_dir, sources, manifest


def _make_product_eval_task_id(index: int, entry: dict[str, Any]) -> str:
    dialogue_id = str(entry.get("dialogue_id", "")).strip()
    turn_idx = int(entry.get("turn_idx", 1) or 1)
    return f"product_{index:05d}_{dialogue_id}_t{turn_idx}"


def _load_eval_data_tasks(eval_data_path: Path) -> dict[str, eval_api.TaskSample]:
    rows = json.loads(eval_data_path.read_text(encoding="utf-8"))
    tasks_by_id: dict[str, eval_api.TaskSample] = {}
    for index, row in enumerate(rows):
        prompt_conversation = list(row.get("prompt_conversation", []) or [])
        non_system = [msg for msg in prompt_conversation if str(msg.get("role", "")).strip() != "system"]
        user_message = ""
        dialogue_context: list[dict[str, str]] = []
        if non_system:
            last_msg = non_system[-1]
            if str(last_msg.get("role", "")).strip() == "user":
                user_message = str(last_msg.get("content", "")).strip()
                dialogue_context = [
                    {
                        "role": str(msg.get("role", "")).strip(),
                        "content": str(msg.get("content", "")).strip(),
                    }
                    for msg in non_system[:-1]
                    if str(msg.get("content", "")).strip()
                ]
            else:
                dialogue_context = [
                    {
                        "role": str(msg.get("role", "")).strip(),
                        "content": str(msg.get("content", "")).strip(),
                    }
                    for msg in non_system
                    if str(msg.get("content", "")).strip()
                ]
        metadata = dict(row.get("source_metadata", {}) or {})
        task_id = _make_product_eval_task_id(index, row)
        task = eval_api.TaskSample(
            task_id=task_id,
            source="product_eval",
            scenario_id="S5",
            intent_type="product_eval",
            difficulty_level="atomic",
            task_description=str(metadata.get("card_name", "") or row.get("dialogue_id", "")).strip(),
            user_message=user_message,
            dialogue_context=dialogue_context[-6:],
            expected_pattern="product_eval",
            gt_a2ui=[],
            gt_assistant_text="",
            completion_criteria=[],
            raw_context={"prompt_conversation": prompt_conversation},
            metadata=metadata,
            episode_turns=[],
            subgoals=[],
            domains=[str(metadata.get("skill", "")).strip()] if str(metadata.get("skill", "")).strip() else [],
        )
        tasks_by_id[task_id] = task
    return tasks_by_id


def _load_tasks_by_id(results_dir: Path) -> dict[str, eval_api.TaskSample]:
    task_dir, sources, manifest = _resolve_task_manifest(results_dir)
    if str(manifest.get("task_source", "")).strip() == "eval_data":
        if task_dir is None:
            raise RuntimeError(
                f"Unable to resolve eval_data for visual eval: {manifest.get('eval_data')}"
            )
        return _load_eval_data_tasks(task_dir)
    tasks = eval_api.load_task_samples(task_dir)
    if sources:
        allowed_sources = set(sources)
        tasks = [task for task in tasks if task.source in allowed_sources]
    return {task.task_id: task for task in tasks}


def _select_candidates(
    candidates: list[VisualEvalTarget],
    *,
    limit: int,
    selection: str,
    seed: int,
) -> list[VisualEvalTarget]:
    if limit <= 0:
      return []
    rng = random.Random(seed)
    pool = list(candidates)
    if selection == "random":
        rng.shuffle(pool)
        return pool[:limit]

    buckets: dict[str, list[VisualEvalTarget]] = {}
    for item in pool:
        buckets.setdefault(item.scenario_id, []).append(item)
    for items in buckets.values():
        items.sort(key=lambda x: (x.baseline_l2_mean + x.baseline_l3_mean, x.task_id))
    ordered: list[VisualEvalTarget] = []
    scenario_ids = sorted(buckets)
    while len(ordered) < limit:
        progressed = False
        for scenario_id in scenario_ids:
            bucket = buckets[scenario_id]
            if not bucket:
                continue
            ordered.append(bucket.pop())
            progressed = True
            if len(ordered) >= limit:
                break
        if not progressed:
            break
    return ordered


def _build_render_url(
    render_url: str,
    *,
    a2ui_messages: list[dict[str, Any]],
    stage_width: int,
    stage_max_height: int,
) -> str:
    query = urlencode(
        {
            "a2ui": json.dumps(a2ui_messages, ensure_ascii=False, separators=(",", ":")),
            "maxWidth": str(stage_width),
            "maxHeight": str(stage_max_height),
            "padding": "24",
        }
    )
    separator = "&" if "?" in render_url else "?"
    return f"{render_url}{separator}{query}"


def _screenshot_rendered_ui(
    render_url: str,
    *,
    a2ui_messages: list[dict[str, Any]],
    output_path: Path,
    viewport_width: int,
    viewport_height: int,
    stage_width: int,
    stage_max_height: int,
    timeout_ms: int,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    target_url = _build_render_url(
        render_url,
        a2ui_messages=a2ui_messages,
        stage_width=stage_width,
        stage_max_height=stage_max_height,
    )
    cmd = [
        "npx",
        "playwright",
        "screenshot",
        "--browser",
        "chromium",
        "--viewport-size",
        f"{viewport_width},{viewport_height}",
        "--wait-for-selector",
        "body[data-render-status=\"ready\"]",
        "--wait-for-timeout",
        "400",
        "--timeout",
        str(timeout_ms),
        "--full-page",
        target_url,
        str(output_path),
    ]
    subprocess.run(cmd, check=True)
    _crop_screenshot_to_stage(output_path)


def _crop_screenshot_to_stage(image_path: Path, *, tolerance: int = 6, margin: int = 10) -> None:
    """Trim page background so the screenshot focuses on the preview stage.

    The render page is captured with a full-page screenshot to preserve long
    UIs, but for short UIs that leaves large page-background whitespace below
    the stage. We crop to the bounding box of pixels that differ from the page
    background, keeping a small margin so the card border/shadow is retained.
    """
    try:
        from PIL import Image
    except ModuleNotFoundError as exc:  # pragma: no cover - optional dependency path
        raise ModuleNotFoundError(
            "visual_eval.py requires Pillow. Install optional visual dependencies "
            "with `pip install -r requirements-visual.txt`."
        ) from exc

    with Image.open(image_path) as image:
        rgb = image.convert("RGB")
        width, height = rgb.size
        if width <= 0 or height <= 0:
            return

        samples = [
            rgb.getpixel((0, 0)),
            rgb.getpixel((width - 1, 0)),
            rgb.getpixel((0, height - 1)),
            rgb.getpixel((width - 1, height - 1)),
            rgb.getpixel((width // 2, 0)),
            rgb.getpixel((width // 2, height - 1)),
        ]
        page_bg = max(set(samples), key=samples.count)
        pixels = rgb.load()

        def is_bg(x: int, y: int) -> bool:
            pixel = pixels[x, y]
            return all(abs(int(pixel[i]) - int(page_bg[i])) <= tolerance for i in range(3))

        top = 0
        while top < height and all(is_bg(x, top) for x in range(width)):
            top += 1
        if top >= height:
            return

        bottom = height - 1
        while bottom >= 0 and all(is_bg(x, bottom) for x in range(width)):
            bottom -= 1

        left = 0
        while left < width and all(is_bg(left, y) for y in range(top, bottom + 1)):
            left += 1

        right = width - 1
        while right >= 0 and all(is_bg(right, y) for y in range(top, bottom + 1)):
            right -= 1

        if left >= right or top >= bottom:
            return

        crop_box = (
            max(0, left - margin),
            max(0, top - margin),
            min(width, right + margin + 1),
            min(height, bottom + margin + 1),
        )
        cropped = rgb.crop(crop_box)
        cropped.save(image_path)


def _extract_json_object(text: str) -> dict[str, Any] | None:
    return eval_api._extract_json_object(text)


def _build_judge_request_kwargs(client: OpenAI) -> dict[str, Any]:
    base_url = str(getattr(client, "base_url", "")).lower()
    if "openrouter.ai" not in base_url:
        return {}
    # Suppress reasoning-token output on OpenRouter so reasoning-heavy VLMs
    # still return the structured JSON payload in `message.content`.
    return {
        "extra_body": {
            "reasoning": {
                "effort": "none",
                "exclude": True,
            }
        }
    }


def _judge_prompt(
    task: eval_api.TaskSample,
    text_response: str,
    *,
    dialogue_context: list[dict[str, str]] | None = None,
    user_message: str | None = None,
    step_idx: int | None = None,
    step_count: int | None = None,
    protocol_version: str = DEFAULT_PROTOCOL_VERSION,
) -> str:
    dialogue_context = dialogue_context if dialogue_context is not None else task.dialogue_context
    user_message = user_message if user_message is not None else task.user_message
    step_line = ""
    if step_idx is not None and step_count is not None:
        step_line = f"- Trajectory step: {step_idx + 1}/{step_count}\n"
    if protocol_version == "0.9.1":
        protocol_line = (
            "This evaluation uses A2UI protocol v0.9.1. "
            "Expect flat component names (Text, Button, ChoicePicker, TextField, etc.). "
            "Do not expect or prefer 0.8-only names/shapes such as SelectionList, Label, "
            "key-wrapped components, or beginRendering/surfaceUpdate."
        )
    else:
        protocol_line = (
            "This evaluation uses A2UI protocol v0.8. "
            "Components may use 0.8 key-wrapped shapes and catalog names."
        )
    return f"""You are a strict multimodal UI judge.

Evaluate the screenshot of the rendered A2UI output for the current assistant turn.
{protocol_line}
Be conservative and visually strict. Do not assume hidden content is fine just because the task sounds good.
Judge only what is visibly shown in the screenshot.

Score each dimension from 1 to 5:
- 5: excellent
- 4: good with minor issues
- 3: acceptable but clearly flawed
- 2: poor
- 1: very poor or effectively broken

Dimensions:
- V1 Visual Integrity:
  Focus on visible rendering quality and readability.
  Check whether the UI is legible, well-bounded, and visually stable.
  Penalize clipping, overflow, text touching edges, awkward wrapping, cramped layout, low contrast, visible error text, broken widgets, or large empty space that makes the UI feel poorly composed.
- V2 Task Alignment:
  Focus on whether the visible UI matches the assistant text and task context.
  Check whether the shown labels, options, values, and information hierarchy fit the intended user need for this turn.
  Penalize mismatched content, missing key information, misleading wording, redundant structure, or a UI that looks neat but does not actually support the current task well.
- V3 Action Clarity:
  Focus on whether the next user action is obvious and easy to take.
  Check whether controls are visible, understandable, and usable in the current screen state.
  Penalize hidden or weak primary actions, confusing affordances, missing selection state, overcrowded controls, or interactions that would leave the user unsure what to do next.

Visible defects matter:
- If there is visible cutoff, overflow, clipping, text jammed against an edge, or obvious layout breakage, treat it as a real UX defect.
- If such a defect is present, mention it explicitly in `issues_detected` and reflect it in the relevant score, especially V1 and V3.

Task info:
- Protocol version: {protocol_version}
- Scenario: {task.scenario_id} {eval_api.SCENARIO_DEFS[task.scenario_id]}
{step_line}- Difficulty: {task.difficulty_level}
- Task description: {task.task_description}
- Dialogue context:
{eval_api._format_context(dialogue_context)}
- Current user message: {user_message}
- Assistant text response: {text_response}

Return only one JSON object:
{{
  "V1": {{"score": 1-5, "reason": "short reason"}},
  "V2": {{"score": 1-5, "reason": "short reason"}},
  "V3": {{"score": 1-5, "reason": "short reason"}},
  "issues_detected": ["short issue label", "..."],
  "overall_note": "one short summary"
}}
"""


def _validate_visual_obj(obj: Any) -> tuple[bool, str]:
    if not isinstance(obj, dict):
        return False, "not_a_dict"
    for dim in VISUAL_DIMS:
        cell = obj.get(dim)
        if not isinstance(cell, dict):
            return False, f"missing_dim:{dim}"
        try:
            score = float(cell["score"])
        except Exception:
            return False, f"invalid_score:{dim}"
        if score < 1 or score > 5:
            return False, f"out_of_range:{dim}"
    return True, ""


def _judge_visual(
    client: OpenAI,
    *,
    vlm_model: str,
    task: eval_api.TaskSample,
    target: VisualEvalTarget,
    text_response: str,
    screenshot_path: Path,
    protocol_version: str = DEFAULT_PROTOCOL_VERSION,
) -> dict[str, Any]:
    image_b64 = base64.b64encode(screenshot_path.read_bytes()).decode("ascii")
    prompt = _judge_prompt(
        task,
        text_response,
        dialogue_context=target.dialogue_context,
        user_message=target.user_message,
        step_idx=target.step_idx,
        step_count=target.step_count,
        protocol_version=protocol_version,
    )
    base_messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{image_b64}",
                    },
                },
            ],
        }
    ]
    last_raw = ""
    request_kwargs = _build_judge_request_kwargs(client)
    for attempt in range(3):
        messages = list(base_messages)
        if attempt > 0:
            messages.append(
                {
                    "role": "user",
                    "content": (
                        "Your previous answer was invalid or incomplete. "
                        "Return one JSON object only. Include V1, V2, V3, "
                        "each with numeric score and short reason, plus "
                        "issues_detected and overall_note."
                    ),
                }
            )
        response = client.chat.completions.create(
            model=vlm_model,
            temperature=0.0,
            max_tokens=900,
            messages=messages,
            **request_kwargs,
        )
        raw_text = response.choices[0].message.content or ""
        last_raw = raw_text
        parsed = _extract_json_object(raw_text)
        if parsed is None:
            continue
        valid, _ = _validate_visual_obj(parsed)
        if valid:
            return parsed
    raise RuntimeError(f"VLM judge returned invalid JSON payload: {last_raw[:800]}")


def _normalize_visual_result(obj: dict[str, Any]) -> dict[str, Any]:
    scores: dict[str, float] = {}
    reasons: dict[str, str] = {}
    for dim in VISUAL_DIMS:
        cell = obj.get(dim)
        if not isinstance(cell, dict):
            raise RuntimeError(f"Missing visual judge dimension: {dim}")
        score = float(cell["score"])
        if score < 1 or score > 5:
            raise RuntimeError(f"Out-of-range score for {dim}: {score}")
        scores[dim] = score
        reasons[dim] = str(cell.get("reason", "")).strip()[:300]
    issues_detected = obj.get("issues_detected", [])
    normalized_issues = []
    if isinstance(issues_detected, list):
        normalized_issues = [str(x).strip()[:120] for x in issues_detected if str(x).strip()]
    return {
        "scores": scores,
        "reasons": reasons,
        "mean": _mean(list(scores.values())),
        "issues_detected": normalized_issues,
        "overall_note": str(obj.get("overall_note", "")).strip()[:500],
    }


def _build_summary(
    *,
    args: argparse.Namespace,
    run_rows: list[dict[str, Any]],
    error_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    judged_rows = [row for row in run_rows if row.get("visual_eval")]
    summary = {
        "model_slug": args.model_slug,
        "protocol_version": args.protocol_version,
        "num_samples": len(run_rows),
        "num_judged": len(judged_rows),
        "num_errors": len(error_rows),
        "judge_skipped": bool(args.skip_judge),
        "vlm_model": None if args.skip_judge else args.vlm_model,
        "render_url": args.render_url,
        "avg_baseline_l2_mean": _mean([row["baseline_l2_mean"] for row in run_rows]),
        "avg_baseline_l3_mean": _mean([row["baseline_l3_mean"] for row in run_rows]),
    }
    if judged_rows:
        summary["avg_visual_mean"] = _mean([row["visual_eval"]["mean"] for row in judged_rows])
        summary["avg_visual_dims"] = {
            dim: _mean([row["visual_eval"]["scores"][dim] for row in judged_rows])
            for dim in VISUAL_DIMS
        }
    return summary


def _build_run_row(
    *,
    target: VisualEvalTarget,
    screenshot_path: Path,
    skip_judge: bool,
) -> dict[str, Any]:
    return {
        "task_id": target.task_id,
        "target_id": target.target_id,
        "scenario_id": target.scenario_id,
        "difficulty_level": target.difficulty_level,
        "model_slug": target.model_slug,
        "user_message": target.user_message,
        "dialogue_context": target.dialogue_context,
        "step_idx": target.step_idx,
        "step_count": target.step_count,
        "screenshot_path": str(screenshot_path),
        "baseline_l2_mean": target.baseline_l2_mean,
        "baseline_l3_mean": target.baseline_l3_mean,
        "visual_eval": None,
        "judge_status": "skipped" if skip_judge else "pending",
        "text_response": target.text_response,
        "a2ui_messages": target.a2ui_messages,
    }


def main() -> None:
    _setup_env()
    args = _parse_args()
    if not args.render_url:
        args.render_url = default_render_url_for_protocol(args.protocol_version)
    results_dir = eval_api.resolve_output_dir(Path(args.results_dir), args.protocol_version)
    api_key = (
        args.judge_api_key
        or os.environ.get("OPENROUTER_API_KEY")
        or os.environ.get("OPENAI_API_KEY")
    )
    if not args.skip_judge and not api_key:
        raise RuntimeError("Missing API key. Set OPENROUTER_API_KEY or pass --judge-api-key.")

    tasks_by_id = _load_tasks_by_id(results_dir)
    candidates = _load_candidates(
        results_dir,
        args.model_slug,
        tasks_by_id,
        protocol_version=args.protocol_version,
    )
    selected = _select_candidates(
        candidates,
        limit=args.limit,
        selection=args.selection,
        seed=args.seed,
    )
    if not selected:
        raise RuntimeError("No eligible visual evaluation samples found.")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = args.output_dir or (
        results_dir / f"visual_eval_{args.model_slug}_{timestamp}"
    )
    screenshots_dir = output_dir / "screenshots"
    output_dir.mkdir(parents=True, exist_ok=True)

    client = None if args.skip_judge else OpenAI(api_key=api_key, base_url=args.vlm_base_url)
    run_rows: list[dict[str, Any]] = []
    error_rows: list[dict[str, Any]] = []

    print(
        "Running minimal visual eval:",
        {
            "model_slug": args.model_slug,
            "protocol_version": args.protocol_version,
            "targets": len(selected),
            "render_url": args.render_url,
            "results_dir": str(results_dir),
            "vlm_model": None if args.skip_judge else args.vlm_model,
            "output_dir": str(output_dir),
            "skip_judge": args.skip_judge,
            "max_workers": args.max_workers,
        },
    )

    if args.skip_judge and args.max_workers > 1:
        print(f"Using parallel screenshot workers: {args.max_workers}")
        indexed_rows: list[tuple[int, dict[str, Any]]] = []
        with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
            future_map = {}
            for idx, target in enumerate(selected, start=1):
                task = tasks_by_id.get(target.task_id)
                if task is None:
                    raise RuntimeError(f"Task not found in manifest task_dir: {target.task_id}")
                screenshot_path = screenshots_dir / f"{idx:02d}_{target.target_id}.png"
                print(f"[queue {idx}/{len(selected)}] screenshot {target.target_id} -> {screenshot_path.name}")
                future = executor.submit(
                    _screenshot_rendered_ui,
                    args.render_url,
                    a2ui_messages=target.a2ui_messages,
                    output_path=screenshot_path,
                    viewport_width=args.viewport_width,
                    viewport_height=args.viewport_height,
                    stage_width=args.stage_width,
                    stage_max_height=args.stage_max_height,
                    timeout_ms=args.screenshot_timeout_ms,
                )
                future_map[future] = (idx, target, screenshot_path)
            completed = 0
            for future in as_completed(future_map):
                idx, target, screenshot_path = future_map[future]
                try:
                    future.result()
                    indexed_rows.append(
                        (
                            idx,
                            _build_run_row(
                                target=target,
                                screenshot_path=screenshot_path,
                                skip_judge=True,
                            ),
                        )
                    )
                    completed += 1
                    print(f"[done {completed}/{len(selected)}] {target.target_id} -> {screenshot_path.name}")
                except Exception as exc:
                    completed += 1
                    error_rows.append(
                        {
                            "task_id": target.task_id,
                            "target_id": target.target_id,
                            "scenario_id": target.scenario_id,
                            "screenshot_path": str(screenshot_path),
                            "error": str(exc),
                        }
                    )
                    print(f"[error {completed}/{len(selected)}] {target.target_id}: {exc}")
        run_rows = [row for _, row in sorted(indexed_rows, key=lambda item: item[0])]
    else:
        for idx, target in enumerate(selected, start=1):
            task = tasks_by_id.get(target.task_id)
            if task is None:
                raise RuntimeError(f"Task not found in manifest task_dir: {target.task_id}")
            screenshot_path = screenshots_dir / f"{idx:02d}_{target.target_id}.png"
            print(f"[{idx}/{len(selected)}] screenshot {target.target_id} -> {screenshot_path.name}")
            try:
                _screenshot_rendered_ui(
                    args.render_url,
                    a2ui_messages=target.a2ui_messages,
                    output_path=screenshot_path,
                    viewport_width=args.viewport_width,
                    viewport_height=args.viewport_height,
                    stage_width=args.stage_width,
                    stage_max_height=args.stage_max_height,
                    timeout_ms=args.screenshot_timeout_ms,
                )
            except Exception as exc:
                error_rows.append(
                    {
                        "task_id": target.task_id,
                        "target_id": target.target_id,
                        "scenario_id": target.scenario_id,
                        "screenshot_path": str(screenshot_path),
                        "error": str(exc),
                    }
                )
                print(f"[error {idx}/{len(selected)}] {target.target_id}: {exc}")
                continue
            row = _build_run_row(
                target=target,
                screenshot_path=screenshot_path,
                skip_judge=args.skip_judge,
            )
            if not args.skip_judge:
                try:
                    judged = _judge_visual(
                        client,
                        vlm_model=args.vlm_model,
                        task=task,
                        target=target,
                        text_response=target.text_response,
                        screenshot_path=screenshot_path,
                        protocol_version=args.protocol_version,
                    )
                    row["visual_eval"] = _normalize_visual_result(judged)
                    row["judge_status"] = "ok"
                except Exception as exc:
                    row["judge_status"] = "error"
                    error_rows.append(
                        {
                            "task_id": target.task_id,
                            "target_id": target.target_id,
                            "scenario_id": target.scenario_id,
                            "screenshot_path": str(screenshot_path),
                            "error": str(exc),
                        }
                    )
                    if not args.continue_on_judge_error:
                        run_rows.append(row)
                        raise
            run_rows.append(row)

    summary = _build_summary(args=args, run_rows=run_rows, error_rows=error_rows)

    (output_dir / "results.json").write_text(
        json.dumps(run_rows, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (output_dir / "errors.json").write_text(
        json.dumps(error_rows, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
