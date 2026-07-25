"""Render-critical detection for A2UI v0.9.1 messages.

Detection-only — returns issues found, does NOT fix them.
Phase 1 rules focus on renderability of the basic catalog wire format.
"""

from __future__ import annotations

from typing import Any

from protocol.v0_9_1.catalog import get_catalog

LEGACY_ACTIONS = frozenset({"beginRendering", "surfaceUpdate", "dataModelUpdate"})
VALID_ACTIONS = frozenset(
    {"createSurface", "updateComponents", "updateDataModel", "deleteSurface"}
)
_SURFACE_ACTIONS = frozenset(
    {
        "createSurface",
        "updateComponents",
        "updateDataModel",
        "deleteSurface",
        "beginRendering",
        "surfaceUpdate",
        "dataModelUpdate",
    }
)


def render_check(
    a2ui_messages: list[dict],
    *,
    catalog_name: str = "basic",
) -> tuple[bool, list[str]]:
    """Check A2UI v0.9.1 messages for render-critical issues.

    Returns (pass, list_of_issue_descriptions).
    """
    expected_catalog_id = get_catalog(catalog_name).catalog_id
    if not a2ui_messages:
        return True, []

    issues: list[str] = []
    surface_ids: list[str] = []
    component_ids: set[str] = set()
    saw_any_components = False
    saw_create_surface = False
    saw_component_or_data_update = False

    for idx, msg in enumerate(a2ui_messages):
        if not isinstance(msg, dict):
            issues.append(f"a2ui[{idx}] is {type(msg).__name__}, not object")
            continue

        legacy_keys = [k for k in msg if k in LEGACY_ACTIONS]
        if legacy_keys:
            issues.append(
                f"a2ui[{idx}]: legacy 0.8 action key(s) {legacy_keys} — "
                "use createSurface/updateComponents/updateDataModel/deleteSurface"
            )
            # Still collect surfaceIds from legacy payloads for multi-surface rule.
            for key in legacy_keys:
                payload = msg.get(key)
                if isinstance(payload, dict):
                    _collect_surface_id(payload, surface_ids)
            continue

        for key in _SURFACE_ACTIONS:
            if key in msg and isinstance(msg[key], dict):
                _collect_surface_id(msg[key], surface_ids)

        if "createSurface" in msg:
            saw_create_surface = True
            cs = msg["createSurface"]
            if isinstance(cs, dict):
                catalog_id = cs.get("catalogId")
                if catalog_id is None or catalog_id == "":
                    issues.append(
                        f"a2ui[{idx}]: createSurface missing required catalogId "
                        f'(expected "{expected_catalog_id}")'
                    )
                elif catalog_id != expected_catalog_id:
                    issues.append(
                        f"a2ui[{idx}]: createSurface catalogId {catalog_id!r} "
                        f"does not match active catalog ({expected_catalog_id!r})"
                    )

        if "updateDataModel" in msg:
            saw_component_or_data_update = True

        if "updateComponents" in msg:
            saw_component_or_data_update = True
            uc = msg["updateComponents"]
            if not isinstance(uc, dict):
                issues.append(
                    f"a2ui[{idx}]: updateComponents must be an object"
                )
                continue
            comps = uc.get("components", [])
            if not isinstance(comps, list):
                issues.append(
                    f"a2ui[{idx}]: updateComponents.components is "
                    f"{type(comps).__name__}, not list"
                )
                continue
            for ci, comp in enumerate(comps):
                if not isinstance(comp, dict):
                    issues.append(
                        f"a2ui[{idx}].updateComponents.components[{ci}] is "
                        f"{type(comp).__name__}, not object"
                    )
                    continue
                saw_any_components = True
                cid = comp.get("id")
                if isinstance(cid, str) and cid:
                    component_ids.add(cid)
                disc = comp.get("component")
                if disc is None:
                    issues.append(
                        f"a2ui[{idx}].components[{ci}] (id={cid!r}): "
                        "missing string 'component' discriminator"
                    )
                elif isinstance(disc, dict):
                    issues.append(
                        f"a2ui[{idx}].components[{ci}] (id={cid!r}): "
                        "key-wrapped legacy 0.8 component shape — "
                        'use string discriminator e.g. "component": "Text"'
                    )
                elif not isinstance(disc, str):
                    issues.append(
                        f"a2ui[{idx}].components[{ci}] (id={cid!r}): "
                        "component discriminator must be a string"
                    )

    if saw_component_or_data_update and not saw_create_surface:
        issues.append(
            "updateComponents/updateDataModel without createSurface in the same "
            "batch — v0.9.1 requires createSurface before component/data updates"
        )

    if len(surface_ids) > 1:
        issues.append(
            f"Multiple surfaceIds found: {surface_ids} — "
            "only one surfaceId per response is supported"
        )

    if saw_any_components and "root" not in component_ids:
        issues.append(
            "No component with id 'root' after updateComponents — "
            "v0.9.1 requires a root component for rendering"
        )

    return len(issues) == 0, issues


def _collect_surface_id(payload: dict[str, Any], surface_ids: list[str]) -> None:
    sid = payload.get("surfaceId", "")
    if isinstance(sid, str) and sid and sid not in surface_ids:
        surface_ids.append(sid)
