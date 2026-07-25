#!/usr/bin/env python3
"""Asserting recompute for docs/compatibility-scorecard.md.

Exit 0 only when algorithm smoke predicates hold AND computed Di match the
claimed baseline (unless --report-only).

Requires project deps for D6b=2 (``jsonschema`` / ``referencing`` from
requirements.txt). Prefer:

  PYTHONPATH=. .venv/bin/python scripts/scorecard_recompute.py
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASIC_CATALOG = ROOT / "protocol/v0_9_1/spec/catalogs/basic/catalog.json"
LUMI_CATALOG = ROOT / "protocol/v0_9_1/spec/catalogs/lumi/catalog.json"
LUMI_INVENTORY = ROOT / "docs/lumi-catalog-inventory.md"
PIN = ROOT / "protocol/v0_9_1/UPSTREAM_PIN.txt"
FIXTURES = ROOT / "protocol/v0_9_1/fixtures"
EVAL_PY = ROOT / "evaluate_api_model.py"
GOLD_DOC = ROOT / "docs/gold-v091-subset.md"
SCHEMA_MOD = ROOT / "protocol/v0_9_1/schema_validate.py"
SCHEMA_TEST = ROOT / "tests/protocol/test_v0_9_1_schema.py"
LOCKED = "https://a2ui.org/specification/v0_9/catalogs/basic/catalog.json"
LUMI_ID = "lumi.ai:a2ui:lumi-catalog"

BASELINE = {
    "D1": 1,
    "D2": 1,
    "D3": 1,
    "D4": 1,
    "D5": 1,
    "D6a": 2,
    "D6b": 2,
    "D7": 2,
    "D8": 0,
}


def score_d1() -> tuple[int, list[str]]:
    errs: list[str] = []
    text = EVAL_PY.read_text(encoding="utf-8")
    if 'default="0.9.1"' not in text and "default='0.9.1'" not in text:
        errs.append("D1: evaluate_api_model default is not 0.9.1")
    if 'choices=["0.8", "0.9.1"]' not in text and "choices=['0.8', '0.9.1']" not in text:
        errs.append("D1: protocol version choices missing 0.8|0.9.1")
    if not PIN.is_file() or not PIN.read_text(encoding="utf-8").strip():
        errs.append("D1: missing protocol/v0_9_1/UPSTREAM_PIN.txt")
    fixtures = list(FIXTURES.glob("*.json"))
    if len(fixtures) < 4:
        errs.append(f"D1: need ≥4 fixtures, found {len(fixtures)}")
    if errs:
        return 0, errs
    # D1=2 needs delete + incremental ≥2-turn + multi-surface policy suite
    return 1, []


def score_d2() -> tuple[int, list[str]]:
    errs: list[str] = []
    if not BASIC_CATALOG.is_file():
        return 0, ["D2: basic catalog missing"]
    cat = json.loads(BASIC_CATALOG.read_text(encoding="utf-8"))
    if cat.get("catalogId") != LOCKED:
        errs.append(f"D2: catalogId unlocked or unexpected: {cat.get('catalogId')!r}")
    n = len(cat.get("components") or {})
    if n != 18:
        errs.append(f"D2: expected 18 component types, got {n}")
    if errs:
        return 0, errs
    return 1, []


def score_d3() -> tuple[int, list[str]]:
    if not LUMI_CATALOG.is_file():
        return 0, []
    errs: list[str] = []
    cat = json.loads(LUMI_CATALOG.read_text(encoding="utf-8"))
    if cat.get("catalogId") != LUMI_ID:
        errs.append(f"D3: catalogId must be {LUMI_ID}")
    if not LUMI_INVENTORY.is_file():
        errs.append("D3: missing docs/lumi-catalog-inventory.md")
    else:
        inv = LUMI_INVENTORY.read_text(encoding="utf-8")
        if "lumi_unique" not in inv and "LUMI-unique" not in inv and "lumi-unique" not in inv:
            errs.append("D3: inventory must classify lumi_unique")
        if "map_basic" not in inv and "mappable" not in inv.lower():
            errs.append("D3: inventory must document map_basic / mappable aliases")
    comps = cat.get("components") or {}
    if "Carousel" not in comps:
        errs.append("D3: MVP requires authored lumi_unique Carousel in catalog")
    if len(comps) < 19:  # basic 18 + Carousel
        errs.append(f"D3: expected basic supersets + unique (≥19), got {len(comps)}")
    if errs:
        # Partial asset present but bar unmet ⇒ still 0 (fail-closed)
        return 0, errs
    return 1, []


def score_d4() -> tuple[int, list[str]]:
    tests = list((ROOT / "tests/protocol").glob("test_v0_9_1_lumi_*.py"))
    fixture = ROOT / "protocol/v0_9_1/fixtures/lumi/ok_carousel.json"
    if not tests or not fixture.is_file():
        return 0, []
    return 1, []


def _count_retained_depth_gold() -> tuple[int, set[str]]:
    """Count 0.9.1-valid retained depth gt_a2ui turns + scenario tags.

    Uses protocol lint only (no evaluate_api_model — avoids openai dep).
    """
    sys.path.insert(0, str(ROOT))
    from protocol.v0_9_1.lint import validate

    retained = 0
    scenarios: set[str] = set()
    eval_dir = ROOT / "data" / "eval_300"
    for path in sorted(eval_dir.glob("*_tasks.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        for task in data:
            if task.get("difficulty_level") != "depth":
                continue
            sid = (task.get("metadata") or {}).get("scenario_id")
            turns = (task.get("context") or {}).get("episode_turns") or []
            for turn in turns:
                gt = turn.get("gt_a2ui")
                if not gt:
                    continue
                try:
                    result = validate(gt)
                    ok = bool(getattr(result, "is_valid", False))
                except Exception:
                    ok = False
                if ok:
                    retained += 1
                    if sid:
                        scenarios.add(str(sid))
    return retained, scenarios


def score_d5() -> tuple[int, list[str]]:
    errs: list[str] = []
    if not GOLD_DOC.is_file():
        return 0, ["D5: missing docs/gold-v091-subset.md"]
    retained, scenarios = _count_retained_depth_gold()
    if retained < 15:
        errs.append(f"D5: need ≥15 retained validating gold turns, got {retained}")
        return 0, errs
    # D5=1 bar met; Product MVP floors (≥3 scenarios) recorded as note if unmet
    if len(scenarios) < 3:
        errs.append(
            f"D5: note — Product MVP floor wants ≥3 scenario_id, got {sorted(scenarios)}"
        )
    return 1, errs


def score_d6a() -> tuple[int, list[str]]:
    text = EVAL_PY.read_text(encoding="utf-8")
    if "prompt_mode=full is not supported with protocol_version=0.9.1" in text:
        return 0, []
    if "_build_full_generation_guide_091" not in text:
        return 1, ["D6a: full guide assembler missing (score capped at 1)"]
    required = ("createSurface", "updateDataModel", "ChoicePicker", "catalogId")
    missing = [t for t in required if t not in text]
    if missing:
        return 1, [f"D6a: full-path text missing tokens: {missing}"]
    return 2, []


def score_d6b() -> tuple[int, list[str]]:
    errs: list[str] = []
    if not SCHEMA_TEST.is_file():
        return 0, ["D6b: missing tests/protocol/test_v0_9_1_schema.py"]
    if not SCHEMA_MOD.is_file():
        return 0, ["D6b: missing protocol/v0_9_1/schema_validate.py"]
    diag = (ROOT / "protocol/v0_9_1/diagnostics.py").read_text(encoding="utf-8")
    if "DATA_TYPE_MISMATCH" not in diag:
        return 1, ["D6b: DATA_TYPE_MISMATCH missing (cap 1)"]
    # Probe: deliberate bad prop must fail
    sys.path.insert(0, str(ROOT))
    from protocol.v0_9_1.lint import validate

    bad = [
        {
            "version": "v0.9.1",
            "createSurface": {"surfaceId": "main", "catalogId": LOCKED},
        },
        {
            "version": "v0.9.1",
            "updateComponents": {
                "surfaceId": "main",
                "components": [
                    {"id": "root", "component": "Column", "children": ["t"]},
                    {"id": "t", "component": "Text", "text": 999},
                ],
            },
        },
    ]
    result = validate(bad)
    codes = {d.code.value for d in result.errors}
    if result.is_valid or not (codes & {"DATA_TYPE_MISMATCH", "DATA_BINDING_INVALID"}):
        errs.append("D6b: bad-prop probe did not fail with DATA_*")
        return 1, errs
    return 2, []


def score_d7() -> tuple[int, list[str]]:
    judge = ROOT / "prompts/l2_judge_v091.txt"
    if not judge.is_file():
        return 0, ["D7: missing prompts/l2_judge_v091.txt"]
    text = EVAL_PY.read_text(encoding="utf-8")
    if "L2_RUBRIC_HINTS_0_9_1" not in text:
        return 1, ["D7: missing versioned L2_RUBRIC_HINTS_0_9_1"]
    # Extract 0.9.1 hints block: from assignment to next top-level assignment/comment
    m = re.search(
        r"L2_RUBRIC_HINTS_0_9_1\s*=\s*\{(.*?)\n\}\n",
        text,
        flags=re.DOTALL,
    )
    if not m:
        return 1, ["D7: could not parse L2_RUBRIC_HINTS_0_9_1"]
    block = m.group(0)
    if "dataModelUpdate" in block:
        return 1, ["D7: stale dataModelUpdate remains in 0.9.1 hints"]
    if "updateDataModel" not in block:
        return 1, ["D7: updateDataModel missing from 0.9.1 hints"]
    return 2, []


def score_d8() -> tuple[int, list[str]]:
    return 0, []


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--report-only",
        action="store_true",
        help="Print computed scores; do not assert baseline match",
    )
    args = ap.parse_args()

    scorers = {
        "D1": score_d1,
        "D2": score_d2,
        "D3": score_d3,
        "D4": score_d4,
        "D5": score_d5,
        "D6a": score_d6a,
        "D6b": score_d6b,
        "D7": score_d7,
        "D8": score_d8,
    }
    computed: dict[str, int] = {}
    errors: list[str] = []
    for key, fn in scorers.items():
        val, errs = fn()
        computed[key] = val
        errors.extend(errs)

    oii = computed["D1"] + computed["D2"]
    lei = computed["D3"] + computed["D4"]
    edi = computed["D5"] + computed["D6a"] + computed["D6b"] + computed["D7"]
    eng = sum(computed.values())

    print("Scorecard recompute (asserting)")
    for k, v in computed.items():
        print(f"  {k}={v}")
    print(f"  OII={oii}/4  LEI={lei}/4  EDI={edi}/8  eng={eng}/18 (internal)")

    if errors:
        print("\nPredicate notes/failures:")
        for e in errors:
            print(f"  - {e}")

    if args.report_only:
        return 1 if any(e.startswith(("D1:", "D2:", "D7:")) for e in errors) else 0

    mismatch = {
        k: (computed[k], BASELINE[k]) for k in BASELINE if computed[k] != BASELINE[k]
    }
    if mismatch:
        print("\nBaseline mismatch (computed vs claimed):")
        for k, (got, want) in mismatch.items():
            print(f"  - {k}: computed={got} claimed={want}")
        return 1

    # Hard failures on D1/D2/D7 predicates even if score numbers match
    hard = [e for e in errors if e.startswith(("D1:", "D2:", "D7:"))]
    if hard:
        return 1

    print("\nGREEN: computed matches claimed baseline 2026-07-25")
    return 0


if __name__ == "__main__":
    sys.exit(main())
