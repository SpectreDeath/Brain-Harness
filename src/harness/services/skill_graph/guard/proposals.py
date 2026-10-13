"""Negation-aware proposal and plan scanner for declared skill anti-patterns."""

from __future__ import annotations

import re

from harness.services.skill_graph.models import (
    AntiPatternViolation,
    SkillCardDefinition,
)

from .ast_scanner import extract_code_blocks, scan_code_ast

NEGATION_MARKERS: tuple[str, ...] = (
    "avoid",
    "do not",
    "don't",
    "prevent",
    "never",
    "without",
)


def check_proposal_anti_patterns(
    skill: SkillCardDefinition,
    proposed_action_or_plan: str,
) -> list[AntiPatternViolation]:
    """Scan proposed plan or tool arguments for symptoms of declared anti-patterns."""
    violations: list[AntiPatternViolation] = []
    text_lower = proposed_action_or_plan.lower()

    # AST analysis on fenced code blocks
    code_blocks = extract_code_blocks(proposed_action_or_plan)
    for block in code_blocks:
        violations.extend(scan_code_ast(block, skill_name=skill.name))

    for ap in getattr(skill, "anti_patterns", []) or []:
        ap_name_lower = ap.name.lower()
        ap_tokens = [
            tok.lower() for tok in re.findall(r"\w+", ap.name) if len(tok) > 3
        ]

        if ap_name_lower in text_lower:
            match_idx = text_lower.find(ap_name_lower)
            window = text_lower[max(0, match_idx - 50) : match_idx]
            if not any(marker in window for marker in NEGATION_MARKERS):
                violations.append(
                    AntiPatternViolation(
                        skill_name=skill.name,
                        anti_pattern=ap.name,
                        symptom=ap.symptom,
                        remedy=ap.remedy,
                        matched_phrase=ap.name,
                    )
                )
        elif ap_tokens and all(t in text_lower for t in ap_tokens):
            min_idx = min(
                text_lower.find(t) for t in ap_tokens if text_lower.find(t) != -1
            )
            window = text_lower[max(0, min_idx - 50) : min_idx]
            if not any(marker in window for marker in NEGATION_MARKERS):
                violations.append(
                    AntiPatternViolation(
                        skill_name=skill.name,
                        anti_pattern=ap.name,
                        symptom=ap.symptom,
                        remedy=ap.remedy,
                        matched_phrase=" ".join(ap_tokens),
                    )
                )

    return violations
