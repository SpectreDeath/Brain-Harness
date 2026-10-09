"""HarnessPlugin lifecycle integration for ReAct agent loops."""

from __future__ import annotations

from typing import Any

import structlog

from harness.agent.base import AGENT_LOOP_KEY
from harness.agent.context_optimizer import (
    AGENT_CONTEXT_OPTIMIZER_KEY,
    AgentContextOptimizer,
)
from harness.agent.session import (
    AGENT_SESSION_MANAGER_KEY,
    AgentSessionManager,
)
from harness.events.bus import EVENT_BUS_KEY, EventBus
from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.llm import LLM_SERVICE_KEY, LLMService
from harness.services.tools import TOOL_REGISTRY_KEY, ToolRegistry

from .loop import ReActAgentLoop

logger = structlog.get_logger()


class ReActAgentPlugin(HarnessPlugin):
    """Plugin providing the ReAct agent loop service."""

    def __init__(self) -> None:
        self._loop: ReActAgentLoop | None = None
        self._ctx: ServiceContext | None = None

    @property
    def name(self) -> str:
        return "agent.react"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def description(self) -> str:
        return "Autonomous ReAct Reason + Act agent execution loop"

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [AGENT_LOOP_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return [LLM_SERVICE_KEY, TOOL_REGISTRY_KEY]

    @property
    def trusted(self) -> bool:
        return True

    async def on_load(self, ctx: ServiceContext) -> None:
        self._ctx = ctx

    async def on_enable(self) -> None:
        assert self._ctx is not None
        llm: LLMService = self._ctx.require(LLM_SERVICE_KEY)
        tools: ToolRegistry = self._ctx.require(TOOL_REGISTRY_KEY)
        event_bus: EventBus | None = self._ctx.optional(EVENT_BUS_KEY)
        session_manager: AgentSessionManager | None = self._ctx.optional(
            AGENT_SESSION_MANAGER_KEY
        )
        optimizer: AgentContextOptimizer | None = self._ctx.optional(
            AGENT_CONTEXT_OPTIMIZER_KEY
        )
        self._loop = ReActAgentLoop(
            llm=llm,
            tool_registry=tools,
            event_bus=event_bus,
            session_manager=session_manager,
            context=self._ctx,
            optimizer=optimizer,
        )
        self._ctx.provide(
            AGENT_LOOP_KEY, self._loop, provider=self.name, allow_override=True
        )
        logger.info(
            "ReAct agent loop enabled",
            telemetry=event_bus is not None,
            sessions=session_manager is not None,
            optimizer=optimizer is not None,
        )

    async def on_disable(self) -> None:
        if self._ctx:
            self._ctx.revoke(AGENT_LOOP_KEY)
        self._loop = None

    async def on_unload(self) -> None:
        self._loop = None
        self._ctx = None


# Module singleton export per Rule 45
plugin = ReActAgentPlugin()
