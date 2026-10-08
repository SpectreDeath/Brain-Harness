"""IoC Micro-Kernel Plugin registering AgentSessionManager into the service context.

Adheres to:
- Rule 1: Everything is a plugin.
- Rule 2: Typed service keys.
- Rule 45: Plugin module singleton export (plugin = AgentSessionPlugin()).
"""

from __future__ import annotations

from typing import Any
import structlog

from harness.agent.session.manager import AGENT_SESSION_MANAGER_KEY, AgentSessionManager
from harness.agent.session.store import (
    AgentSessionStore,
    InMemoryAgentSessionStore,
    StorageBackedSessionStore,
)
from harness.events.bus import EVENT_BUS_KEY, EventBus
from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.agent_graph import AGENT_GRAPH_STORE_KEY

logger = structlog.get_logger()


class AgentSessionPlugin(HarnessPlugin):
    """Plugin providing authoritative agent session persistence and lifecycle service."""

    def __init__(self, store: AgentSessionStore | None = None) -> None:
        self._custom_store = store
        self._manager: AgentSessionManager | None = None
        self._ctx: ServiceContext | None = None

    @property
    def name(self) -> str:
        return "agent.session"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def description(self) -> str:
        return "Persistent agent session management and trajectory storage"

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [AGENT_SESSION_MANAGER_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    @property
    def trusted(self) -> bool:
        return True

    @property
    def manager(self) -> AgentSessionManager | None:
        return self._manager

    async def on_load(self, ctx: ServiceContext) -> None:
        self._ctx = ctx

    async def on_enable(self) -> None:
        if not self._ctx:
            return

        event_bus: EventBus | None = self._ctx.optional(EVENT_BUS_KEY)
        store: AgentSessionStore
        if self._custom_store is not None:
            store = self._custom_store
        else:
            from harness.services.storage import STORAGE_SERVICE_KEY

            storage = self._ctx.optional(STORAGE_SERVICE_KEY)
            if storage is not None:
                store = StorageBackedSessionStore(storage)
            else:
                store = InMemoryAgentSessionStore()

        graph_store = self._ctx.optional(AGENT_GRAPH_STORE_KEY)
        self._manager = AgentSessionManager(
            store=store,
            event_bus=event_bus,
            context=self._ctx,
            graph_store=graph_store,
        )
        self._ctx.provide(
            AGENT_SESSION_MANAGER_KEY,
            self._manager,
            provider=self.name,
            allow_override=True,
        )

        logger.info(
            "Agent session manager enabled",
            store=store.__class__.__name__,
            telemetry=event_bus is not None,
        )

    async def on_disable(self) -> None:
        if self._ctx:
            self._ctx.revoke(AGENT_SESSION_MANAGER_KEY)
        self._manager = None

    async def on_unload(self) -> None:
        self._manager = None
        self._ctx = None


# Module singleton export (Rule 45)
plugin = AgentSessionPlugin()
