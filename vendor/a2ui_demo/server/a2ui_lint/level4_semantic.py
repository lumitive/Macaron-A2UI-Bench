"""Level 4: Semantic / best-practice lint checks.

These are mostly WARNINGs for suboptimal patterns that won't break rendering
but often indicate lossy schema transforms or broken interaction semantics.
"""

from __future__ import annotations

from .context import ValidationContext
from .diagnostics import Diagnostic, DiagnosticCode, Severity, ValidationResult

C = DiagnosticCode
S = Severity

MAX_NESTING_DEPTH = 10
_PROMPT_MARKERS = ("please specify",)
_INPUT_COMPONENT_TYPES = {
    "ActionSelectionList",
    "Button",
    "CheckBox",
    "DateTimeInput",
    "DropdownSelection",
    "MultipleChoice",
    "OrderedSelectionList",
    "PasswordKeypad",
    "SelectionGrid",
    "SelectionList",
    "TextField",
    "TickSlider",
}
_SECURE_INPUT_PATH_HINTS = {"code", "otp", "pass", "passcode", "password", "pin"}


def check_level4(ctx: ValidationContext) -> ValidationResult:
    result = ValidationResult()
    _check_missing_message_types(ctx, result)
    _check_message_order(ctx, result)
    _check_duplicate_begin_rendering(ctx, result)
    _check_weight_outside_flex(ctx, result)
    _check_nesting_depth(ctx, result)
    _check_empty_children(ctx, result)
    _check_prompt_without_input(ctx, result)
    _check_password_keypad_misuse(ctx, result)
    _check_datetime_literal_only(ctx, result)
    _check_modal_trigger_wiring(ctx, result)
    _check_slider_label_overflow_risk(ctx, result)
    _check_selection_binding_scalar(ctx, result)
    _check_selection_single_item_proxy(ctx, result)
    return result


def _check_missing_message_types(ctx: ValidationContext, result: ValidationResult) -> None:
    if not ctx.begin_renderings:
        result.add(
            Diagnostic(
                S.WARNING,
                C.LINT_MISSING_MESSAGE_TYPE,
                "No beginRendering message found",
                suggestion="Add a beginRendering message to initialize the surface.",
            )
        )
    if not ctx.surface_updates:
        result.add(
            Diagnostic(
                S.WARNING,
                C.LINT_MISSING_MESSAGE_TYPE,
                "No surfaceUpdate message found",
                suggestion="Add a surfaceUpdate message to define components.",
            )
        )
    if not ctx.data_model_updates and _needs_data_model_update(ctx):
        result.add(
            Diagnostic(
                S.WARNING,
                C.LINT_MISSING_MESSAGE_TYPE,
                "No dataModelUpdate message found",
                suggestion="Add a dataModelUpdate message to populate data.",
            )
        )


def _needs_data_model_update(ctx: ValidationContext) -> bool:
    if ctx.template_bindings:
        return True
    for info in ctx.components.values():
        if _contains_data_path_ref(info.comp_props):
            return True
    return False


def _contains_data_path_ref(obj: object) -> bool:
    if isinstance(obj, dict):
        path = obj.get("path")
        if isinstance(path, str):
            return True
        for v in obj.values():
            if _contains_data_path_ref(v):
                return True
    elif isinstance(obj, list):
        for item in obj:
            if _contains_data_path_ref(item):
                return True
    return False


def _check_message_order(ctx: ValidationContext, result: ValidationResult) -> None:
    first_begin_by_surface = _first_index_by_surface(ctx.begin_renderings)
    first_surface_by_surface = _first_index_by_surface(ctx.surface_updates)

    for surface_id, begin_idx in first_begin_by_surface.items():
        surface_idx = first_surface_by_surface.get(surface_id)
        if surface_idx is None:
            result.add(
                Diagnostic(
                    S.WARNING,
                    C.LINT_MESSAGE_ORDER,
                    f"Surface '{surface_id}' has beginRendering but no prior surfaceUpdate",
                    suggestion="Send at least one surfaceUpdate before beginRendering for this surface.",
                )
            )
            continue
        if begin_idx < surface_idx:
            result.add(
                Diagnostic(
                    S.WARNING,
                    C.LINT_MESSAGE_ORDER,
                    f"beginRendering for surface '{surface_id}' appears before initial surfaceUpdate",
                    suggestion="Reorder messages for this surface: surfaceUpdate first, then beginRendering.",
                )
            )


def _first_index_by_surface(entries: list[tuple[int, dict]]) -> dict[str, int]:
    first: dict[str, int] = {}
    for msg_idx, payload in entries:
        if not isinstance(payload, dict):
            continue
        surface_id = payload.get("surfaceId")
        if not isinstance(surface_id, str) or not surface_id:
            continue
        if surface_id not in first:
            first[surface_id] = msg_idx
    return first


def _check_duplicate_begin_rendering(ctx: ValidationContext, result: ValidationResult) -> None:
    counts: dict[str, int] = {}
    for _, payload in ctx.begin_renderings:
        surface_id = payload.get("surfaceId")
        if isinstance(surface_id, str) and surface_id:
            counts[surface_id] = counts.get(surface_id, 0) + 1

    for surface_id, count in counts.items():
        if count > 1:
            result.add(
                Diagnostic(
                    S.WARNING,
                    C.LINT_DUPLICATE_BEGIN_RENDERING,
                    f"Surface '{surface_id}' has {count} beginRendering messages",
                    suggestion="Keep only one beginRendering per surface unless you intentionally restart rendering.",
                )
            )


def _check_weight_outside_flex(ctx: ValidationContext, result: ValidationResult) -> None:
    flex_children: set[str] = set()
    for comp_id, info in ctx.components.items():
        if info.comp_type in ("Row", "Column"):
            for child_id in ctx.children_graph.get(comp_id, []):
                flex_children.add(child_id)

    for comp_id, info in ctx.components.items():
        if "weight" in info.comp_dict and comp_id not in flex_children:
            result.add(
                Diagnostic(
                    S.WARNING,
                    C.LINT_WEIGHT_OUTSIDE_FLEX,
                    f"Component '{comp_id}' has 'weight' but is not a direct child of Row/Column",
                    path=f"/messages/{info.msg_idx}/surfaceUpdate/components/{info.comp_idx}/weight",
                    suggestion="'weight' (flex-grow) only works on direct children of Row or Column.",
                )
            )


def _check_nesting_depth(ctx: ValidationContext, result: ValidationResult) -> None:
    if not ctx.root_ids:
        return

    def depth(cid: str, visited: set[str]) -> int:
        if cid in visited or cid not in ctx.components:
            return 0
        visited.add(cid)
        children = ctx.children_graph.get(cid, [])
        if not children:
            return 1
        return 1 + max(depth(child, visited) for child in children)

    for root in ctx.root_ids:
        tree_depth = depth(root, set())
        if tree_depth > MAX_NESTING_DEPTH:
            result.add(
                Diagnostic(
                    S.WARNING,
                    C.LINT_DEEP_NESTING,
                    f"Component tree rooted at '{root}' has nesting depth {tree_depth} (max recommended: {MAX_NESTING_DEPTH})",
                    suggestion="Consider flattening the component hierarchy.",
                )
            )


def _check_empty_children(ctx: ValidationContext, result: ValidationResult) -> None:
    container_children_types = ctx.schema.container_children_types
    for comp_id, info in ctx.components.items():
        if info.comp_type in container_children_types:
            children_obj = info.comp_props.get("children", {})
            if isinstance(children_obj, dict):
                explicit = children_obj.get("explicitList")
                template = children_obj.get("template")
                if explicit is not None and isinstance(explicit, list) and len(explicit) == 0:
                    result.add(
                        Diagnostic(
                            S.WARNING,
                            C.LINT_EMPTY_CHILDREN,
                            f"{info.comp_type} '{comp_id}' has empty explicitList",
                            path=f"/messages/{info.msg_idx}/surfaceUpdate/components/{info.comp_idx}",
                            suggestion="Add child component IDs or use a template.",
                        )
                    )
                if explicit is None and template is None:
                    result.add(
                        Diagnostic(
                            S.WARNING,
                            C.LINT_EMPTY_CHILDREN,
                            f"{info.comp_type} '{comp_id}' has no explicitList or template in children",
                            path=f"/messages/{info.msg_idx}/surfaceUpdate/components/{info.comp_idx}",
                            suggestion="Add either 'explicitList' or 'template' to children.",
                        )
                    )

        if info.comp_type == "Tabs":
            tab_items = info.comp_props.get("tabItems")
            if isinstance(tab_items, list) and len(tab_items) == 0:
                result.add(
                    Diagnostic(
                        S.WARNING,
                        C.LINT_EMPTY_CHILDREN,
                        f"Tabs '{comp_id}' has empty tabItems",
                        path=f"/messages/{info.msg_idx}/surfaceUpdate/components/{info.comp_idx}",
                        suggestion="Add at least one tab item.",
                    )
                )


def _check_prompt_without_input(ctx: ValidationContext, result: ValidationResult) -> None:
    if not ctx.root_ids:
        return

    model = _build_root_model(ctx)
    subtitle = model.get("subtitle")
    if not isinstance(subtitle, str):
        return
    subtitle_lower = subtitle.lower()
    if not any(marker in subtitle_lower for marker in _PROMPT_MARKERS):
        return

    reachable = _reachable_components(ctx)
    has_input = any(
        ctx.components[comp_id].comp_type in _INPUT_COMPONENT_TYPES
        for comp_id in reachable
        if comp_id in ctx.components
    )
    if has_input:
        return

    result.add(
        Diagnostic(
            S.WARNING,
            C.LINT_PROMPT_WITHOUT_INPUT,
            f"Prompt text '{subtitle}' asks for user input but no reachable input component exists",
            suggestion="Either add a reachable input component or keep this clarification in natural-language chat instead of a card.",
        )
    )


def _check_password_keypad_misuse(ctx: ValidationContext, result: ValidationResult) -> None:
    for comp_id, info in ctx.components.items():
        if info.comp_type != "PasswordKeypad":
            continue
        value_ref = info.comp_props.get("value")
        path = value_ref.get("path") if isinstance(value_ref, dict) else None
        if not isinstance(path, str) or not path:
            continue
        normalized_path = path.lower().replace("-", "_")
        if any(hint in normalized_path for hint in _SECURE_INPUT_PATH_HINTS):
            continue
        result.add(
            Diagnostic(
                S.WARNING,
                C.LINT_PASSWORD_KEYPAD_MISUSE,
                f"PasswordKeypad '{comp_id}' is bound to '{path}', which does not look like a secure credential field",
                path=f"/messages/{info.msg_idx}/surfaceUpdate/components/{info.comp_idx}/component/PasswordKeypad",
                suggestion="Use PasswordKeypad only for password/PIN/OTP flows. For generic text collection, prefer TextField or plain chat.",
            )
        )


def _check_datetime_literal_only(ctx: ValidationContext, result: ValidationResult) -> None:
    for comp_id, info in ctx.components.items():
        if info.comp_type != "DateTimeInput":
            continue
        value_ref = info.comp_props.get("value")
        path = value_ref.get("path") if isinstance(value_ref, dict) else None
        if isinstance(path, str) and path:
            continue
        result.add(
            Diagnostic(
                S.WARNING,
                C.LINT_DATETIME_LITERAL_ONLY,
                f"DateTimeInput '{comp_id}' has no writable value.path binding",
                path=f"/messages/{info.msg_idx}/surfaceUpdate/components/{info.comp_idx}/component/DateTimeInput/value",
                suggestion="Bind DateTimeInput.value to a data path when the picker is meant to collect user input.",
            )
        )


def _check_modal_trigger_wiring(ctx: ValidationContext, result: ValidationResult) -> None:
    for comp_id, info in ctx.components.items():
        if info.comp_type != "FullScreenModal":
            continue
        entry_point_child = info.comp_props.get("entryPointChild")
        if not isinstance(entry_point_child, str):
            continue
        entry_info = ctx.components.get(entry_point_child)
        if entry_info is None or entry_info.comp_type != "Button":
            result.add(
                Diagnostic(
                    S.WARNING,
                    C.LINT_MODAL_TRIGGER_INVALID,
                    f"FullScreenModal '{comp_id}' entryPointChild does not resolve to a Button",
                    suggestion="Set entryPointChild to a Button that dispatches showFullModal with modalId.",
                )
            )
            continue

        action = entry_info.comp_props.get("action")
        if not isinstance(action, dict):
            result.add(
                Diagnostic(
                    S.WARNING,
                    C.LINT_MODAL_TRIGGER_INVALID,
                    f"Button '{entry_point_child}' does not define an action for FullScreenModal '{comp_id}'",
                    suggestion="Wire the entry button to action.name='showFullModal' and include modalId in action.context.",
                )
            )
            continue

        action_name = action.get("name")
        modal_id = _extract_action_context_literal(action.get("context"), "modalId")
        if action_name != "showFullModal" or modal_id != comp_id:
            result.add(
                Diagnostic(
                    S.WARNING,
                    C.LINT_MODAL_TRIGGER_INVALID,
                    f"FullScreenModal '{comp_id}' is wired with action '{action_name}' and modalId '{modal_id or ''}'",
                    suggestion="Use action.name='showFullModal' and set action.context modalId to the FullScreenModal component id.",
                )
            )


def _check_slider_label_overflow_risk(ctx: ValidationContext, result: ValidationResult) -> None:
    model = _build_root_model(ctx)
    for comp_id, info in ctx.components.items():
        if info.comp_type != "Row":
            continue
        children_obj = info.comp_props.get("children")
        explicit = children_obj.get("explicitList") if isinstance(children_obj, dict) else None
        if not isinstance(explicit, list) or len(explicit) != 2:
            continue
        parent_id = ctx.parent_graph.get(comp_id)
        if parent_id is None:
            continue
        sibling_ids = ctx.children_graph.get(parent_id, [])
        if not any(
            sibling_id != comp_id
            and ctx.components.get(sibling_id, None) is not None
            and ctx.components[sibling_id].comp_type == "TickSlider"
            for sibling_id in sibling_ids
        ):
            continue

        labels = [
            _resolve_label_text(ctx.components.get(child_id), model)
            for child_id in explicit
            if isinstance(child_id, str)
        ]
        labels = [label for label in labels if label]
        if len(labels) != 2:
            continue
        if max(len(label) for label in labels) < 24 and sum(len(label) for label in labels) < 44:
            continue
        result.add(
            Diagnostic(
                S.WARNING,
                C.LINT_SLIDER_LABEL_OVERFLOW_RISK,
                f"Row '{comp_id}' uses long end labels next to a TickSlider: '{labels[0]}' / '{labels[1]}'",
                suggestion="Keep slider endpoints short and move longer guidance into a separate title or helper text.",
            )
        )


def _check_selection_binding_scalar(ctx: ValidationContext, result: ValidationResult) -> None:
    for comp_id, info in ctx.components.items():
        if info.comp_type != "SelectionList":
            continue
        selection = info.comp_props.get("selection")
        path = selection.get("path") if isinstance(selection, dict) else None
        if not isinstance(path, str) or not path.startswith("/"):
            continue
        actual_type = _find_value_type_at_path(ctx, path)
        if actual_type not in {"valueBoolean", "valueNumber", "valueString"}:
            continue
        result.add(
            Diagnostic(
                S.WARNING,
                C.LINT_SELECTION_BINDING_SCALAR,
                f"SelectionList '{comp_id}' writes to scalar data path '{path}' ({actual_type})",
                path=f"/messages/{info.msg_idx}/surfaceUpdate/components/{info.comp_idx}/component/SelectionList/selection/path",
                suggestion="Bind SelectionList to an array-like selection path, or use CheckBox/TextField for scalar values.",
            )
        )


def _check_selection_single_item_proxy(ctx: ValidationContext, result: ValidationResult) -> None:
    for comp_id, info in ctx.components.items():
        if info.comp_type != "SelectionList":
            continue
        items = info.comp_props.get("items")
        max_selection = info.comp_props.get("maxSelection", 1)
        if not isinstance(items, list) or len(items) != 1 or max_selection != 1:
            continue
        result.add(
            Diagnostic(
                S.WARNING,
                C.LINT_SELECTION_SINGLE_ITEM_PROXY,
                f"SelectionList '{comp_id}' contains only one selectable item",
                path=f"/messages/{info.msg_idx}/surfaceUpdate/components/{info.comp_idx}/component/SelectionList/items",
                suggestion="Single-item SelectionList behaves like a checkbox proxy. Use it only for explicit opt-in semantics or switch to CheckBox.",
            )
        )


def _reachable_components(ctx: ValidationContext) -> set[str]:
    reachable: set[str] = set()
    queue = list(ctx.root_ids)
    while queue:
        comp_id = queue.pop()
        if comp_id in reachable:
            continue
        reachable.add(comp_id)
        queue.extend(ctx.children_graph.get(comp_id, []))
    return reachable


def _build_root_model(ctx: ValidationContext) -> dict[str, object]:
    model: dict[str, object] = {}
    for _, payload in ctx.data_model_updates:
        if not isinstance(payload, dict):
            continue
        path = payload.get("path", "/")
        if path != "/":
            continue
        contents = payload.get("contents")
        if isinstance(contents, list):
            model.update(_parse_data_model_entries(contents))
    return model


def _parse_data_model_entries(entries: list[object]) -> dict[str, object]:
    parsed: dict[str, object] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        key = entry.get("key")
        if not isinstance(key, str) or not key:
            continue
        for value_key in ("valueString", "valueNumber", "valueBoolean", "valueMap"):
            if value_key not in entry:
                continue
            value = entry[value_key]
            if value_key == "valueMap" and isinstance(value, list):
                value = _parse_data_model_entries(value)
            parsed[key] = value
            break
    return parsed


def _resolve_label_text(info: object, model: dict[str, object]) -> str | None:
    if info is None or not hasattr(info, "comp_type") or not hasattr(info, "comp_props"):
        return None
    comp_type = getattr(info, "comp_type")
    comp_props = getattr(info, "comp_props")
    if comp_type not in {"Label", "Text"} or not isinstance(comp_props, dict):
        return None
    text_ref = comp_props.get("text")
    if not isinstance(text_ref, dict):
        return None
    literal = text_ref.get("literalString")
    if isinstance(literal, str) and literal:
        return literal
    path = text_ref.get("path")
    if not isinstance(path, str) or not path.startswith("/"):
        return None
    current: object = model
    for segment in [part for part in path.split("/") if part]:
        if not isinstance(current, dict):
            return None
        current = current.get(segment)
    return current if isinstance(current, str) else None


def _extract_action_context_literal(context: object, key: str) -> str | None:
    if not isinstance(context, list):
        return None
    for item in context:
        if not isinstance(item, dict) or item.get("key") != key:
            continue
        value = item.get("value")
        if not isinstance(value, dict):
            continue
        literal = value.get("literalString")
        if isinstance(literal, str) and literal:
            return literal
    return None


def _find_value_type_at_path(ctx: ValidationContext, target_path: str) -> str | None:
    for _, payload in ctx.data_model_updates:
        if not isinstance(payload, dict):
            continue
        base = payload.get("path", "/")
        if not isinstance(base, str):
            base = "/"
        if not base.startswith("/"):
            base = f"/{base}"
        contents = payload.get("contents")
        if not isinstance(contents, list):
            continue
        found = _search_entries(base, contents, target_path)
        if found:
            return found
    return None


def _search_entries(prefix: str, entries: list[object], target_path: str) -> str | None:
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        key = entry.get("key")
        if not isinstance(key, str) or not key:
            continue
        path = f"{prefix.rstrip('/')}/{key}" if prefix != "/" else f"/{key}"
        if path == target_path:
            for value_key in ("valueString", "valueNumber", "valueBoolean", "valueMap"):
                if value_key in entry:
                    return value_key
        value_map = entry.get("valueMap")
        if isinstance(value_map, list):
            found = _search_entries(path, value_map, target_path)
            if found:
                return found
    return None
