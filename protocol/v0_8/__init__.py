from __future__ import annotations

from typing import Any

from protocol.types import ProtocolStack


def _not_implemented_validate(*args: Any, **kwargs: Any) -> Any:
    raise NotImplementedError("0.8 validate adapter pending Task 2")


def _not_implemented_render_check(
    messages: list[dict[str, Any]],
) -> tuple[bool, list[str]]:
    raise NotImplementedError("0.8 render_check adapter pending Task 2")


def build_stack() -> ProtocolStack:
    return ProtocolStack(
        version="0.8",
        catalog_id="",
        strip_gt_a2ui=False,
        generation_guide="",
        validate=_not_implemented_validate,
        render_check=_not_implemented_render_check,
        component_schema_context="",
    )
