"""0.8 generation guide and judge schema context.

Copied from evaluate_api_model.A2UI_MINIMAL_GUIDE / _build_component_schema_context
to avoid circular imports (protocol must not import evaluate_api_model).
"""

from __future__ import annotations

import json
from pathlib import Path

# Copied from evaluate_api_model.A2UI_MINIMAL_GUIDE (do not import that module).
GENERATION_GUIDE = """You are a conversational AI assistant. Reply with natural language text and optional A2UI messages.

Always output valid JSON:
{"text_response": "...", "a2ui": [...]}

# A2UI Protocol

Allowed message types (each message must contain exactly one action key):
- beginRendering: create/start rendering a surface
- surfaceUpdate: define/update the component tree on a surface
- dataModelUpdate: write/update data model values
- deleteSurface: remove a surface

Component item format:
{"id": "x", "component": {"TypeName": {...}}}

Use ONLY these component names:
- Button: Clickable action trigger. Usually include `action.name` and connect visible content via `child`.
- Card: Single-card container shell. Use `child` as the main root content of this card.
- Column: Vertical layout container. Arrange child component IDs in `children`.
- DateTimeInput: Date/time picker input. Main binding field is `value`.
- Divider: Visual separator line. Use `axis` to choose horizontal or vertical.
- FullScreenModal: Full-screen modal container. Wire `entryPointChild` and `contentChild`.
- Icon: Icon display component. Field `name` is `{literalString: "icon-name"}`, `style` is `line` or `filled`.
  Valid icon names (use ONLY these): star, home, search, time, like, dislike, thumbs-up, thumbs-down,
  success, tips, fire, lightning, protection, alarm, alarm-clock, calendar-thirty, stopwatch, hourglass-null,
  arrow-left, arrow-right, arrow-circle-up, arrow-circle-down, arrow-circle-left, arrow-circle-right,
  book, book-one, book-open, notes, copy, link, share, share-two, rss, history, refresh,
  phone-telephone, mail-open, camera, pic-one, local-two, shopping-bag-one,
  knife-fork, chef-hat-one, cook, bowl, pot, platte, goblet, tea-drink, avocado-one, cheese, refrigerator,
  birthday-cake, leaves-two, sleep, abdominal, afferent,
  smiling-face-with-squinting-eyes, grinning-face-with-tightly-closed-eyes-open-mouth,
  anguished-face, disappointed-face, emotion-unhappy,
  more, more-one, hamburger-button, all-application, setting-three, equalizer, application-effect,
  preview-open, preview-close-one, left-c, right-c.
- Image: Image display component. Main field is `url`.
- Label: Plain text display component. Main field is `text`, optional `variant`.
- MarkdownView: Rich text/markdown display. Main field is `text`.
- PasswordKeypad: Secure keypad input. Provide `value.path` and submission `action`.
- Row: Horizontal layout container. Arrange child component IDs in `children`.
- SelectionList: Option selection list. Core fields are `selection` and `items`.
- Tabs: Tabbed content switcher. Define tab entries in `tabItems`.
- TickSlider: Discrete slider input. Core fields are `value` and `max`."""

_ROOT = Path(__file__).resolve().parents[2]
_COMPONENT_SCHEMA_DIR = _ROOT / "vendor" / "a2ui_demo" / "resources" / "components" / "schemas"

_FALLBACK_SCHEMA_CONTEXT = (
    "## Available Components\n"
    "Label, MarkdownView, Icon, Image, Button, SelectionList, SelectionWrap, "
    "TickSlider, DateTimeInput, Card, Column, Row, Tabs, Divider, FullScreenModal, "
    "PasswordKeypad"
)


def _component_name_from_schema_file(path: Path) -> str:
    stem = path.stem.removesuffix("_schema")
    return "".join(part[:1].upper() + part[1:] for part in stem.split("_") if part)


def _format_component_prop_list(props: list[str]) -> str:
    if not props:
        return "(none)"
    return ", ".join(props[:6])


def _build_component_schema_context() -> str:
    """Mirror evaluate_api_model._build_component_schema_context (summary only)."""
    if not _COMPONENT_SCHEMA_DIR.exists():
        return _FALLBACK_SCHEMA_CONTEXT

    names: list[str] = []
    summary_lines: list[str] = []
    for path in sorted(_COMPONENT_SCHEMA_DIR.glob("*_schema.json")):
        if path.name in {"catalog_schema.json", "surface_update_schema.json"}:
            continue
        try:
            obj = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        comp_name = str(obj.get("title") or _component_name_from_schema_file(path))
        desc = " ".join(str(obj.get("description", "")).strip().split()) or "A2UI component."
        props = list((obj.get("properties") or {}).keys())
        names.append(comp_name)
        summary_lines.append(
            f"- {comp_name}: {desc} Key props: {_format_component_prop_list(props)}"
        )

    catalog = "## Available Components\n" + ", ".join(names)
    return (
        catalog
        + "\n\n## Component Quick Reference\n"
        + "\n".join(summary_lines)
        + "\n\nUse any component from this catalog if it helps the task and remains schema-valid."
    )


COMPONENT_SCHEMA_CONTEXT = _build_component_schema_context()
