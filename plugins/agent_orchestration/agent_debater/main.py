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

logger = structlog.get_logger(__name__)

AGENT_DEBATER_SERVICE_KEY: ServiceKey[Any] = ServiceKey("service.agent_debater")
CRITIC_EVALUATION_SERVICE_KEY: ServiceKey[Any] = ServiceKey("service.critic_evaluation")


def _resolve_critic_eval(ctx: ServiceContext | None = None) -> Any:
    """Resolve CriticEvaluationService from IoC container or dynamic critic_loop fallback."""
    if ctx is not None:
        svc = ctx.optional(CRITIC_EVALUATION_SERVICE_KEY)
        if svc is not None:
            return svc
    import importlib

    return importlib.import_module("plugins.agent_orchestration.critic_loop.main")._EVAL_INSTANCE


def conduct_dialectical_debate(
    topic: str,
    pro_arguments: list[str],
    con_arguments: list[str],
) -> dict[str, Any]:
    """Structure dialectical argument rounds between Proposer and Challenger."""
    return _resolve_critic_eval().conduct_dialectical_debate(topic, pro_arguments, con_arguments)


def synthesize_debate_verdict(debate_summary: dict[str, Any]) -> dict[str, Any]:
    """Synthesize an impartial arbiter decision based on debate rounds."""
    return _resolve_critic_eval().synthesize_debate_verdict(debate_summary)


class AgentDebaterPlugin(HarnessPlugin):
    """Adapter plugin registering Agent Debater into the IoC container."""

    def __init__(self) -> None:
        self._delegate: Any | None = None

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
        return [AGENT_DEBATER_SERVICE_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return [CRITIC_EVALUATION_SERVICE_KEY]

    async def on_load(self, ctx: ServiceContext) -> None:
        self._delegate = _resolve_critic_eval(ctx)
        ctx.provide(AGENT_DEBATER_SERVICE_KEY, self._delegate, provider=self.name)
        logger.info("AgentDebater provided AgentDebaterService", plugin=self.name)

    async def enable(self, context: ServiceContext) -> None:
        await self.on_load(context)

    async def on_disable(self) -> None:
        pass

    async def disable(self, context: Any = None) -> None:
        await self.on_disable()


plugin = AgentDebaterPlugin()
