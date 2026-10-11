"""Plan feasibility, risk evaluation, and mitigation review."""

from __future__ import annotations

import sys
from typing import Any

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


def review_plan_feasibility(goal: str, steps: list[str]) -> dict[str, Any]:
    """Evaluate plan steps for verification steps, risks, and mitigations."""
    if not steps:
        return {
            "status": "ok",
            "goal": goal,
            "score": 0,
            "feasible": False,
            "risks": ["Plan has no action steps defined."],
            "recommendations": ["Add sequential action steps to achieve the stated goal."],
        }

    risks: list[str] = []
    recommendations: list[str] = []
    has_verification = False
    has_backup_or_test = False

    for step in steps:
        s_lower = step.lower()
        if any(w in s_lower for w in ("verify", "test", "check", "validate", "assert", "inspect")):
            has_verification = True
        if any(w in s_lower for w in ("backup", "rollback", "fallback", "dry-run", "dry run")):
            has_backup_or_test = True

    if not has_verification:
        risks.append("No explicit verification, testing, or validation step in plan.")
        recommendations.append("Append an automated test or verification step at the end of the plan.")

    if len(steps) < 2:
        recommendations.append("Break the single monolithic step into atomic, testable sub-steps.")

    if len(steps) > 12:
        recommendations.append("Plan exceeds 12 steps; consider decomposing into sub-phases.")

    score = 100
    if not has_verification:
        score -= 25
    if not has_backup_or_test and any(
        "delete" in s.lower() or "drop" in s.lower() or "replace" in s.lower() for s in steps
    ):
        score -= 20
        risks.append("Destructive modifications planned without explicit backup/rollback precaution.")

    return {
        "status": "ok",
        "goal": goal,
        "total_steps": len(steps),
        "score": max(0, score),
        "feasible": score >= 50,
        "has_verification_step": has_verification,
        "risks": risks,
        "recommendations": recommendations,
    }


__all__ = ["review_plan_feasibility"]
