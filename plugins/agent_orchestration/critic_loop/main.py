"""Critic Evaluation & Safety Gatekeeper Plugin for Brain Harness.

Provides an authoritative, typed evaluation seam unifying:
1. Rubric scoring and heuristic criteria assessment
2. Destructive shell command screening
3. AST static code analysis and anti-pattern detection
4. Plan feasibility and risk mitigation review
5. Dialectical multi-agent debate and arbiter verdict synthesis
6. Autonomous generate-critique-revise loops
"""

from __future__ import annotations

import sys
import types
from pathlib import Path
from typing import Any

import structlog

# Ensure Harness core src is on sys.path for isolated subprocesses
_HARNESS_SRC = Path(__file__).resolve().parents[3] / "src"
if _HARNESS_SRC.exists() and str(_HARNESS_SRC) not in sys.path:
    sys.path.insert(0, str(_HARNESS_SRC))

if __name__ not in sys.modules:
    sys.modules[__name__] = sys.modules.get("__main__") or types.ModuleType(__name__)

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from plugins.agent_orchestration.critic_loop.engine import (
    CRITIC_EVALUATION_SERVICE_KEY,
    CRITIC_LOOP_KEY,
    CommandSafetyReport,
    CriticEvaluationService,
    CriticEvaluationServiceImpl,
    CriticLoopService,
    DebateRound,
    RubricCriterionScore,
    RubricScoreReport,
    _DANGEROUS_PATTERNS,
    _EVAL_INSTANCE,
    check_command_safety,
    conduct_dialectical_debate,
    evaluate_code_ast,
    evaluate_rubric,
    review_plan_feasibility,
    synthesize_debate_verdict,
)

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

logger = structlog.get_logger(__name__)


# Top-level tool entrypoints
def evaluate(content: str, rubric: list[str]) -> dict[str, Any]:
    """Unified evaluation entrypoint delegating to evaluate_rubric."""
    return _EVAL_INSTANCE.evaluate(content, rubric)


async def run_critic_loop(
    task: str,
    draft: str,
    *,
    rubric: list[str] | None = None,
    max_iterations: int = 3,
    threshold: float = 0.85,
    llm_service: Any | None = None,
) -> dict[str, Any]:
    """Run iterative multi-turn critique and refinement until threshold is achieved."""
    return await _EVAL_INSTANCE.refine(
        task=task,
        draft=draft,
        rubric=rubric,
        max_iterations=max_iterations,
        threshold=threshold,
        llm_service=llm_service,
    )


def critic_check_safety(command: str) -> dict[str, Any]:
    """Scan shell commands for dangerous or irreversible operations."""
    return _EVAL_INSTANCE.check_command_safety(command)


def critic_evaluate_code(code: str, language: str = "python") -> dict[str, Any]:
    """Statically inspect syntax, AST complexity, and anti-patterns."""
    return _EVAL_INSTANCE.evaluate_code_ast(code, language)


def critic_review_plan(goal: str, steps: list[str]) -> dict[str, Any]:
    """Evaluate plan steps for verification steps, risks, and mitigations."""
    return _EVAL_INSTANCE.review_plan_feasibility(goal, steps)


class CriticLoopPlugin(HarnessPlugin):
    """Authoritative plugin providing critic evaluation, safety gating, and dialectical debate."""

    @property
    def name(self) -> str:
        return "plugin.critic_loop"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return (
            "Authoritative critic, rubric evaluation, destructive command safety gate, "
            "and dialectical debate arbiter."
        )

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [CRITIC_EVALUATION_SERVICE_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, ctx: ServiceContext) -> None:
        ctx.provide(CRITIC_EVALUATION_SERVICE_KEY, _EVAL_INSTANCE, provider=self.name)
        logger.info("CriticEvaluationService provided", plugin=self.name)

    async def enable(self, context: ServiceContext) -> None:
        await self.on_load(context)

    async def on_disable(self) -> None:
        pass

    async def disable(self, context: Any = None) -> None:
        await self.on_disable()


plugin = CriticLoopPlugin()

__all__ = [
    "CRITIC_EVALUATION_SERVICE_KEY",
    "CRITIC_LOOP_KEY",
    "CommandSafetyReport",
    "CriticEvaluationService",
    "CriticEvaluationServiceImpl",
    "CriticLoopPlugin",
    "CriticLoopService",
    "DebateRound",
    "RubricCriterionScore",
    "RubricScoreReport",
    "_DANGEROUS_PATTERNS",
    "_EVAL_INSTANCE",
    "check_command_safety",
    "conduct_dialectical_debate",
    "critic_check_safety",
    "critic_evaluate_code",
    "critic_review_plan",
    "evaluate",
    "evaluate_code_ast",
    "evaluate_rubric",
    "plugin",
    "review_plan_feasibility",
    "run_critic_loop",
    "synthesize_debate_verdict",
]
