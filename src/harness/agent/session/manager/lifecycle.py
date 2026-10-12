"""Session lifecycle mutations, step recording, and execution status updates."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from harness.agent.session.models import AgentSession
from harness.events.types import EventType, agent_event
from harness.services.agent_graph import ThreadSpawnStatus

if TYPE_CHECKING:
    from harness.agent.base import AgentStep
    from harness.agent.session.store import AgentSessionStore
    from harness.events.bus import EventBus
    from harness.services.agent_graph import AgentExecutionGraphService

logger = structlog.get_logger()


class SessionLifecycleMixin:
    """Manages session step recording, completion, failure, and execution graph status."""

    store: AgentSessionStore
    event_bus: EventBus | None
    graph_store: AgentExecutionGraphService | None

    async def record_step(self, session_id: str, step: AgentStep) -> AgentSession:
        """Append an execution step to the session and update persistence store."""
        session = await self.store.get(session_id)
        if not session:
            raise KeyError(f"Session '{session_id}' not found")

        session.add_step(step)
        await self.store.save(session)

        if self.event_bus:
            await self.event_bus.emit(
                agent_event(
                    EventType.AGENT_STEP_COMPLETED,
                    agent_name="agent.session_manager",
                    task=session.task,
                    session_id=session_id,
                    step=step.step_number,
                    action=step.action,
                )
            )
        return session

    async def complete_session(
        self,
        session_id: str,
        final_answer: str,
        *,
        total_tokens: int = 0,
    ) -> AgentSession:
        """Mark a session as completed and persist final answer."""
        session = await self.store.get(session_id)
        if not session:
            raise KeyError(f"Session '{session_id}' not found")

        session.mark_completed(final_answer, total_tokens=total_tokens)
        await self.store.save(session)
        logger.info("Agent session completed", session_id=session_id)

        # Wire into authoritative Thread DAG lifecycle (Rule 17)
        if self.graph_store is not None:
            self.graph_store.update_thread_status(
                node_id=session_id,
                status="completed",
                tokens_used=total_tokens,
                completed=True,
            )
            if session.parent_session_id:
                self.graph_store.close_spawn_edge(
                    parent_id=session.parent_session_id,
                    child_id=session_id,
                    status=ThreadSpawnStatus.COMPLETED,
                )

        if self.event_bus:
            await self.event_bus.emit(
                agent_event(
                    EventType.AGENT_TASK_COMPLETED,
                    agent_name="agent.session_manager",
                    task=session.task,
                    session_id=session_id,
                    final_answer=final_answer[:200],
                    steps_count=len(session.steps),
                )
            )
        return session

    async def fail_session(self, session_id: str, error_message: str) -> AgentSession:
        """Mark a session as failed and persist error details."""
        session = await self.store.get(session_id)
        if not session:
            raise KeyError(f"Session '{session_id}' not found")

        session.mark_error(error_message)
        await self.store.save(session)
        logger.warning("Agent session failed", session_id=session_id, error=error_message)

        # Wire into authoritative Thread DAG lifecycle (Rule 17)
        if self.graph_store is not None:
            self.graph_store.update_thread_status(
                node_id=session_id,
                status="failed",
                completed=True,
            )
            if session.parent_session_id:
                self.graph_store.close_spawn_edge(
                    parent_id=session.parent_session_id,
                    child_id=session_id,
                    status=ThreadSpawnStatus.FAILED,
                )

        if self.event_bus:
            await self.event_bus.emit(
                agent_event(
                    EventType.AGENT_TASK_FAILED,
                    agent_name="agent.session_manager",
                    task=session.task,
                    session_id=session_id,
                    final_answer=error_message[:200],
                    steps_count=len(session.steps),
                )
            )
        return session
