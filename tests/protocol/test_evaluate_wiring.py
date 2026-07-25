"""Unit tests for evaluate_api_model protocol-stack wiring helpers.

No live API calls.
"""

from __future__ import annotations

from pathlib import Path

from evaluate_api_model import (
    _a2ui_summary,
    parse_args,
    resolve_output_dir,
    strip_episode_gt_a2ui,
)


def test_resolve_output_dir_appends_protocol_version(tmp_path: Path):
    base = tmp_path / "results"
    assert resolve_output_dir(base, "0.8") == base / "0.8"
    assert resolve_output_dir(base, "0.9.1") == base / "0.9.1"


def test_resolve_output_dir_noop_when_already_versioned(tmp_path: Path):
    base = tmp_path / "results" / "0.9.1"
    assert resolve_output_dir(base, "0.9.1") == base
    assert resolve_output_dir(tmp_path / "0.8", "0.8") == tmp_path / "0.8"


def test_strip_episode_gt_a2ui_removes_gold():
    turns = [
        {"user_message": "hi", "gt_a2ui": [{"surfaceUpdate": {}}], "intent_type": "ui"},
        {"user_message": "bye", "expected_pattern": "none"},
    ]
    cleaned = strip_episode_gt_a2ui(turns)
    assert "gt_a2ui" not in cleaned[0]
    assert cleaned[0]["user_message"] == "hi"
    assert cleaned[0]["intent_type"] == "ui"
    assert "gt_a2ui" not in cleaned[1]
    # Original untouched
    assert "gt_a2ui" in turns[0]


def test_a2ui_summary_includes_0_9_1_flat_components():
    messages = [
        {
            "version": "v0.9",
            "createSurface": {
                "surfaceId": "s1",
                "catalogId": "https://a2ui.org/specification/v0_9/catalogs/basic/catalog.json",
            },
        },
        {
            "version": "v0.9",
            "updateComponents": {
                "surfaceId": "s1",
                "components": [
                    {"id": "root", "component": "Text", "text": "hello"},
                ],
            },
        },
        {
            "version": "v0.9",
            "updateDataModel": {
                "surfaceId": "s1",
                "path": "/form",
                "value": {"name": "Ada", "count": 3},
            },
        },
    ]
    summary = _a2ui_summary(messages)
    assert summary != "(no A2UI messages)"
    assert "createSurface" in summary
    assert "updateComponents" in summary
    assert "Text" in summary
    assert "updateDataModel" in summary
    assert "path=/form" in summary
    assert "value_keys=" in summary
    assert "name" in summary
    assert "count" in summary


def test_a2ui_summary_updateDataModel_contents_fallback():
    """0.8-style contents[] on updateDataModel still summarizes by key."""
    messages = [
        {
            "updateDataModel": {
                "surfaceId": "s1",
                "contents": [{"key": "x"}, {"key": "y"}],
            }
        }
    ]
    summary = _a2ui_summary(messages)
    assert "updateDataModel" in summary
    assert "keys=" in summary
    assert "x" in summary
    assert "y" in summary


def test_a2ui_summary_still_handles_0_8_shapes():
    messages = [
        {"beginRendering": {"surfaceId": "s1"}},
        {
            "surfaceUpdate": {
                "surfaceId": "s1",
                "components": [{"id": "root", "component": {"Text": {"text": "hi"}}}],
            }
        },
        {"dataModelUpdate": {"surfaceId": "s1", "contents": [{"key": "a"}]}},
        {"deleteSurface": {"surfaceId": "s1"}},
    ]
    summary = _a2ui_summary(messages)
    assert "beginRendering" in summary
    assert "surfaceUpdate" in summary
    assert "Text" in summary
    assert "dataModelUpdate" in summary
    assert "deleteSurface" in summary


def test_protocol_version_cli_default_is_0_9_1(monkeypatch):
    monkeypatch.setattr("sys.argv", ["evaluate_api_model.py"])
    args = parse_args()
    assert args.protocol_version == "0.9.1"


def test_protocol_version_cli_accepts_0_9_1(monkeypatch):
    monkeypatch.setattr(
        "sys.argv",
        ["evaluate_api_model.py", "--protocol-version", "0.9.1"],
    )
    args = parse_args()
    assert args.protocol_version == "0.9.1"


def test_full_prompt_mode_with_0_9_1_assembles_guide():
    from evaluate_api_model import resolve_generation_guide
    from protocol import get_protocol_stack

    stack = get_protocol_stack("0.9.1")
    guide = resolve_generation_guide(prompt_mode="full", stack=stack)
    assert guide
    assert "catalogId" in guide
