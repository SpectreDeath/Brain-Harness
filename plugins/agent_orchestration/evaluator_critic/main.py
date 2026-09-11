"""Evaluator, Critic, and Safety Gatekeeper Plugin (Thin Adapter).

Delegates to the authoritative CriticEvaluationService seam while maintaining
100% backward-compatible function signatures and entrypoint contracts.
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

from plugins.agent_orchestration.critic_loop.main import (
    CRITIC_EVALUATION_SERVICE_KEY,
    CriticEvaluationService,
    _EVAL_INSTANCE,
)

logger = structlog.get_logger(__name__)


def critic_check_safety(command: str) -> dict[str, Any]:
    """Scan a shell command for dangerous, destructive, or irreversible operations."""
    return _EVAL_INSTANCE.check_command_safety(command)


def critic_evaluate_code(code: str, language: str = "python") -> dict[str, Any]:
    """Statically analyze code syntax, metrics, and safety anti-patterns."""
    return _EVAL_INSTANCE.evaluate_code_ast(code, language)


def critic_review_plan(goal: str, steps: list[str]) -> dict[str, Any]:
    """Evaluate plan steps for completeness, verification, and risk mitigation."""
    return _EVAL_INSTANCE.review_plan_feasibility(goal, steps)


class EvaluatorCriticPlugin(HarnessPlugin):
    """Adapter plugin registering Evaluator Critic into the IoC container."""

    @property
    def name(self) -> str:
        return "plugin.evaluator_critic"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return (
            "Adversarial code review, AST static analysis, destructive command safety filter, "
            "and plan feasibility critique (delegates to CriticEvaluationService)."
        )

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [CRITIC_EVALUATION_SERVICE_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, ctx: ServiceContext) -> None:
        ctx.provide(CRITIC_EVALUATION_SERVICE_KEY, _EVAL_INSTANCE, provider=self.name)
        logger.info("EvaluatorCritic provided CriticEvaluationService", plugin=self.name)

    async def enable(self, context: ServiceContext) -> None:
        await self.on_load(context)

    async def on_disable(self) -> None:
        pass

    async def disable(self, context: Any = None) -> None:
        await self.on_disable()


plugin = EvaluatorCriticPlugin()
