"""Active runtime interceptor evaluating proposed agent actions against skill anti-patterns and AST gates."""

from __future__ import annotations

from typing import Any

from harness.services.skill_graph.models import (
    ActionGateResult,
    AntiPatternViolation,
    InvariantViolation,
    SkillCardDefinition,
)

from .ast_scanner import (
    extract_combined_text,
    scan_blocked_calls,
    scan_code_ast,
)
from .formatter import format_self_repair_observation
from .invariants import (
    check_rule15_credentials,
    check_rule30_powershell_glob,
    check_skill_invariants,
)
from .proposals import check_proposal_anti_patterns


class AntiPatternGuard:
    """Active runtime interceptor evaluating proposed agent actions against skill anti-patterns."""

    @classmethod
    def evaluate_action(
        cls,
        action_name: str,
        action_input: dict[str, Any],
        active_skills: list[str] | None = None,
        skill_lookup: Any = None,
    ) -> list[AntiPatternViolation]:
        """Authoritative action evaluator checking proposed tool calls and arguments."""
        violations: list[AntiPatternViolation] = []
        combined_text = extract_combined_text(action_name, action_input)
        system_guard_name = active_skills[0] if active_skills else "system_guard"

        # 1. AST syntax tree scanning for blocked calls (eval, exec, input, __import__)
        violations.extend(scan_blocked_calls(combined_text, skill_name=system_guard_name))

        # 2. Rule 15 Credential Exposure Guard
        violations.extend(check_rule15_credentials(combined_text, skill_name=system_guard_name))

        # 3. Rule 30 PowerShell Glob Non-Expansion Guard
        violations.extend(
            check_rule30_powershell_glob(
                action_name=action_name,
                action_input=action_input,
                combined_text=combined_text,
                skill_name=system_guard_name,
            )
        )

        # 4. Check declared anti-patterns and invariants for active skills
        if active_skills and skill_lookup:
            for skill_name in active_skills:
                skill = (
                    skill_lookup(skill_name)
                    if callable(skill_lookup)
                    else (
                        skill_lookup.get(skill_name)
                        if isinstance(skill_lookup, dict)
                        else None
                    )
                )
                if skill:
                    violations.extend(cls.check_proposal(skill, combined_text))
                    violations.extend(
                        cls.check_invariants(
                            skill=skill,
                            action_name=action_name,
                            action_input=action_input,
                            combined_text=combined_text,
                        )
                    )

        return violations

    @classmethod
    def evaluate_action_gate(
        cls,
        action_name: str,
        action_input: dict[str, Any],
        active_skills: list[str] | None = None,
        skill_lookup: Any = None,
    ) -> ActionGateResult:
        """Authoritative action gate evaluation returning a slotted ActionGateResult."""
        violations = cls.evaluate_action(
            action_name=action_name,
            action_input=action_input,
            active_skills=active_skills,
            skill_lookup=skill_lookup,
        )
        if not violations:
            return ActionGateResult(
                action_name=action_name,
                is_blocked=False,
                violations=(),
                observation={"status": "ok"},
            )
        obs = cls.format_self_repair_observation(violations)
        return ActionGateResult(
            action_name=action_name,
            is_blocked=True,
            violations=tuple(violations),
            observation=obs,
        )

    @classmethod
    def check_invariants(
        cls,
        skill: SkillCardDefinition,
        action_name: str,
        action_input: dict[str, Any],
        combined_text: str,
    ) -> list[InvariantViolation]:
        """Scan proposed action and input against declared mandatory invariants for a skill."""
        return check_skill_invariants(
            skill=skill,
            action_name=action_name,
            action_input=action_input,
            combined_text=combined_text,
        )

    @classmethod
    def _check_code_ast(
        cls, code_block: str, skill: SkillCardDefinition
    ) -> list[AntiPatternViolation]:
        """Run AST visitor on fenced python codeblock to catch blocked library calls."""
        return scan_code_ast(code_block, skill_name=skill.name)

    @classmethod
    def format_self_repair_observation(
        cls, violations: list[Any]
    ) -> dict[str, Any]:
        """Format violations into an actionable ReAct observation dictionary for in-flight self-repair."""
        return format_self_repair_observation(violations)

    @classmethod
    def check_proposal(
        cls,
        skill: SkillCardDefinition,
        proposed_action_or_plan: str,
    ) -> list[AntiPatternViolation]:
        """Scan proposed plan or tool arguments for symptoms of declared anti-patterns."""
        return check_proposal_anti_patterns(
            skill=skill,
            proposed_action_or_plan=proposed_action_or_plan,
        )


__all__ = ["AntiPatternGuard"]
