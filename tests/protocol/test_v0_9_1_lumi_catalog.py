"""LUMI catalog MVP lint ≡ render_check tests."""

from __future__ import annotations

import json
from pathlib import Path

from protocol import get_protocol_stack
from protocol.v0_9_1.catalog import LUMI_CATALOG_ID, get_catalog
from protocol.v0_9_1.lint import validate

_FIX = Path(__file__).resolve().parents[2] / "protocol" / "v0_9_1" / "fixtures" / "lumi"


def _load(name: str):
    return json.loads((_FIX / name).read_text(encoding="utf-8"))


def test_lumi_catalog_info():
    info = get_catalog("lumi")
    assert info.catalog_id == LUMI_CATALOG_ID
    assert "Carousel" in info.component_types
    assert "Text" in info.component_types


def test_facade_basic_unchanged():
    stack = get_protocol_stack("0.9.1", catalog="basic")
    assert stack.catalog_name == "basic"
    assert "Carousel" not in get_catalog("basic").component_types


def test_ok_carousel_lint_and_render():
    messages = _load("ok_carousel.json")
    stack = get_protocol_stack("0.9.1", catalog="lumi")
    result = stack.validate(messages)
    assert result.errors == []
    ok, issues = stack.render_check(messages)
    assert ok, issues


def test_wrong_catalog_id_on_lumi_stack():
    messages = _load("wrong_catalog_id.json")
    result = validate(messages, catalog_name="lumi")
    codes = [d.code.value for d in result.errors]
    assert "STRUCT_MISSING_CATALOG_ID" in codes


def test_carousel_rejected_on_basic():
    messages = _load("carousel_on_basic.json")
    result = validate(messages, catalog_name="basic")
    codes = [d.code.value for d in result.errors]
    assert "STRUCT_UNKNOWN_COMPONENT" in codes


def test_lumi_guide_mentions_carousel_and_catalog_id():
    stack = get_protocol_stack("0.9.1", catalog="lumi")
    assert LUMI_CATALOG_ID in stack.generation_guide
    assert "Carousel" in stack.generation_guide
