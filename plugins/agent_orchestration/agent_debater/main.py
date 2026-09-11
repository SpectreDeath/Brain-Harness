"""Dialectical Multi-Agent Debater & Arbiter Verdict Synthesis Plugin (Thin Adapter).

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


def conduct_dialectical_debate(
    topic: str,
    pro_arguments: list[str],
    con_arguments: list[str],
) -> dict[str, Any]:
    """Structure dialectical argument rounds between Proposer and Challenger."""
    return _EVAL_INSTANCE.conduct_dialectical_debate(topic, pro_arguments, con_arguments)


def synthesize_debate_verdict(debate_summary: dict[str, Any]) -> dict[str, Any]:
    """Synthesize an impartial arbiter decision based on debate rounds."""
    return _EVAL_INSTANCE.synthesize_debate_verdict(debate_summary)


class AgentDebaterPlugin(HarnessPlugin):
    """Adapter plugin registering Agent Debater into the IoC container."""

    @property
    def name(self) -> str:
        return "plugin.agent_debater"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return (
            "Dialectical multi-agent debater and arbiter verdict synthesis "
            "(delegates to CriticEvaluationService)."
        )

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [CRITIC_EVALUATION_SERVICE_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, ctx: ServiceContext) -> None:
        ctx.provide(CRITIC_EVALUATION_SERVICE_KEY, _EVAL_INSTANCE, provider=self.name)
        logger.info("AgentDebater provided CriticEvaluationService", plugin=self.name)

    async def enable(self, context: ServiceContext) -> None:
        await self.on_load(context)

    async def on_disable(self) -> None:
        pass

    async def disable(self, context: Any = None) -> None:
        await self.on_disable()


plugin = AgentDebaterPlugin()
