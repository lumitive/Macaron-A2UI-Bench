from __future__ import annotations

import sys
from pathlib import Path

from protocol.types import ProtocolStack
from protocol.v0_8.guides import COMPONENT_SCHEMA_CONTEXT, GENERATION_GUIDE

_ROOT = Path(__file__).resolve().parents[2]
_VENDOR = _ROOT / "vendor"
if str(_VENDOR) not in sys.path:
    sys.path.insert(0, str(_VENDOR))

from a2ui_demo.server.a2ui_lint import validate  # type: ignore
from render_check import render_check


def build_stack() -> ProtocolStack:
    return ProtocolStack(
        version="0.8",
        catalog_id="legacy-0.8-vendor-a2ui-demo",  # local sentinel; not an upstream catalog URI
        strip_gt_a2ui=False,
        generation_guide=GENERATION_GUIDE,
        validate=validate,
        render_check=render_check,
        component_schema_context=COMPONENT_SCHEMA_CONTEXT,
    )
