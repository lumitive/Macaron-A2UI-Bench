"""Build A2UI message schema dynamically from resources/components/schemas."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESOURCES_ROOT = PROJECT_ROOT / "resources"
COMPONENT_SCHEMAS_DIR = RESOURCES_ROOT / "components" / "schemas"
_RESERVED_SCHEMA_FILES = {"catalog_schema.json", "surface_update_schema.json"}

_MESSAGE_SCHEMA_TEMPLATE: dict = {
    "title": "A2UI Message Schema",
    "description": (
        "Describes a JSON payload for an A2UI message. A message MUST contain "
        "exactly one of the action properties: 'beginRendering', "
        "'surfaceUpdate', 'dataModelUpdate', or 'deleteSurface'."
    ),
    "type": "object",
    "properties": {
        "beginRendering": {
            "type": "object",
            "description": "Signals the client to begin rendering a surface.",
            "properties": {
                "surfaceId": {
                    "type": "string",
                    "description": "The unique identifier for the UI surface.",
                },
                "root": {
                    "type": "string",
                    "description": "The ID of the root component to render.",
                },
                "styles": {
                    "type": "object",
                    "description": "Optional styling information for the UI.",
                    "properties": {
                        "font": {"type": "string"},
                        "primaryColor": {
                            "type": "string",
                            "pattern": "^#[0-9a-fA-F]{6}$",
                        },
                    },
                },
            },
            "required": ["root", "surfaceId"],
        },
        "surfaceUpdate": {
            "type": "object",
            "description": "Updates a surface with a new set of components.",
            "properties": {
                "surfaceId": {
                    "type": "string",
                    "description": "The unique identifier for the UI surface.",
                },
                "components": {
                    "type": "array",
                    "description": "A list containing all UI components for the surface.",
                    "minItems": 1,
                    "items": {
                        "type": "object",
                        "description": "Represents a single component in a UI widget tree.",
                        "properties": {
                            "id": {
                                "type": "string",
                                "description": "The unique identifier for this component.",
                            },
                            "weight": {
                                "type": "number",
                                "description": (
                                    "The relative weight of this component within a Row "
                                    "or Column."
                                ),
                            },
                            "component": {
                                "type": "object",
                                "description": (
                                    "A wrapper object that MUST contain exactly one key, "
                                    "which is the name of the component type."
                                ),
                                "properties": {},
                            },
                        },
                        "required": ["id", "component"],
                    },
                },
            },
            "required": ["surfaceId", "components"],
        },
        "dataModelUpdate": {
            "type": "object",
            "description": "Updates the data model for a surface.",
            "properties": {
                "surfaceId": {
                    "type": "string",
                    "description": "The unique identifier for the UI surface.",
                },
                "path": {
                    "type": "string",
                    "description": "Optional path within the data model.",
                },
                "contents": {
                    "type": "array",
                    "description": "Array of typed data entries.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "key": {"type": "string"},
                            "valueString": {"type": "string"},
                            "valueNumber": {"type": "number"},
                            "valueBoolean": {"type": "boolean"},
                            "valueMap": {
                                "type": "array",
                                "description": "Represents a map as an adjacency list.",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "key": {"type": "string"},
                                        "valueString": {"type": "string"},
                                        "valueNumber": {"type": "number"},
                                        "valueBoolean": {"type": "boolean"},
                                        "valueMap": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "key": {"type": "string"},
                                                    "valueString": {"type": "string"},
                                                    "valueNumber": {"type": "number"},
                                                    "valueBoolean": {"type": "boolean"},
                                                },
                                                "required": ["key"],
                                            },
                                        },
                                    },
                                    "required": ["key"],
                                },
                            },
                        },
                        "required": ["key"],
                    },
                },
            },
            "required": ["contents", "surfaceId"],
        },
        "deleteSurface": {
            "type": "object",
            "description": "Signals the client to delete the surface.",
            "properties": {
                "surfaceId": {
                    "type": "string",
                    "description": "The unique identifier for the UI surface.",
                },
            },
            "required": ["surfaceId"],
        },
    },
}


def _component_name_from_schema_file(path: Path, schema: dict) -> str:
    title = schema.get("title")
    if isinstance(title, str) and title.strip():
        return title.strip()

    stem = path.stem.removesuffix("_schema")
    return "".join(part[:1].upper() + part[1:] for part in stem.split("_") if part)


def iter_component_schema_files() -> list[Path]:
    if not COMPONENT_SCHEMAS_DIR.exists():
        return []
    return [
        path
        for path in sorted(COMPONENT_SCHEMAS_DIR.glob("*.json"))
        if path.name not in _RESERVED_SCHEMA_FILES
    ]


def load_component_schema_map() -> dict[str, dict]:
    component_schemas: dict[str, dict] = {}
    for path in iter_component_schema_files():
        schema = json.loads(path.read_text(encoding="utf-8"))
        component_name = _component_name_from_schema_file(path, schema)
        schema_copy = deepcopy(schema)
        schema_copy.pop("$schema", None)
        schema_copy.pop("title", None)
        component_schemas[component_name] = schema_copy
    return component_schemas


def list_component_names() -> list[str]:
    return list(load_component_schema_map().keys())


def build_a2ui_message_schema_dict() -> dict:
    schema = deepcopy(_MESSAGE_SCHEMA_TEMPLATE)
    component_properties = schema["properties"]["surfaceUpdate"]["properties"]["components"]["items"]["properties"]["component"]["properties"]
    component_properties.update(load_component_schema_map())
    return schema


def build_a2ui_message_schema_text() -> str:
    return json.dumps(build_a2ui_message_schema_dict(), indent=2, ensure_ascii=False)
