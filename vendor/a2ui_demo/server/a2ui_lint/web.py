"""A2UI Lint — Web Demo.

Run:  python -m server.a2ui_lint.web
Open: http://localhost:8080
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from . import validate, validate_raw

app = FastAPI(title="A2UI Lint Web Demo")

STATIC_DIR = Path(__file__).parent / "static"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESOURCES_COMPONENT_SCHEMAS_DIR = PROJECT_ROOT / "resources" / "components" / "schemas"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_json_from_example(raw: str) -> str:
    """Pull the JSON array that follows 'A2UI JSON:' in a few-shot example."""
    marker = "A2UI JSON:\n"
    idx = raw.find(marker)
    if idx == -1:
        return "[]"
    return raw[idx + len(marker):].strip()


def _example_stats(messages: list[dict]) -> dict:
    """Compute quick stats from parsed A2UI messages."""
    component_count = 0
    surface_ids: list[str] = []
    for msg in messages:
        for key in ("beginRendering", "surfaceUpdate", "dataModelUpdate"):
            obj = msg.get(key)
            if obj and "surfaceId" in obj:
                sid = obj["surfaceId"]
                if sid not in surface_ids:
                    surface_ids.append(sid)
        su = msg.get("surfaceUpdate")
        if su:
            component_count += len(su.get("components", []))
    return {
        "message_count": len(messages),
        "component_count": component_count,
        "surface_ids": surface_ids,
    }


def _resolve_schema_path(schema_path: str | None) -> str | None:
    """Resolve a schema filename to an absolute path, or return None."""
    if not schema_path:
        return None
    p = Path(schema_path)
    if not p.is_absolute():
        p = RESOURCES_COMPONENT_SCHEMAS_DIR / p
    if p.exists():
        return str(p)
    return None


# ---------------------------------------------------------------------------
# Pre-built error examples
# ---------------------------------------------------------------------------

ERROR_EXAMPLES: list[dict] = [
    {
        "name": "Missing Component Ref",
        "json": json.dumps([
            {"beginRendering": {"surfaceId": "s1", "root": "nonexistent-id", "styles": {}}},
            {"surfaceUpdate": {"surfaceId": "s1", "components": [
                {"id": "root-col", "component": {"Column": {"children": {"explicitList": ["t1"]}}}}
            ]}}
        ], indent=2),
    },
    {
        "name": "Duplicate ID",
        "json": json.dumps([
            {"beginRendering": {"surfaceId": "s1", "root": "root-col", "styles": {}}},
            {"surfaceUpdate": {"surfaceId": "s1", "components": [
                {"id": "root-col", "component": {"Column": {"children": {"explicitList": ["t1"]}}}},
                {"id": "t1", "component": {"Text": {"text": {"literalString": "Hello"}}}},
                {"id": "t1", "component": {"Text": {"text": {"literalString": "World"}}}}
            ]}}
        ], indent=2),
    },
    {
        "name": "Absolute Path in Template",
        "json": json.dumps([
            {"beginRendering": {"surfaceId": "s1", "root": "root-list", "styles": {}}},
            {"surfaceUpdate": {"surfaceId": "s1", "components": [
                {"id": "root-list", "component": {"List": {
                    "children": {"template": {"componentId": "item-card", "dataBinding": "/items"}},
                    "direction": "vertical"
                }}},
                {"id": "item-card", "component": {"Text": {"text": {"path": "/items/0/title"}, "usageHint": "body"}}}
            ]}},
            {"dataModelUpdate": {"surfaceId": "s1", "path": "/", "contents": [
                {"key": "items", "valueMap": [
                    {"key": "i1", "valueMap": [{"key": "title", "valueString": "Item 1"}]}
                ]}
            ]}}
        ], indent=2),
    },
    {
        "name": "Missing Required Field",
        "json": json.dumps([
            {"beginRendering": {"surfaceId": "s1", "root": "root-text", "styles": {}}},
            {"surfaceUpdate": {"surfaceId": "s1", "components": [
                {"id": "root-text", "component": {"Text": {}}}
            ]}}
        ], indent=2),
    },
]

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/")
async def index():
    return FileResponse(STATIC_DIR / "index.html")


class ValidateRequest(BaseModel):
    json_text: str
    levels: list[int] = [1, 2, 3, 4]
    raw_mode: bool = False
    schema_path: str | None = None


@app.post("/api/validate")
async def api_validate(req: ValidateRequest):
    levels = set(req.levels) if req.levels else None
    resolved_schema = _resolve_schema_path(req.schema_path)

    if req.raw_mode:
        text, messages, result = validate_raw(req.json_text, levels=levels, schema_path=resolved_schema)
        stats = _example_stats(messages) if messages else {"message_count": 0, "component_count": 0, "surface_ids": []}
        return JSONResponse({
            "text_content": text,
            **result.to_dict(),
            **stats,
        })

    # Direct JSON mode
    try:
        parsed = json.loads(req.json_text)
    except json.JSONDecodeError as e:
        return JSONResponse({
            "is_valid": False,
            "error_count": 1,
            "warning_count": 0,
            "diagnostics": [{"severity": "error", "code": "PARSE_ERROR", "message": f"JSON parse error: {e}"}],
            "message_count": 0,
            "component_count": 0,
            "surface_ids": [],
        })

    if isinstance(parsed, dict):
        parsed = [parsed]

    result = validate(parsed, levels=levels, schema_path=resolved_schema)
    stats = _example_stats(parsed)
    return JSONResponse({**result.to_dict(), **stats})


@app.get("/api/examples")
async def api_examples():
    from ..ui_examples import (
        EMAIL_LIST_EXAMPLE,
        NEWS_CARDS_EXAMPLE,
        SIMPLE_DATA_EXAMPLE,
        TABS_EXAMPLE,
        FORM_EXAMPLE,
        IMAGE_GALLERY_EXAMPLE,
        DATETIME_EXAMPLE,
    )

    valid_examples = [
        ("Email List", EMAIL_LIST_EXAMPLE),
        ("News Cards", NEWS_CARDS_EXAMPLE),
        ("Weather Card", SIMPLE_DATA_EXAMPLE),
        ("Product Tabs", TABS_EXAMPLE),
        ("Feedback Form", FORM_EXAMPLE),
        ("Image Gallery", IMAGE_GALLERY_EXAMPLE),
        ("Date/Time Picker", DATETIME_EXAMPLE),
    ]

    examples = []
    for name, raw in valid_examples:
        examples.append({"name": name, "json": _extract_json_from_example(raw), "valid": True})

    for err in ERROR_EXAMPLES:
        examples.append({"name": err["name"], "json": err["json"], "valid": False})

    return JSONResponse(examples)


@app.get("/api/schemas")
async def api_schemas():
    """List available component schema files in resources/components/schemas."""
    if not RESOURCES_COMPONENT_SCHEMAS_DIR.exists():
        return JSONResponse([])
    files = sorted(p.name for p in RESOURCES_COMPONENT_SCHEMAS_DIR.glob("*_schema.json"))
    return JSONResponse(files)


@app.get("/api/prompt")
async def api_prompt(schema_path: str | None = Query(default=None)):
    """Generate a complete LLM system prompt, optionally using a custom schema."""
    from ..a2ui_prompt import build_a2ui_prompt_from_schema

    try:
        prompt = build_a2ui_prompt_from_schema(schema_path)
    except FileNotFoundError as e:
        return JSONResponse({"error": f"Schema not found: {e}"}, status_code=404)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

    return JSONResponse({"prompt": prompt})


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
