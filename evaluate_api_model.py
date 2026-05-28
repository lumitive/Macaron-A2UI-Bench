#!/usr/bin/env python3
"""Evaluate API models on A2UI tasks with L1/L2/L3 scenario-dimension metrics.

Usage:
  python evaluate_api_model.py \
    --task-dir ./data/eval_300 \
    --models openai/gpt-4o-mini deepseek/deepseek-chat-v3.1 openai/gpt-5.4 \
    --judge-model openai/gpt-5.4 \
    --max-per-scenario 10
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import random
import re
import sys
import time
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_EVAL_ROOT = Path(__file__).resolve().parent
if str(_EVAL_ROOT) not in sys.path:
    sys.path.insert(0, str(_EVAL_ROOT))


def _iter_search_roots() -> list[Path]:
    roots: list[Path] = []
    seen: set[Path] = set()
    for base in (_EVAL_ROOT, *_EVAL_ROOT.parents):
        for candidate in (base, base.parent):
            candidate = candidate.resolve()
            if candidate not in seen:
                seen.add(candidate)
                roots.append(candidate)
    return roots


def _find_nearby_dir(name: str) -> Path | None:
    for root in _iter_search_roots():
        candidate = root / name
        if candidate.exists():
            return candidate
    return None

from openai import AsyncOpenAI

from render_check import render_check as _render_check


DEFAULT_MODELS = [
    "openai/gpt-4o-mini",
    "deepseek/deepseek-chat-v3.1",
    "openai/gpt-5.4",
    "qwen/qwen3-30b-a3b-instruct-2507",
    "google/gemini-3-flash-preview"
]

DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_TASK_SOURCES = ["multiwoz", "sgd", "esconv", "annomi"]


L1_DIMS = {
    "L1-1": "JSON Parse Correctness",
    "L1-2": "Schema Compliance",
    "L1-3": "Reference Integrity",
    "L1-4": "Required Fields Completeness",
    "L1-5": "Value Format Correctness",
}

L2_DIMS = {
    "D2-1": "Trigger Appropriateness",
    "D2-2": "Component-Intent Alignment",
    "D2-3": "Text-UI Grounding",
    "D2-4": "Data Model Utilization",
    "D2-5": "Action Completeness",
}

L3_DIMS = {
    "U3-A": "Value-Add over Text",
    "U3-B": "Conversational Naturalness",
    "U3-C": "Cognitive Load",
}

SCENARIO_DEFS = {
    "S1": "Emotional support & strategy branching (primarily esconv/annomi)",
    "S2": "Behavior change & commitment facilitation (primarily annomi/esconv)",
    "S3": "Slot filling & process advancement (primarily multiwoz/sgd)",
    "S4": "Candidate result display & comparison decision (primarily multiwoz/sgd)",
    "S5": "Transaction closure & failure recovery (primarily multiwoz/sgd)",
}

L2_RUBRIC_HINTS = {
    "S1": {
        "D2-1": "Good: user expresses ambivalence/emotion, model presents parallel options via selection UI; Bad: model has converged on advice yet still pops a selection card.",
        "D2-2": "Good: emotion branching uses clearly selectable, submittable interactive components; Bad: only static Text wrapping text to mimic interaction.",
        "D2-3": "Good: option labels strictly come from choices in text_response; Bad: UI invents options not mentioned in text.",
        "D2-4": "Good: dataModelUpdate records current emotional state; Bad: no state management at all.",
        "D2-5": "Good: interactive controls have action.name and context passes back user selection; Bad: actionable elements lack action.",
    },
    "S2": {
        "D2-1": "Good: user expresses willingness to act, model triggers commitment/assessment UI; Bad: still in exploratory discussion yet pushes commitment card.",
        "D2-2": "Good: uses scalar assessment or commitment-type interactive components; Bad: commitment scenario only has static display without interactive components.",
        "D2-3": "Good: quantified ranges or commitment options match dimensions built in text; Bad: endpoints/options are fabricated.",
        "D2-4": "Good: dataModelUpdate records commitment content and timing; Bad: commitment flow has no state record.",
        "D2-5": "Good: submit action contains commitment payload in context; Bad: only 'submitted' with no concrete data passed back.",
    },
    "S3": {
        "D2-1": "Good: triggers form UI when user needs to fill in information; Bad: collects slots via text Q&A without providing input components.",
        "D2-2": "Good: uses editable input components to collect parameters; Bad: uses plain Text to display questions but gives no input entry.",
        "D2-3": "Good: form fields match information requested in text; Bad: form includes extra fields not mentioned in text.",
        "D2-4": "Good: dataModelUpdate records collected parameters; Bad: multi-turn collection but no state accumulation.",
        "D2-5": "Good: submit action contains complete input values in context; Bad: cannot track input values after submission.",
    },
    "S4": {
        "D2-1": "Good: triggers result display UI when search results exist; Bad: has results but doesn't trigger structured display.",
        "D2-2": "Good: candidates displayed in structured, comparable, actionable UI; Bad: only fragmented text.",
        "D2-3": "Good: displayed candidates match count and content described in text; Bad: text says 3 candidates but UI shows only 2.",
        "D2-4": "Good: dataModelUpdate records search criteria and results; Bad: candidate data only in text with no structured record.",
        "D2-5": "Good: selecting a candidate's interactive element passes back candidate ID or equivalent; Bad: selection leads to flow stall.",
    },
    "S5": {
        "D2-1": "Good: triggers confirm/cancel UI during transaction closure; Bad: closure phase has no interactive components.",
        "D2-2": "Good: confirmation page has clear confirm/cancel/modify actions; Bad: only text summary without executable operations.",
        "D2-3": "Good: confirmation info matches booking details in text; Bad: confirmation page contradicts text.",
        "D2-4": "Good: dataModelUpdate records booking status; Bad: no state update after confirmation.",
        "D2-5": "Good: confirm action contains complete booking info in context; Bad: critical operation has no action.",
    },
}

L3_RUBRIC_HINTS = {
    "S1": {
        "U3-A": "Good: selection card lets user click instead of manually describing emotional direction; Bad: only Text wrapping 'you could try A or B'.",
        "U3-B": "Good: acknowledges user emotion first, then naturally introduces interaction; Bad: cold-starts UI push while user emotion is intense.",
        "U3-C": "Good: only one core interaction per turn, 2-4 options; Bad: stacks multiple components or too many options at once.",
    },
    "S2": {
        "U3-A": "Good: quantified/commitment interaction converts abstract intent into actionable steps; Bad: UI merely restates text content.",
        "U3-B": "Good: uses supportive framing like 'let's assess your readiness' before pushing interaction; Bad: abruptly demands 'please rate yourself'.",
        "U3-C": "Good: assess first, then commit — step by step; Bad: asks for assessment + plan + commitment all at once.",
    },
    "S3": {
        "U3-A": "Good: form collection lets user fill in rather than Q&A one by one; Bad: form only displays known info without editable fields.",
        "U3-B": "Good: 'to find the best option for you, I need a few details' naturally leads to form; Bad: blank form pops up without context.",
        "U3-C": "Good: collects core info step by step; Bad: pops a 10+ field form all at once.",
    },
    "S4": {
        "U3-A": "Good: structured display lets user compare and select; Bad: candidate info only listed as plain Text.",
        "U3-B": "Good: 'based on your requirements, here are the options' naturally introduces results; Bad: jumps straight to results without transition.",
        "U3-C": "Good: balanced candidate count and density, grouped when necessary; Bad: displays 20+ candidates at once without grouping.",
    },
    "S5": {
        "U3-A": "Good: confirmation page lets user confirm/cancel in one click; Bad: confirmation page only shows text without action buttons.",
        "U3-B": "Good: 'here is your booking summary, please confirm' naturally leads in; Bad: demands confirmation without transition.",
        "U3-C": "Good: confirmation page focuses on key info and core actions; Bad: piles up extra options during confirmation.",
    },
}

OUTPUT_SCHEMA_HINT = """You must output ONLY a JSON object (no markdown):
{
  "text_response": "string",
  "a2ui": [ ... ]
}
"""


A2UI_MINIMAL_GUIDE = """You are a conversational AI assistant. Reply with natural language text and optional A2UI messages.

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

A2UI_CONCISE_GUIDE = """A2UI Key Points (concise):
1) a2ui is a message array; each message object must contain exactly one action key:
   beginRendering | surfaceUpdate | dataModelUpdate | deleteSurface
2) beginRendering:
   {"beginRendering":{"surfaceId":"...","root":"...","styles":{"primaryColor":"#1976D2"}}}
3) surfaceUpdate:
   {"surfaceUpdate":{"surfaceId":"...","components":[{"id":"c1","component":{"Label":{"text":{"literalString":"..."}}}}]}}
4) dataModelUpdate:
   {"dataModelUpdate":{"surfaceId":"...","path":"/","contents":[{"key":"k","valueString":"v"}]}}
5) deleteSurface:
   {"deleteSurface":{"surfaceId":"..."}}
6) component wrapper must have exactly one component type key. Common components:
   Layout: Card, Column, Row
   Display: Label, MarkdownView, Icon, Image, Divider
   Input: SelectionList, SelectionWrap, TickSlider, DateTimeInput, Button
   Other: Tabs, FullScreenModal, PasswordKeypad
7) Only return an empty array [] for no_ui_chat or when expected_pattern is none/delete; do not fabricate UI unrelated to the task.
"""

# Message protocol and key rules (aligned with data_generation_v2/rewrite_pipeline + repair_pipeline)
# to reduce STRUCT_INVALID_ACTION_KEY: a2ui must be an array of MESSAGES, not raw component items.
A2UI_MESSAGE_PROTOCOL_AND_RULES = """
## A2UI Message Protocol (CRITICAL)

The `a2ui` array is a list of **messages**. Each element must be a message object with **exactly ONE** action key (do NOT put raw component items like {"id": "...", "component": {...}} at the top level).

- `beginRendering`: {surfaceId: string, root: string} — create surface; root is the ID of the top-level component.
- `surfaceUpdate`: {surfaceId: string, components: array} — define the component tree. Each item in components: {"id": "unique_id", "component": {"TypeName": {...props}}}.
- `dataModelUpdate`: {surfaceId: string, path: "/", contents: array} — write data. Each entry: {key: "name", valueString: "text"} or valueNumber / valueBoolean.
- `deleteSurface`: {surfaceId: string} — remove surface.

Correct pattern: use ONE surfaceId; include beginRendering (root pointing to top component), then surfaceUpdate (with components array), then dataModelUpdate if needed. Components go **inside** surfaceUpdate.components, not directly in a2ui.

## Key Rules
1. Every surfaceUpdate must have a matching beginRendering with root pointing to the top-level component ID.
2. All component IDs referenced as children must exist in the same surfaceUpdate.components.
3. Use only ONE surface (one surfaceId) per reply. Do not create multiple surfaces.
4. If using SelectionList/SelectionWrap, selection must include "literalArray": [] alongside "path"; do not add the selection key to dataModelUpdate.
5. If using interactive components (SelectionList, TickSlider, DateTimeInput), include a Button for confirm/submit.
6. dataModelUpdate valueString must not be empty "".
"""


_A2UI_DEMO_ROOT = Path(
    os.environ.get("A2UI_DEMO_ROOT")
    or ((_EVAL_ROOT / "vendor" / "a2ui_demo") if (_EVAL_ROOT / "vendor" / "a2ui_demo").exists() else _find_nearby_dir("a2ui_demo"))
)
_COMPONENT_SCHEMA_DIR = _A2UI_DEMO_ROOT / "resources" / "components" / "schemas"
_COMPONENT_CATALOG_CACHE: tuple[str, str] | None = None


VALUE_FORMAT_CODES = {
    "STRUCT_WRONG_TYPE",
    "STRUCT_INVALID_ENUM",
    "STRUCT_MULTIPLE_VALUE_TYPES",
    "STRUCT_NO_VALUE_TYPE",
}


@dataclass
class TaskSample:
    task_id: str
    source: str
    scenario_id: str
    intent_type: str
    difficulty_level: str
    task_description: str
    user_message: str
    dialogue_context: list[dict[str, str]]
    expected_pattern: str
    gt_a2ui: list[dict] = field(default_factory=list)  # legacy reference, not used directly in L2/L3 prompts
    gt_assistant_text: str = ""
    completion_criteria: list[str] = field(default_factory=list)
    raw_context: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    episode_turns: list[dict[str, Any]] = field(default_factory=list)
    subgoals: list[str] = field(default_factory=list)
    domains: list[str] = field(default_factory=list)


def _component_name_from_schema_file(path: Path) -> str:
    stem = path.stem.removesuffix("_schema")
    return "".join(part[:1].upper() + part[1:] for part in stem.split("_") if part)


def _format_component_prop_list(props: list[str]) -> str:
    if not props:
        return "(none)"
    return ", ".join(props[:6])


def _load_component_catalog_and_summary() -> tuple[str, str]:
    global _COMPONENT_CATALOG_CACHE
    if _COMPONENT_CATALOG_CACHE is not None:
        return _COMPONENT_CATALOG_CACHE

    if not _COMPONENT_SCHEMA_DIR.exists():
        fallback = (
            "## Available Components\n"
            "Label, MarkdownView, Icon, Image, Button, SelectionList, SelectionWrap, "
            "TickSlider, DateTimeInput, Card, Column, Row, Tabs, Divider, FullScreenModal, "
            "PasswordKeypad"
        )
        _COMPONENT_CATALOG_CACHE = (fallback, fallback)
        return _COMPONENT_CATALOG_CACHE

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
    summary = (
        catalog
        + "\n\n## Component Quick Reference\n"
        + "\n".join(summary_lines)
        + "\n\nUse any component from this catalog if it helps the task and remains schema-valid."
    )
    _COMPONENT_CATALOG_CACHE = (catalog, summary)
    return _COMPONENT_CATALOG_CACHE


def _build_generation_guide(prompt_mode: str) -> str:
    component_catalog, component_summary = _load_component_catalog_and_summary()

    if prompt_mode in ("minimal", "sft"):
        return A2UI_MINIMAL_GUIDE

    # full mode: load from pre-built txt file
    full_prompt_path = Path(__file__).parent / "system_prompt_full.txt"
    if full_prompt_path.exists():
        return full_prompt_path.read_text(encoding="utf-8")

    # fallback: dynamic build (legacy)
    try:
        a2ui_demo_parent = _A2UI_DEMO_ROOT.parent
        if str(a2ui_demo_parent) not in sys.path:
            sys.path.insert(0, str(a2ui_demo_parent))
        from a2ui_demo.server.a2ui_prompt import build_component_catalog  # type: ignore
        from a2ui_demo.server.a2ui_schema_registry import build_a2ui_message_schema_text  # type: ignore

        component_catalog = build_component_catalog()
        a2ui_schema = build_a2ui_message_schema_text()
        return (
            "A2UI Key Points (full version, from a2ui_demo):\n"
            "You must strictly follow schema field names; do not use onClick/onPress/content or other undefined names. "
            "Common components: Label, MarkdownView, Button, SelectionList, SelectionWrap, "
            "TickSlider, DateTimeInput, Card, Column, Row, Divider, Icon, Image, Tabs.\n\n"
            f"{A2UI_MESSAGE_PROTOCOL_AND_RULES}\n\n"
            f"{component_catalog}\n\n"
            "## A2UI JSON Schema\n"
            f"{a2ui_schema}\n"
        )
    except Exception as e:
        print(f"[warn] failed to load full A2UI prompt, fallback to concise: {e}")
        return (
            A2UI_CONCISE_GUIDE + "\n\n"
            + A2UI_MESSAGE_PROTOCOL_AND_RULES + "\n\n"
            + component_catalog
        )


def _load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())


def _setup_env() -> None:
    _load_env_file(_EVAL_ROOT / ".env")
    for root in _iter_search_roots()[:4]:
        _load_env_file(root / ".env")


def _ensure_a2ui_lint_import():
    if not (_A2UI_DEMO_ROOT / "server" / "a2ui_lint" / "__init__.py").exists():
        raise RuntimeError(
            "Missing bundled a2ui_demo dependency. Restore vendor/a2ui_demo or set A2UI_DEMO_ROOT to a compatible checkout."
        )
    a2ui_demo_parent = _A2UI_DEMO_ROOT.parent
    if str(a2ui_demo_parent) not in sys.path:
        sys.path.insert(0, str(a2ui_demo_parent))
    from a2ui_demo.server.a2ui_lint import validate  # type: ignore
    return validate


def _extract_json_object(text: str) -> dict[str, Any] | None:
    def _is_model_output_dict(obj: dict[str, Any]) -> bool:
        return any(key in obj for key in ("text_response", "a2ui", "a2ui_messages"))

    def _model_output_priority(obj: dict[str, Any]) -> tuple[int, int, int]:
        return (
            1 if ("a2ui" in obj or "a2ui_messages" in obj) else 0,
            1 if "text_response" in obj else 0,
            len(obj),
        )

    content = text.strip()
    if content.startswith("```"):
        content = content.strip("`")
        if content.startswith("json"):
            content = content[4:].strip()
    try:
        obj = json.loads(content)
        if isinstance(obj, dict):
            return obj
    except Exception:
        pass

    # Find ALL valid JSON objects by brace matching.
    # For model outputs, strongly prefer objects that contain `a2ui` /
    # `a2ui_messages` / `text_response` instead of arbitrarily selecting an
    # inner component dict with more top-level keys.
    candidates: list[tuple[int, dict[str, Any]]] = []
    start = content.find("{")
    while start >= 0:
        depth = 0
        in_str = False
        esc = False
        for i in range(start, len(content)):
            ch = content[i]
            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    in_str = False
                continue
            if ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    cand = content[start : i + 1]
                    try:
                        obj = json.loads(cand)
                        if isinstance(obj, dict):
                            candidates.append((start, obj))
                    except Exception:
                        pass
                    break
        start = content.find("{", start + 1)

    if not candidates:
        return None

    output_candidates = [(start, obj) for start, obj in candidates if _is_model_output_dict(obj)]
    if output_candidates:
        # Prefer objects that actually look like the target output schema,
        # then prefer earlier matches in the text.
        return max(
            output_candidates,
            key=lambda item: (*_model_output_priority(item[1]), -item[0]),
        )[1]

    # Fallback for judge outputs and other generic JSON payloads: preserve the
    # previous "outer object" heuristic by taking the dict with the most keys.
    return max(candidates, key=lambda item: len(item[1]))[1]


def _coerce_output(raw_output: str) -> tuple[str, list[dict], bool, str]:
    """Return (assistant_text, a2ui_messages, parse_error, parse_note)."""
    obj = _extract_json_object(raw_output)
    if obj is None:
        return "", [], True, "json_object_parse_failed"

    text = str(obj.get("text_response", "")).strip()
    a2ui = obj.get("a2ui_messages", obj.get("a2ui", []))
    if not isinstance(a2ui, list):
        return text, [], True, "a2ui_messages_not_list"

    fixed_messages: list[dict] = []
    for m in a2ui:
        if isinstance(m, dict):
            fixed_messages.append(m)
        else:
            return text, [], True, "a2ui_message_not_dict"
    return text, fixed_messages, False, ""


def _infer_scenario_id(task: dict) -> str:
    sid = str(task.get("metadata", {}).get("scenario_id", "")).strip()
    if sid in SCENARIO_DEFS:
        return sid

    source = task.get("source", "")
    intent = task.get("intent_type", "")
    if source in ("multiwoz", "sgd"):
        if intent == "information_grounding":
            return "S4"
        if intent == "booking_confirmation":
            return "S5"
        return "S3"
    if intent in ("continuous_self_assessment", "action_commitment"):
        return "S2"
    return "S1"


def load_task_samples(task_dir: Path) -> list[TaskSample]:
    tasks: list[TaskSample] = []
    merged_path = task_dir / "all_tasks.json"
    if merged_path.exists():
        datasets = [json.loads(merged_path.read_text(encoding="utf-8"))]
    else:
        datasets = [
            json.loads(path.read_text(encoding="utf-8"))
            for path in sorted(task_dir.glob("*_tasks.json"))
        ]

    for data in datasets:
        for t in data:
            source = t.get("source", "")
            ctx = t.get("context", {}) or {}
            tasks.append(
                TaskSample(
                    task_id=t.get("task_id", ""),
                    source=source,
                    scenario_id=_infer_scenario_id(t),
                    intent_type=t.get("intent_type", ""),
                    difficulty_level=t.get("difficulty_level", "atomic"),
                    task_description=t.get("task_description", ""),
                    user_message=ctx.get("user_message", ""),
                    dialogue_context=ctx.get("dialogue_context", [])[-6:],
                    expected_pattern=t.get("expected_pattern", ""),
                    gt_a2ui=t.get("gt_a2ui", []),
                    gt_assistant_text=t.get("gt_assistant_text", ""),
                    completion_criteria=t.get("completion_criteria", []),
                    raw_context=ctx,
                    metadata=t.get("metadata", {}) or {},
                    episode_turns=ctx.get("episode_turns", []) or [],
                    subgoals=ctx.get("subgoals", []) or [],
                    domains=ctx.get("domains", []) or [],
                )
            )
    return tasks


def sample_balanced(tasks: list[TaskSample], max_per_scenario: int, seed: int) -> list[TaskSample]:
    if max_per_scenario <= 0:
        return sorted(tasks, key=lambda x: (x.scenario_id, x.source, x.task_id))
    random.seed(seed)
    by_s: dict[str, list[TaskSample]] = defaultdict(list)
    for t in tasks:
        by_s[t.scenario_id].append(t)

    sampled: list[TaskSample] = []
    for sid in sorted(SCENARIO_DEFS.keys()):
        bucket = by_s.get(sid, [])
        random.shuffle(bucket)
        sampled.extend(bucket[:max_per_scenario])

    # If some scenarios are sparse, keep deterministic order.
    sampled.sort(key=lambda x: (x.scenario_id, x.source, x.task_id))
    return sampled


def _format_context(dialogue_context: list[dict[str, str]]) -> str:
    if not dialogue_context:
        return "(conversation start)"
    lines = []
    for m in dialogue_context[-6:]:
        role = str(m.get("role", "user")).title()
        content = str(m.get("content", "")).strip()
        lines.append(f"{role}: {content}")
    return "\n".join(lines)


def _format_bullets(items: list[str]) -> str:
    cleaned = [str(x).strip() for x in items if str(x).strip()]
    if not cleaned:
        return "(none)"
    return "\n".join(f"- {x}" for x in cleaned)


def _build_task_addendum(task: TaskSample, step_idx: int | None = None, total_steps: int | None = None) -> str:
    blocks: list[str] = []
    if task.difficulty_level == "depth" and task.episode_turns:
        label = ""
        if step_idx is not None and total_steps is not None:
            label = f" (current turn {step_idx + 1}/{total_steps})"
        blocks.append(
            "[Replay Task]\n"
            f"This is a multi-turn sequential task{label}. Generate only the current turn's assistant output, "
            "and stay consistent with your previous replies while continuing to advance the overall task."
        )
        deps = task.raw_context.get("cross_turn_dependencies", []) or []
        if deps:
            blocks.append("[Cross-turn Dependencies]\n" + _format_bullets(deps))
        pre_summary = str(task.raw_context.get("pre_episode_summary", "")).strip()
        if pre_summary:
            blocks.append("[Pre-Episode Summary]\n" + pre_summary)
        pre_state = task.raw_context.get("pre_episode_state", {}) or {}
        state_lines: list[str] = []
        if pre_state.get("domain"):
            state_lines.append(f"- domain: {pre_state['domain']}")
        active_surfaces = pre_state.get("active_surfaces_at_start", []) or []
        if active_surfaces:
            state_lines.append(f"- active_surfaces_at_start: {active_surfaces}")
        if pre_state.get("search_context"):
            state_lines.append(f"- search_context: {pre_state['search_context']}")
        known_facts = task.raw_context.get("known_facts", []) or []
        for fact in known_facts[:6]:
            state_lines.append(f"- known_fact: {fact}")
        if task.raw_context.get("stage_at_start"):
            state_lines.append(f"- stage_at_start: {task.raw_context['stage_at_start']}")
        if state_lines:
            blocks.append("[Known State At Start]\n" + "\n".join(state_lines))
    if task.difficulty_level == "width":
        if task.domains:
            blocks.append("[Composite Domains]\n" + ", ".join(task.domains))
        if task.subgoals:
            blocks.append("[Composite Subgoals]\n" + _format_bullets(task.subgoals))
        if task.intent_type == "no_ui_chat" or task.expected_pattern == "none":
            blocks.append(
                "[Width Requirement]\n"
                "This is a single-turn composite request, but the best strategy is to use one clear text-only reply "
                "to coordinate all subgoals; do not force-generate A2UI just to appear complex."
            )
        else:
            blocks.append(
                "[Width Requirement]\n"
                "This is a single-turn composite coordination task. You should try to cover all subgoals in one reply; "
                "if necessary, you may output multiple surfaces or multiple A2UI updates in the same reply."
            )
    if task.completion_criteria:
        blocks.append("[Success Criteria]\n" + _format_bullets(task.completion_criteria))
    return "\n\n".join(blocks)


def _build_component_schema_context() -> str:
    _, summary = _load_component_catalog_and_summary()
    return summary


def build_generation_messages(
    task: TaskSample,
    generation_guide: str,
    *,
    dialogue_context: list[dict[str, str]] | None = None,
    user_message: str | None = None,
    expected_pattern: str | None = None,
    intent_type: str | None = None,
    step_idx: int | None = None,
    total_steps: int | None = None,
) -> list[dict[str, str]]:
    dialogue_context = dialogue_context if dialogue_context is not None else task.dialogue_context
    user_message = user_message if user_message is not None else task.user_message
    expected_pattern = expected_pattern if expected_pattern is not None else task.expected_pattern
    intent_type = intent_type if intent_type is not None else task.intent_type
    requirement_line = (
        "Based on the task description and dialogue context, generate a natural language reply and appropriate A2UI interactive components. "
        "You must output a strict JSON object in the format "
        '{"text_response":"...","a2ui":[...]}.'
    )

    system = (
        "You are an A2UI task assistant. You must output both a natural language reply and A2UI messages.\n"
        + generation_guide
        + "\n"
        + requirement_line
        + "\n"
        + OUTPUT_SCHEMA_HINT
    )
    addendum = _build_task_addendum(task, step_idx=step_idx, total_steps=total_steps)
    user = (
        f"[Scenario] {task.scenario_id}: {SCENARIO_DEFS[task.scenario_id]}\n"
        f"[Intent] {intent_type}\n"
        f"[Task] {task.task_description}\n"
        + (addendum + "\n\n" if addendum else "")
        + f"[Dialogue Context]\n{_format_context(dialogue_context)}\n\n"
        + f"[Current User Message]\n{user_message}\n\n"
        "Generate the best assistant output for the current turn."
    )
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def _history_turn_to_plain_text(role: str, content: str) -> str:
    if role != "assistant":
        return content
    try:
        parsed = json.loads(content)
    except (json.JSONDecodeError, TypeError):
        return content
    if not isinstance(parsed, dict):
        return content
    text_response = parsed.get("text_response")
    if isinstance(text_response, str) and text_response.strip():
        return text_response.strip()
    return content


def build_sft_messages(
    task: TaskSample,
    system_prompt: str,
) -> list[dict[str, str]]:
    """Build prompt messages as plain dialogue history with no historical A2UI."""
    messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]

    # Replay dialogue_context as multi-turn conversation
    for turn in task.dialogue_context:
        role = turn.get("role", "user")
        content = str(turn.get("content", "")).strip()
        if not content:
            continue
        content = _history_turn_to_plain_text(role, content)
        messages.append({"role": role, "content": content})

    # Current user message
    user_message = task.user_message.strip()
    if user_message:
        messages.append({"role": "user", "content": user_message})

    return messages


def evaluate_l1_scores(
    parse_error: bool,
    messages: list[dict],
    validate_fn,
) -> tuple[dict[str, float], bool, dict[str, Any]]:
    if parse_error:
        scores = {k: 0.0 for k in L1_DIMS}
        return scores, False, {
            "error_count": 1,
            "warning_count": 0,
            "diagnostic_codes": ["JSON_PARSE_FAILED"],
            "warning_codes": [],
            "policy_error_codes": [],
        }

    try:
        validation = validate_fn(messages, levels={1, 2, 3, 4})
    except Exception:
        scores = {k: 0.0 for k in L1_DIMS}
        return scores, False, {
            "error_count": 1,
            "warning_count": 0,
            "diagnostic_codes": ["VALIDATOR_CRASH"],
            "warning_codes": [],
            "policy_error_codes": [],
        }
    error_codes = [d.code.value for d in validation.errors]
    warning_codes = [d.code.value for d in validation.warnings]
    all_codes = error_codes + warning_codes
    error_count = len(validation.errors)
    warning_count = len(validation.warnings)

    # Map diagnostic codes to L1 dimensions by prefix:
    #   L1-2 Schema Compliance:      STRUCT_*
    #   L1-3 Reference Integrity:    REF_*
    #   L1-4 Required Fields / Data: DATA_*
    #   L1-5 Semantic Lint:          LINT_*
    dim_issue_count: dict[str, int] = {"L1-2": 0, "L1-3": 0, "L1-4": 0, "L1-5": 0}
    dim_has_error: dict[str, bool] = {"L1-2": False, "L1-3": False, "L1-4": False, "L1-5": False}
    _prefix_to_dim = {
        "STRUCT_": "L1-2",
        "REF_": "L1-3",
        "DATA_": "L1-4",
        "LINT_": "L1-5",
    }
    for d in validation.errors:
        code = d.code.value
        for prefix, dim in _prefix_to_dim.items():
            if code.startswith(prefix):
                dim_issue_count[dim] += 1
                dim_has_error[dim] = True
                break
    for d in validation.warnings:
        code = d.code.value
        for prefix, dim in _prefix_to_dim.items():
            if code.startswith(prefix):
                dim_issue_count[dim] += 1
                break

    # Overall L1 pass = no errors at all
    l1_pass = (error_count == 0)

    # Per-dimension scoring:
    #   - If L1 fails (any error anywhere) => ALL dimensions get 0.
    #     Rationale: when output has structural errors, the validator may not
    #     reach deeper checks (REF/DATA/LINT), so "no error reported" in those
    #     dims is unreliable — it means "not checked", not "passed".
    #   - If L1 passes (no errors) => per-dim score = 5 - warning_count, floor 0
    l1 = {"L1-1": 5.0}  # JSON parse OK
    if not l1_pass:
        for dim in ["L1-2", "L1-3", "L1-4", "L1-5"]:
            l1[dim] = 0.0
    else:
        for dim in ["L1-2", "L1-3", "L1-4", "L1-5"]:
            l1[dim] = float(max(0, 5 - dim_issue_count[dim]))
    codes = error_codes
    details = {
        "is_valid": bool(validation.is_valid),
        "error_count": error_count,
        "warning_count": warning_count,
        "diagnostic_codes": codes,
        "warning_codes": warning_codes,
        "policy_error_codes": [],
    }
    return l1, l1_pass, details


def _a2ui_summary(messages: list[dict]) -> str:
    if not messages:
        return "(no A2UI messages)"
    lines = []
    for msg in messages:
        if "surfaceUpdate" in msg:
            su = msg["surfaceUpdate"]
            sid = su.get("surfaceId", "?")
            c_types = []
            for c in su.get("components", []):
                c_types.extend(list(c.get("component", {}).keys()))
            lines.append(f"surfaceUpdate({sid}): {', '.join(c_types)}")
        elif "dataModelUpdate" in msg:
            dm = msg["dataModelUpdate"]
            sid = dm.get("surfaceId", "?")
            keys = [x.get("key", "") for x in dm.get("contents", [])]
            lines.append(f"dataModelUpdate({sid}): keys={keys}")
        elif "beginRendering" in msg:
            lines.append(f"beginRendering({msg['beginRendering'].get('surfaceId', '?')})")
        elif "deleteSurface" in msg:
            lines.append(f"deleteSurface({msg['deleteSurface'].get('surfaceId', '?')})")
    return "\n".join(lines)[:2000]


def _truncate_json_for_prompt(payload: Any, *, max_chars: int) -> str:
    """Serialize JSON for judge prompts with a simple head-tail truncation."""
    raw = json.dumps(payload, ensure_ascii=False, indent=1)
    if len(raw) <= max_chars:
        return raw
    head = max_chars // 2
    tail = max_chars - head
    return raw[:head] + "\n... (truncated) ...\n" + raw[-tail:]


def _build_l2_rubric_hints(scenario_id: str) -> str:
    hints = L2_RUBRIC_HINTS[scenario_id]
    lines = []
    for k in ["D2-1", "D2-2", "D2-3", "D2-4", "D2-5"]:
        lines.append(f"- {k} ({L2_DIMS[k]}): {hints[k]}")
    return "\n".join(lines)


def _build_l3_rubric_hints(scenario_id: str) -> str:
    hints = L3_RUBRIC_HINTS[scenario_id]
    lines = []
    for k in ["U3-A", "U3-B", "U3-C"]:
        lines.append(f"- {k} ({L3_DIMS[k]}): {hints[k]}")
    return "\n".join(lines)


# Load prompts from files
_PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"
_L2_PROMPT_TEMPLATE: str | None = None
_L3_PROMPT_TEMPLATE: str | None = None


def _get_l2_prompt_template() -> str:
    global _L2_PROMPT_TEMPLATE
    if _L2_PROMPT_TEMPLATE is None:
        _L2_PROMPT_TEMPLATE = (_PROMPTS_DIR / "l2_judge.txt").read_text(encoding="utf-8")
    return _L2_PROMPT_TEMPLATE


def _get_l3_prompt_template() -> str:
    global _L3_PROMPT_TEMPLATE
    if _L3_PROMPT_TEMPLATE is None:
        _L3_PROMPT_TEMPLATE = (_PROMPTS_DIR / "l3_judge.txt").read_text(encoding="utf-8")
    return _L3_PROMPT_TEMPLATE


def build_l2_judge_messages(
    task: TaskSample,
    text_response: str,
    a2ui_messages: list[dict],
    *,
    dialogue_context: list[dict[str, str]] | None = None,
    user_message: str | None = None,
) -> list[dict[str, str]]:
    """Build L2 judge prompt with rich principle-grounded rubrics."""
    dialogue_context = dialogue_context if dialogue_context is not None else task.dialogue_context
    user_message = user_message if user_message is not None else task.user_message
    a2ui_raw = _truncate_json_for_prompt(a2ui_messages, max_chars=3000)

    addendum = _build_task_addendum(task)
    prompt = _get_l2_prompt_template().format(
        rubric_hints=_build_l2_rubric_hints(task.scenario_id),
        scenario_id=task.scenario_id,
        scenario_def=SCENARIO_DEFS[task.scenario_id],
        task_description=(task.task_description + ("\n\n" + addendum if addendum else "")),
        dialogue_context=_format_context(dialogue_context),
        user_message=user_message,
        text_response=text_response,
        a2ui_summary=_a2ui_summary(a2ui_messages),
        a2ui_raw_json=a2ui_raw,
        component_schema_context=_build_component_schema_context(),
    )
    return [{"role": "user", "content": prompt}]


def build_l3_judge_messages(
    task: TaskSample,
    text_response: str,
    a2ui_messages: list[dict],
    *,
    dialogue_context: list[dict[str, str]] | None = None,
    user_message: str | None = None,
) -> list[dict[str, str]]:
    """Build L3 judge prompt with rich principle-grounded rubrics."""
    dialogue_context = dialogue_context if dialogue_context is not None else task.dialogue_context
    user_message = user_message if user_message is not None else task.user_message
    addendum = _build_task_addendum(task)
    model_output_raw = _truncate_json_for_prompt(
        {
            "text_response": text_response,
            "a2ui": a2ui_messages,
        },
        max_chars=8000,
    )
    prompt = _get_l3_prompt_template().format(
        rubric_hints=_build_l3_rubric_hints(task.scenario_id),
        scenario_id=task.scenario_id,
        scenario_def=SCENARIO_DEFS[task.scenario_id],
        task_description=(task.task_description + ("\n\n" + addendum if addendum else "")),
        dialogue_context=_format_context(dialogue_context),
        user_message=user_message,
        text_response=text_response,
        a2ui_summary=_a2ui_summary(a2ui_messages),
        model_output_raw_json=model_output_raw,
        component_schema_context=_build_component_schema_context(),
    )
    return [{"role": "user", "content": prompt}]


def _strict_dim_scores(raw: Any, dims: dict[str, str]) -> tuple[dict[str, float], bool, str]:
    """Strict judge parser: no fallback score and no missing-dimension tolerance."""
    zeros = {did: 0.0 for did in dims}
    if not isinstance(raw, dict):
        return zeros, False, "judge_invalid_format"

    out: dict[str, float] = {}
    for did in dims:
        if did not in raw:
            return zeros, False, f"judge_missing_dim:{did}"
        cell = raw[did]
        if not isinstance(cell, dict) or "score" not in cell:
            return zeros, False, f"judge_missing_score:{did}"
        try:
            score_f = float(cell["score"])
        except Exception:
            return zeros, False, f"judge_non_numeric_score:{did}"
        if score_f < 0.0 or score_f > 5.0:
            return zeros, False, f"judge_score_out_of_range:{did}"
        out[did] = score_f
    return out, True, ""


async def _chat_completion_json(
    client: AsyncOpenAI,
    model: str,
    messages: list[dict[str, str]],
    temperature: float = 0.7,
    max_tokens: int = 2200,
    retries: int = 3,
    request_timeout: float = 180.0,
) -> str:
    wait = 1.0
    last_err = ""
    for _ in range(retries):
        base_request_kwargs: dict[str, Any] = dict(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        # Strongly prefer JSON-mode responses for both generation and judge calls.
        base_request_kwargs["response_format"] = {"type": "json_object"}
        # NOTE: Do NOT enable reasoning for structured JSON tasks — reasoning
        # tokens consume the max_tokens budget and can leave content empty.
        # See: https://github.com/openai/openai-python/issues/2546
        if "kimi-k2.5" in model:
            base_request_kwargs["extra_body"] = {"reasoning": {"effort": "none", "exclude": True}}

        try:
            resp = await asyncio.wait_for(
                client.chat.completions.create(**base_request_kwargs),
                timeout=request_timeout,
            )
            return (resp.choices[0].message.content or "").strip()
        except Exception as e:
            last_err = str(e)
            # Fall back when a provider rejects response_format explicitly.
            lowered = last_err.lower()
            if "response_format" in lowered or "json_object" in lowered or "json schema" in lowered:
                fallback_kwargs = dict(base_request_kwargs)
                fallback_kwargs.pop("response_format", None)
                try:
                    resp = await asyncio.wait_for(
                        client.chat.completions.create(**fallback_kwargs),
                        timeout=request_timeout,
                    )
                    return (resp.choices[0].message.content or "").strip()
                except Exception as fallback_exc:
                    last_err = str(fallback_exc)
            await asyncio.sleep(wait)
            wait *= 2
    return f'{{"error":"{last_err[:200]}"}}'


def _make_override_task(
    task: TaskSample,
    *,
    user_message: str,
    dialogue_context: list[dict[str, str]],
    expected_pattern: str,
    gt_a2ui: list[dict] | None,
    gt_assistant_text: str = "",
    intent_type: str | None = None,
) -> TaskSample:
    return TaskSample(
        task_id=task.task_id,
        source=task.source,
        scenario_id=task.scenario_id,
        intent_type=intent_type or task.intent_type,
        difficulty_level=task.difficulty_level,
        task_description=task.task_description,
        user_message=user_message,
        dialogue_context=dialogue_context,
        expected_pattern=expected_pattern,
        gt_a2ui=gt_a2ui or [],
        gt_assistant_text=gt_assistant_text,
        completion_criteria=task.completion_criteria,
        raw_context=task.raw_context,
        metadata=task.metadata,
        episode_turns=task.episode_turns,
        subgoals=task.subgoals,
        domains=task.domains,
    )


async def _score_prediction(
    scoring_task: TaskSample,
    text_response: str,
    a2ui_messages: list[dict],
    raw_pred: str,
    parse_error: bool,
    parse_note: str,
    *,
    judge_model: str,
    judge_client: AsyncOpenAI,
    validate_fn,
    judge_sem: asyncio.Semaphore,
    precomputed_l1: tuple[dict[str, float], bool, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if parse_error:
        print(f"\n[PARSE ERROR] task={scoring_task.task_id} note={parse_note}")
        print(f"  RAW OUTPUT (first 500 chars): {raw_pred[:500]}")
        print()

    if precomputed_l1 is not None:
        l1_scores, l1_pass, l1_details = precomputed_l1
    else:
        l1_scores, l1_pass, l1_details = evaluate_l1_scores(parse_error, a2ui_messages, validate_fn)
    l2_scores = {k: 0.0 for k in L2_DIMS}
    l3_scores = {k: 0.0 for k in L3_DIMS}
    l2_judge_note = ""
    l3_judge_note = ""
    l2_judge_valid = False
    l3_judge_valid = False
    skip_l2l3 = False
    render_check_pass = True
    render_check_issues: list[str] = []

    if (
        scoring_task.difficulty_level != "depth"
        and (scoring_task.intent_type == "no_ui_chat" or scoring_task.expected_pattern in ("none", "delete"))
    ):
        skip_l2l3 = True
        l2_judge_note = "skipped: no_ui_chat task"
        l3_judge_note = "skipped: no_ui_chat task"

    # Render check gate: after L1 pass, before L2/L3 judge call
    if l1_pass and not skip_l2l3 and a2ui_messages:
        render_check_pass, render_check_issues = _render_check(a2ui_messages)
        if not render_check_pass:
            # Penalize instead of skipping: give L2/L3 floor scores (1.0)
            l2_scores = {k: 1.0 for k in L2_DIMS}
            l3_scores = {k: 1.0 for k in L3_DIMS}
            l2_judge_valid = True
            l3_judge_valid = True
            l2_judge_note = f"penalized: render_check failed ({len(render_check_issues)} issues)"
            l3_judge_note = f"penalized: render_check failed ({len(render_check_issues)} issues)"

    # Also penalize L1-fail tasks (don't skip, give floor scores)
    if not l1_pass and not skip_l2l3:
        l2_scores = {k: 1.0 for k in L2_DIMS}
        l3_scores = {k: 1.0 for k in L3_DIMS}
        l2_judge_valid = True
        l3_judge_valid = True
        l2_judge_note = "penalized: L1 failed"
        l3_judge_note = "penalized: L1 failed"

    if l1_pass and not skip_l2l3 and render_check_pass:
        async with judge_sem:
            raw_l2_judge = await _chat_completion_json(
                judge_client,
                judge_model,
                build_l2_judge_messages(scoring_task, text_response, a2ui_messages),
                temperature=0.0,
                max_tokens=2000,
            )
        l2_obj = _extract_json_object(raw_l2_judge)
        if l2_obj is not None:
            l2_scores, l2_judge_valid, l2_err = _strict_dim_scores(l2_obj, L2_DIMS)
            if l2_judge_valid:
                l2_judge_note = str(l2_obj.get("overall_note", ""))[:200]
            else:
                print(f"\n[L2 JUDGE PARSE ERROR] task={scoring_task.task_id} err={l2_err}")
                print(f"  RAW L2 JUDGE (first 500 chars): {raw_l2_judge[:500]}")
                print()
                l2_judge_note = f"l2_judge_invalid:{l2_err}"
                l2_scores = {k: 0.0 for k in L2_DIMS}
        else:
            print(f"\n[L2 JUDGE JSON ERROR] task={scoring_task.task_id}")
            print(f"  RAW L2 JUDGE (first 500 chars): {raw_l2_judge[:500]}")
            print()
            l2_judge_note = "l2_judge_json_parse_failed"

        async with judge_sem:
            raw_l3_judge = await _chat_completion_json(
                judge_client,
                judge_model,
                build_l3_judge_messages(scoring_task, text_response, a2ui_messages),
                temperature=0.0,
                max_tokens=2000,
            )
        l3_obj = _extract_json_object(raw_l3_judge)
        if l3_obj is not None:
            l3_scores, l3_judge_valid, l3_err = _strict_dim_scores(l3_obj, L3_DIMS)
            if l3_judge_valid:
                l3_judge_note = str(l3_obj.get("overall_note", ""))[:200]
            else:
                print(f"\n[L3 JUDGE PARSE ERROR] task={scoring_task.task_id} err={l3_err}")
                print(f"  RAW L3 JUDGE (first 500 chars): {raw_l3_judge[:500]}")
                print()
                l3_judge_note = f"l3_judge_invalid:{l3_err}"
                l3_scores = {k: 0.0 for k in L3_DIMS}
        else:
            print(f"\n[L3 JUDGE JSON ERROR] task={scoring_task.task_id}")
            print(f"  RAW L3 JUDGE (first 500 chars): {raw_l3_judge[:500]}")
            print()
            l3_judge_note = "l3_judge_json_parse_failed"

    return {
        "model_output": {
            "raw": raw_pred,
            "text_response": text_response,
            "a2ui_messages": a2ui_messages,
            "parse_error": parse_error,
            "parse_note": parse_note,
        },
        "l1": {
            "pass": l1_pass,
            "scores": l1_scores,
            "details": l1_details,
        },
        "render_check": {
            "pass": render_check_pass,
            "issues": render_check_issues,
        },
        "l2": {"scores": l2_scores, "judge_note": l2_judge_note, "judge_valid": l2_judge_valid},
        "l3": {"scores": l3_scores, "judge_note": l3_judge_note, "judge_valid": l3_judge_valid},
        "skip_l2l3": skip_l2l3,
        "hard_fail": {
            "any": False,
            "missing_required_a2ui": False,
        },
    }


async def _predict_single_turn(
    task: TaskSample,
    *,
    model_name: str,
    model_client: AsyncOpenAI,
    model_sem: asyncio.Semaphore,
    generation_guide: str,
    model_max_tokens: int,
    step_idx: int | None = None,
    total_steps: int | None = None,
) -> tuple[str, str, list[dict], bool, str]:
    async with model_sem:
        raw_pred = await _chat_completion_json(
            model_client,
            model_name,
            build_generation_messages(
                task,
                generation_guide,
                step_idx=step_idx,
                total_steps=total_steps,
            ),
            temperature=0.7,
            max_tokens=model_max_tokens,
        )
    text_response, a2ui_messages, parse_error, parse_note = _coerce_output(raw_pred)
    return raw_pred, text_response, a2ui_messages, parse_error, parse_note


def _build_depth_rollout_text(step_rollouts: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for idx, step in enumerate(step_rollouts, start=1):
        step_meta = step.get("step_meta", {}) or {}
        out = step.get("model_output", {}) or {}
        user_msg = str(step_meta.get("user_message", "")).strip()
        text = str(out.get("text_response", "")).strip()
        if not text:
            text = str(out.get("raw", "")).strip()
        lines.append(f"[Step {idx} User]\n{user_msg}")
        lines.append(f"[Step {idx} Assistant]\n{text}")
    return "\n\n".join(lines)[:12000]


def _aggregate_depth_result(
    task: TaskSample,
    step_rollouts: list[dict[str, Any]],
    overall_scored: dict[str, Any],
) -> dict[str, Any]:
    final_output = step_rollouts[-1]["model_output"] if step_rollouts else {}
    parse_notes = [
        r["model_output"]["parse_note"]
        for r in step_rollouts
        if r["model_output"]["parse_note"]
    ]
    parse_error_count = sum(1 for r in step_rollouts if r["model_output"]["parse_error"])
    return {
        "task_id": task.task_id,
        "source": task.source,
        "scenario_id": task.scenario_id,
        "intent_type": task.intent_type,
        "difficulty_level": task.difficulty_level,
        "expected_pattern": task.expected_pattern,
        "model_output": {
            "trajectory_mode": "depth_rollout",
            "steps": [{"step_idx": idx, **step} for idx, step in enumerate(step_rollouts)],
            "raw": final_output.get("raw", ""),
            "text_response": final_output.get("text_response", ""),
            "a2ui_messages": final_output.get("a2ui_messages", []),
            "parse_error": any(r["model_output"]["parse_error"] for r in step_rollouts),
            "parse_note": "; ".join(parse_notes),
        },
        "l1": overall_scored["l1"],
        "l2": overall_scored["l2"],
        "l3": overall_scored["l3"],
        "skip_l2l3": overall_scored["skip_l2l3"],
        "hard_fail": overall_scored["hard_fail"],
        "trajectory": {
            "step_count": len(step_rollouts),
            "parse_error_step_count": parse_error_count,
            "judge_target": "single L2/L3 over full depth rollout",
        },
    }


async def evaluate_one_task(
    task: TaskSample,
    model_name: str,
    judge_model: str,
    model_client: AsyncOpenAI,
    judge_client: AsyncOpenAI,
    validate_fn,
    model_sem: asyncio.Semaphore,
    judge_sem: asyncio.Semaphore,
    generation_guide: str,
    model_max_tokens: int,
) -> dict[str, Any]:
    if task.difficulty_level == "depth" and task.episode_turns:
        running_context = list(task.raw_context.get("initial_dialogue_context", task.dialogue_context))
        step_rollouts: list[dict[str, Any]] = []
        total_steps = len(task.episode_turns)
        flat_a2ui_messages: list[dict] = []
        parse_notes: list[str] = []
        last_raw_pred = ""
        last_user_message = ""
        # Per-step L1 validation (avoids false REF_DUPLICATE_ID from cross-step ID reuse)
        step_l1_results: list[tuple[dict[str, float], bool, dict[str, Any]]] = []
        for step_idx, step in enumerate(task.episode_turns):
            scoring_task = _make_override_task(
                task,
                user_message=str(step.get("user_message", "")).strip(),
                dialogue_context=running_context[-8:],
                expected_pattern=str(step.get("expected_pattern", task.expected_pattern)),
                gt_a2ui=step.get("gt_a2ui", []),
                gt_assistant_text=str(step.get("gt_assistant_text", "")),
                intent_type=str(step.get("intent_type", task.intent_type)),
            )
            raw_pred, text_response, a2ui_messages, parse_error, parse_note = await _predict_single_turn(
                scoring_task,
                model_name=model_name,
                model_client=model_client,
                model_sem=model_sem,
                generation_guide=generation_guide,
                model_max_tokens=model_max_tokens,
                step_idx=step_idx,
                total_steps=total_steps,
            )
            last_raw_pred = raw_pred
            last_user_message = scoring_task.user_message
            flat_a2ui_messages.extend(a2ui_messages)
            # L1 per-step: validate this step's a2ui independently
            step_l1 = evaluate_l1_scores(parse_error, a2ui_messages, validate_fn)
            step_l1_results.append(step_l1)
            if parse_note:
                parse_notes.append(f"step{step_idx + 1}:{parse_note}")
            step_rollouts.append(
                {
                    "step_meta": {
                        "step_idx": step_idx,
                        "intent_type": scoring_task.intent_type,
                        "expected_pattern": scoring_task.expected_pattern,
                        "user_message": scoring_task.user_message,
                    },
                    "model_output": {
                        "raw": raw_pred,
                        "text_response": text_response,
                        "a2ui_messages": a2ui_messages,
                        "parse_error": parse_error,
                        "parse_note": parse_note,
                    },
                }
            )
            scored_text = text_response.strip() if text_response.strip() else raw_pred.strip()
            running_context.append({"role": "user", "content": scoring_task.user_message})
            running_context.append({"role": "assistant", "content": scored_text})

        rollout_text = _build_depth_rollout_text(step_rollouts)
        # Aggregate per-step L1: pass only if ALL steps pass; merge diagnostics
        agg_l1_pass = all(s[1] for s in step_l1_results)
        agg_error_count = sum(s[2].get("error_count", 0) for s in step_l1_results)
        agg_warning_count = sum(s[2].get("warning_count", 0) for s in step_l1_results)
        agg_diag_codes: list[str] = []
        agg_warn_codes: list[str] = []
        for s in step_l1_results:
            agg_diag_codes.extend(s[2].get("diagnostic_codes", []))
            agg_warn_codes.extend(s[2].get("warning_codes", []))
        # Aggregate per-dimension issue counts across steps
        _prefix_to_dim_agg = {
            "STRUCT_": "L1-2", "REF_": "L1-3",
            "DATA_": "L1-4", "LINT_": "L1-5",
        }
        agg_dim_issues: dict[str, int] = {"L1-2": 0, "L1-3": 0, "L1-4": 0, "L1-5": 0}
        agg_dim_has_error: dict[str, bool] = {"L1-2": False, "L1-3": False, "L1-4": False, "L1-5": False}
        for code in agg_diag_codes:
            for prefix, dim in _prefix_to_dim_agg.items():
                if code.startswith(prefix):
                    agg_dim_issues[dim] += 1
                    agg_dim_has_error[dim] = True
                    break
        for code in agg_warn_codes:
            for prefix, dim in _prefix_to_dim_agg.items():
                if code.startswith(prefix):
                    agg_dim_issues[dim] += 1
                    break

        if agg_l1_pass:
            agg_l1_scores = {"L1-1": 5.0}
            for dim in ["L1-2", "L1-3", "L1-4", "L1-5"]:
                agg_l1_scores[dim] = float(max(0, 5 - agg_dim_issues[dim]))
        else:
            # Consistent with evaluate_l1_scores: if L1 fails (any error anywhere),
            # ALL dimensions get 0. Rationale: when output has structural errors,
            # the validator may not reach deeper checks (REF/DATA/LINT), so "no
            # error reported" in those dims is unreliable.
            agg_l1_scores = {"L1-1": 0.0}
            for dim in ["L1-2", "L1-3", "L1-4", "L1-5"]:
                agg_l1_scores[dim] = 0.0
        agg_l1_details = {
            "is_valid": agg_l1_pass,
            "error_count": agg_error_count,
            "warning_count": agg_warning_count,
            "diagnostic_codes": agg_diag_codes,
            "warning_codes": agg_warn_codes,
            "policy_error_codes": [],
            "per_step_pass": [s[1] for s in step_l1_results],
        }
        depth_l1 = (agg_l1_scores, agg_l1_pass, agg_l1_details)

        overall_scoring_task = _make_override_task(
            task,
            user_message=last_user_message,
            dialogue_context=running_context[-8:],
            expected_pattern=task.expected_pattern,
            gt_a2ui=task.gt_a2ui,
            gt_assistant_text=task.gt_assistant_text,
            intent_type=task.intent_type,
        )
        overall_scored = await _score_prediction(
            overall_scoring_task,
            rollout_text,
            flat_a2ui_messages,
            last_raw_pred,
            False,
            "; ".join(parse_notes),
            judge_model=judge_model,
            judge_client=judge_client,
            validate_fn=validate_fn,
            judge_sem=judge_sem,
            precomputed_l1=depth_l1,
        )
        return _aggregate_depth_result(task, step_rollouts, overall_scored)

    raw_pred, text_response, a2ui_messages, parse_error, parse_note = await _predict_single_turn(
        task,
        model_name=model_name,
        model_client=model_client,
        model_sem=model_sem,
        generation_guide=generation_guide,
        model_max_tokens=model_max_tokens,
    )
    scored = await _score_prediction(
        task,
        text_response,
        a2ui_messages,
        raw_pred,
        parse_error,
        parse_note,
        judge_model=judge_model,
        judge_client=judge_client,
        validate_fn=validate_fn,
        judge_sem=judge_sem,
    )
    return {
        "task_id": task.task_id,
        "source": task.source,
        "scenario_id": task.scenario_id,
        "intent_type": task.intent_type,
        "difficulty_level": task.difficulty_level,
        "expected_pattern": task.expected_pattern,
        **scored,
    }


def _avg(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def aggregate_results(task_results: list[dict[str, Any]]) -> dict[str, Any]:
    # Overall L1 pass rate
    l1_pass_rate = _avg([1.0 if r["l1"]["pass"] else 0.0 for r in task_results])
    parse_ok_rate = _avg([0.0 if r["model_output"]["parse_error"] else 1.0 for r in task_results])

    # Dimension means
    level_dim_means: dict[str, dict[str, float]] = {"l1": {}, "l2": {}, "l3": {}}
    for did in L1_DIMS:
        level_dim_means["l1"][did] = _avg([r["l1"]["scores"][did] for r in task_results])

    # All scorable tasks for L2/L3: everything except no_ui_chat (skip_l2l3)
    l23_scorable = [r for r in task_results if not r.get("skip_l2l3")]
    # L2/L3 eligible (passed L1): used for judge success rate reporting
    l23_eligible = [r for r in l23_scorable if r["l1"]["pass"] and not r["hard_fail"]["any"]]
    hard_fail_missing_a2ui_rate = _avg([1.0 if r["hard_fail"]["missing_required_a2ui"] else 0.0 for r in task_results])
    hard_fail_any_rate = _avg([1.0 if r["hard_fail"]["any"] else 0.0 for r in task_results])
    skipped_no_ui_count = sum(1 for r in task_results if r.get("skip_l2l3"))

    # Judge success rates (only among l23_eligible)
    l2_judge_ok = [r for r in l23_eligible if r["l2"].get("judge_valid")]
    l3_judge_ok = [r for r in l23_eligible if r["l3"].get("judge_valid")]
    l2_judge_rate = len(l2_judge_ok) / len(l23_eligible) if l23_eligible else 0.0
    l3_judge_rate = len(l3_judge_ok) / len(l23_eligible) if l23_eligible else 0.0
    # L2/L3 dimension means: average over ALL scorable tasks (not just L1-passed).
    # Tasks that failed L1 contribute floor scores (0.0) — no survivorship bias.
    for did in L2_DIMS:
        level_dim_means["l2"][did] = _avg([r["l2"]["scores"][did] for r in l23_scorable]) if l23_scorable else 0.0
    for did in L3_DIMS:
        level_dim_means["l3"][did] = _avg([r["l3"]["scores"][did] for r in l23_scorable]) if l23_scorable else 0.0

    # Scenario × dimension matrices
    scenario_dim: dict[str, dict[str, dict[str, float]]] = {
        "l1": defaultdict(dict),
        "l2": defaultdict(dict),
        "l3": defaultdict(dict),
    }
    by_s: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in task_results:
        by_s[r["scenario_id"]].append(r)

    for sid in SCENARIO_DEFS:
        bucket = by_s.get(sid, [])
        # All scorable tasks in this scenario (exclude no_ui_chat)
        bucket_l23_scorable = [r for r in bucket if not r.get("skip_l2l3")]
        for did in L1_DIMS:
            scenario_dim["l1"][sid][did] = _avg([r["l1"]["scores"][did] for r in bucket]) if bucket else 0.0
        # L2/L3: average over all scorable tasks; L1 failures contribute 0.0
        for did in L2_DIMS:
            scenario_dim["l2"][sid][did] = _avg([r["l2"]["scores"][did] for r in bucket_l23_scorable]) if bucket_l23_scorable else 0.0
        for did in L3_DIMS:
            scenario_dim["l3"][sid][did] = _avg([r["l3"]["scores"][did] for r in bucket_l23_scorable]) if bucket_l23_scorable else 0.0

    l1_total = _avg(list(level_dim_means["l1"].values()))
    l2_total = _avg(list(level_dim_means["l2"].values()))
    l3_total = _avg(list(level_dim_means["l3"].values()))
    # Overall score: L1 failures already contribute 0 to L2/L3 means (no survivorship bias),
    # so no additional l1_pass_rate discount is needed.
    overall_0_100 = (
        0.40 * (l1_total / 5.0)
        + 0.30 * (l2_total / 5.0)
        + 0.30 * (l3_total / 5.0)
    ) * 100.0

    # Render check pass rate
    render_check_pass_rate = _avg([
        1.0 if r.get("render_check", {}).get("pass", True) else 0.0
        for r in task_results
    ])

    return {
        "task_count": len(task_results),
        "l1_pass_rate": l1_pass_rate,
        "json_parse_ok_rate": parse_ok_rate,
        "render_check_pass_rate": render_check_pass_rate,
        "l23_scorable_count": len(l23_scorable),
        "l23_eligible_count": len(l23_eligible),
        "skipped_no_ui_count": skipped_no_ui_count,
        "l2_judge_success_rate": l2_judge_rate,
        "l3_judge_success_rate": l3_judge_rate,
        "l2_judge_ok_count": len(l2_judge_ok),
        "l3_judge_ok_count": len(l3_judge_ok),
        "hard_fail_missing_a2ui_rate": hard_fail_missing_a2ui_rate,
        "hard_fail_any_rate": hard_fail_any_rate,
        "level_dim_means": level_dim_means,
        "scenario_x_dimension": scenario_dim,
        "level_totals_0_5": {
            "L1": l1_total,
            "L2": l2_total,
            "L3": l3_total,
        },
        "overall_score_0_100": overall_0_100,
    }


def save_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def build_leaderboard(model_to_summary: dict[str, dict[str, Any]]) -> dict[str, Any]:
    rows = []
    for model, summary in model_to_summary.items():
        rows.append(
            {
                "model": model,
                "overall_score_0_100": round(summary["overall_score_0_100"], 3),
                "L1_total_0_5": round(summary["level_totals_0_5"]["L1"], 3),
                "L2_total_0_5": round(summary["level_totals_0_5"]["L2"], 3),
                "L3_total_0_5": round(summary["level_totals_0_5"]["L3"], 3),
                "l1_pass_rate": round(summary["l1_pass_rate"], 4),
            }
        )
    rows.sort(key=lambda x: x["overall_score_0_100"], reverse=True)

    observed_order = [r["model"] for r in rows]
    expected_order = [m for m in ["openai/gpt-5.4", "deepseek/deepseek-chat-v3.1", "openai/gpt-4o-mini"] if m in model_to_summary]
    pairwise_deltas = []
    for i in range(len(rows) - 1):
        a = rows[i]
        b = rows[i + 1]
        pairwise_deltas.append(
            {
                "better_model": a["model"],
                "worse_model": b["model"],
                "delta_overall": round(a["overall_score_0_100"] - b["overall_score_0_100"], 4),
            }
        )

    return {
        "leaderboard": rows,
        "gradient_analysis": {
            "expected_order": expected_order,
            "observed_order": observed_order,
            "matches_expected_prefix": (observed_order[: len(expected_order)] == expected_order) if expected_order else None,
            "pairwise_deltas": pairwise_deltas,
        },
    }


async def evaluate_models(args) -> None:
    _setup_env()
    api_key = args.api_key or os.environ.get("OPENAI_API_KEY", "")
    base_url = args.base_url or os.environ.get("OPENAI_BASE_URL", DEFAULT_BASE_URL)
    judge_api_key = args.judge_api_key or os.environ.get("JUDGE_OPENAI_API_KEY", "") or api_key
    judge_base_url = args.judge_base_url or os.environ.get("JUDGE_OPENAI_BASE_URL", "") or base_url
    if not api_key:
        raise RuntimeError("Missing API key. Set OPENAI_API_KEY or pass --api-key.")
    if not judge_api_key:
        raise RuntimeError("Missing judge API key. Set JUDGE_OPENAI_API_KEY or pass --judge-api-key.")

    validate_fn = _ensure_a2ui_lint_import()
    generation_guide = _build_generation_guide(args.prompt_mode)
    print(f"Prompt mode: {args.prompt_mode}, guide_chars={len(generation_guide)}")
    task_dir = Path(args.task_dir)
    out_dir = Path(args.output_dir)

    source_filter = set(args.sources)
    all_tasks = [
        task for task in load_task_samples(task_dir)
        if task.source in source_filter
    ]
    selected = sample_balanced(all_tasks, args.max_per_scenario, args.seed)
    if not selected:
        raise RuntimeError(f"No tasks loaded from {task_dir} for sources={args.sources}.")

    print(f"Loaded tasks: total={len(all_tasks)}, selected={len(selected)}")
    by_s = defaultdict(int)
    for t in selected:
        by_s[t.scenario_id] += 1
    print("Scenario distribution:", dict(sorted(by_s.items())))

    save_json(
        out_dir / "task_sample_manifest.json",
        {
            "task_dir": str(task_dir),
            "max_per_scenario": args.max_per_scenario,
            "seed": args.seed,
            "selected_task_ids": [t.task_id for t in selected],
            "scenario_distribution": dict(sorted(by_s.items())),
        },
    )

    model_client = AsyncOpenAI(api_key=api_key, base_url=base_url)
    judge_client = AsyncOpenAI(api_key=judge_api_key, base_url=judge_base_url)
    model_to_summary: dict[str, dict[str, Any]] = {}

    for model_name in args.models:
        print(f"\n=== Evaluating model: {model_name} ===")
        start = time.time()

        model_sem = asyncio.Semaphore(args.model_concurrency)
        judge_sem = asyncio.Semaphore(args.judge_concurrency)

        coros = [
            evaluate_one_task(
                task=t,
                model_name=model_name,
                judge_model=args.judge_model,
                model_client=model_client,
                judge_client=judge_client,
                validate_fn=validate_fn,
                model_sem=model_sem,
                judge_sem=judge_sem,
                generation_guide=generation_guide,
                model_max_tokens=args.model_max_tokens,
            )
            for t in selected
        ]
        task_results = await asyncio.gather(*coros)
        summary = aggregate_results(task_results)
        summary["model"] = model_name
        summary["judge_model"] = args.judge_model
        summary["elapsed_seconds"] = round(time.time() - start, 2)
        summary["generation_prompt"] = {
            "prompt_mode": args.prompt_mode,
            "model_max_tokens": args.model_max_tokens,
            "schema_hint": generation_guide,
            "output_format_hint": OUTPUT_SCHEMA_HINT.strip(),
        }

        model_key = model_name.replace("/", "__")
        save_json(out_dir / model_key / "summary.json", summary)
        save_json(out_dir / model_key / "task_results.json", task_results)
        model_to_summary[model_name] = summary

        print(
            f"done: overall={summary['overall_score_0_100']:.2f}, "
            f"L1pass={summary['l1_pass_rate']:.3f}, "
            f"L1/L2/L3={summary['level_totals_0_5']['L1']:.2f}/"
            f"{summary['level_totals_0_5']['L2']:.2f}/"
            f"{summary['level_totals_0_5']['L3']:.2f}, "
            f"judge_ok(L2/L3)={summary['l2_judge_ok_count']}/{summary['l3_judge_ok_count']} "
            f"of {summary['l23_eligible_count']} eligible"
        )

    leaderboard = build_leaderboard(model_to_summary)
    save_json(out_dir / "comparison.json", {"models": model_to_summary, **leaderboard})

    print("\n=== Leaderboard ===")
    for i, row in enumerate(leaderboard["leaderboard"], start=1):
        print(
            f"{i}. {row['model']} | overall={row['overall_score_0_100']:.2f} | "
            f"L1={row['L1_total_0_5']:.2f} L2={row['L2_total_0_5']:.2f} L3={row['L3_total_0_5']:.2f}"
        )
    print(f"\nSaved to: {out_dir}")


def parse_args():
    parser = argparse.ArgumentParser(description="Evaluate API models on A2UI tasks.")
    parser.add_argument(
        "--task-dir",
        type=Path,
        default=_EVAL_ROOT / "data" / "eval_300",
        help="Directory containing *_tasks.json files.",
    )
    parser.add_argument(
        "--sources",
        nargs="+",
        default=DEFAULT_TASK_SOURCES,
        choices=DEFAULT_TASK_SOURCES,
        help="Task sources to load.",
    )
    parser.add_argument(
        "--models",
        nargs="+",
        default=DEFAULT_MODELS,
        help="Models to evaluate.",
    )
    parser.add_argument(
        "--judge-model",
        default="openai/gpt-5.4",
        help="Judge model for L2/L3 scoring.",
    )
    parser.add_argument("--max-per-scenario", type=int, default=10, help="Max sampled tasks per scenario; use 0 to keep all tasks.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for sampling.")
    parser.add_argument("--model-concurrency", type=int, default=6, help="Concurrency for model calls.")
    parser.add_argument("--judge-concurrency", type=int, default=6, help="Concurrency for judge calls.")
    parser.add_argument("--model-max-tokens", type=int, default=2200, help="Max completion tokens for model generation calls.")
    parser.add_argument(
        "--prompt-mode",
        choices=["minimal", "full"],
        default="minimal",
        help="Prompt verbosity: minimal (component list + descriptions), full (complete schema from a2ui_demo).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=_EVAL_ROOT / "results",
        help="Output directory.",
    )
    parser.add_argument("--api-key", default="", help="API key (fallback to OPENAI_API_KEY env).")
    parser.add_argument("--base-url", default="", help="API base URL (fallback to OPENAI_BASE_URL env).")
    parser.add_argument("--judge-api-key", default="", help="Judge API key (fallback to JUDGE_OPENAI_API_KEY, then model API key).")
    parser.add_argument("--judge-base-url", default="", help="Judge API base URL (fallback to JUDGE_OPENAI_BASE_URL, then model base URL).")
    return parser.parse_args()


def main():
    args = parse_args()
    asyncio.run(evaluate_models(args))


if __name__ == "__main__":
    main()
