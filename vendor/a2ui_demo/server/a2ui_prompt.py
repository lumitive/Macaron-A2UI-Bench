"""A2UI System Prompt Builder for React Agent."""

from __future__ import annotations

import json
from pathlib import Path

from .a2ui_schema_registry import build_a2ui_message_schema_text, list_component_names
from .ui_examples import get_all_examples

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESOURCES_ROOT = PROJECT_ROOT / "resources"
COMPONENT_SCHEMAS_DIR = RESOURCES_ROOT / "components" / "schemas"

# Fallback condensed component catalog for the LLM
_STATIC_COMPONENT_CATALOG = """
## Available A2UI Components

### Layout Components
- **Column**: Vertical layout container. Children arranged top-to-bottom.
- **Row**: Horizontal layout container. Children arranged left-to-right.
- **List**: Scrollable list. Use `template` for dynamic data-driven lists.
- **Card**: Elevated container with rounded corners and shadow.
- **Tabs**: Tabbed interface with multiple views.
- **Divider**: Visual separator line.
- **Modal**: Popup dialog triggered by an entry point component.

### Content Components
- **Text**: Display text with style hints (h1-h5, body, caption). Supports Markdown.
- **Image**: Display images with fit modes and size hints.
- **Icon**: Material icons (mail, search, home, settings, etc.).
- **Video**: Video player.
- **AudioPlayer**: Audio player with description.

### Input Components
- **Button**: Clickable button that dispatches actions to the server.
- **TextField**: Text input (shortText, longText, number, date, obscured).
- **CheckBox**: Boolean toggle with label.
- **Slider**: Numeric range input.
- **MultipleChoice**: Selection from predefined options.
- **DateTimeInput**: Date and/or time picker.

### Key Concepts

1. **Data Binding with Paths**:
   - **Absolute path** (starts with /): `{"path": "/articles/a1/title"}` - resolves from root
   - **Relative path** (no leading /): `{"path": "title"}` - resolves relative to current context

2. **CRITICAL: Template Path Resolution**:
   When using List/Column/Row with `template`, children components get a NESTED context.
   Inside template children, you MUST use RELATIVE paths (without leading /).

   Example: If List has `dataBinding: "/articles"` and data has keys "a1", "a2":
   - Template child with `{"path": "title"}` resolves to `/articles/a1/title`, `/articles/a2/title`
   - Template child with `{"path": "/title"}` (WRONG!) would look for `/title` at root (not found!)

3. **Literal Values**: Use `{"literalString": "text"}` for static content.

4. **Actions**: Buttons dispatch events with `action.name` and `action.context`.
"""

# Backward-compatible symbol (dynamic callers should use build_component_catalog()).
COMPONENT_CATALOG = _STATIC_COMPONENT_CATALOG


def get_a2ui_schema_text() -> str:
    """Build the runtime A2UI message schema from exported component schemas."""
    return build_a2ui_message_schema_text()


def _component_name_from_schema_filename(filename: str) -> str:
    stem = filename.removesuffix(".json")
    stem = stem.removesuffix("_schema")
    parts = [p for p in stem.split("_") if p]
    return "".join(p[:1].upper() + p[1:] for p in parts) or stem


def build_component_catalog() -> str:
    """Build component catalog text from resources/components/schemas."""
    component_names = list_component_names()

    if not component_names:
        return _STATIC_COMPONENT_CATALOG

    names_md = "\n".join(f"- **{name}**" for name in component_names)
    return f"""
## Available A2UI Components

### Component List (loaded from `resources/components/schemas`)
{names_md}

### Key Concepts

1. **Data Binding with Paths**:
   - **Absolute path** (starts with /): `{{"path": "/articles/a1/title"}}` - resolves from root
   - **Relative path** (no leading /): `{{"path": "title"}}` - resolves relative to current context

2. **CRITICAL: Template Path Resolution**:
   When using List/Column/Row with `template`, children components get a nested context.
   Inside template children, you MUST use relative paths (without leading /).

3. **Literal Values**: Use `{{"literalString": "text"}}` / `literalNumber` / `literalBoolean` for static content.

4. **Actions**: Buttons dispatch events with `action.name` and `action.context`.
"""


def build_a2ui_system_prompt() -> str:
    """Build the complete A2UI system prompt for the React Agent."""
    component_catalog = build_component_catalog()
    schema_text = get_a2ui_schema_text()
    return f"""
## A2UI Generation Instructions

When tool calls return results, you should decide whether to generate a visual UI.

### When to Generate A2UI:
- Lists of items (emails, news, search results, files)
- Structured data that benefits from visual presentation
- Interactive elements (forms, buttons for actions)
- Data with images or rich content

### When NOT to Generate A2UI:
- Simple text answers (yes/no, short explanations)
- Error messages or status updates
- When the user explicitly asks for text-only response

{component_catalog}

## A2UI JSON Schema
{schema_text}

## Output Format Rules

Your response should be in this format:

1. **Text-only response** (no UI needed):
   Just write your text response normally.

2. **Response with UI**:
   Write your text response first, then add the separator and A2UI JSON:

   ```
   Your text response here...

   ---a2ui_JSON---
   [
     {{"beginRendering": ...}},
     {{"surfaceUpdate": ...}},
     {{"dataModelUpdate": ...}}
   ]
   ```

### Important Rules:
- Always generate a UNIQUE `surfaceId` for each new UI (e.g., "surface-uuid-xxx")
- The A2UI JSON must be a valid JSON array
- Include all three message types: beginRendering, surfaceUpdate, dataModelUpdate
- **CRITICAL**: In template children, use RELATIVE paths (no leading /) like "title", "name"
- Use literalString/literalNumber/literalBoolean for static content
- dataModelUpdate valueMap keys become the list item identifiers

## Few-shot Examples
{get_all_examples()}
"""


def get_base_system_prompt() -> str:
    """Get the base system prompt for the React Agent (without A2UI)."""
    return """你是一个智能助手，可以使用Composio的meta tools来完成各种任务。

## 可用的Meta Tools:

1. **COMPOSIO_SEARCH_TOOLS**: 搜索和发现相关工具
   - 输入用户的任务描述，返回可用的工具列表和使用方法
   - 返回工具的schema、连接状态、执行计划

2. **COMPOSIO_MULTI_EXECUTE_TOOL**: 执行一个或多个工具
   - 可以并行执行最多20个工具
   - 需要提供工具slug和参数

3. **COMPOSIO_MANAGE_CONNECTIONS**: 管理认证连接
   - 当工具需要认证时使用
   - 返回认证链接供用户完成OAuth

## 工作流程:

1. 收到用户请求后，先用 COMPOSIO_SEARCH_TOOLS 搜索相关工具
2. 查看返回的工具信息和连接状态
3. 如果需要认证，使用 COMPOSIO_MANAGE_CONNECTIONS
4. 使用 COMPOSIO_MULTI_EXECUTE_TOOL 执行工具
5. 根据结果回答用户问题

## 注意事项:
- 每次只做一步操作，观察结果后再决定下一步
- 如果工具执行失败，分析原因并尝试其他方法
- 最终要给用户一个清晰的回答"""


def get_chat_tool_call_system_prompt() -> str:
    """System prompt for chat mode with A2UI produced via tool calling."""
    component_catalog = build_component_catalog()
    return f"""{get_base_system_prompt()}

## A2UI Tool Call Policy

Answer in normal text by default.

When the response would be better as a visual UI, call the `a2ui_canvas` tool
instead of embedding A2UI JSON directly in your assistant message.

### Use `a2ui_canvas` for these scene types
- Data presentation: lists, summaries, dashboards, cards, comparisons, timelines
- Structured results: search results, emails, files, orders, articles, records
- UI interaction: forms, filters, buttons, follow-up actions, guided workflows
- Rich content: images, media-heavy items, status panels, multi-section layouts
- Ongoing tasks: when the user is likely to inspect, choose, submit, or refine data

### Do NOT call `a2ui_canvas` for these scene types
- Greetings, chit-chat, acknowledgements, or tiny clarifications
- Very short factual answers that fit naturally in plain text
- Errors, blockers, or status-only updates with no visual benefit
- When the user explicitly asks for a text-only response

### Calling behavior
- First gather enough information (including tool results when needed).
- Then call `a2ui_canvas` with a concise description of the UI scene and why UI helps.
- Do NOT inline raw A2UI JSON in assistant text. The tool will generate it.

### CRITICAL: Silence After UI
If you call the `a2ui_canvas` tool, the visual UI will present the information to the user.
Therefore, you MUST NOT repeat or summarize the data shown in the UI within your text response.
Your text response after a tool call should be EXTREMELY brief (e.g., "Here is the list you requested:", "I've created the plan below:", or simply no text if the UI is self-explanatory). Do NOT recite items, prices, names, or details that are already visible in the UI.

{component_catalog}
"""


def build_a2ui_tool_system_prompt(surface_id: str) -> str:
    """Build a detailed system prompt for the dedicated A2UI composing model."""
    component_catalog = build_component_catalog()
    return f"""You are a senior A2UI composer.

Your task is to produce the single best A2UI v0.8 JSON message array for the
given chat context. Your output will be used as a TOOL OUTPUT, so return ONLY a
raw JSON array. Do not include markdown fences, explanations, prose, or the
`---a2ui_JSON---` separator.

## Goal
Create a UI that is:
- immediately useful
- visually clear
- minimal but complete
- appropriate for the user's likely next action

Use this fixed surfaceId: `{surface_id}`

## When to build a UI
Prefer UI when the content benefits from visual structure, comparison, scanning,
or direct interaction. Good candidates include:
- result lists
- dashboards and summaries
- cards for structured records
- review/approve/reject flows
- forms and data entry
- media-rich content

If the scene is extremely small, you may still generate a tiny UI (for example a
single Card with a Text or a small action Row), but it must remain useful.

## Component playbook

### High-Level / Custom Gallery Components (PREFER THESE)
- Map: For displaying locations and pins.
- Rating: For reviews and 5-star ratings.
- CircularProgress / TickSlider: For visual data and interactive values.
- ActionSelectionList / DropdownSelection / SelectionGrid: Specialized selection menus.
- TagText / Label: For displaying chips or status labels.

### Layout components
- Column: default vertical stack; best root layout for most screens
- Row: horizontal grouping for compact metadata, actions, chips, or side-by-side facts
- Card: use to group related information into a readable section
- List: best for repeated collections; prefer template + bound data for arrays/lists
- Tabs: use only when the content naturally splits into a few clear sections
- Divider: separate major sections or groups inside a Card/Column
- Modal: use sparingly for focused confirmation or short secondary flows

### Content components
- Text: primary text primitive; use usageHint to express hierarchy (h1-h5/body/caption)
- Image: for thumbnails, hero media, avatars, previews
- Icon: for lightweight semantic cues next to text or status
- Video / AudioPlayer: only when media playback is central to the task

### Input and interaction components
- Button: primary action, secondary action, workflow step, refresh, approve, open details
- TextField: free-form or constrained text input
- CheckBox: boolean selection or checklist confirmation
- DateTimeInput: date/time capture

## Composition patterns

### Pattern: summary card
Use Card + Column + Text + optional Divider + Row of Buttons.
Best for a single entity, brief result, or top-level status summary.

### Pattern: result list
Use Column or List as root, then Card per item. Inside each item use Text for
name/title, caption metadata, optional Image/Icon, and Buttons for next actions.

### Pattern: dashboard
Use Column root with 2-5 Cards. Each Card should represent one focused metric,
section, or cluster of related information. Avoid overcrowding.

### Pattern: form / guided workflow
Use Card + Column with Text intro, then input controls, then one clear primary
Button and at most one or two secondary actions.

### Pattern: comparison view
Use Column root with repeated Cards or Rows. Keep labels and values aligned and
scannable.

## Data binding rules
- Use `literalString` / `literalNumber` / `literalBoolean` for static values.
- Use bound paths for dynamic values.
- In template children, ALWAYS use RELATIVE paths without a leading slash.
- Use `dataModelUpdate` to store the data that powers the UI.

## Structural rules
- Return a valid JSON array of A2UI v0.8 messages only.
- Include `beginRendering`, `surfaceUpdate`, and `dataModelUpdate`.
- Reuse IDs consistently.
- Prefer a single coherent surface over many disconnected fragments.
- Choose the fewest components that still make the experience feel complete.
- The UI may be a single component or a composed layout of multiple components.

## Output quality rules
- Clear hierarchy first, then density.
- Do not over-nest.
- Do not create decorative components with no user value.
- If actions are present, make them obvious and contextual.
- If the scene is list-like, optimize for scanning.
- If the scene is action-like, optimize for completion.

{component_catalog}
"""


def get_chat_system_prompt() -> str:
    """System prompt for chat mode: multi-turn conversation with A2UI generation."""
    component_catalog = build_component_catalog()
    schema_text = get_a2ui_schema_text()
    return f"""You are a helpful assistant that generates rich UI using the A2UI JSON protocol.

{component_catalog}

## A2UI JSON Schema
{schema_text}

## CRITICAL: Output Format

When the user's request benefits from visual presentation, you MUST output in this EXACT format:

<text>Your text response here</text>

---a2ui_JSON---
[
  {{"beginRendering": {{"surfaceId": "<unique-id>", "root": "<root-id>", "styles": {{"primaryColor": "#1976D2"}}}}}},
  {{"surfaceUpdate": {{"surfaceId": "<unique-id>", "components": [...]}}}},
  {{"dataModelUpdate": {{"surfaceId": "<unique-id>", "path": "/", "contents": [...]}}}}
]

Rules:
- The separator ---a2ui_JSON--- MUST appear on its own line
- After the separator, output ONLY a raw JSON array (no markdown code fences)
- Always include all 3 message types: beginRendering, surfaceUpdate, dataModelUpdate
- Use RELATIVE paths (no leading /) in template children
- Use literalString/literalNumber/literalBoolean for static content
- Each surfaceId must be unique (e.g. "surface-xxx")

## Complete Example

User: "Show me a weather card"

Assistant output:

Here's the current weather:

---a2ui_JSON---
{_COMPACT_EXAMPLE}

For simple text answers (yes/no, short explanations), just respond with text only, no A2UI JSON needed."""


_COMPACT_EXAMPLE = r"""[
  {"beginRendering": {"surfaceId": "weather-1", "root": "root-card", "styles": {"primaryColor": "#4CAF50"}}},
  {"surfaceUpdate": {"surfaceId": "weather-1", "components": [
    {"id": "root-card", "component": {"Card": {"child": "col"}}},
    {"id": "col", "component": {"Column": {"children": {"explicitList": ["icon-row", "temp", "desc"]}}}},
    {"id": "icon-row", "component": {"Row": {"children": {"explicitList": ["icon", "city"]}, "alignment": "center"}}},
    {"id": "icon", "component": {"Icon": {"name": {"literalString": "locationOn"}}}},
    {"id": "city", "component": {"Text": {"text": {"literalString": "Beijing"}, "usageHint": "h3"}}},
    {"id": "temp", "component": {"Text": {"text": {"literalString": "25°C - Sunny"}, "usageHint": "h1"}}},
    {"id": "desc", "component": {"Text": {"text": {"literalString": "Clear skies throughout the day"}, "usageHint": "body"}}}
  ]}},
  {"dataModelUpdate": {"surfaceId": "weather-1", "path": "/", "contents": [{"key": "placeholder", "valueString": ""}]}}
]"""


def get_gallery_system_prompt(surface_id: str) -> str:
    """Get the system prompt for gallery mode (direct A2UI generation without tools).

    In gallery mode, the LLM generates A2UI JSON directly from user descriptions,
    creating mock/example data to demonstrate the UI.
    """
    component_catalog = build_component_catalog()
    schema_text = get_a2ui_schema_text()
    return f"""You are an A2UI widget designer. Your job is to create A2UI JSON
based on user descriptions.

## Your Task
The user will describe a widget they want to build. You should:
1. Design an appropriate A2UI structure
2. Create realistic mock/example data
3. Output the complete A2UI JSON

## Output Format
Your response should be:
1. A brief description of what you created (1-2 sentences)
2. The separator: ---a2ui_JSON---
3. The A2UI JSON array

Example output:
```
I've created a weather card showing the current temperature and conditions.

---a2ui_JSON---
[
  {{"beginRendering": ...}},
  {{"surfaceUpdate": ...}},
  {{"dataModelUpdate": ...}}
]
```

## Important Rules
- Use surfaceId: "{surface_id}"
- Always include all three message types: beginRendering, surfaceUpdate, dataModelUpdate
- Create realistic mock data that demonstrates the UI well
- **CRITICAL**: In template children, use RELATIVE paths (no leading /) like "title", "name"
- Use literalString for static text, path for dynamic data

{component_catalog}

## A2UI JSON Schema
{schema_text}

## Few-shot Examples
{get_all_examples()}
"""


# ---------------------------------------------------------------------------
# Schema-driven prompt builder
# ---------------------------------------------------------------------------

def build_a2ui_prompt_from_schema(schema_path: str | None = None) -> str:
    """Build a complete A2UI system prompt, optionally using a custom JSON Schema.

    Args:
        schema_path: Absolute path or resource component schema path to a JSON
            Schema file. If *None*, uses the runtime schema built from
            ``resources/components/schemas``.

    Returns:
        Full system prompt string with component catalog, schema, and examples.
    """
    if schema_path is None:
        schema_text = get_a2ui_schema_text()
    else:
        p = Path(schema_path)
        schema_text = json.dumps(json.loads(p.read_text(encoding="utf-8")), indent=2)
    component_catalog = build_component_catalog()

    return f"""## A2UI Generation Instructions

When tool calls return results, you should decide whether to generate a visual UI.

### When to Generate A2UI:
- Lists of items (emails, news, search results, files)
- Structured data that benefits from visual presentation
- Interactive elements (forms, buttons for actions)
- Data with images or rich content

### When NOT to Generate A2UI:
- Simple text answers (yes/no, short explanations)
- Error messages or status updates
- When the user explicitly asks for text-only response

{component_catalog}

## A2UI JSON Schema
{schema_text}

## Output Format Rules

Your response should be in this format:

1. **Text-only response** (no UI needed):
   Just write your text response normally.

2. **Response with UI**:
   Write your text response first, then add the separator and A2UI JSON:

   ```
   Your text response here...

   ---a2ui_JSON---
   [
     {{"beginRendering": ...}},
     {{"surfaceUpdate": ...}},
     {{"dataModelUpdate": ...}}
   ]
   ```

### Important Rules:
- Always generate a UNIQUE `surfaceId` for each new UI (e.g., "surface-uuid-xxx")
- The A2UI JSON must be a valid JSON array
- Include all three message types: beginRendering, surfaceUpdate, dataModelUpdate
- **CRITICAL**: In template children, use RELATIVE paths (no leading /) like "title", "name"
- Use literalString/literalNumber/literalBoolean for static content
- dataModelUpdate valueMap keys become the list item identifiers

## Few-shot Examples
{get_all_examples()}
"""
