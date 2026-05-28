"""Level 2: Reference integrity checks.

Validates that component references resolve, detects orphans, cycles,
and duplicate IDs.
"""

from __future__ import annotations

from .context import ValidationContext
from .diagnostics import Diagnostic, DiagnosticCode, Severity, ValidationResult

C = DiagnosticCode
S = Severity


def check_level2(ctx: ValidationContext) -> ValidationResult:
    result = ValidationResult()
    _check_root_refs(ctx, result)
    _check_child_refs(ctx, result)
    _check_explicit_list_refs(ctx, result)
    _check_template_refs(ctx, result)
    _check_tab_refs(ctx, result)
    _check_duplicate_ids(ctx, result)
    _check_orphans(ctx, result)
    _check_cycles(ctx, result)
    return result


# ---------------------------------------------------------------------------
# root references
# ---------------------------------------------------------------------------

def _check_root_refs(ctx: ValidationContext, result: ValidationResult) -> None:
    for msg_idx, br in ctx.begin_renderings:
        root = br.get("root")
        if isinstance(root, str) and root not in ctx.components:
            result.add(Diagnostic(S.ERROR, C.REF_MISSING_ROOT,
                f"beginRendering.root references non-existent component '{root}'",
                path=f"/messages/{msg_idx}/beginRendering/root",
                suggestion=f"Ensure a component with id=\"{root}\" exists in surfaceUpdate."))


# ---------------------------------------------------------------------------
# single-child refs (Card.child, Button.child, Modal.*)
# ---------------------------------------------------------------------------

def _check_child_refs(ctx: ValidationContext, result: ValidationResult) -> None:
    container_child_fields = ctx.schema.container_child_fields
    for comp_id, info in ctx.components.items():
        if info.comp_type not in container_child_fields:
            continue
        for field_name in container_child_fields[info.comp_type]:
            child = info.comp_props.get(field_name)
            if isinstance(child, str) and child not in ctx.components:
                result.add(Diagnostic(S.ERROR, C.REF_MISSING_COMPONENT,
                    f"{info.comp_type}.{field_name} references non-existent component '{child}'",
                    path=f"/messages/{info.msg_idx}/surfaceUpdate/components/{info.comp_idx}/component/{info.comp_type}/{field_name}",
                    suggestion=f"Add a component with id=\"{child}\" to surfaceUpdate.components."))


# ---------------------------------------------------------------------------
# explicitList refs
# ---------------------------------------------------------------------------

def _check_explicit_list_refs(ctx: ValidationContext, result: ValidationResult) -> None:
    container_children_types = ctx.schema.container_children_types
    for comp_id, info in ctx.components.items():
        if info.comp_type not in container_children_types:
            continue
        children_obj = info.comp_props.get("children", {})
        if not isinstance(children_obj, dict):
            continue
        explicit = children_obj.get("explicitList", [])
        if not isinstance(explicit, list):
            continue
        for i, cid in enumerate(explicit):
            if isinstance(cid, str) and cid not in ctx.components:
                result.add(Diagnostic(S.ERROR, C.REF_MISSING_COMPONENT,
                    f"{info.comp_type} explicitList[{i}] references non-existent component '{cid}'",
                    path=f"/messages/{info.msg_idx}/surfaceUpdate/components/{info.comp_idx}/component/{info.comp_type}/children/explicitList/{i}",
                    suggestion=f"Add a component with id=\"{cid}\" to surfaceUpdate.components."))


# ---------------------------------------------------------------------------
# template refs
# ---------------------------------------------------------------------------

def _check_template_refs(ctx: ValidationContext, result: ValidationResult) -> None:
    container_children_types = ctx.schema.container_children_types
    for comp_id, info in ctx.components.items():
        if info.comp_type not in container_children_types:
            continue
        children_obj = info.comp_props.get("children", {})
        if not isinstance(children_obj, dict):
            continue
        template = children_obj.get("template", {})
        if not isinstance(template, dict):
            continue
        tid = template.get("componentId")
        if isinstance(tid, str) and tid not in ctx.components:
            result.add(Diagnostic(S.ERROR, C.REF_MISSING_COMPONENT,
                f"template.componentId references non-existent component '{tid}'",
                path=f"/messages/{info.msg_idx}/surfaceUpdate/components/{info.comp_idx}/component/{info.comp_type}/children/template/componentId",
                suggestion=f"Add a component with id=\"{tid}\" to surfaceUpdate.components."))


# ---------------------------------------------------------------------------
# tab item child refs
# ---------------------------------------------------------------------------

def _check_tab_refs(ctx: ValidationContext, result: ValidationResult) -> None:
    for comp_id, info in ctx.components.items():
        if info.comp_type != "Tabs":
            continue
        tab_items = info.comp_props.get("tabItems", [])
        if not isinstance(tab_items, list):
            continue
        for ti, tab in enumerate(tab_items):
            if not isinstance(tab, dict):
                continue
            child = tab.get("child")
            if isinstance(child, str) and child not in ctx.components:
                result.add(Diagnostic(S.ERROR, C.REF_MISSING_COMPONENT,
                    f"Tabs.tabItems[{ti}].child references non-existent component '{child}'",
                    path=f"/messages/{info.msg_idx}/surfaceUpdate/components/{info.comp_idx}/component/Tabs/tabItems/{ti}/child",
                    suggestion=f"Add a component with id=\"{child}\" to surfaceUpdate.components."))


# ---------------------------------------------------------------------------
# duplicate IDs
# ---------------------------------------------------------------------------

def _check_duplicate_ids(ctx: ValidationContext, result: ValidationResult) -> None:
    for comp_id, locs in ctx.duplicate_ids.items():
        loc_strs = [f"messages/{m}/surfaceUpdate/components/{c}" for m, c in locs]
        result.add(Diagnostic(S.ERROR, C.REF_DUPLICATE_ID,
            f"Duplicate component ID '{comp_id}' found at: {', '.join(loc_strs)}",
            suggestion=f"Each component ID must be unique. Rename duplicates of '{comp_id}'."))


# ---------------------------------------------------------------------------
# orphan components (unreachable from root)
# ---------------------------------------------------------------------------

def _check_orphans(ctx: ValidationContext, result: ValidationResult) -> None:
    if not ctx.root_ids or not ctx.components:
        return

    # BFS from all roots
    reachable: set[str] = set()
    queue = list(ctx.root_ids)
    while queue:
        cid = queue.pop()
        if cid in reachable:
            continue
        reachable.add(cid)
        for child in ctx.children_graph.get(cid, []):
            if child not in reachable:
                queue.append(child)

    # Any component not reachable and not a template component is orphan
    for comp_id in ctx.components:
        if comp_id not in reachable and comp_id not in ctx.template_component_ids:
            info = ctx.components[comp_id]
            result.add(Diagnostic(S.WARNING, C.REF_ORPHAN_COMPONENT,
                f"Component '{comp_id}' is not reachable from any root",
                path=f"/messages/{info.msg_idx}/surfaceUpdate/components/{info.comp_idx}",
                suggestion="This component may be unused. Check if it should be referenced somewhere."))


# ---------------------------------------------------------------------------
# cycle detection (DFS)
# ---------------------------------------------------------------------------

def _check_cycles(ctx: ValidationContext, result: ValidationResult) -> None:
    WHITE, GRAY, BLACK = 0, 1, 2
    color: dict[str, int] = {cid: WHITE for cid in ctx.components}
    path_stack: list[str] = []

    def dfs(node: str) -> bool:
        color[node] = GRAY
        path_stack.append(node)
        for child in ctx.children_graph.get(node, []):
            if child not in color:
                continue
            if color[child] == GRAY:
                # Found cycle
                cycle_start = path_stack.index(child)
                cycle = path_stack[cycle_start:] + [child]
                result.add(Diagnostic(S.ERROR, C.REF_CYCLE,
                    f"Circular reference detected: {' → '.join(cycle)}",
                    suggestion="Break the cycle by removing one of the references."))
                path_stack.pop()
                color[node] = BLACK
                return True
            if color[child] == WHITE:
                if dfs(child):
                    path_stack.pop()
                    color[node] = BLACK
                    return False  # already reported
        path_stack.pop()
        color[node] = BLACK
        return False

    for cid in ctx.components:
        if color.get(cid, WHITE) == WHITE:
            dfs(cid)
