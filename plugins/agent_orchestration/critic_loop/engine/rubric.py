"""Rubric criteria checklist evaluation and score breakdown."""

from __future__ import annotations

import re
import sys
from typing import Any

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


def evaluate_rubric(content: str, rubric: list[str]) -> dict[str, Any]:
    """Score content against a criteria checklist with breakdown."""
    scores: list[dict[str, Any]] = []
    total_score = 0.0

    for item in rubric:
        item_lower = item.lower()
        score = 0.5
        reasons: list[str] = []

        if "type" in item_lower or "typing" in item_lower:
            has_types = bool(re.search(r":\s*[a-zA-Z0-9_|\[\]]+\b|->\s*[a-zA-Z0-9_|\[\]]+", content))
            score = 1.0 if has_types else 0.3
            reasons.append("Type annotations verified" if has_types else "Missing explicit type annotations")
        elif "docstring" in item_lower or "documentation" in item_lower or "comment" in item_lower:
            has_docs = '"""' in content or "'''" in content or "#" in content
            score = 1.0 if has_docs else 0.4
            reasons.append("Docstrings present" if has_docs else "Missing docstrings / comments")
        elif "error" in item_lower or "exception" in item_lower or "try" in item_lower:
            has_err = "try:" in content or "except" in content or "raise" in content
            score = 1.0 if has_err else 0.4
            reasons.append("Error handling verified" if has_err else "No exception handling detected")
        elif "clean" in item_lower or "style" in item_lower:
            lines = content.splitlines()
            long_lines = sum(1 for ln in lines if len(ln) > 120)
            score = max(0.2, 1.0 - (long_lines * 0.1))
            reasons.append(
                f"Line length acceptable ({long_lines} long lines)"
                if long_lines == 0
                else f"{long_lines} lines exceed 120 chars"
            )
        else:
            tokens = [t for t in re.findall(r"\w+", item_lower) if len(t) > 3]
            matches = sum(1 for t in tokens if t in content.lower())
            ratio = matches / len(tokens) if tokens else 0.5
            score = min(1.0, 0.4 + (ratio * 0.6))
            reasons.append(f"Keyword alignment: {int(ratio * 100)}%")

        scores.append({
            "criterion": item,
            "score": round(score, 2),
            "feedback": "; ".join(reasons),
        })
        total_score += score

    overall = total_score / len(rubric) if rubric else 1.0
    return {
        "score": round(overall, 2),
        "overall_score": round(overall, 2),
        "criteria_count": len(rubric),
        "breakdown": scores,
        "passed": overall >= 0.80,
    }


__all__ = ["evaluate_rubric"]
