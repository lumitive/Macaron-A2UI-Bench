from __future__ import annotations

from typing import Any

from protocol.types import ProtocolStack
from protocol.v0_9_1.lint import LOCKED_CATALOG_ID, validate

CATALOG_ID = LOCKED_CATALOG_ID


def _not_implemented_render_check(
    messages: list[dict[str, Any]],
) -> tuple[bool, list[str]]:
    raise NotImplementedError("0.9.1 render_check pending Task 4")


def build_stack() -> ProtocolStack:
    return ProtocolStack(
        version="0.9.1",
        catalog_id=CATALOG_ID,
        strip_gt_a2ui=True,
        generation_guide="",
        validate=validate,
        render_check=_not_implemented_render_check,
        component_schema_context="",
    )
