"""Active invariant and architectural boundary checkers for skills and actions."""

from __future__ import annotations

from typing import Any

from harness.services.skill_graph.models import (
    InvariantViolation,
    SkillCardDefinition,
)

from .rules import (
    check_inv_artifact_metadata,
    check_inv_credentials,
    check_inv_knowledge_vault,
    check_inv_powershell_glob,
    check_inv_scratch_execution,
    check_inv_utf8_streams,
    check_rule15_credentials,
    check_rule30_powershell_glob,
)


def check_skill_invariants(
    skill: SkillCardDefinition,
    action_name: str,
    action_input: dict[str, Any],
    combined_text: str,
) -> list[InvariantViolation]:
    """Scan proposed action and input against declared mandatory invariants for a skill."""
    violations: list[InvariantViolation] = []
    text_lower = combined_text.lower()

    for inv in getattr(skill, "invariants", []) or []:
        inv_rule = getattr(inv, "rule", "") or ""
        if not inv_rule:
            continue
        inv_lower = inv_rule.lower()
        is_blocking = getattr(inv, "is_blocking", True)

        v = (
            check_inv_artifact_metadata(inv_rule, inv_lower, action_name, action_input, text_lower, skill.name, is_blocking)
            or check_inv_scratch_execution(inv_rule, inv_lower, action_name, action_input, combined_text, skill.name, is_blocking)
            or check_inv_powershell_glob(inv_rule, inv_lower, action_name, action_input, combined_text, skill.name, is_blocking)
            or check_inv_credentials(inv_rule, inv_lower, action_name, action_input, combined_text, skill.name, is_blocking)
            or check_inv_utf8_streams(inv_rule, inv_lower, action_name, action_input, combined_text, skill.name, is_blocking)
            or check_inv_knowledge_vault(inv_rule, inv_lower, action_name, action_input, skill.name, is_blocking)
        )
        if v is not None:
            violations.append(v)

    return violations


__all__ = [
    "check_rule15_credentials",
    "check_rule30_powershell_glob",
    "check_skill_invariants",
]
