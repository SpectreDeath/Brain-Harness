"""Session creation, child linkage, and execution scope orchestration."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any, TYPE_CHECKING
import uuid

import structlog

from harness.agent.session.models import AgentSession
from harness.agent.session.scope import AgentSessionScope
from harness.events.types import EventType, agent_event

if TYPE_CHECKING:
    from harness.agent.session.store import AgentSessionStore
    from harness.events.bus import EventBus
    from harness.services.agent_graph import AgentExecutionGraphService

logger = structlog.get_logger()


class SessionCreationMixin:
    """Manages session creation, child linkage, and execution scope context."""

    store: AgentSessionStore
    event_bus: EventBus | None
    graph_store: AgentExecutionGraphService | None

    @asynccontextmanager
    async def session_scope(
        self,
        task: str,
        *,
        session_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        agent_name: str = "agent.session_manager",
        parent_session_id: str | None = None,
    ) -> AsyncIterator[AgentSessionScope]:
        """Async context manager orchestrating complete agent execution lifecycle."""
        session: AgentSession | None = None
        if session_id:
            session = await self.get_session(session_id)  # type: ignore[attr-defined]
        if session is None:
            session = await self.create_session(
                task,
                session_id=session_id,
                metadata=metadata,
                parent_session_id=parent_session_id,
            )

        scope = AgentSessionScope(self, session, agent_name=agent_name)  # type: ignore[arg-type]
        try:
            yield scope
        except Exception as exc:
            if not scope._completed:
                scope.mark_error(str(exc))
            raise
        finally:
            await scope.finalize()

    async def create_session(
        self,
        task: str,
        *,
        session_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        parent_session_id: str | None = None,
        node_id: str | None = None,
        role: str | None = None,
    ) -> AgentSession:
        """Create and persist a new agent execution session."""
        sid = session_id or f"sess_{uuid.uuid4().hex[:12]}"
        session = AgentSession(
            session_id=sid,
            task=task,
            metadata=metadata or {},
            parent_session_id=parent_session_id,
            node_id=node_id,
            role=role,
        )
        await self.store.save(session)

        # Link child session to parent if applicable
        if parent_session_id:
            parent = await self.store.get(parent_session_id)
            if parent:
                parent.add_child_session(sid)
                await self.store.save(parent)

        # Wire into authoritative Thread DAG lifecycle (Rule 17)
        if self.graph_store is not None:
            self.graph_store.register_thread(
                node_id=sid,
                role=role or "agent",
                task=task,
                parent_id=parent_session_id,
                metadata={"node_id": node_id, **(metadata or {})},
            )

        logger.info(
            "Agent session created",
            session_id=sid,
            task=task[:50],
            parent_session_id=parent_session_id,
            node_id=node_id,
        )

        if self.event_bus:
            await self.event_bus.emit(
                agent_event(
                    EventType.AGENT_TASK_STARTED,
                    agent_name="agent.session_manager",
                    task=task,
                    session_id=sid,
                )
            )
        return session

    async def create_child_session(
        self,
        parent_session_id: str,
        task: str,
        *,
        session_id: str | None = None,
        node_id: str | None = None,
        role: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AgentSession:
        """Create and link a child sub-agent session to an existing parent session."""
        return await self.create_session(
            task=task,
            session_id=session_id,
            metadata=metadata,
            parent_session_id=parent_session_id,
            node_id=node_id,
            role=role,
        )
