"""A2UI v0.9.1 structural lint (basic or LUMI catalog).

No silent 0.8→0.9.1 conversion — legacy shapes are rejected with
``STRUCT_LEGACY_0_8_SHAPE``.
"""

from __future__ import annotations

from typing import Any

from protocol.v0_9_1.catalog import LOCKED_CATALOG_ID, get_catalog
from protocol.v0_9_1.diagnostics import (
    Diagnostic,
    DiagnosticCode,
    Severity,
    ValidationResult,
)

C = DiagnosticCode
S = Severity

ACCEPTED_VERSIONS = frozenset({"v0.9", "v0.9.1"})
VALID_ACTIONS = frozenset(
    {"createSurface", "updateComponents", "updateDataModel", "deleteSurface"}
)
LEGACY_ACTIONS = frozenset({"beginRendering", "surfaceUpdate", "dataModelUpdate"})
LEGACY_MARKERS = frozenset(
    {
        "literalString",
        "literalNumber",
        "literalBoolean",
        "valueString",
        "valueNumber",
        "valueBoolean",
        "valueMap",
        "pathString",  # rare; keep conservative
    }
)


def validate(
    messages: list[dict],
    levels: set[int] | None = None,
    *,
    catalog_name: str = "basic",
) -> ValidationResult:
    """Validate a list of parsed A2UI v0.9.1 messages.

    ``levels`` is accepted for ProtocolStack / ``evaluate_l1_scores`` duck-typing
    but Phase 1 runs the full structural+ref suite regardless of the set.
    """
    _ = levels  # Phase 1: single-pass structural lint
    catalog = get_catalog(catalog_name)
    expected_catalog_id = catalog.catalog_id
    known_components = catalog.component_types
    result = ValidationResult()

    if not isinstance(messages, list):
        result.add(
            Diagnostic(
                S.ERROR,
                C.STRUCT_WRONG_TYPE,
                f"A2UI payload must be a JSON array, got {type(messages).__name__}",
            )
        )
        return result

    component_ids: set[str] = set()
    saw_any_components = False
    saw_create_surface = False
    saw_component_or_data_update = False
    primary_surface_id: str | None = None

    for msg_idx, msg in enumerate(messages):
        base = f"/messages/{msg_idx}"
        if not isinstance(msg, dict):
            result.add(
                Diagnostic(
                    S.ERROR,
                    C.STRUCT_MESSAGE_NOT_DICT,
                    f"Message {msg_idx} is not a dict (got {type(msg).__name__})",
                    path=base,
                )
            )
            continue

        _check_version(msg, msg_idx, base, result)

        legacy_keys = [k for k in msg if k in LEGACY_ACTIONS]
        if legacy_keys:
            result.add(
                Diagnostic(
                    S.ERROR,
                    C.STRUCT_LEGACY_0_8_SHAPE,
                    f"Message {msg_idx} uses legacy 0.8 action key(s): {legacy_keys}",
                    path=base,
                    suggestion=(
                        "Use createSurface / updateComponents / updateDataModel / "
                        "deleteSurface; do not convert silently from 0.8."
                    ),
                )
            )
            continue

        if _contains_legacy_markers(msg):
            result.add(
                Diagnostic(
                    S.ERROR,
                    C.STRUCT_LEGACY_0_8_SHAPE,
                    f"Message {msg_idx} contains legacy 0.8 typed wrappers "
                    f"(literalString/valueString/…)",
                    path=base,
                    suggestion="Use native JSON literals or path bindings for v0.9.1.",
                )
            )

        action_keys = [k for k in msg if k in VALID_ACTIONS]
        other_keys = [
            k for k in msg if k not in VALID_ACTIONS and k != "version"
        ]
        if not action_keys:
            hint = f" Unknown keys: {other_keys}." if other_keys else ""
            result.add(
                Diagnostic(
                    S.ERROR,
                    C.STRUCT_UNKNOWN_ACTION,
                    f"Message {msg_idx} has no valid v0.9.1 action key.{hint}",
                    path=base,
                    suggestion=(
                        "Each message must contain exactly one of: "
                        + ", ".join(sorted(VALID_ACTIONS))
                    ),
                )
            )
            continue
        if len(action_keys) > 1:
            result.add(
                Diagnostic(
                    S.ERROR,
                    C.STRUCT_MULTIPLE_ACTION_KEYS,
                    f"Message {msg_idx} has multiple action keys: {action_keys}",
                    path=base,
                )
            )
            continue

        action = action_keys[0]
        payload = msg.get(action)
        if not isinstance(payload, dict):
            result.add(
                Diagnostic(
                    S.ERROR,
                    C.STRUCT_WRONG_TYPE,
                    f"{action} must be an object",
                    path=f"{base}/{action}",
                )
            )
            continue

        surface_id = payload.get("surfaceId")
        if isinstance(surface_id, str):
            if primary_surface_id is None:
                primary_surface_id = surface_id
            elif surface_id != primary_surface_id:
                result.add(
                    Diagnostic(
                        S.ERROR,
                        C.REF_SURFACE_ID_MISMATCH,
                        f"surfaceId {surface_id!r} does not match "
                        f"primary {primary_surface_id!r}",
                        path=f"{base}/{action}/surfaceId",
                    )
                )

        if action == "createSurface":
            saw_create_surface = True
            _check_create_surface(
                payload,
                f"{base}/createSurface",
                result,
                expected_catalog_id,
            )
        elif action == "updateComponents":
            saw_component_or_data_update = True
            saw = _check_update_components(
                payload,
                f"{base}/updateComponents",
                result,
                component_ids,
                known_components,
            )
            saw_any_components = saw_any_components or saw
        elif action == "updateDataModel":
            saw_component_or_data_update = True
            _check_update_data_model(payload, f"{base}/updateDataModel", result)
        elif action == "deleteSurface":
            if "surfaceId" not in payload:
                result.add(
                    Diagnostic(
                        S.ERROR,
                        C.STRUCT_MISSING_REQUIRED,
                        "deleteSurface missing required field 'surfaceId'",
                        path=f"{base}/deleteSurface",
                    )
                )

    if saw_component_or_data_update and not saw_create_surface:
        result.add(
            Diagnostic(
                S.ERROR,
                C.LINT_MESSAGE_ORDER,
                "updateComponents/updateDataModel without createSurface in the "
                "same batch",
                suggestion=(
                    "Include a createSurface message before component or data "
                    "model updates."
                ),
            )
        )

    if saw_any_components and "root" not in component_ids:
        result.add(
            Diagnostic(
                S.ERROR,
                C.REF_MISSING_ROOT,
                "No component with id 'root' after updateComponents "
                "(v0.9.1 requires a root component)",
                suggestion='Include a component with "id": "root".',
            )
        )

    # Deep jsonschema pass after structural/ref checks (D6b).
    # Skip when structural errors already present — schema noise is unhelpful.
    if result.is_valid:
        from protocol.v0_9_1.schema_validate import validate_messages_schema

        result.merge(validate_messages_schema(messages, catalog_name=catalog_name))

    return result


def _check_version(
    msg: dict[str, Any], msg_idx: int, base: str, result: ValidationResult
) -> None:
    version = msg.get("version")
    if version not in ACCEPTED_VERSIONS:
        result.add(
            Diagnostic(
                S.ERROR,
                C.STRUCT_PROTOCOL_VERSION_MISMATCH,
                f"Message {msg_idx} version {version!r} is not accepted "
                f"for protocol 0.9.1 (expected one of {sorted(ACCEPTED_VERSIONS)})",
                path=f"{base}/version",
                suggestion='Set "version": "v0.9.1" (or "v0.9").',
            )
        )


def _check_create_surface(
    payload: dict[str, Any],
    path: str,
    result: ValidationResult,
    expected_catalog_id: str,
) -> None:
    if "surfaceId" not in payload:
        result.add(
            Diagnostic(
                S.ERROR,
                C.STRUCT_MISSING_REQUIRED,
                "createSurface missing required field 'surfaceId'",
                path=path,
            )
        )
    catalog_id = payload.get("catalogId")
    if catalog_id is None or catalog_id == "":
        result.add(
            Diagnostic(
                S.ERROR,
                C.STRUCT_MISSING_CATALOG_ID,
                "createSurface missing required catalogId",
                path=f"{path}/catalogId",
                suggestion=f'Set "catalogId": "{expected_catalog_id}"',
            )
        )
    elif catalog_id != expected_catalog_id:
        result.add(
            Diagnostic(
                S.ERROR,
                C.STRUCT_MISSING_CATALOG_ID,
                f"createSurface catalogId {catalog_id!r} does not match active "
                f"catalog ({expected_catalog_id!r})",
                path=f"{path}/catalogId",
                suggestion=f'Use "{expected_catalog_id}"',
            )
        )


def _check_update_components(
    payload: dict[str, Any],
    path: str,
    result: ValidationResult,
    component_ids: set[str],
    known_components: frozenset[str],
) -> bool:
    if "surfaceId" not in payload:
        result.add(
            Diagnostic(
                S.ERROR,
                C.STRUCT_MISSING_REQUIRED,
                "updateComponents missing required field 'surfaceId'",
                path=path,
            )
        )
    comps = payload.get("components")
    if comps is None:
        result.add(
            Diagnostic(
                S.ERROR,
                C.STRUCT_MISSING_REQUIRED,
                "updateComponents missing required field 'components'",
                path=path,
            )
        )
        return False
    if not isinstance(comps, list):
        result.add(
            Diagnostic(
                S.ERROR,
                C.STRUCT_WRONG_TYPE,
                "updateComponents.components must be an array",
                path=f"{path}/components",
            )
        )
        return False

    saw_any = False
    for ci, comp in enumerate(comps):
        cpath = f"{path}/components/{ci}"
        if not isinstance(comp, dict):
            result.add(
                Diagnostic(
                    S.ERROR,
                    C.STRUCT_WRONG_TYPE,
                    f"Component at {cpath} is not an object",
                    path=cpath,
                )
            )
            continue
        saw_any = True
        cid = comp.get("id")
        if not isinstance(cid, str) or not cid:
            result.add(
                Diagnostic(
                    S.ERROR,
                    C.STRUCT_MISSING_REQUIRED,
                    "Component missing required string 'id'",
                    path=cpath,
                )
            )
        else:
            if cid in component_ids:
                result.add(
                    Diagnostic(
                        S.ERROR,
                        C.REF_DUPLICATE_ID,
                        f"Duplicate component id {cid!r}",
                        path=f"{cpath}/id",
                    )
                )
            component_ids.add(cid)

        discriminator = comp.get("component")
        if discriminator is None:
            result.add(
                Diagnostic(
                    S.ERROR,
                    C.STRUCT_MISSING_REQUIRED,
                    "Component missing flat 'component' discriminator string",
                    path=cpath,
                    suggestion='Use "component": "Text" (not key-wrapped 0.8 shape).',
                )
            )
            continue
        if isinstance(discriminator, dict):
            result.add(
                Diagnostic(
                    S.ERROR,
                    C.STRUCT_LEGACY_0_8_SHAPE,
                    "Component uses key-wrapped 0.8 component shape; "
                    "v0.9.1 requires a string discriminator",
                    path=f"{cpath}/component",
                    suggestion='Use "component": "Text" with flat properties.',
                )
            )
            continue
        if not isinstance(discriminator, str):
            result.add(
                Diagnostic(
                    S.ERROR,
                    C.STRUCT_WRONG_TYPE,
                    "component discriminator must be a string",
                    path=f"{cpath}/component",
                )
            )
            continue
        if discriminator not in known_components:
            result.add(
                Diagnostic(
                    S.ERROR,
                    C.STRUCT_UNKNOWN_COMPONENT,
                    f"Unknown component type {discriminator!r} "
                    f"for active catalog",
                    path=f"{cpath}/component",
                    suggestion=f"Use one of: {', '.join(sorted(known_components))}",
                )
            )
    return saw_any


def _check_update_data_model(
    payload: dict[str, Any], path: str, result: ValidationResult
) -> None:
    if "surfaceId" not in payload:
        result.add(
            Diagnostic(
                S.ERROR,
                C.STRUCT_MISSING_REQUIRED,
                "updateDataModel missing required field 'surfaceId'",
                path=path,
            )
        )
    if "value" not in payload:
        result.add(
            Diagnostic(
                S.ERROR,
                C.STRUCT_MISSING_REQUIRED,
                "updateDataModel missing required field 'value'",
                path=path,
                suggestion='Provide a JSON "value" object (not 0.8 contents[]).',
            )
        )


def _contains_legacy_markers(obj: Any) -> bool:
    if isinstance(obj, dict):
        if any(k in LEGACY_MARKERS for k in obj):
            return True
        return any(_contains_legacy_markers(v) for v in obj.values())
    if isinstance(obj, list):
        return any(_contains_legacy_markers(v) for v in obj)
    return False
