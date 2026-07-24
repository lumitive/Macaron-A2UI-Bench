from __future__ import annotations

from protocol.types import ProtocolStack
from protocol.v0_9_1.guides import COMPONENT_SCHEMA_CONTEXT, GENERATION_GUIDE
from protocol.v0_9_1.lint import LOCKED_CATALOG_ID, validate
from protocol.v0_9_1.render_check import render_check

CATALOG_ID = LOCKED_CATALOG_ID


def build_stack() -> ProtocolStack:
    return ProtocolStack(
        version="0.9.1",
        catalog_id=CATALOG_ID,
        strip_gt_a2ui=True,
        generation_guide=GENERATION_GUIDE,
        validate=validate,
        render_check=render_check,
        component_schema_context=COMPONENT_SCHEMA_CONTEXT,
    )
