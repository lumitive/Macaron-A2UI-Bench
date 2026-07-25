"""jsonschema-backed L1 for A2UI v0.9.1 message lists.

Validates against vendored ``server_to_client_list.json`` with catalog +
common_types resolved offline via a ``referencing.Registry``.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from protocol.v0_9_1.catalog import get_catalog
from protocol.v0_9_1.diagnostics import (
    Diagnostic,
    DiagnosticCode,
    Severity,
    ValidationResult,
)

C = DiagnosticCode
S = Severity

_SPEC_DIR = Path(__file__).resolve().parent / "spec"
_JSON_DIR = _SPEC_DIR / "json"


@lru_cache(maxsize=4)
def _validator_for_catalog(catalog_name: str):
    """Build a Draft202012 validator for the message-list schema + catalog."""
    from referencing import Registry, Resource
    from jsonschema import Draft202012Validator

    catalog_path = get_catalog(catalog_name).path
    if not catalog_path.is_file():
        raise FileNotFoundError(f"catalog not found: {catalog_path}")

    list_path = _JSON_DIR / "server_to_client_list.json"
    if not list_path.is_file():
        raise FileNotFoundError(f"schema not found: {list_path}")

    docs: list[tuple[str | None, dict[str, Any]]] = []
    for path in (
        _JSON_DIR / "server_to_client_list.json",
        _JSON_DIR / "server_to_client.json",
        _JSON_DIR / "common_types.json",
        catalog_path,
    ):
        doc = json.loads(path.read_text(encoding="utf-8"))
        docs.append((doc.get("$id"), doc))

    catalog_doc = json.loads(catalog_path.read_text(encoding="utf-8"))
    # server_to_client.json refs "catalog.json#/$defs/..."
    extra_uris = {
        "catalog.json": catalog_doc,
        "https://a2ui.org/specification/v0_9/catalog.json": catalog_doc,
    }

    registry: Registry = Registry()
    for uri, doc in docs:
        if uri:
            registry = registry.with_resource(uri, Resource.from_contents(doc))
    for uri, doc in extra_uris.items():
        registry = registry.with_resource(uri, Resource.from_contents(doc))

    list_schema = json.loads(list_path.read_text(encoding="utf-8"))
    return Draft202012Validator(list_schema, registry=registry)


def schema_available() -> bool:
    """True when the vendored list schema is present."""
    return (_JSON_DIR / "server_to_client_list.json").is_file()


def validate_messages_schema(
    messages: list[dict],
    *,
    catalog_name: str = "basic",
) -> ValidationResult:
    """Validate a message list with jsonschema; map failures to DATA_* codes."""
    result = ValidationResult()
    if not schema_available():
        return result

    try:
        import jsonschema  # noqa: F401
        import referencing  # noqa: F401
    except ImportError:
        # Optional dep missing (local smoke without requirements.txt) — skip deep L1.
        return result

    try:
        validator = _validator_for_catalog(catalog_name)
    except Exception as exc:  # pragma: no cover - missing vendor assets
        result.add(
            Diagnostic(
                S.ERROR,
                C.DATA_BINDING_INVALID,
                f"Failed to load jsonschema validator: {exc}",
            )
        )
        return result

    if not isinstance(messages, list):
        result.add(
            Diagnostic(
                S.ERROR,
                C.STRUCT_WRONG_TYPE,
                f"A2UI payload must be a JSON array, got {type(messages).__name__}",
            )
        )
        return result

    errors = sorted(validator.iter_errors(messages), key=lambda e: list(e.absolute_path))
    for err in errors:
        path = "/" + "/".join(str(p) for p in err.absolute_path)
        # Prefer type / const / enum faults as DATA_TYPE_MISMATCH (prop/value).
        validator_name = err.validator or ""
        if validator_name in {"type", "const", "enum", "oneOf", "anyOf", "required"}:
            code = C.DATA_TYPE_MISMATCH
        else:
            code = C.DATA_BINDING_INVALID
        msg = err.message
        if len(msg) > 240:
            msg = msg[:237] + "..."
        result.add(
            Diagnostic(
                S.ERROR,
                code,
                f"jsonschema: {msg}",
                path=path or "/",
                suggestion="Fix message envelope or component props to match v0.9.1 schema.",
            )
        )
        # One high-signal error is enough for L1 scoring; avoid flood.
        if len(result.errors) >= 8:
            break

    return result
