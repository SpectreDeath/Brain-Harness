"""Active execution scope managing session lifecycle, step recording, and event dispatch."""

from __future__ import annotations

from typing import TYPE_CHECKING
from harness.agent.base import AgentStep
from harness.events.types import EventType, agent_event
from harness.services.agent_graph import ThreadSpawnStatus

if TYPE_CHECKING:
    from harness.agent.session.manager import AgentSessionManager
    from harness.agent.session.models import AgentSession


class AgentSessionScope:
    """Active execution scope managing session lifecycle, step recording, and event dispatch."""

    def __init__(
        self,
        manager: AgentSessionManager,
        session: AgentSession,
        *,
        agent_name: str = "agent.session_manager",
    ) -> None:
        self.manager = manager
        self.session = session
        self.agent_name = agent_name
        self._completed = False

    @property
    def session_id(self) -> str:
        return self.session.session_id

    @property
    def task(self) -> str:
        return self.session.task

    @property
    def status(self) -> str:
        return self.session.status

    @property
    def steps(self) -> list[AgentStep]:
        return self.session.steps

    @property
    def final_answer(self) -> str:
        return self.session.final_answer

    async def record_step(self, step: AgentStep) -> None:
        """Record an execution step into the active session with immediate persistence & telemetry."""
        await self.manager.record_step(self.session_id, step)

    def mark_completed(self, answer: str, total_tokens: int = 0) -> None:
        """Mark the session as completed."""
        self.session.mark_completed(answer, total_tokens=total_tokens)
        self._completed = True

    def mark_max_steps(self, fallback_answer: str = "") -> None:
        """Mark the session as max steps reached."""
        self.session.mark_max_steps(fallback_answer=fallback_answer)
        self._completed = True

    def mark_error(self, error_message: str) -> None:
        """Mark the session as terminated with error."""
        self.session.mark_error(error_message)
        self._completed = True

    async def finalize(self) -> AgentSession:
        """Persist final state and emit terminal telemetry event."""
        await self.manager.store.save(self.session)

        # Update thread graph if available (Rule 17)
        graph = self.manager.graph_store
        if graph is not None:
            st = "completed" if self.session.status in ("completed", "max_steps_reached") else "failed"
            edge_st = ThreadSpawnStatus.COMPLETED if st == "completed" else ThreadSpawnStatus.FAILED
            graph.update_thread_status(
                node_id=self.session.session_id,
                status=st,
                tokens_used=self.session.total_tokens,
                completed=True,
            )
            if self.session.parent_session_id:
                graph.close_spawn_edge(
                    parent_id=self.session.parent_session_id,
                    child_id=self.session.session_id,
                    status=edge_st,
                )

        if self.manager.event_bus:
            evt_type = (
                EventType.AGENT_TASK_COMPLETED
                if self.session.status in ("completed", "max_steps_reached")
                else EventType.AGENT_TASK_FAILED
            )
            await self.manager.event_bus.emit(
                agent_event(
                    evt_type,
                    agent_name=self.agent_name,
                    task=self.session.task,
                    session_id=self.session.session_id,
                    status=self.session.status,
                    final_answer=self.session.final_answer[:200],
                    steps_count=len(self.session.steps),
                )
            )
        return self.session
