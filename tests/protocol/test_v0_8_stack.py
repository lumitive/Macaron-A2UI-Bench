import json
from pathlib import Path

from protocol import get_protocol_stack

FIXTURE = Path(__file__).parent / "fixtures" / "v0_8_minimal_ok.json"


def test_v0_8_validate_passes_minimal():
    stack = get_protocol_stack("0.8")
    messages = json.loads(FIXTURE.read_text())
    result = stack.validate(messages, levels={1, 2, 3, 4})
    assert result.is_valid or len(result.errors) == 0


def test_v0_8_stack_exposes_guide_and_render_check():
    stack = get_protocol_stack("0.8")
    assert stack.catalog_id == "legacy-0.8-vendor-a2ui-demo"
    assert "beginRendering" in stack.generation_guide
    assert "Available Components" in stack.component_schema_context
    messages = json.loads(FIXTURE.read_text())
    ok, issues = stack.render_check(messages)
    assert ok is True
    assert issues == []
