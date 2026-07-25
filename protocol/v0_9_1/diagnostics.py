"""Diagnostic models for A2UI v0.9.1 validation.

Duck-types with vendor 0.8 lint for ``evaluate_l1_scores``:
``.errors`` / ``.warnings`` / ``.is_valid`` and diagnostics with ``.code.value``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Severity(Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class DiagnosticCode(Enum):
    # Structural
    STRUCT_PROTOCOL_VERSION_MISMATCH = "STRUCT_PROTOCOL_VERSION_MISMATCH"
    STRUCT_LEGACY_0_8_SHAPE = "STRUCT_LEGACY_0_8_SHAPE"
    STRUCT_UNKNOWN_ACTION = "STRUCT_UNKNOWN_ACTION"
    STRUCT_MISSING_CATALOG_ID = "STRUCT_MISSING_CATALOG_ID"
    STRUCT_UNKNOWN_COMPONENT = "STRUCT_UNKNOWN_COMPONENT"
    STRUCT_MESSAGE_NOT_DICT = "STRUCT_MESSAGE_NOT_DICT"
    STRUCT_MISSING_REQUIRED = "STRUCT_MISSING_REQUIRED"
    STRUCT_WRONG_TYPE = "STRUCT_WRONG_TYPE"
    STRUCT_MULTIPLE_ACTION_KEYS = "STRUCT_MULTIPLE_ACTION_KEYS"

    # References
    REF_MISSING_ROOT = "REF_MISSING_ROOT"
    REF_SURFACE_ID_MISMATCH = "REF_SURFACE_ID_MISMATCH"
    REF_DUPLICATE_ID = "REF_DUPLICATE_ID"

    # Data / lint placeholders for prefix contract
    DATA_BINDING_INVALID = "DATA_BINDING_INVALID"
    DATA_TYPE_MISMATCH = "DATA_TYPE_MISMATCH"
    LINT_MESSAGE_ORDER = "LINT_MESSAGE_ORDER"


@dataclass(frozen=True)
class Diagnostic:
    severity: Severity
    code: DiagnosticCode
    message: str
    path: str = ""
    suggestion: str = ""


@dataclass
class ValidationResult:
    diagnostics: list[Diagnostic] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not any(d.severity == Severity.ERROR for d in self.diagnostics)

    @property
    def errors(self) -> list[Diagnostic]:
        return [d for d in self.diagnostics if d.severity == Severity.ERROR]

    @property
    def warnings(self) -> list[Diagnostic]:
        return [d for d in self.diagnostics if d.severity == Severity.WARNING]

    def add(self, diag: Diagnostic) -> None:
        self.diagnostics.append(diag)

    def merge(self, other: ValidationResult) -> None:
        self.diagnostics.extend(other.diagnostics)
