"""Slotted domain models, protocols, and dangerous shell patterns for Critic Loop (Rule 12 & Rule 43)."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from harness.kernel.context import ServiceKey

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

# Dangerous shell patterns for safety gatekeeping
_DANGEROUS_PATTERNS = [
    (r"\brm\s+-[rfRF]{1,4}\s+[/~]", "Recursive root or home directory removal"),
    (r"\brm\s+-[rfRF]{1,4}\s+\*", "Wildcard file deletion"),
    (r"\bdel\s+/[fFqQsS]{1,4}\s+[cC]:\\", "System drive deletion"),
    (r"\bformat\s+[a-zA-Z]:", "Disk format operation"),
    (r"\bgit\s+reset\s+--hard\b", "Destructive hard git reset (discards all uncommitted work)"),
    (r"\bgit\s+clean\s+-[fFxd]{1,4}\b", "Forced git directory purge"),
    (r"\bgit\s+push\s+.*--force\b", "Forced git push (overwrites remote commit history)"),
    (r"\bdrop\s+(database|schema|table)\b", "Database object destruction"),
    (r"\bdd\s+if=.*of=/dev/[a-z]+", "Raw disk block overwrite"),
    (r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:", "Fork bomb definition"),
    (r"\b(shutdown|reboot|init\s+0|halt)\b", "System termination command"),
]


@dataclass(slots=True, frozen=True)
class RubricCriterionScore:
    """Slotted and frozen individual rubric criterion score (Rule 12 & Rule 43)."""

    criterion: str
    score: float
    feedback: str


@dataclass(slots=True, frozen=True)
class RubricScoreReport:
    """Slotted and frozen overall rubric evaluation report (Rule 12 & Rule 43)."""

    score: float
    overall_score: float
    criteria_count: int
    breakdown: list[RubricCriterionScore] = field(default_factory=list)
    passed: bool = False


@dataclass(slots=True, frozen=True)
class CommandSafetyReport:
    """Slotted and frozen command safety screening report (Rule 12 & Rule 43)."""

    command: str
    is_safe: bool
    risk_level: str
    violations_count: int
    violations: list[str] = field(default_factory=list)
    status: str = "ok"


@dataclass(slots=True, frozen=True)
class DebateRound:
    """Slotted and frozen dialectical debate round (Rule 12 & Rule 43)."""

    round_number: int
    proposer_claim: str
    challenger_counter: str


@runtime_checkable
class CriticEvaluationService(Protocol):
    """Authoritative protocol for critic, safety evaluation, and dialectical debate."""

    def evaluate_rubric(self, content: str, rubric: list[str]) -> dict[str, Any]:
        """Score content against a criteria checklist with breakdown."""
        ...

    def evaluate(self, content: str, rubric: list[str]) -> dict[str, Any]:
        """Score content against a criteria checklist (unified evaluation seam)."""
        ...

    def check_command_safety(self, command: str) -> dict[str, Any]:
        """Scan shell commands for dangerous or irreversible operations."""
        ...

    def evaluate_code_ast(self, code: str, language: str = "python") -> dict[str, Any]:
        """Statically inspect syntax, AST complexity, and anti-patterns."""
        ...

    def review_plan_feasibility(self, goal: str, steps: list[str]) -> dict[str, Any]:
        """Evaluate plan steps for verification steps, risks, and mitigations."""
        ...

    def conduct_dialectical_debate(
        self,
        topic: str,
        pro_arguments: list[str],
        con_arguments: list[str],
    ) -> dict[str, Any]:
        """Orchestrate dialectical argument rounds between Proposer and Challenger."""
        ...

    def synthesize_debate_verdict(self, debate_summary: dict[str, Any]) -> dict[str, Any]:
        """Synthesize an impartial arbiter decision based on debate rounds."""
        ...

    async def refine(
        self,
        task: str,
        draft: str,
        *,
        rubric: list[str] | None = None,
        max_iterations: int = 3,
        threshold: float = 0.85,
        llm_service: Any | None = None,
    ) -> dict[str, Any]:
        """Run iterative multi-turn critique and refinement until threshold is achieved."""
        ...


CRITIC_EVALUATION_SERVICE_KEY = ServiceKey[CriticEvaluationService]("service.critic_evaluation")
CRITIC_LOOP_KEY = CRITIC_EVALUATION_SERVICE_KEY  # Backward-compatible alias

__all__ = [
    "CRITIC_EVALUATION_SERVICE_KEY",
    "CRITIC_LOOP_KEY",
    "CommandSafetyReport",
    "CriticEvaluationService",
    "DebateRound",
    "RubricCriterionScore",
    "RubricScoreReport",
    "_DANGEROUS_PATTERNS",
]
