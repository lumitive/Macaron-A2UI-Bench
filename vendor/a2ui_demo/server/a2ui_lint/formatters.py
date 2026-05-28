"""Output formatters for validation results."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .diagnostics import ValidationResult

from .diagnostics import Severity


# ---------------------------------------------------------------------------
# CLI (ANSI colored terminal output)
# ---------------------------------------------------------------------------

_COLORS = {
    Severity.ERROR: "\033[91m",   # red
    Severity.WARNING: "\033[93m", # yellow
    Severity.INFO: "\033[96m",    # cyan
}
_RESET = "\033[0m"
_BOLD = "\033[1m"


def format_for_cli(result: "ValidationResult") -> str:
    if not result.diagnostics:
        return f"{_BOLD}✓ Validation passed — no issues found.{_RESET}"

    lines: list[str] = []
    grouped: dict[Severity, list] = {s: [] for s in Severity}
    for d in result.diagnostics:
        grouped[d.severity].append(d)

    for sev in (Severity.ERROR, Severity.WARNING, Severity.INFO):
        items = grouped[sev]
        if not items:
            continue
        color = _COLORS[sev]
        label = sev.value.upper()
        lines.append(f"\n{_BOLD}{color}━━━ {label}S ({len(items)}) ━━━{_RESET}")
        for i, d in enumerate(items, 1):
            lines.append(f"  {color}{i}. [{d.code.value}]{_RESET} {d.message}")
            if d.path:
                lines.append(f"     at: {d.path}")
            if d.suggestion:
                lines.append(f"     → {d.suggestion}")

    summary_parts = []
    if result.errors:
        summary_parts.append(f"{_COLORS[Severity.ERROR]}{len(result.errors)} error(s){_RESET}")
    if result.warnings:
        summary_parts.append(f"{_COLORS[Severity.WARNING]}{len(result.warnings)} warning(s){_RESET}")
    if result.infos:
        summary_parts.append(f"{_COLORS[Severity.INFO]}{len(result.infos)} info(s){_RESET}")

    lines.append(f"\n{_BOLD}Summary: {', '.join(summary_parts)}{_RESET}")
    status = "FAIL" if not result.is_valid else "PASS (warnings only)"
    status_color = _COLORS[Severity.ERROR] if not result.is_valid else _COLORS[Severity.WARNING]
    lines.append(f"{status_color}{_BOLD}Result: {status}{_RESET}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# LLM retry prompt (structured plaintext)
# ---------------------------------------------------------------------------

def format_for_llm(result: "ValidationResult") -> str:
    """Format validation errors as a concise, actionable prompt for LLM retry."""
    if not result.diagnostics:
        return ""

    lines = [
        "Your A2UI JSON has validation errors. Fix ALL of the following issues:\n"
    ]

    for i, d in enumerate(result.diagnostics, 1):
        severity = d.severity.value.upper()
        lines.append(f"{i}. [{severity}] {d.code.value}: {d.message}")
        if d.path:
            lines.append(f"   Location: {d.path}")
        if d.suggestion:
            lines.append(f"   Fix: {d.suggestion}")

    lines.append(
        "\nRules reminder:"
        "\n- Each message needs exactly ONE action key (beginRendering/surfaceUpdate/dataModelUpdate/deleteSurface)"
        "\n- All component IDs referenced as children must exist in surfaceUpdate.components"
        "\n- Inside template children, use RELATIVE paths (no leading /) like \"title\", \"name\""
        "\n- Every data entry needs a 'key' and exactly one value property (valueString/valueNumber/valueBoolean/valueMap)"
        "\n\nRegenerate the COMPLETE A2UI JSON with all fixes applied."
    )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# JSON serialization
# ---------------------------------------------------------------------------

def to_json(result: "ValidationResult", indent: int = 2) -> str:
    return json.dumps(result.to_dict(), indent=indent, ensure_ascii=False)
