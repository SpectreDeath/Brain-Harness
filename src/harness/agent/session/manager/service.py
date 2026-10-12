"""Authoritative AgentSessionManager coordinating lifecycle, hierarchy, query, and export."""

from __future__ import annotations

from typing import TYPE_CHECKING

from harness.agent.session.manager.creation import SessionCreationMixin
from harness.agent.session.manager.export import SessionExportMixin
from harness.agent.session.manager.hierarchy import SessionHierarchyMixin
from harness.agent.session.manager.lifecycle import SessionLifecycleMixin
from harness.agent.session.manager.query import SessionQueryMixin
from harness.agent.session.store import AgentSessionStore, InMemoryAgentSessionStore
from harness.events.bus import EventBus
from harness.kernel.context import ServiceContext
from harness.services.agent_graph import (
    AGENT_GRAPH_STORE_KEY,
    AgentExecutionGraphService,
)


class AgentSessionManager(
    SessionCreationMixin,
    SessionLifecycleMixin,
    SessionHierarchyMixin,
    SessionQueryMixin,
    SessionExportMixin,
):
    """Authoritative lifecycle and persistence orchestrator for agent sessions."""

    def __init__(
        self,
        store: AgentSessionStore | None = None,
        event_bus: EventBus | None = None,
        context: ServiceContext | None = None,
        graph_store: AgentExecutionGraphService | None = None,
    ) -> None:
        self.store = store or InMemoryAgentSessionStore()
        self.event_bus = event_bus
        self.context = context
        self._graph_store = graph_store

    @property
    def graph_store(self) -> AgentExecutionGraphService | None:
        """Resolve authoritative AgentExecutionGraphService from store or context."""
        if self._graph_store is not None:
            return self._graph_store
        if self.context is not None:
            return self.context.optional(AGENT_GRAPH_STORE_KEY)
        return None
