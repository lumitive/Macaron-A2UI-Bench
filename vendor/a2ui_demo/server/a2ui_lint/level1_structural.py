"""Level 1: Structural / schema validation.

Checks that each message has valid shape, required fields, correct types,
and legal enum values. All diagnostics at this level are ERROR severity.
"""

from __future__ import annotations

from .context import (
    VALID_ACTION_KEYS,
    ValidationContext,
)
from .diagnostics import Diagnostic, DiagnosticCode, Severity, ValidationResult

C = DiagnosticCode
S = Severity


def check_level1(ctx: ValidationContext) -> ValidationResult:
    result = ValidationResult()
    for msg_idx, msg in enumerate(ctx.messages):
        base = f"/messages/{msg_idx}"
        if not isinstance(msg, dict):
            result.add(Diagnostic(S.ERROR, C.STRUCT_MESSAGE_NOT_DICT,
                f"Message {msg_idx} is not a dict (got {type(msg).__name__})",
                path=base))
            continue
        _check_action_keys(msg, msg_idx, base, result)
        _check_begin_rendering(msg, base, result)
        _check_surface_update(msg, msg_idx, base, ctx, result)
        _check_data_model_update(msg, base, ctx, result)
        _check_delete_surface(msg, base, result)
        _check_schema_type_mismatches(msg, base, ctx, result)
    return result


# ---------------------------------------------------------------------------
# action key checks
# ---------------------------------------------------------------------------

def _check_action_keys(msg: dict, msg_idx: int, base: str, result: ValidationResult) -> None:
    found = [k for k in msg if k in VALID_ACTION_KEYS]
    if not found:
        result.add(Diagnostic(S.ERROR, C.STRUCT_INVALID_ACTION_KEY,
            f"Message {msg_idx} has no valid action key. Keys: {list(msg.keys())}",
            path=base,
            suggestion=f"Each message must contain exactly one of: {', '.join(sorted(VALID_ACTION_KEYS))}"))
    if len(found) > 1:
        result.add(Diagnostic(S.ERROR, C.STRUCT_MULTIPLE_ACTION_KEYS,
            f"Message {msg_idx} has multiple action keys: {found}",
            path=base,
            suggestion="Split into separate messages, one action per message."))


# ---------------------------------------------------------------------------
# beginRendering
# ---------------------------------------------------------------------------

def _check_begin_rendering(msg: dict, base: str, result: ValidationResult) -> None:
    br = msg.get("beginRendering")
    if br is None:
        return
    path = f"{base}/beginRendering"
    if not isinstance(br, dict):
        result.add(Diagnostic(S.ERROR, C.STRUCT_WRONG_TYPE,
            "beginRendering must be an object", path=path))
        return
    for req in ("root", "surfaceId"):
        if req not in br:
            result.add(Diagnostic(S.ERROR, C.STRUCT_MISSING_REQUIRED,
                f"beginRendering missing required field '{req}'",
                path=path, suggestion=f"Add \"{req}\": \"...\" to beginRendering."))
    if "surfaceId" in br and not isinstance(br["surfaceId"], str):
        result.add(Diagnostic(S.ERROR, C.STRUCT_WRONG_TYPE,
            "beginRendering.surfaceId must be a string", path=f"{path}/surfaceId"))
    if "root" in br and not isinstance(br["root"], str):
        result.add(Diagnostic(S.ERROR, C.STRUCT_WRONG_TYPE,
            "beginRendering.root must be a string", path=f"{path}/root"))


# ---------------------------------------------------------------------------
# surfaceUpdate
# ---------------------------------------------------------------------------

def _check_surface_update(msg: dict, msg_idx: int, base: str, ctx: ValidationContext, result: ValidationResult) -> None:
    su = msg.get("surfaceUpdate")
    if su is None:
        return
    path = f"{base}/surfaceUpdate"
    if not isinstance(su, dict):
        result.add(Diagnostic(S.ERROR, C.STRUCT_WRONG_TYPE,
            "surfaceUpdate must be an object", path=path))
        return
    for req in ("surfaceId", "components"):
        if req not in su:
            result.add(Diagnostic(S.ERROR, C.STRUCT_MISSING_REQUIRED,
                f"surfaceUpdate missing required field '{req}'",
                path=path, suggestion=f"Add \"{req}\" to surfaceUpdate."))
    if "surfaceId" in su and not isinstance(su["surfaceId"], str):
        result.add(Diagnostic(S.ERROR, C.STRUCT_WRONG_TYPE,
            "surfaceUpdate.surfaceId must be a string", path=f"{path}/surfaceId"))
    comps = su.get("components")
    if comps is not None:
        if not isinstance(comps, list):
            result.add(Diagnostic(S.ERROR, C.STRUCT_WRONG_TYPE,
                "surfaceUpdate.components must be an array", path=f"{path}/components"))
        else:
            for ci, comp in enumerate(comps):
                cpath = f"{path}/components/{ci}"
                _check_component(comp, cpath, ctx, result)


def _check_component(comp: dict | object, path: str, ctx: ValidationContext, result: ValidationResult) -> None:
    if not isinstance(comp, dict):
        result.add(Diagnostic(S.ERROR, C.STRUCT_WRONG_TYPE,
            f"Component at {path} is not an object", path=path))
        return

    # Required: id
    if "id" not in comp:
        result.add(Diagnostic(S.ERROR, C.STRUCT_MISSING_REQUIRED,
            "Component missing required 'id' field", path=path,
            suggestion="Every component must have a unique \"id\" string."))
    elif not isinstance(comp["id"], str):
        result.add(Diagnostic(S.ERROR, C.STRUCT_WRONG_TYPE,
            "Component id must be a string", path=f"{path}/id"))

    # Required: component wrapper
    wrapper = comp.get("component")
    if wrapper is None:
        result.add(Diagnostic(S.ERROR, C.STRUCT_MISSING_COMPONENT_WRAPPER,
            "Component missing 'component' wrapper", path=path,
            suggestion="Add \"component\": {\"TypeName\": {...}} to the component."))
        return
    if not isinstance(wrapper, dict):
        result.add(Diagnostic(S.ERROR, C.STRUCT_WRONG_TYPE,
            "component wrapper must be an object", path=f"{path}/component"))
        return

    # Exactly one component type key
    type_keys = list(wrapper.keys())
    if len(type_keys) == 0:
        result.add(Diagnostic(S.ERROR, C.STRUCT_MISSING_COMPONENT_WRAPPER,
            "component wrapper is empty — needs exactly one component type",
            path=f"{path}/component"))
        return
    if len(type_keys) > 1:
        result.add(Diagnostic(S.ERROR, C.STRUCT_MULTIPLE_COMPONENT_TYPES,
            f"component wrapper has multiple keys: {type_keys}",
            path=f"{path}/component",
            suggestion="Use exactly one component type per wrapper."))

    comp_type = type_keys[0]
    schema = ctx.schema
    if comp_type not in schema.known_component_types:
        result.add(Diagnostic(S.ERROR, C.STRUCT_UNKNOWN_COMPONENT_TYPE,
            f"Unknown component type '{comp_type}'",
            path=f"{path}/component",
            suggestion=f"Known types: {', '.join(sorted(schema.known_component_types))}"))
        return

    props = wrapper[comp_type]
    if not isinstance(props, dict):
        result.add(Diagnostic(S.ERROR, C.STRUCT_WRONG_TYPE,
            f"{comp_type} properties must be an object", path=f"{path}/component/{comp_type}"))
        return

    tpath = f"{path}/component/{comp_type}"
    _check_component_props(comp_type, props, tpath, ctx, result)


def _check_component_props(comp_type: str, props: dict, path: str, ctx: ValidationContext, result: ValidationResult) -> None:
    """Validate required fields and enum values for each component type (schema-driven)."""
    schema = ctx.schema

    # 1. Check required fields from schema
    for fld in schema.component_required_fields.get(comp_type, []):
        if fld not in props:
            result.add(Diagnostic(S.ERROR, C.STRUCT_MISSING_REQUIRED,
                f"Missing required field '{fld}'",
                path=path,
                suggestion=f"Add \"{fld}\" to the component."))

    # 2. Check enum values from schema
    for fld, allowed in schema.component_enums.get(comp_type, {}).items():
        val = props.get(fld)
        if val is not None and val not in allowed:
            result.add(Diagnostic(S.ERROR, C.STRUCT_INVALID_ENUM,
                f"Invalid value '{val}' for '{fld}'",
                path=f"{path}/{fld}",
                suggestion=f"Valid values: {', '.join(sorted(allowed))}"))

    # 3. Special: Icon literal name check
    if comp_type == "Icon":
        name_obj = props.get("name")
        if isinstance(name_obj, dict):
            lit = name_obj.get("literalString")
            if lit is not None and lit not in schema.icon_names:
                result.add(Diagnostic(S.ERROR, C.STRUCT_INVALID_ENUM,
                    f"Invalid icon name '{lit}'",
                    path=f"{path}/name/literalString",
                    suggestion=f"Valid icons: {', '.join(sorted(schema.icon_names))}"))

    # 4. Structural checks for children (protocol-level, not per-component)
    if comp_type in schema.container_children_types:
        children = props.get("children")
        if children is not None and not isinstance(children, dict):
            result.add(Diagnostic(S.ERROR, C.STRUCT_WRONG_TYPE,
                "children must be an object",
                path=f"{path}/children"))
            children = None
        if isinstance(children, dict):
            has_explicit = "explicitList" in children
            has_template = "template" in children
            if has_explicit:
                el = children["explicitList"]
                if not isinstance(el, list):
                    result.add(Diagnostic(S.ERROR, C.STRUCT_WRONG_TYPE,
                        "explicitList must be an array",
                        path=f"{path}/children/explicitList"))
            if has_template:
                tmpl = children["template"]
                if not isinstance(tmpl, dict):
                    result.add(Diagnostic(S.ERROR, C.STRUCT_WRONG_TYPE,
                        "template must be an object",
                        path=f"{path}/children/template"))
                else:
                    for req in ("componentId", "dataBinding"):
                        if req not in tmpl:
                            result.add(Diagnostic(S.ERROR, C.STRUCT_MISSING_REQUIRED,
                                f"template missing required field '{req}'",
                                path=f"{path}/children/template"))
                    if "componentId" in tmpl and not isinstance(tmpl["componentId"], str):
                        result.add(Diagnostic(S.ERROR, C.STRUCT_WRONG_TYPE,
                            "template.componentId must be a string",
                            path=f"{path}/children/template/componentId"))
                    if "dataBinding" in tmpl and not isinstance(tmpl["dataBinding"], str):
                        result.add(Diagnostic(S.ERROR, C.STRUCT_WRONG_TYPE,
                            "template.dataBinding must be a string",
                            path=f"{path}/children/template/dataBinding"))

    # 5. Structural: Tabs.tabItems array items
    if comp_type == "Tabs":
        tab_items = props.get("tabItems")
        if isinstance(tab_items, list):
            for ti, tab in enumerate(tab_items):
                if isinstance(tab, dict):
                    for req in ("title", "child"):
                        if req not in tab:
                            result.add(Diagnostic(S.ERROR, C.STRUCT_MISSING_REQUIRED,
                                f"tabItems[{ti}] missing required field '{req}'",
                                path=f"{path}/tabItems/{ti}"))

    # 6. Structural: Button.action.name
    if comp_type == "Button":
        action = props.get("action")
        if isinstance(action, dict) and "name" not in action:
            result.add(Diagnostic(S.ERROR, C.STRUCT_MISSING_REQUIRED,
                "Button.action missing required 'name' field",
                path=f"{path}/action"))


# ---------------------------------------------------------------------------
# dataModelUpdate
# ---------------------------------------------------------------------------

def _check_data_model_update(msg: dict, base: str, ctx: ValidationContext, result: ValidationResult) -> None:
    dmu = msg.get("dataModelUpdate")
    if dmu is None:
        return
    path = f"{base}/dataModelUpdate"
    if not isinstance(dmu, dict):
        result.add(Diagnostic(S.ERROR, C.STRUCT_WRONG_TYPE,
            "dataModelUpdate must be an object", path=path))
        return
    for req in ("surfaceId", "contents"):
        if req not in dmu:
            result.add(Diagnostic(S.ERROR, C.STRUCT_MISSING_REQUIRED,
                f"dataModelUpdate missing required field '{req}'",
                path=path, suggestion=f"Add \"{req}\" to dataModelUpdate."))
    if "surfaceId" in dmu and not isinstance(dmu["surfaceId"], str):
        result.add(Diagnostic(S.ERROR, C.STRUCT_WRONG_TYPE,
            "dataModelUpdate.surfaceId must be a string", path=f"{path}/surfaceId"))
    if "path" in dmu and not isinstance(dmu["path"], str):
        result.add(Diagnostic(S.ERROR, C.STRUCT_WRONG_TYPE,
            "dataModelUpdate.path must be a string", path=f"{path}/path"))
    contents = dmu.get("contents")
    if contents is not None:
        if not isinstance(contents, list):
            result.add(Diagnostic(S.ERROR, C.STRUCT_WRONG_TYPE,
                "dataModelUpdate.contents must be an array", path=f"{path}/contents"))
        else:
            _check_data_entries(contents, f"{path}/contents", ctx, result)


def _check_data_entries(entries: list, path: str, ctx: ValidationContext, result: ValidationResult) -> None:
    value_type_keys = ctx.schema.value_type_keys
    for i, entry in enumerate(entries):
        epath = f"{path}/{i}"
        if not isinstance(entry, dict):
            result.add(Diagnostic(S.ERROR, C.STRUCT_WRONG_TYPE,
                f"Data entry at {epath} is not an object", path=epath))
            continue
        if "key" not in entry:
            result.add(Diagnostic(S.ERROR, C.STRUCT_MISSING_REQUIRED,
                "Data entry missing required 'key' field", path=epath))
        elif not isinstance(entry["key"], str):
            result.add(Diagnostic(S.ERROR, C.STRUCT_WRONG_TYPE,
                "Data entry 'key' must be a string", path=f"{epath}/key"))
        # Exactly one value* property
        val_keys = [k for k in entry if k in value_type_keys]
        if len(val_keys) == 0 and "key" in entry:
            result.add(Diagnostic(S.ERROR, C.STRUCT_NO_VALUE_TYPE,
                f"Data entry '{entry.get('key', '?')}' has no value property",
                path=epath,
                suggestion=f"Add exactly one of: {', '.join(sorted(value_type_keys))}"))
        if len(val_keys) > 1:
            result.add(Diagnostic(S.ERROR, C.STRUCT_MULTIPLE_VALUE_TYPES,
                f"Data entry '{entry.get('key', '?')}' has multiple value properties: {val_keys}",
                path=epath,
                suggestion="Use exactly one value property per entry."))
        # Recurse into valueMap
        vmap = entry.get("valueMap")
        if isinstance(vmap, list):
            _check_data_entries(vmap, f"{epath}/valueMap", ctx, result)


# ---------------------------------------------------------------------------
# deleteSurface
# ---------------------------------------------------------------------------

def _check_delete_surface(msg: dict, base: str, result: ValidationResult) -> None:
    ds = msg.get("deleteSurface")
    if ds is None:
        return
    path = f"{base}/deleteSurface"
    if not isinstance(ds, dict):
        result.add(Diagnostic(S.ERROR, C.STRUCT_WRONG_TYPE,
            "deleteSurface must be an object", path=path))
        return
    if "surfaceId" not in ds:
        result.add(Diagnostic(S.ERROR, C.STRUCT_MISSING_REQUIRED,
            "deleteSurface missing required 'surfaceId'",
            path=path))


def _check_schema_type_mismatches(msg: dict, base: str, ctx: ValidationContext, result: ValidationResult) -> None:
    """Supplement hand-written checks with JSON Schema type validation."""
    validator = ctx.schema.get_jsonschema_validator()
    if validator is None:
        return

    try:
        errors = list(validator.iter_errors(msg))
    except Exception:
        return

    for err in errors:
        for leaf in _iter_leaf_errors(err):
            if leaf.validator != "type":
                continue
            path = _to_json_pointer(base, leaf.absolute_path)
            if _has_wrong_type_diag(path, result):
                continue
            expected = leaf.validator_value
            actual = type(leaf.instance).__name__
            result.add(Diagnostic(
                S.ERROR,
                C.STRUCT_WRONG_TYPE,
                f"Schema type mismatch: expected {expected}, got {actual}",
                path=path,
            ))


def _iter_leaf_errors(err: object) -> list[object]:
    context = getattr(err, "context", None)
    if not context:
        return [err]
    leaves: list[object] = []
    for child in context:
        leaves.extend(_iter_leaf_errors(child))
    return leaves


def _to_json_pointer(base: str, path_parts: object) -> str:
    parts = []
    for p in path_parts:
        s = str(p).replace("~", "~0").replace("/", "~1")
        parts.append(s)
    if not parts:
        return base
    return f"{base}/{'/'.join(parts)}"


def _has_wrong_type_diag(path: str, result: ValidationResult) -> bool:
    return any(
        d.code == C.STRUCT_WRONG_TYPE and d.path == path
        for d in result.diagnostics
    )
