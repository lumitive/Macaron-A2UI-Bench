import json
from pathlib import Path

from protocol import get_protocol_stack


def test_v0_8_fixture_fails_on_v0_9_1():
    messages = json.loads(
        (Path(__file__).parent / "fixtures" / "v0_8_minimal_ok.json").read_text()
    )
    result = get_protocol_stack("0.9.1").validate(messages)
    assert result.errors, "0.8 messages must not validate as 0.9.1"


def test_v0_9_1_fixture_fails_on_v0_8():
    root = Path(__file__).resolve().parents[2]
    messages = json.loads(
        (root / "protocol" / "v0_9_1" / "fixtures" / "ok_create_update.json").read_text()
    )
    result = get_protocol_stack("0.8").validate(messages)
    assert result.errors, "0.9.1 messages must not validate as 0.8"
