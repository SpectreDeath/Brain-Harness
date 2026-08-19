"""Agent session state machine and persistent trajectory store seam.

Provides authoritative lifecycle management, step checkpointing, persistent storage,
and trajectory auditing for autonomous agent executions.
"""

from __future__ import annotations

import json
import time
import uuid
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import asdict, dataclass, field
from typing import Any

import structlog

from harness.agent.base import AgentStep, AgentTaskResult, AgentTrajectory
from harness.events.bus import EVENT_BUS_KEY, EventBus
from harness.events.types import EventType, agent_event
from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin

logger = structlog.get_logger()

AGENT_SESSION_MANAGER_KEY: ServiceKey[AgentSessionManager] = ServiceKey("agent.session_manager")


@dataclass
class AgentSession:
    """Persistent, stateful execution session for an agent task run."""

    session_id: str
    task: str
    status: str = "running"  # "running", "completed", "max_steps_reached", "error", "paused"
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    completed_at: float | None = None
    final_answer: str = ""
    total_tokens: int = 0
    steps: list[AgentStep] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_step(self, step: AgentStep) -> None:
        """Add a step and touch the updated timestamp."""
        self.steps.append(step)
        self.updated_at = time.time()

    def mark_completed(self, answer: str, total_tokens: int = 0) -> None:
        """Mark session as successfully completed."""
        self.status = "completed"
        self.final_answer = answer
        if total_tokens:
            self.total_tokens = total_tokens
        now = time.time()
        self.updated_at = now
        self.completed_at = now

    def mark_error(self, error_message: str) -> None:
        """Mark session as terminated with an error."""
        self.status = "error"
        self.final_answer = error_message
        now = time.time()
        self.updated_at = now
        self.completed_at = now

    def mark_max_steps(self, fallback_answer: str = "") -> None:
        """Mark session as having reached the max step limit."""
        self.status = "max_steps_reached"
        self.final_answer = fallback_answer or (
            self.steps[-1].thought if self.steps else "Max steps reached without answer"
        )
        now = time.time()
        self.updated_at = now
        self.completed_at = now

    def to_result(self) -> AgentTaskResult:
        """Convert session snapshot to immutable AgentTaskResult."""
        return AgentTaskResult(
            task=self.task,
            status=self.status,
            final_answer=self.final_answer,
            steps=list(self.steps),
            total_tokens=self.total_tokens,
            metadata={**self.metadata, "session_id": self.session_id},
            session_id=self.session_id,
        )

    def to_trajectory(self) -> AgentTrajectory:
        """Convert session snapshot into an active AgentTrajectory."""
        traj = AgentTrajectory(
            task=self.task,
            steps=list(self.steps),
            status=self.status,
            final_answer=self.final_answer,
            total_tokens=self.total_tokens,
            metadata={**self.metadata, "session_id": self.session_id},
        )
        traj.session_id = self.session_id
        return traj

    def to_dict(self) -> dict[str, Any]:
        """Convert session to standard dictionary."""
        return {
            "session_id": self.session_id,
            "task": self.task,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "completed_at": self.completed_at,
            "final_answer": self.final_answer,
            "total_tokens": self.total_tokens,
            "steps": [s.to_dict() for s in self.steps],
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AgentSession:
        """Reconstitute an AgentSession from a dictionary."""
        raw_steps = data.get("steps", [])
        steps = [
            s if isinstance(s, AgentStep) else AgentStep(
                step_number=s.get("step_number", 0),
                thought=s.get("thought", ""),
                action=s.get("action"),
                action_input=s.get("action_input", {}),
                observation=s.get("observation"),
            )
            for s in raw_steps
        ]
        return cls(
            session_id=data["session_id"],
            task=data["task"],
            status=data.get("status", "running"),
            created_at=data.get("created_at", time.time()),
            updated_at=data.get("updated_at", time.time()),
            completed_at=data.get("completed_at"),
            final_answer=data.get("final_answer", ""),
            total_tokens=data.get("total_tokens", 0),
            steps=steps,
            metadata=data.get("metadata", {}),
        )

    def to_markdown(self) -> str:
        """Render session execution history as a clean markdown document."""
        lines = [
            f"# Agent Execution Session: `{self.session_id}`",
            "",
            f"- **Task**: {self.task}",
            f"- **Status**: `{self.status}`",
            f"- **Created**: {time.ctime(self.created_at)}",
            f"- **Steps Executed**: {len(self.steps)}",
            f"- **Total Tokens**: {self.total_tokens}",
        ]
        if self.completed_at:
            duration = self.completed_at - self.created_at
            lines.append(f"- **Duration**: {duration:.2f}s")
        lines.append("")

        if self.final_answer:
            lines.extend(["## Final Answer", "", self.final_answer, ""])

        lines.extend(["## Step Trajectory", ""])
        for step in self.steps:
            lines.append(f"### Step {step.step_number}")
            if step.thought:
                lines.append(f"**Thought:** {step.thought}")
            if step.action:
                lines.append(f"**Action:** `{step.action}`")
                lines.append("```json")
                lines.append(json.dumps(step.action_input, indent=2))
                lines.append("```")
            if step.observation is not None:
                lines.append("**Observation:**")
                lines.append("```json" if isinstance(step.observation, (dict, list)) else "")
                lines.append(
                    json.dumps(step.observation, indent=2)
                    if isinstance(step.observation, (dict, list))
                    else str(step.observation)
                )
                if isinstance(step.observation, (dict, list)):
                    lines.append("```")
            lines.append("")

        return "\n".join(lines)


class AgentSessionStore(ABC):
    """Abstract interface for agent session storage backends."""

    @abstractmethod
    async def save(self, session: AgentSession) -> None:
        """Save or update an agent session."""

    @abstractmethod
    async def get(self, session_id: str) -> AgentSession | None:
        """Retrieve a session by its unique ID."""

    @abstractmethod
    async def list(
        self,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AgentSession]:
        """List sessions optionally filtered by status."""

    @abstractmethod
    async def delete(self, session_id: str) -> bool:
        """Delete a session by ID."""


class InMemoryAgentSessionStore(AgentSessionStore):
    """Volatile in-memory implementation of AgentSessionStore."""

    def __init__(self) -> None:
        self._sessions: dict[str, AgentSession] = {}

    async def save(self, session: AgentSession) -> None:
        self._sessions[session.session_id] = session

    async def get(self, session_id: str) -> AgentSession | None:
        return self._sessions.get(session_id)

    async def list(
        self,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AgentSession]:
        items = list(self._sessions.values())
        if status:
            items = [s for s in items if s.status == status]
        # Sort descending by created_at
        items.sort(key=lambda s: s.created_at, reverse=True)
        return items[offset : offset + limit]

    async def delete(self, session_id: str) -> bool:
        return self._sessions.pop(session_id, None) is not None


class StorageBackedSessionStore(AgentSessionStore):
    """Persistent session store backed by the StorageService."""

    def __init__(self, storage: Any, prefix: str = "agent:session:") -> None:
        self.storage = storage
        self.prefix = prefix

    def _key(self, session_id: str) -> str:
        return f"{self.prefix}{session_id}"

    async def save(self, session: AgentSession) -> None:
        data = session.to_dict()
        await self.storage.set(self._key(session.session_id), data)

    async def get(self, session_id: str) -> AgentSession | None:
        data = await self.storage.get(self._key(session_id))
        if data is None:
            return None
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except Exception:
                return None
        return AgentSession.from_dict(data)

    async def list(
        self,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AgentSession]:
        keys = await self.storage.list_keys(prefix=self.prefix)
        sessions: list[AgentSession] = []
        for key in keys:
            data = await self.storage.get(key)
            if data is not None:
                if isinstance(data, str):
                    try:
                        data = json.loads(data)
                    except Exception:
                        continue
                sess = AgentSession.from_dict(data)
                if status is None or sess.status == status:
                    sessions.append(sess)

        sessions.sort(key=lambda s: s.created_at, reverse=True)
        return sessions[offset : offset + limit]

    async def delete(self, session_id: str) -> bool:
        return await self.storage.delete(self._key(session_id))


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


class AgentSessionManager:
    """Authoritative lifecycle and persistence orchestrator for agent sessions."""

    def __init__(
        self,
        store: AgentSessionStore | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        self.store = store or InMemoryAgentSessionStore()
        self.event_bus = event_bus

    @asynccontextmanager
    async def session_scope(
        self,
        task: str,
        *,
        session_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        agent_name: str = "agent.session_manager",
    ) -> AsyncIterator[AgentSessionScope]:
        """Async context manager orchestrating complete agent execution lifecycle."""
        session: AgentSession | None = None
        if session_id:
            session = await self.get_session(session_id)
        if session is None:
            session = await self.create_session(
                task, session_id=session_id, metadata=metadata
            )

        scope = AgentSessionScope(self, session, agent_name=agent_name)
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
    ) -> AgentSession:
        """Create and persist a new agent execution session."""
        sid = session_id or f"sess_{uuid.uuid4().hex[:12]}"
        session = AgentSession(
            session_id=sid,
            task=task,
            metadata=metadata or {},
        )
        await self.store.save(session)
        logger.info("Agent session created", session_id=sid, task=task[:50])

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

    async def get_session(self, session_id: str) -> AgentSession | None:
        """Retrieve a session by ID."""
        return await self.store.get(session_id)

    async def list_sessions(
        self,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AgentSession]:
        """List persisted sessions."""
        return await self.store.list(status=status, limit=limit, offset=offset)

    async def export_session(self, session_id: str, format: str = "json") -> str:
        """Export an agent execution session to JSON or Markdown."""
        session = await self.store.get(session_id)
        if not session:
            raise KeyError(f"Session '{session_id}' not found")

        if format.lower() == "markdown" or format.lower() == "md":
            return session.to_markdown()
        return json.dumps(session.to_dict(), indent=2)


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

        event_bus: EventBus | None = self._ctx.optional(EVENT_BUS_KEY) if hasattr(self._ctx, "optional") else None
        store: AgentSessionStore
        if self._custom_store is not None:
            store = self._custom_store
        else:
            from harness.services.storage import STORAGE_SERVICE_KEY

            storage = self._ctx.optional(STORAGE_SERVICE_KEY) if hasattr(self._ctx, "optional") else None
            if storage is not None:
                store = StorageBackedSessionStore(storage)
            else:
                store = InMemoryAgentSessionStore()

        self._manager = AgentSessionManager(store=store, event_bus=event_bus)
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
