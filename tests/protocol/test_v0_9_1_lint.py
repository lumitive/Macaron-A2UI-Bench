import json
from pathlib import Path

from protocol.v0_9_1.lint import validate

FIX = Path(__file__).parents[2] / "protocol" / "v0_9_1" / "fixtures"


def _load(name: str):
    return json.loads((FIX / name).read_text())


def test_ok_fixture_has_no_errors():
    result = validate(_load("ok_create_update.json"))
    assert result.errors == []


def test_rejects_beginRendering():
    result = validate(_load("bad_beginRendering.json"))
    codes = [d.code.value for d in result.errors]
    assert "STRUCT_LEGACY_0_8_SHAPE" in codes


def test_requires_root_component():
    result = validate(_load("missing_root.json"))
    codes = [d.code.value for d in result.errors]
    assert "REF_MISSING_ROOT" in codes


def test_version_mismatch():
    result = validate(_load("version_mismatch.json"))
    codes = [d.code.value for d in result.errors]
    assert "STRUCT_PROTOCOL_VERSION_MISMATCH" in codes


def test_unknown_action():
    result = validate([{"version": "v0.9.1", "doSomethingWeird": {"surfaceId": "main"}}])
    codes = [d.code.value for d in result.errors]
    assert "STRUCT_UNKNOWN_ACTION" in codes


def test_missing_catalog_id():
    result = validate(
        [
            {
                "version": "v0.9.1",
                "createSurface": {"surfaceId": "main"},
            }
        ]
    )
    codes = [d.code.value for d in result.errors]
    assert "STRUCT_MISSING_CATALOG_ID" in codes


def test_unknown_component():
    result = validate(
        [
            {
                "version": "v0.9.1",
                "createSurface": {
                    "surfaceId": "main",
                    "catalogId": (
                        "https://a2ui.org/specification/v0_9/catalogs/basic/catalog.json"
                    ),
                },
            },
            {
                "version": "v0.9.1",
                "updateComponents": {
                    "surfaceId": "main",
                    "components": [
                        {"id": "root", "component": "NotARealWidget", "text": "x"},
                    ],
                },
            },
        ]
    )
    codes = [d.code.value for d in result.errors]
    assert "STRUCT_UNKNOWN_COMPONENT" in codes


def test_accepts_v0_9_version():
    messages = _load("ok_create_update.json")
    for msg in messages:
        msg["version"] = "v0.9"
    result = validate(messages)
    assert result.errors == []


def test_update_without_createSurface_fails():
    result = validate(
        [
            {
                "version": "v0.9.1",
                "updateComponents": {
                    "surfaceId": "main",
                    "components": [
                        {"id": "root", "component": "Text", "text": "hi"},
                    ],
                },
            }
        ]
    )
    codes = [d.code.value for d in result.errors]
    assert "LINT_MESSAGE_ORDER" in codes


def test_updateDataModel_without_createSurface_fails():
    result = validate(
        [
            {
                "version": "v0.9.1",
                "updateDataModel": {
                    "surfaceId": "main",
                    "path": "/",
                    "value": {"x": 1},
                },
            }
        ]
    )
    codes = [d.code.value for d in result.errors]
    assert "LINT_MESSAGE_ORDER" in codes
