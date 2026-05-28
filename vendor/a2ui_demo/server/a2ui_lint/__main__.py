"""CLI entry point: python -m server.a2ui_lint input.json"""

from __future__ import annotations

import argparse
import json
import sys

from . import validate, validate_raw
from .formatters import format_for_cli, format_for_llm, to_json


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="a2ui_lint",
        description="Validate A2UI JSON messages.",
    )
    parser.add_argument(
        "input",
        help="Path to JSON file, or '-' to read from stdin.",
    )
    parser.add_argument(
        "--levels",
        type=str,
        default=None,
        help="Comma-separated validation levels to run (e.g. '1,2'). Default: all.",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json", "llm"],
        default="text",
        help="Output format. Default: text (colored terminal).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors (exit code 1 if any warnings).",
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Input is a raw LLM response (contains ---a2ui_JSON--- separator).",
    )
    args = parser.parse_args()

    # Parse levels
    levels = None
    if args.levels:
        try:
            levels = {int(x.strip()) for x in args.levels.split(",")}
        except ValueError:
            print("Error: --levels must be comma-separated integers (1-4)", file=sys.stderr)
            return 2

    # Read input
    try:
        if args.input == "-":
            content = sys.stdin.read()
        else:
            with open(args.input) as f:
                content = f.read()
    except (FileNotFoundError, OSError) as e:
        print(f"Error reading input: {e}", file=sys.stderr)
        return 2

    # Validate
    if args.raw:
        text, messages, result = validate_raw(content, levels=levels)
        if text:
            print(f"Text content: {text[:200]}{'...' if len(text) > 200 else ''}\n",
                  file=sys.stderr)
    else:
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as e:
            print(f"JSON parse error: {e}", file=sys.stderr)
            return 2
        if isinstance(parsed, dict):
            parsed = [parsed]
        if not isinstance(parsed, list):
            print(f"Expected JSON array, got {type(parsed).__name__}", file=sys.stderr)
            return 2
        result = validate(parsed, levels=levels)

    # Output
    if args.format == "json":
        print(to_json(result))
    elif args.format == "llm":
        print(format_for_llm(result))
    else:
        print(format_for_cli(result))

    # Exit code
    if result.errors:
        return 1
    if args.strict and result.warnings:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
