"""Track 3: L2 hints versioning, full prompt, gold keep/strip."""

from __future__ import annotations

import json
from pathlib import Path

from evaluate_api_model import (
    L2_RUBRIC_HINTS_0_8,
    L2_RUBRIC_HINTS_0_9_1,
    _build_l2_rubric_hints,
    filter_episode_gt_a2ui,
    resolve_generation_guide,
    strip_episode_gt_a2ui,
)
from protocol import get_protocol_stack
from protocol.v0_9_1.lint import LOCKED_CATALOG_ID, validate

ROOT = Path(__file__).parents[2]
EVAL_300 = ROOT / "data" / "eval_300"


def test_l2_hints_091_use_updateDataModel_not_dataModelUpdate():
    blob = json.dumps(L2_RUBRIC_HINTS_0_9_1)
    assert "updateDataModel" in blob
    assert "dataModelUpdate" not in blob
    # 0.8 path still uses legacy term
    assert "dataModelUpdate" in json.dumps(L2_RUBRIC_HINTS_0_8)

    text_091 = _build_l2_rubric_hints("S3", "0.9.1")
    assert "updateDataModel" in text_091
    assert "dataModelUpdate" not in text_091


def test_resolve_generation_guide_full_091_mentions_catalogId():
    stack = get_protocol_stack("0.9.1")
    guide = resolve_generation_guide(prompt_mode="full", stack=stack)
    assert guide
    assert "catalogId" in guide
    assert "createSurface" in guide
    assert "updateDataModel" in guide
    assert "ChoicePicker" in guide
    assert stack.catalog_id in guide


def test_filter_keeps_valid_091_gold_strips_08():
    stack = get_protocol_stack("0.9.1")
    valid = [
        {
            "version": "v0.9.1",
            "createSurface": {
                "surfaceId": "main",
                "catalogId": LOCKED_CATALOG_ID,
            },
        },
        {
            "version": "v0.9.1",
            "updateComponents": {
                "surfaceId": "main",
                "components": [
                    {"id": "root", "component": "Column", "children": ["t"]},
                    {"id": "t", "component": "Text", "text": "hi"},
                ],
            },
        },
    ]
    legacy = [{"surfaceUpdate": {"surfaceId": "main", "components": []}}]
    turns = [
        {"user_message": "a", "gt_a2ui": valid},
        {"user_message": "b", "gt_a2ui": legacy},
        {"user_message": "c"},
    ]
    filtered = filter_episode_gt_a2ui(turns, validate_fn=stack.validate)
    assert filtered[0].get("gt_a2ui") == valid
    assert "gt_a2ui" not in filtered[1]
    assert "gt_a2ui" not in filtered[2]
    # unconditional strip still removes everything
    stripped = strip_episode_gt_a2ui(turns)
    assert "gt_a2ui" not in stripped[0]


def test_gold_subset_retained_count_and_scenarios():
    """Asserting floor for D5=1 / Product MVP scenario tags."""
    subset_doc = (ROOT / "docs" / "gold-v091-subset.md").read_text(encoding="utf-8")
    assert "depth_esconv_0e86e8a3" in subset_doc

    retained = 0
    scenarios: set[str] = set()
    for path in sorted(EVAL_300.glob("*_tasks.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        for task in data:
            if task.get("difficulty_level") != "depth":
                continue
            sid = (task.get("metadata") or {}).get("scenario_id")
            turns = (task.get("context") or {}).get("episode_turns") or []
            filtered = filter_episode_gt_a2ui(turns, validate_fn=validate)
            for turn in filtered:
                if turn.get("gt_a2ui"):
                    retained += 1
                    if sid:
                        scenarios.add(sid)
                    assert validate(turn["gt_a2ui"]).is_valid

    assert retained >= 15, retained
    assert len(scenarios) >= 3, scenarios
