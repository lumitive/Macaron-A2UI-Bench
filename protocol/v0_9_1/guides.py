"""0.9.1 generation guide and judge schema context.

Built from the vendored basic catalog + rules.txt. Protocol must not import
evaluate_api_model (avoids circular imports).
"""

from __future__ import annotations

import json
from pathlib import Path

from protocol.v0_9_1.lint import LOCKED_CATALOG_ID

_SPEC_DIR = Path(__file__).resolve().parent / "spec"
_CATALOG_PATH = _SPEC_DIR / "catalogs" / "basic" / "catalog.json"
_RULES_PATH = _SPEC_DIR / "catalogs" / "basic" / "rules.txt"

GENERATION_GUIDE = f"""You are a conversational AI assistant. Reply with natural language text and optional A2UI messages.

Always output valid JSON:
{{"text_response": "...", "a2ui": [...]}}

# A2UI Protocol v0.9.1

Every message object must include `"version": "v0.9.1"` and exactly one action key.

Allowed message types:
- createSurface: create a surface (required `surfaceId` + `catalogId`)
- updateComponents: define/update the flat component list on a surface
- updateDataModel: write/update data model values (`value` object, optional `path`)
- deleteSurface: remove a surface

Locked basic catalogId (always use this exact string):
{LOCKED_CATALOG_ID}

Component item format (flat string discriminator — NOT 0.8 key-wrapped):
{{"id": "x", "component": "Text", "text": "Hello"}}

Rules:
- Use native JSON literals (strings, numbers, booleans, arrays, objects). Do NOT use 0.8 wrappers like literalString / valueString.
- Do NOT use 0.8 action keys (beginRendering, surfaceUpdate, dataModelUpdate).
- If any components are sent, include a component with `"id": "root"`.
- Prefer a single surfaceId across the response.

Minimal example:
[
  {{
    "version": "v0.9.1",
    "createSurface": {{
      "surfaceId": "main",
      "catalogId": "{LOCKED_CATALOG_ID}"
    }}
  }},
  {{
    "version": "v0.9.1",
    "updateComponents": {{
      "surfaceId": "main",
      "components": [
        {{"id": "root", "component": "Column", "children": ["title"]}},
        {{"id": "title", "component": "Text", "text": "Hello"}}
      ]
    }}
  }}
]

Use ONLY these basic-catalog component names:
- Text: Display text. Required `text`. Optional `variant`.
- Image: Image display. Required `url`. Optional `description`, `fit`, `variant`.
- Icon: Icon display. Field `name`.
- Video: Video player. Required `url`.
- AudioPlayer: Audio player. Required `url`. Optional `description`.
- Row: Horizontal layout. Arrange child IDs in `children`.
- Column: Vertical layout. Arrange child IDs in `children`.
- List: List layout. Field `children`; optional `direction`, `align`.
- Card: Card container. Field `child` (single child id).
- Tabs: Tabbed content. Field `tabs`.
- Modal: Modal dialog. Fields `trigger`, `content`.
- Divider: Visual separator. Optional `axis`.
- Button: Clickable action. Required `action`; usually wire visible content via `child`.
- TextField: Text input. Required `label`; bind via `value`.
- CheckBox: Checkbox. Required `label`; bind via `value`.
- ChoicePicker: Option selection (replaces 0.8 SelectionList). Fields `label`, `options`, `value`; optional `variant`, `displayStyle`, `filterable`.
- Slider: Numeric slider. Fields `label`, `min`, `max`, `value`.
- DateTimeInput: Date/time input. Fields `value`, `label`; optional `enableDate`, `enableTime`, `min`, `max`.
"""


def _component_prop_keys(schema: dict) -> list[str]:
    props: dict = {}
    for part in schema.get("allOf") or []:
        if isinstance(part, dict) and isinstance(part.get("properties"), dict):
            props.update(part["properties"])
    if isinstance(schema.get("properties"), dict):
        props.update(schema["properties"])
    return [k for k in props if k != "component"]


def _component_description(name: str, schema: dict) -> str:
    desc = " ".join(str(schema.get("description", "")).strip().split())
    if desc:
        return desc
    for part in schema.get("allOf") or []:
        if isinstance(part, dict):
            d = " ".join(str(part.get("description", "")).strip().split())
            if d:
                return d
    defaults = {
        "Text": "Plain text display.",
        "Image": "Image display.",
        "Icon": "Icon display.",
        "Video": "Video player.",
        "AudioPlayer": "Audio player.",
        "Row": "Horizontal layout container.",
        "Column": "Vertical layout container.",
        "List": "List layout container.",
        "Card": "Card container shell.",
        "Tabs": "Tabbed content switcher.",
        "Modal": "Modal dialog container.",
        "Divider": "Visual separator.",
        "Button": "Clickable action trigger.",
        "TextField": "Text input field.",
        "CheckBox": "Checkbox input.",
        "ChoicePicker": "Option selection (one or more).",
        "Slider": "Numeric slider input.",
        "DateTimeInput": "Date/time picker input.",
    }
    return defaults.get(name, "A2UI component.")


def _format_props(props: list[str]) -> str:
    if not props:
        return "(none)"
    return ", ".join(props[:8])


def _build_component_schema_context() -> str:
    """Short schema/rules summary for L2/L3 `{component_schema_context}`."""
    fallback = (
        "## Available Components\n"
        "Text, Image, Icon, Video, AudioPlayer, Row, Column, List, Card, Tabs, "
        "Modal, Divider, Button, TextField, CheckBox, ChoicePicker, Slider, "
        "DateTimeInput"
    )
    if not _CATALOG_PATH.exists():
        return fallback

    try:
        catalog = json.loads(_CATALOG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return fallback

    components = catalog.get("components") or {}
    if not isinstance(components, dict) or not components:
        return fallback

    names: list[str] = []
    summary_lines: list[str] = []
    for name in sorted(components):
        schema = components[name]
        if not isinstance(schema, dict):
            continue
        names.append(name)
        props = _component_prop_keys(schema)
        summary_lines.append(
            f"- {name}: {_component_description(name, schema)} "
            f"Key props: {_format_props(props)}"
        )

    rules_block = ""
    if _RULES_PATH.exists():
        rules_text = _RULES_PATH.read_text(encoding="utf-8").strip()
        if rules_text:
            rules_block = "\n\n## Basic Catalog Rules\n" + rules_text

    return (
        "## Available Components\n"
        + ", ".join(names)
        + "\n\n## Component Quick Reference\n"
        + "\n".join(summary_lines)
        + rules_block
        + "\n\n## Wire-format notes\n"
        "- Protocol version: v0.9.1; actions: createSurface / updateComponents / "
        "updateDataModel / deleteSurface.\n"
        f"- Locked catalogId: {LOCKED_CATALOG_ID}\n"
        '- Components use flat `"component": "TypeName"` discriminators and native literals.\n'
        "- Prefer ChoicePicker for selection (not 0.8 SelectionList).\n"
        "\nUse any component from this catalog if it helps the task and remains schema-valid."
    )


COMPONENT_SCHEMA_CONTEXT = _build_component_schema_context()
