"""jsonschema-backed L1 tests for A2UI v0.9.1."""

from __future__ import annotations

import json
from pathlib import Path

from protocol.v0_9_1.lint import validate
from protocol.v0_9_1.schema_validate import schema_available, validate_messages_schema

FIX = Path(__file__).parents[2] / "protocol" / "v0_9_1" / "fixtures"


def _load(name: str):
    return json.loads((FIX / name).read_text(encoding="utf-8"))


def test_schema_assets_available():
    assert schema_available()


def test_ok_create_update_passes_schema_and_lint():
    messages = _load("ok_create_update.json")
    schema_result = validate_messages_schema(messages)
    assert schema_result.errors == []
    lint_result = validate(messages)
    assert lint_result.errors == []


def test_deliberate_bad_prop_type_fails():
    messages = _load("ok_create_update.json")
    # Text.text must be DynamicString (string or path object), not a number.
    messages[1]["updateComponents"]["components"][1]["text"] = 12345
    schema_result = validate_messages_schema(messages)
    assert schema_result.errors
    codes = {d.code.value for d in schema_result.errors}
    assert codes & {"DATA_TYPE_MISMATCH", "DATA_BINDING_INVALID"}

    lint_result = validate(messages)
    assert not lint_result.is_valid
    lint_codes = {d.code.value for d in lint_result.errors}
    assert lint_codes & {"DATA_TYPE_MISMATCH", "DATA_BINDING_INVALID"}
