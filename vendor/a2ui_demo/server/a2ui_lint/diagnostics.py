"""Diagnostic data models for A2UI validation."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Severity(Enum):
    """Severity level for a diagnostic."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class DiagnosticCode(Enum):
    """Diagnostic codes grouped by category prefix."""

    # --- Level 1: Structural ---
    STRUCT_INVALID_ACTION_KEY = "STRUCT_INVALID_ACTION_KEY"
    STRUCT_MULTIPLE_ACTION_KEYS = "STRUCT_MULTIPLE_ACTION_KEYS"
    STRUCT_MISSING_REQUIRED = "STRUCT_MISSING_REQUIRED"
    STRUCT_WRONG_TYPE = "STRUCT_WRONG_TYPE"
    STRUCT_MULTIPLE_COMPONENT_TYPES = "STRUCT_MULTIPLE_COMPONENT_TYPES"
    STRUCT_UNKNOWN_COMPONENT_TYPE = "STRUCT_UNKNOWN_COMPONENT_TYPE"
    STRUCT_INVALID_ENUM = "STRUCT_INVALID_ENUM"
    STRUCT_MULTIPLE_VALUE_TYPES = "STRUCT_MULTIPLE_VALUE_TYPES"
    STRUCT_NO_VALUE_TYPE = "STRUCT_NO_VALUE_TYPE"
    STRUCT_MESSAGE_NOT_DICT = "STRUCT_MESSAGE_NOT_DICT"
    STRUCT_MISSING_COMPONENT_WRAPPER = "STRUCT_MISSING_COMPONENT_WRAPPER"

    # --- Level 2: References ---
    REF_MISSING_COMPONENT = "REF_MISSING_COMPONENT"
    REF_MISSING_ROOT = "REF_MISSING_ROOT"
    REF_DUPLICATE_ID = "REF_DUPLICATE_ID"
    REF_ORPHAN_COMPONENT = "REF_ORPHAN_COMPONENT"
    REF_CYCLE = "REF_CYCLE"
    REF_SURFACE_ID_MISMATCH = "REF_SURFACE_ID_MISMATCH"

    # --- Level 3: Data model ---
    DATA_PATH_NOT_FOUND = "DATA_PATH_NOT_FOUND"
    DATA_BINDING_INVALID = "DATA_BINDING_INVALID"
    DATA_ABSOLUTE_PATH_IN_TEMPLATE = "DATA_ABSOLUTE_PATH_IN_TEMPLATE"
    DATA_TYPE_MISMATCH = "DATA_TYPE_MISMATCH"

    # --- Level 4: Semantic / lint ---
    LINT_MISSING_MESSAGE_TYPE = "LINT_MISSING_MESSAGE_TYPE"
    LINT_MESSAGE_ORDER = "LINT_MESSAGE_ORDER"
    LINT_WEIGHT_OUTSIDE_FLEX = "LINT_WEIGHT_OUTSIDE_FLEX"
    LINT_DEEP_NESTING = "LINT_DEEP_NESTING"
    LINT_EMPTY_CHILDREN = "LINT_EMPTY_CHILDREN"
    LINT_DUPLICATE_BEGIN_RENDERING = "LINT_DUPLICATE_BEGIN_RENDERING"
    LINT_PROMPT_WITHOUT_INPUT = "LINT_PROMPT_WITHOUT_INPUT"
    LINT_PASSWORD_KEYPAD_MISUSE = "LINT_PASSWORD_KEYPAD_MISUSE"
    LINT_DATETIME_LITERAL_ONLY = "LINT_DATETIME_LITERAL_ONLY"
    LINT_MODAL_TRIGGER_INVALID = "LINT_MODAL_TRIGGER_INVALID"
    LINT_SLIDER_LABEL_OVERFLOW_RISK = "LINT_SLIDER_LABEL_OVERFLOW_RISK"
    LINT_SELECTION_BINDING_SCALAR = "LINT_SELECTION_BINDING_SCALAR"
    LINT_SELECTION_SINGLE_ITEM_PROXY = "LINT_SELECTION_SINGLE_ITEM_PROXY"


@dataclass(frozen=True)
class Diagnostic:
    """A single validation diagnostic."""

    severity: Severity
    code: DiagnosticCode
    message: str
    path: str = ""           # JSON-pointer style, e.g. "/messages/0/surfaceUpdate/components/2"
    suggestion: str = ""     # Actionable fix hint

    def to_dict(self) -> dict:
        d: dict = {
            "severity": self.severity.value,
            "code": self.code.value,
            "message": self.message,
        }
        if self.path:
            d["path"] = self.path
        if self.suggestion:
            d["suggestion"] = self.suggestion
        return d


@dataclass
class ValidationResult:
    """Aggregated result of a validation run."""

    diagnostics: list[Diagnostic] = field(default_factory=list)

    # --- convenience properties ---

    @property
    def is_valid(self) -> bool:
        return not any(d.severity == Severity.ERROR for d in self.diagnostics)

    @property
    def errors(self) -> list[Diagnostic]:
        return [d for d in self.diagnostics if d.severity == Severity.ERROR]

    @property
    def warnings(self) -> list[Diagnostic]:
        return [d for d in self.diagnostics if d.severity == Severity.WARNING]

    @property
    def infos(self) -> list[Diagnostic]:
        return [d for d in self.diagnostics if d.severity == Severity.INFO]

    # --- output helpers (delegated to formatters) ---

    def format_for_llm(self) -> str:
        from .formatters import format_for_llm
        return format_for_llm(self)

    def format_for_cli(self) -> str:
        from .formatters import format_for_cli
        return format_for_cli(self)

    def to_dict(self) -> dict:
        return {
            "is_valid": self.is_valid,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "diagnostics": [d.to_dict() for d in self.diagnostics],
        }

    def add(self, diag: Diagnostic) -> None:
        self.diagnostics.append(diag)

    def merge(self, other: ValidationResult) -> None:
        self.diagnostics.extend(other.diagnostics)
