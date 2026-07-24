from __future__ import annotations

from typing import Any

from protocol.types import ProtocolStack

CATALOG_ID = "https://a2ui.org/specification/v0_9/catalogs/basic/catalog.json"


def _not_implemented_validate(*args: Any, **kwargs: Any) -> Any:
    raise NotImplementedError("0.9.1 validate pending Task 3")


def _not_implemented_render_check(
    messages: list[dict[str, Any]],
) -> tuple[bool, list[str]]:
    raise NotImplementedError("0.9.1 render_check pending Task 3")


def build_stack() -> ProtocolStack:
    return ProtocolStack(
        version="0.9.1",
        catalog_id=CATALOG_ID,
        strip_gt_a2ui=True,
        generation_guide="",
        validate=_not_implemented_validate,
        render_check=_not_implemented_render_check,
        component_schema_context="",
    )
