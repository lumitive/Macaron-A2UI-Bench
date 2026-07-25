from __future__ import annotations

from functools import partial

from protocol.types import ProtocolStack
from protocol.v0_9_1.catalog import get_catalog
from protocol.v0_9_1.guides import (
    build_component_schema_context,
    build_generation_guide,
)
from protocol.v0_9_1.lint import LOCKED_CATALOG_ID, validate
from protocol.v0_9_1.render_check import render_check

CATALOG_ID = LOCKED_CATALOG_ID


def build_stack(catalog: str = "basic") -> ProtocolStack:
    info = get_catalog(catalog)
    return ProtocolStack(
        version="0.9.1",
        catalog_id=info.catalog_id,
        catalog_name=info.name,
        # True ⇒ filter_episode_gt_a2ui (keep validating 0.9.1 gold; strip 0.8).
        strip_gt_a2ui=True,
        generation_guide=build_generation_guide(info.name),
        validate=partial(validate, catalog_name=info.name),
        render_check=partial(render_check, catalog_name=info.name),
        component_schema_context=build_component_schema_context(info.name),
    )
