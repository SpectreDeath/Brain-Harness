"""Context Optimizer Plugin — Micro-kernel IoC provider for context optimization (Rule 1 & Rule 45)."""

from __future__ import annotations

import sys
from typing import Any

import structlog

# Rule 23: Windows UTF-8 Stream Codec Entrypoint Invariant
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.context_optimizer import (
    AGENT_CONTEXT_OPTIMIZER_KEY,
    CONTEXT_OPTIMIZER_SERVICE_KEY,
    ContextOptimizationConfig,
    ContextOptimizerService,
    DefaultContextOptimizerService,
)
from harness.services.llm import LLMMessage

logger = structlog.get_logger(__name__)


class ContextOptimizerPlugin(HarnessPlugin):
    """Plugin providing pre-LLM context optimization, observation compaction, and strategy pipelines."""

    def __init__(self, config: ContextOptimizationConfig | None = None) -> None:
        super().__init__()
        self._service: ContextOptimizerService = DefaultContextOptimizerService(config=config)

    @property
    def name(self) -> str:
        return "plugin.context_optimizer"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Pre-LLM context optimization, observation compaction, and composable pruning strategies"

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [CONTEXT_OPTIMIZER_SERVICE_KEY, AGENT_CONTEXT_OPTIMIZER_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, context: ServiceContext) -> None:
        """Register the service into the micro-kernel IoC container (Rule 1 & Rule 2)."""
        if isinstance(self._service, DefaultContextOptimizerService):
            self._service.context = context
        context.provide(CONTEXT_OPTIMIZER_SERVICE_KEY, self._service)
        context.provide(AGENT_CONTEXT_OPTIMIZER_KEY, self._service)
        logger.info(
            "context_optimizer_service_provided",
            service=str(CONTEXT_OPTIMIZER_SERVICE_KEY),
        )

    async def enable(self, context: ServiceContext) -> None:
        await self.on_load(context)

    async def on_disable(self) -> None:
        pass

    async def disable(self, context: Any = None) -> None:
        await self.on_disable()

    def compact_observation(self, action_name: str, observation: Any, *, max_chars: int | None = None) -> str:
        return self._service.compact_observation(action_name, observation, max_chars=max_chars)

    def optimize_messages(
        self, messages: list[LLMMessage], *, config: ContextOptimizationConfig | None = None
    ) -> list[LLMMessage]:
        return self._service.optimize_messages(messages, config=config)


# Rule 45: Export instantiated module singleton plugin instance
plugin = ContextOptimizerPlugin()


# Top-level entrypoints matching plugin.json declarations
def context_compact_observation(action_name: str, observation: Any, max_chars: int | None = None, **kwargs: Any) -> dict[str, Any]:
    """Compact raw tool observation into a token-efficient string."""
    res = plugin.compact_observation(action_name, observation, max_chars=max_chars)
    return {"status": "ok", "compacted_observation": res}


def context_optimize_messages(
    messages: list[dict[str, Any]],
    max_total_messages: int | None = None,
    recent_messages_preserve: int | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Prune message sequence using registered optimization strategies."""
    llm_msgs = [LLMMessage(role=m.get("role", "user"), content=m.get("content", "")) for m in messages]
    kwargs_cfg: dict[str, Any] = {}
    if max_total_messages is not None:
        kwargs_cfg["max_total_messages"] = max_total_messages
    if recent_messages_preserve is not None:
        kwargs_cfg["recent_messages_preserve"] = recent_messages_preserve
    cfg = ContextOptimizationConfig(**kwargs_cfg) if kwargs_cfg else None
    opt_msgs = plugin.optimize_messages(llm_msgs, config=cfg)
    return {
        "status": "ok",
        "original_count": len(messages),
        "optimized_count": len(opt_msgs),
        "messages": [{"role": m.role, "content": m.content} for m in opt_msgs],
    }
