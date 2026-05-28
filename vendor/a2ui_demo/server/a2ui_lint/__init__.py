"""A2UI Lint — Validation engine for A2UI JSON messages.

Public API:
    validate(messages, levels=None, schema_path=None) → ValidationResult
    validate_raw(response, levels=None, schema_path=None) → (text_content, a2ui_messages|None, ValidationResult)
"""

from __future__ import annotations

import json
import logging

from .component_schema import ComponentSchema
from .context import ValidationContext, get_schema
from .diagnostics import Diagnostic, DiagnosticCode, Severity, ValidationResult
from .level1_structural import check_level1
from .level2_references import check_level2
from .level3_data import check_level3
from .level4_semantic import check_level4

__all__ = ["validate", "validate_raw", "ValidationResult", "Diagnostic", "DiagnosticCode", "Severity"]

logger = logging.getLogger(__name__)

SEPARATOR = "---a2ui_JSON---"

_LEVEL_CHECKERS = {
    1: check_level1,
    2: check_level2,
    3: check_level3,
    4: check_level4,
}


def validate(
    messages: list[dict],
    levels: set[int] | None = None,
    schema_path: str | None = None,
) -> ValidationResult:
    """Validate a list of parsed A2UI messages.

    Args:
        messages: Parsed A2UI message dicts.
        levels: Which validation levels to run (1-4). None means all.
        schema_path: Optional path to a custom JSON Schema file.
            If None, uses the bundled schema.json.

    Returns:
        ValidationResult with all diagnostics.
    """
    schema = ComponentSchema.from_file(schema_path) if schema_path else get_schema()
    ctx = ValidationContext(messages=messages, schema=schema)
    result = ValidationResult()
    run_levels = levels or {1, 2, 3, 4}
    for lvl in sorted(run_levels):
        checker = _LEVEL_CHECKERS.get(lvl)
        if checker:
            result.merge(checker(ctx))
    return result


def validate_raw(
    response: str,
    levels: set[int] | None = None,
    schema_path: str | None = None,
) -> tuple[str, list[dict] | None, ValidationResult]:
    """Extract A2UI JSON from a raw LLM response, clean it, parse it, and validate.

    This absorbs the logic from the old ``a2ui_validator.py``.

    Args:
        response: Raw LLM response string (text + separator + JSON).
        levels: Validation levels to run (1-4). None = all.
        schema_path: Optional path to a custom JSON Schema file.

    Returns:
        (text_content, a2ui_messages_or_None, ValidationResult)
    """
    result = ValidationResult()

    if SEPARATOR not in response:
        return response.strip(), None, result

    text_content, json_str = response.split(SEPARATOR, 1)
    text_content = text_content.strip()

    # Clean common LLM formatting artifacts
    json_str = json_str.strip()
    if json_str.startswith("```json"):
        json_str = json_str[len("```json"):]
    if json_str.startswith("```"):
        json_str = json_str[len("```"):]
    if json_str.endswith("```"):
        json_str = json_str[:-len("```")]
    json_str = json_str.strip()

    if not json_str:
        return text_content, None, result

    # Parse JSON
    try:
        parsed = json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse A2UI JSON: {e}")
        result.add(Diagnostic(
            Severity.ERROR,
            DiagnosticCode.STRUCT_INVALID_ACTION_KEY,
            f"JSON parse error: {e}",
            suggestion="Ensure the A2UI JSON is valid JSON.",
        ))
        return text_content, None, result

    # Normalize to list
    if isinstance(parsed, dict):
        parsed = [parsed]
    if not isinstance(parsed, list):
        logger.error(f"A2UI JSON is not a list or dict: {type(parsed)}")
        result.add(Diagnostic(
            Severity.ERROR,
            DiagnosticCode.STRUCT_WRONG_TYPE,
            f"A2UI payload must be a JSON array, got {type(parsed).__name__}",
        ))
        return text_content, None, result

    # Run validation
    validation = validate(parsed, levels=levels, schema_path=schema_path)
    result.merge(validation)

    logger.info(
        f"Parsed {len(parsed)} A2UI messages: "
        f"{len(result.errors)} errors, {len(result.warnings)} warnings"
    )

    # Return parsed messages even if there are errors (caller decides)
    return text_content, parsed, result
