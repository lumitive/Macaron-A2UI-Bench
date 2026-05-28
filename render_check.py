"""Render-critical detection for A2UI messages.

Detection-only module — returns a list of issues found, does NOT fix them.
Rules extracted from data_generation_v2/repair_pipeline.py:post_process_a2ui().
"""

from __future__ import annotations

from typing import Any

# Component types that use selection semantics
_SELECTION_TYPES = frozenset(
    {
        "SelectionList",
        "SelectionWrap",
        "SelectionGrid",
        "OrderedSelectionList",
        "ActionSelectionList",
    }
)


def _check_selection_missing_literal_array(
    comp_type: str, props: dict[str, Any]
) -> str | None:
    """Rule 1: SelectionList missing literalArray.

    Selection ref has `path` but no `literalArray: []`.  Without literalArray
    the renderer initialises the data model path as a Map instead of a List,
    which crashes selection handling.
    """
    if comp_type not in _SELECTION_TYPES:
        return None
    sel = props.get("selection", {})
    if isinstance(sel, dict) and sel.get("path") and "literalArray" not in sel:
        return (
            f"{comp_type}: selection has path='{sel['path']}' but missing "
            f"'literalArray' — renderer will create Map instead of List"
        )
    return None


def _check_tickslider_in_row(
    components: list[dict[str, Any]],
) -> list[str]:
    """Rule 2: TickSlider inside Row.

    TickSlider renders as a Column internally and crashes with unconstrained
    width when placed inside a Row.
    """
    comp_map: dict[str, dict[str, Any]] = {}
    for comp in components:
        if not isinstance(comp, dict):
            continue
        cid = comp.get("id", "")
        if cid:
            comp_map[cid] = comp

    issues: list[str] = []
    for comp in components:
        if not isinstance(comp, dict):
            continue
        for comp_type, props in comp.get("component", {}).items():
            if comp_type != "Row" or not isinstance(props, dict):
                continue
            children_obj = props.get("children", {})
            if not isinstance(children_obj, dict):
                continue
            child_ids = children_obj.get("explicitList", [])
            if not child_ids:
                continue
            for cid in child_ids:
                child_comp = comp_map.get(cid, {})
                for cct in child_comp.get("component", {}):
                    if cct == "TickSlider":
                        issues.append(
                            f"TickSlider (id={cid}) is a child of Row "
                            f"(id={comp.get('id', '?')}) — causes crash"
                        )
    return issues


def _check_component_entries_are_dicts(
    components: list[Any],
) -> list[str]:
    """Rule 8: surfaceUpdate.components must be a list of objects.

    Some malformed model outputs partially parse into string fragments inside the
    components array. That is not renderable and should fail render_check
    cleanly instead of crashing the checker.
    """
    issues: list[str] = []
    for idx, comp in enumerate(components):
        if isinstance(comp, dict):
            continue
        issues.append(
            f"surfaceUpdate.components[{idx}] is {type(comp).__name__}, not object"
        )
    return issues


def _check_single_surface_id(a2ui_messages: list[dict[str, Any]]) -> str | None:
    """Rule 3: Multiple surfaceIds in one response.

    The gallery viewer overwrites all surfaceIds to one value, so
    multi-surface entries break rendering.
    """
    surface_ids: list[str] = []
    for msg in a2ui_messages:
        if not isinstance(msg, dict):
            continue
        for k in ("surfaceUpdate", "dataModelUpdate", "beginRendering"):
            if k in msg and isinstance(msg[k], dict):
                sid = msg[k].get("surfaceId", "")
                if sid and sid not in surface_ids:
                    surface_ids.append(sid)
    if len(surface_ids) > 1:
        return (
            f"Multiple surfaceIds found: {surface_ids} — "
            f"only one surfaceId per response is supported"
        )
    return None


def _check_button_action_context_not_array(
    comp_type: str, props: dict[str, Any]
) -> str | None:
    """Rule 4: Button.action.context is dict instead of list.

    The schema requires context to be an array of {key, value} objects.
    """
    if comp_type != "Button":
        return None
    action = props.get("action")
    if not isinstance(action, dict):
        return None
    ctx = action.get("context")
    if isinstance(ctx, dict):
        return (
            f"Button (action={action.get('name', '?')}): "
            f"action.context is dict instead of list"
        )
    return None


def _check_selection_item_value_wrapped(
    comp_type: str, props: dict[str, Any]
) -> list[str]:
    """Rule 5: Selection item value wrapped in object.

    Item value must be a plain string, not {literalString: X} or {path: X}.
    """
    if comp_type not in _SELECTION_TYPES:
        return []
    issues: list[str] = []
    for idx, item in enumerate(props.get("items", [])):
        val = item.get("value")
        if isinstance(val, dict):
            issues.append(
                f"{comp_type}: items[{idx}].value is dict {val} "
                f"instead of plain string"
            )
    return issues


def _check_datetime_fields_wrapped(
    comp_type: str, props: dict[str, Any]
) -> list[str]:
    """Rule 6: DateTimeInput fields wrapped in object.

    firstDate/lastDate must be plain strings; enableDate/enableTime must be bool.
    """
    if comp_type != "DateTimeInput":
        return []
    issues: list[str] = []
    for fld in ("firstDate", "lastDate"):
        val = props.get(fld)
        if isinstance(val, dict):
            issues.append(
                f"DateTimeInput: {fld} is dict {val} instead of plain string"
            )
    for fld in ("enableDate", "enableTime"):
        val = props.get(fld)
        if val is not None and not isinstance(val, bool):
            issues.append(
                f"DateTimeInput: {fld} is {type(val).__name__}({val}) "
                f"instead of bool"
            )
    return issues


def _check_data_model_update_missing_path(
    a2ui_messages: list[dict[str, Any]],
) -> list[str]:
    """Rule 7: dataModelUpdate missing path.

    Every dataModelUpdate must have a "path" field (defaults to "/").
    """
    issues: list[str] = []
    for idx, msg in enumerate(a2ui_messages):
        if not isinstance(msg, dict):
            issues.append(f"a2ui[{idx}] is {type(msg).__name__}, not object")
            continue
        if "dataModelUpdate" in msg and isinstance(msg["dataModelUpdate"], dict):
            if "path" not in msg["dataModelUpdate"]:
                issues.append(
                    f"a2ui[{idx}]: dataModelUpdate missing 'path' field"
                )
    return issues


def render_check(a2ui_messages: list[dict[str, Any]]) -> tuple[bool, list[str]]:
    """Check A2UI messages for render-critical issues.

    Returns (pass, list_of_issue_descriptions).
    """
    if not a2ui_messages:
        return True, []

    issues: list[str] = []

    # Rule 3: single surfaceId (message-level check)
    issue = _check_single_surface_id(a2ui_messages)
    if issue:
        issues.append(issue)

    # Rule 7: dataModelUpdate missing path (message-level check)
    issues.extend(_check_data_model_update_missing_path(a2ui_messages))

    # Component-level checks
    for idx, msg in enumerate(a2ui_messages):
        if not isinstance(msg, dict):
            issues.append(f"a2ui[{idx}] is {type(msg).__name__}, not object")
            continue
        su = msg.get("surfaceUpdate")
        if not isinstance(su, dict):
            continue
        components = su.get("components", [])
        if not isinstance(components, list):
            issues.append(
                f"a2ui[{idx}].surfaceUpdate.components is {type(components).__name__}, not list"
            )
            continue
        issues.extend(_check_component_entries_are_dicts(components))

        # Rule 2: TickSlider inside Row (needs full component list)
        issues.extend(_check_tickslider_in_row(components))

        # Per-component checks
        for comp in components:
            if not isinstance(comp, dict):
                continue
            comp_dict = comp.get("component", {})
            if not isinstance(comp_dict, dict):
                continue
            for comp_type, props in comp_dict.items():
                if not isinstance(props, dict):
                    continue
                # Rule 1: selection missing literalArray
                issue = _check_selection_missing_literal_array(comp_type, props)
                if issue:
                    issues.append(issue)
                # Rule 4: Button.action.context not array
                issue = _check_button_action_context_not_array(comp_type, props)
                if issue:
                    issues.append(issue)
                # Rule 5: selection item value wrapped
                issues.extend(
                    _check_selection_item_value_wrapped(comp_type, props)
                )
                # Rule 6: DateTimeInput fields wrapped
                issues.extend(_check_datetime_fields_wrapped(comp_type, props))

    return len(issues) == 0, issues
