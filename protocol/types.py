from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Literal

ProtocolVersion = Literal["0.8", "0.9.1"]

ValidateFn = Callable[..., Any]
RenderCheckFn = Callable[[list[dict[str, Any]]], tuple[bool, list[str]]]


@dataclass(frozen=True)
class ProtocolStack:
    version: ProtocolVersion
    catalog_id: str
    strip_gt_a2ui: bool
    generation_guide: str
    validate: ValidateFn
    render_check: RenderCheckFn
    component_schema_context: str
    catalog_name: str = "basic"
