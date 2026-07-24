"""Tests for A2UI v0.9.1 render_check."""

from __future__ import annotations

import json
from pathlib import Path

from protocol import get_protocol_stack
from protocol.v0_9_1.render_check import render_check
from prompts import load_l2_judge_prompt, load_l3_judge_prompt

FIX = Path(__file__).parents[2] / "protocol" / "v0_9_1" / "fixtures"
LOCKED = "https://a2ui.org/specification/v0_9/catalogs/basic/catalog.json"


def _load(name: str):
    return json.loads((FIX / name).read_text())


def test_empty_passes():
    ok, issues = render_check([])
    assert ok and issues == []


def test_legacy_surfaceUpdate_fails():
    ok, issues = render_check(
        [{"surfaceUpdate": {"surfaceId": "s", "components": []}}]
    )
    assert not ok
    assert any(
        "0.8" in i or "legacy" in i.lower() or "surfaceUpdate" in i for i in issues
    )


def test_legacy_beginRendering_fails():
    ok, issues = render_check(_load("bad_beginRendering.json"))
    assert not ok
    assert any("beginRendering" in i or "legacy" in i.lower() or "0.8" in i for i in issues)


def test_ok_fixture_passes():
    ok, issues = render_check(_load("ok_create_update.json"))
    assert ok, issues
    assert issues == []


def test_missing_root_fails():
    ok, issues = render_check(_load("missing_root.json"))
    assert not ok
    assert any("root" in i.lower() for i in issues)


def test_multiple_surface_ids_fail():
    ok, issues = render_check(
        [
            {
                "version": "v0.9.1",
                "createSurface": {"surfaceId": "a", "catalogId": LOCKED},
            },
            {
                "version": "v0.9.1",
                "updateComponents": {
                    "surfaceId": "b",
                    "components": [
                        {"id": "root", "component": "Text", "text": "x"},
                    ],
                },
            },
        ]
    )
    assert not ok
    assert any("surfaceId" in i for i in issues)


def test_createSurface_requires_catalogId():
    ok, issues = render_check(
        [{"version": "v0.9.1", "createSurface": {"surfaceId": "main"}}]
    )
    assert not ok
    assert any("catalogId" in i for i in issues)


def test_key_wrapped_component_fails():
    ok, issues = render_check(
        [
            {
                "version": "v0.9.1",
                "createSurface": {"surfaceId": "main", "catalogId": LOCKED},
            },
            {
                "version": "v0.9.1",
                "updateComponents": {
                    "surfaceId": "main",
                    "components": [
                        {"id": "root", "component": {"Text": {"text": "hi"}}},
                    ],
                },
            },
        ]
    )
    assert not ok
    assert any(
        "component" in i.lower() or "key-wrapped" in i.lower() or "legacy" in i.lower()
        for i in issues
    )


def test_build_stack_wires_render_check_and_guides():
    stack = get_protocol_stack("0.9.1")
    assert "v0.9.1" in stack.generation_guide or "0.9.1" in stack.generation_guide
    assert LOCKED in stack.generation_guide
    assert "Available Components" in stack.component_schema_context
    assert "ChoicePicker" in stack.component_schema_context
    ok, issues = stack.render_check(_load("ok_create_update.json"))
    assert ok and issues == []


def test_versioned_judge_prompt_loaders():
    l2_08 = load_l2_judge_prompt()
    l2_091 = load_l2_judge_prompt("0.9.1")
    l3_08 = load_l3_judge_prompt("0.8")
    l3_091 = load_l3_judge_prompt("0.9.1")
    assert "SelectionList" in l2_08 or "dataModelUpdate" in l2_08
    assert "updateDataModel" in l2_091
    assert "ChoicePicker" in l2_091
    assert "updateComponents" in l2_091 or "updateDataModel" in l2_091
    assert "dataModelUpdate" in l3_08
    assert "updateDataModel" in l3_091
    assert l2_08 != l2_091
    assert l3_08 != l3_091
