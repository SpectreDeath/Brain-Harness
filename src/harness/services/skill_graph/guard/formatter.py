"""Observation formatting for agent in-flight self-repair."""

from __future__ import annotations

from typing import Any

from harness.services.skill_graph.models import InvariantViolation


def format_self_repair_observation(violations: list[Any]) -> dict[str, Any]:
    """Format violations into an actionable ReAct observation dictionary for in-flight self-repair."""
    if not violations:
        return {"status": "ok"}
    v = violations[0]
    if isinstance(v, InvariantViolation) or hasattr(v, "is_blocking"):
        return {
            "status": "error",
            "invariant_violation": f"{getattr(v, 'rule', '')} ({getattr(v, 'skill_name', '')})",
            "rule": getattr(v, "rule", ""),
            "is_blocking": getattr(v, "is_blocking", True),
            "prescribed_remedy": getattr(v, "remedy", "Adhere strictly to the skill invariant rule"),
            "matched_phrase": getattr(v, "matched_phrase", ""),
            "corrective_action_required": True,
        }
    return {
        "status": "error",
        "anti_pattern_violation": f"{v.anti_pattern} ({v.skill_name})",
        "symptom": v.symptom,
        "prescribed_remedy": v.remedy,
        "matched_phrase": v.matched_phrase,
        "corrective_action_required": True,
    }
