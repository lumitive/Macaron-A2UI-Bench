#!/usr/bin/env python3
"""Build a fixed-size evaluation split from the bundled source tasks."""

from __future__ import annotations

import argparse
import json
import math
import random
from collections import defaultdict
from pathlib import Path
from typing import Any


_EVAL_ROOT = Path(__file__).resolve().parent


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


def _find_nearby_dir(name: str) -> Path | None:
    for root in _iter_search_roots():
        candidate = root / name
        if candidate.exists():
            return candidate
    return None


DEFAULT_INPUT_DIR = _EVAL_ROOT / "data" / "source"
DEFAULT_OUTPUT_DIR = _EVAL_ROOT / "data" / "eval_300"
DEFAULT_SOURCES = ["annomi", "esconv", "multiwoz", "sgd"]
DEFAULT_DIFFICULTIES = ["atomic", "depth", "width"]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare an A2UI benchmark evaluation split.")
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--per-difficulty", type=int, default=100)
    parser.add_argument("--sources", nargs="+", default=DEFAULT_SOURCES)
    parser.add_argument("--difficulties", nargs="+", default=DEFAULT_DIFFICULTIES)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def _load_tasks(path: Path) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def _manifest_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return f"./{resolved.relative_to(_EVAL_ROOT).as_posix()}"
    except ValueError:
        return str(path)


def _largest_remainder_allocation(counts: dict[bool, int], quota: int) -> dict[bool, int]:
    total = sum(counts.values())
    if total <= 0:
        return {key: 0 for key in counts}
    raw = {key: quota * value / total for key, value in counts.items()}
    base = {key: min(counts[key], math.floor(value)) for key, value in raw.items()}
    assigned = sum(base.values())
    remainders = sorted(
        ((raw[key] - base[key], key) for key in counts),
        reverse=True,
    )
    idx = 0
    while assigned < quota and idx < len(remainders):
        _, key = remainders[idx]
        if base[key] < counts[key]:
            base[key] += 1
            assigned += 1
        idx += 1
        if idx == len(remainders) and assigned < quota:
            idx = 0
            if all(base[key] >= counts[key] for key in counts):
                break
    return base


def _sample_bucket(
    items: list[dict[str, Any]],
    quota: int,
    rng: random.Random,
) -> list[dict[str, Any]]:
    if quota > len(items):
        raise ValueError(f"Quota {quota} exceeds bucket size {len(items)}.")
    by_label: dict[bool, list[dict[str, Any]]] = defaultdict(list)
    for item in items:
        by_label[bool(item.get("is_positive", True))].append(item)
    if len(by_label) <= 1:
        pool = list(items)
        rng.shuffle(pool)
        return pool[:quota]

    allocations = _largest_remainder_allocation(
        {label: len(bucket) for label, bucket in by_label.items()},
        quota,
    )
    sampled: list[dict[str, Any]] = []
    for label in sorted(by_label, reverse=True):
        pool = list(by_label[label])
        rng.shuffle(pool)
        sampled.extend(pool[: allocations[label]])
    rng.shuffle(sampled)
    return sampled


def main() -> None:
    args = _parse_args()
    rng = random.Random(args.seed)

    if args.per_difficulty % len(args.sources) != 0:
        raise ValueError("--per-difficulty must be divisible by number of sources.")
    per_source_quota = args.per_difficulty // len(args.sources)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, Any] = {
        "input_dir": _manifest_path(args.input_dir),
        "output_dir": _manifest_path(args.output_dir),
        "seed": args.seed,
        "per_difficulty": args.per_difficulty,
        "per_source_quota": per_source_quota,
        "sources": args.sources,
        "difficulties": args.difficulties,
        "files": {},
    }

    total_selected = 0
    for source in args.sources:
        input_path = args.input_dir / f"{source}_tasks.json"
        if not input_path.exists():
            raise FileNotFoundError(f"Missing source file: {input_path}")
        tasks = _load_tasks(input_path)
        selected_for_source: list[dict[str, Any]] = []
        file_summary: dict[str, Any] = {}
        for difficulty in args.difficulties:
            bucket = [task for task in tasks if task.get("difficulty_level") == difficulty]
            if len(bucket) < per_source_quota:
                raise ValueError(
                    f"Source={source} difficulty={difficulty} has only {len(bucket)} items, "
                    f"need {per_source_quota}."
                )
            sampled = _sample_bucket(bucket, per_source_quota, rng)
            selected_for_source.extend(sampled)
            file_summary[difficulty] = {
                "available": len(bucket),
                "selected": len(sampled),
                "positive": sum(1 for item in sampled if item.get("is_positive", True)),
                "negative": sum(1 for item in sampled if not item.get("is_positive", True)),
            }
        selected_for_source.sort(key=lambda item: (item.get("difficulty_level", ""), item.get("task_id", "")))
        output_path = args.output_dir / f"{source}_tasks.json"
        output_path.write_text(json.dumps(selected_for_source, ensure_ascii=False, indent=2), encoding="utf-8")
        manifest["files"][source] = file_summary
        total_selected += len(selected_for_source)

    manifest["total_selected"] = total_selected
    (args.output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
