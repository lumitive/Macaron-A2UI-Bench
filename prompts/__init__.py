"""Judge prompt templates for A2UI evaluation.

Split into L2 (task construction quality) and L3 (experience quality).
Each prompt is loaded from this package and formatted at evaluation time.
"""

from pathlib import Path

_DIR = Path(__file__).parent


def load_l2_judge_prompt() -> str:
    return (_DIR / "l2_judge.txt").read_text(encoding="utf-8")


def load_l3_judge_prompt() -> str:
    return (_DIR / "l3_judge.txt").read_text(encoding="utf-8")
