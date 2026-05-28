"""Parse JSON Schema to extract component metadata for validation."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ComponentSchema:
    """Component metadata extracted from an A2UI JSON Schema."""

    known_component_types: set[str] = field(default_factory=set)
    component_required_fields: dict[str, list[str]] = field(default_factory=dict)
    component_enums: dict[str, dict[str, set[str]]] = field(default_factory=dict)
    container_child_fields: dict[str, list[str]] = field(default_factory=dict)
    container_children_types: set[str] = field(default_factory=set)
    icon_names: set[str] = field(default_factory=set)
    value_type_keys: set[str] = field(default_factory=set)
    type_hints: dict[str, str] = field(default_factory=dict)
    raw_schema: dict = field(default_factory=dict)
    _jsonschema_validator: object | None = field(default=None, init=False, repr=False)

    @classmethod
    def from_file(cls, path: str | Path) -> ComponentSchema:
        with open(path, "r", encoding="utf-8") as f:
            schema = json.load(f)
        return cls.from_dict(schema)

    @classmethod
    def from_dict(cls, schema: dict) -> ComponentSchema:
        self = cls()
        self.raw_schema = schema
        self._parse(schema)
        return self

    def get_jsonschema_validator(self) -> object | None:
        """Lazily build a JSON Schema validator for supplemental type checks."""
        if self._jsonschema_validator is not None:
            return self._jsonschema_validator
        if not self.raw_schema:
            return None
        try:
            from jsonschema import Draft7Validator
        except Exception:
            return None
        self._jsonschema_validator = Draft7Validator(self.raw_schema)
        return self._jsonschema_validator

    # ------------------------------------------------------------------
    # internal parsing
    # ------------------------------------------------------------------

    def _parse(self, schema: dict) -> None:
        # Navigate to the component type definitions
        component_defs = (
            schema
            .get("properties", {})
            .get("surfaceUpdate", {})
            .get("properties", {})
            .get("components", {})
            .get("items", {})
            .get("properties", {})
            .get("component", {})
            .get("properties", {})
        )

        for comp_type, comp_schema in component_defs.items():
            self.known_component_types.add(comp_type)

            # Required fields
            required = comp_schema.get("required", [])
            if required:
                self.component_required_fields[comp_type] = list(required)

            # Properties
            props = comp_schema.get("properties", {})

            # Enum values for direct string properties
            enums: dict[str, set[str]] = {}
            for prop_name, prop_schema in props.items():
                if prop_schema.get("type") == "string" and "enum" in prop_schema:
                    enums[prop_name] = set(prop_schema["enum"])
            if enums:
                self.component_enums[comp_type] = enums

            # Container detection: single-child fields (type: "string" with "child" in name)
            child_fields: list[str] = []
            for prop_name, prop_schema in props.items():
                if (
                    prop_schema.get("type") == "string"
                    and "child" in prop_name.lower()
                ):
                    child_fields.append(prop_name)
            if child_fields:
                self.container_child_fields[comp_type] = child_fields

            # Multi-child container: has "children" with explicitList sub-property
            children_schema = props.get("children", {})
            if isinstance(children_schema, dict):
                children_props = children_schema.get("properties", {})
                if "explicitList" in children_props:
                    self.container_children_types.add(comp_type)

        # Icon names: Icon.name.properties.literalString.enum
        icon_schema = (
            component_defs
            .get("Icon", {})
            .get("properties", {})
            .get("name", {})
            .get("properties", {})
            .get("literalString", {})
        )
        if "enum" in icon_schema:
            self.icon_names = set(icon_schema["enum"])

        # Value type keys from dataModelUpdate.contents.items.properties
        dmu_content_props = (
            schema
            .get("properties", {})
            .get("dataModelUpdate", {})
            .get("properties", {})
            .get("contents", {})
            .get("items", {})
            .get("properties", {})
        )
        for key in dmu_content_props:
            if key.startswith("value"):
                self.value_type_keys.add(key)

        # Derive type hints: component type → expected data value type
        self._derive_type_hints(component_defs)

    def _derive_type_hints(self, component_defs: dict) -> None:
        """Infer type hints from component value/text field schemas.

        If a component's primary value field (text, value) only has
        literalString+path → valueString, literalNumber+path → valueNumber,
        literalBoolean+path → valueBoolean.
        """
        literal_to_value = {
            "literalString": "valueString",
            "literalNumber": "valueNumber",
            "literalBoolean": "valueBoolean",
        }

        for comp_type, comp_schema in component_defs.items():
            props = comp_schema.get("properties", {})
            # Check "text" field first, then "value" field
            for field_name in ("text", "value"):
                field_schema = props.get(field_name)
                if not isinstance(field_schema, dict):
                    continue
                field_props = field_schema.get("properties", {})
                if not field_props:
                    continue
                # Find which literal* key is present (excluding "path")
                literal_keys = [
                    k for k in field_props
                    if k in literal_to_value
                ]
                if len(literal_keys) == 1:
                    self.type_hints[comp_type] = literal_to_value[literal_keys[0]]
                    break  # found primary field, stop
