"""Level 3: Data model consistency checks.

Validates data bindings, path references, and type compatibility
between components and data model entries.
"""

from __future__ import annotations

from .context import ValidationContext
from .diagnostics import Diagnostic, DiagnosticCode, Severity, ValidationResult

C = DiagnosticCode
S = Severity


def check_level3(ctx: ValidationContext) -> ValidationResult:
    result = ValidationResult()
    _check_template_data_bindings(ctx, result)
    _check_component_path_exists(ctx, result)
    _check_type_compatibility(ctx, result)
    return result


# ---------------------------------------------------------------------------
# template dataBinding → data path exists and points to a map
# ---------------------------------------------------------------------------

def _check_template_data_bindings(ctx: ValidationContext, result: ValidationResult) -> None:
    for tid, binding in ctx.template_bindings.items():
        if not binding:
            continue
        # dataBinding should be an absolute path
        if not binding.startswith("/"):
            result.add(Diagnostic(S.ERROR, C.DATA_BINDING_INVALID,
                f"template dataBinding '{binding}' for component '{tid}' should be an absolute path",
                suggestion=f"Change to \"/{binding.lstrip('/')}\""))
            continue
        # Check the path exists in the data model
        if ctx.data_paths and binding not in ctx.data_paths:
            result.add(Diagnostic(S.WARNING, C.DATA_PATH_NOT_FOUND,
                f"template dataBinding '{binding}' for component '{tid}' not found in dataModelUpdate",
                suggestion="Ensure the dataModelUpdate contains data at this path."))


# ---------------------------------------------------------------------------
# component path references → exist in data model
# ---------------------------------------------------------------------------

def _check_component_path_exists(ctx: ValidationContext, result: ValidationResult) -> None:
    """For non-template components, check that absolute path refs exist."""
    if not ctx.data_paths:
        return  # No data model, skip

    template_subtree: set[str] = set()
    queue = list(ctx.template_component_ids)
    while queue:
        cid = queue.pop()
        if cid in template_subtree:
            continue
        template_subtree.add(cid)
        for child in ctx.children_graph.get(cid, []):
            queue.append(child)

    for comp_id, info in ctx.components.items():
        if comp_id in template_subtree:
            # Template subtree paths are context-scoped and cannot be
            # reliably resolved statically from the global data model.
            continue
        paths = _collect_paths(info.comp_props)
        for p in paths:
            if p.startswith("/") and p not in ctx.data_paths:
                result.add(Diagnostic(S.WARNING, C.DATA_PATH_NOT_FOUND,
                    f"Component '{comp_id}' references data path '{p}' not found in dataModelUpdate",
                    suggestion="Check the dataModelUpdate contents or fix the path."))


def _collect_paths(obj: object) -> list[str]:
    """Recursively collect all {"path": "..."} values."""
    paths: list[str] = []
    if isinstance(obj, dict):
        if "path" in obj and isinstance(obj["path"], str):
            paths.append(obj["path"])
        for v in obj.values():
            paths.extend(_collect_paths(v))
    elif isinstance(obj, list):
        for item in obj:
            paths.extend(_collect_paths(item))
    return paths


# ---------------------------------------------------------------------------
# type compatibility: component ↔ data value type
# ---------------------------------------------------------------------------

def _check_type_compatibility(ctx: ValidationContext, result: ValidationResult) -> None:
    """Check that e.g. Text uses valueString, Slider uses valueNumber, etc."""
    if not ctx.data_paths:
        return

    for comp_id, info in ctx.components.items():
        expected_vtype = ctx.schema.type_hints.get(info.comp_type)
        if not expected_vtype:
            continue

        # Find path references in the primary value field
        primary_field = _get_primary_value_field(info.comp_type, info.comp_props)
        if not primary_field:
            continue
        path_ref = primary_field.get("path") if isinstance(primary_field, dict) else None
        if not isinstance(path_ref, str) or not path_ref.startswith("/"):
            continue

        # Look up what type is stored at this path in the data model
        actual = _find_value_type_at_path(ctx, path_ref)
        if actual and actual != expected_vtype:
            result.add(Diagnostic(S.WARNING, C.DATA_TYPE_MISMATCH,
                f"Component '{comp_id}' ({info.comp_type}) expects {expected_vtype} "
                f"but data at '{path_ref}' is {actual}",
                suggestion=f"Change the data entry to use {expected_vtype} or use a different component."))


def _get_primary_value_field(comp_type: str, props: dict) -> dict | None:
    if comp_type == "Text":
        return props.get("text")
    if comp_type == "Slider":
        return props.get("value")
    if comp_type == "CheckBox":
        return props.get("value")
    return None


def _find_value_type_at_path(ctx: ValidationContext, target_path: str) -> str | None:
    """Search data model updates for the value type at the given path."""
    for _, dmu in ctx.data_model_updates:
        base = dmu.get("path", "/")
        if not isinstance(base, str):
            base = "/"
        if not base.startswith("/"):
            base = "/" + base
        contents = dmu.get("contents", [])
        found = _search_entries(base, contents, target_path)
        if found:
            return found
    return None


def _search_entries(prefix: str, entries: list, target: str) -> str | None:
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        key = entry.get("key", "")
        if not isinstance(key, str):
            continue
        path = f"{prefix.rstrip('/')}/{key}" if prefix != "/" else f"/{key}"
        if path == target:
            for vk in ("valueString", "valueNumber", "valueBoolean", "valueMap"):
                if vk in entry:
                    return vk
        vmap = entry.get("valueMap")
        if isinstance(vmap, list):
            found = _search_entries(path, vmap, target)
            if found:
                return found
    return None
