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
from dataclasses import dataclass, field
from typing import Any

import structlog

from harness.agent.base import AgentStep, AgentTaskResult, AgentTrajectory
from harness.events.bus import EVENT_BUS_KEY, EventBus
from harness.events.types import EventType, agent_event
from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.agent_graph import (
    AGENT_GRAPH_STORE_KEY,
    AgentExecutionGraphService,
    ThreadSpawnStatus,
)

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
    parent_session_id: str | None = None
    children_session_ids: list[str] = field(default_factory=list)
    node_id: str | None = None
    role: str | None = None

    def add_step(self, step: AgentStep) -> None:
        """Add a step and touch the updated timestamp."""
        self.steps.append(step)
        self.updated_at = time.time()

    def add_child_session(self, child_session_id: str) -> None:
        """Link a child sub-agent session to this parent session."""
        if child_session_id not in self.children_session_ids:
            self.children_session_ids.append(child_session_id)
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
            metadata={
                **self.metadata,
                "session_id": self.session_id,
                "parent_session_id": self.parent_session_id,
                "node_id": self.node_id,
                "role": self.role,
            },
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
            metadata={
                **self.metadata,
                "session_id": self.session_id,
                "parent_session_id": self.parent_session_id,
                "node_id": self.node_id,
                "role": self.role,
            },
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
            "parent_session_id": self.parent_session_id,
            "children_session_ids": list(self.children_session_ids),
            "node_id": self.node_id,
            "role": self.role,
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
            parent_session_id=data.get("parent_session_id"),
            children_session_ids=list(data.get("children_session_ids", [])),
            node_id=data.get("node_id"),
            role=data.get("role"),
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
        if self.parent_session_id:
            lines.append(f"- **Parent Session**: `{self.parent_session_id}`")
        if self.node_id or self.role:
            lines.append(f"- **Node / Role**: `{self.node_id or 'none'}` ({self.role or 'default'})")
        if self.children_session_ids:
            lines.append(f"- **Child Sessions**: {len(self.children_session_ids)}")
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


@dataclass(slots=True, frozen=True)
class SessionTreeNode:
    """Immutable, slotted node in a hierarchical session execution tree."""

    session_id: str
    task: str
    status: str
    created_at: float
    updated_at: float
    completed_at: float | None
    final_answer: str
    total_tokens: int
    steps_count: int
    role: str | None = None
    node_id: str | None = None
    parent_session_id: str | None = None
    children: tuple[SessionTreeNode, ...] = ()
    depth: int = 0
    subtree_tokens: int = 0
    subtree_steps: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert tree node to standard dictionary."""
        return {
            "session_id": self.session_id,
            "task": self.task,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "completed_at": self.completed_at,
            "final_answer": self.final_answer,
            "total_tokens": self.total_tokens,
            "steps_count": self.steps_count,
            "role": self.role,
            "node_id": self.node_id,
            "parent_session_id": self.parent_session_id,
            "depth": self.depth,
            "subtree_tokens": self.subtree_tokens,
            "subtree_steps": self.subtree_steps,
            "children": [c.to_dict() for c in self.children],
        }


@dataclass(slots=True, frozen=True)
class SessionTreeSnapshot:
    """Immutable, slotted snapshot of a hierarchical agent session trajectory."""

    root: SessionTreeNode
    total_sessions: int
    total_tokens: int
    total_steps: int
    total_duration: float
    max_depth: int
    completed_count: int
    failed_count: int
    metrics: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert snapshot to hierarchical dictionary."""
        return {
            "root": self.root.to_dict(),
            "total_sessions": self.total_sessions,
            "total_tokens": self.total_tokens,
            "total_steps": self.total_steps,
            "total_duration": self.total_duration,
            "max_depth": self.max_depth,
            "completed_count": self.completed_count,
            "failed_count": self.failed_count,
            "metrics": dict(self.metrics),
        }


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
        return bool(await self.storage.delete(self._key(session_id)))


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


class AgentSessionManager:
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
            session = await self.get_session(session_id)
        if session is None:
            session = await self.create_session(
                task,
                session_id=session_id,
                metadata=metadata,
                parent_session_id=parent_session_id,
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

    async def get_subtree_metrics(self, session_id: str) -> dict[str, Any]:
        """Compute recursive aggregations (tokens, steps, duration, statuses) across a session subtree."""
        tree = await self.get_session_tree(session_id)
        if not tree:
            return {
                "total_sessions": 0,
                "total_tokens": 0,
                "total_steps": 0,
                "total_duration": 0.0,
                "completed_count": 0,
                "failed_count": 0,
            }

        total_tokens = 0
        total_steps = 0
        completed_count = 0
        failed_count = 0
        total_sessions = 0
        min_created = float("inf")
        max_completed = 0.0

        def _collect(node: dict[str, Any]) -> None:
            nonlocal total_tokens, total_steps, completed_count, failed_count, total_sessions, min_created, max_completed
            total_sessions += 1
            total_tokens += int(node.get("total_tokens", 0) or 0)
            total_steps += len(node.get("steps", []) or [])
            st = node.get("status", "")
            if st == "completed":
                completed_count += 1
            elif st in ("error", "failed", "max_steps_reached"):
                failed_count += 1

            cr = float(node.get("created_at", 0) or 0)
            if cr > 0 and cr < min_created:
                min_created = cr
            cm = float(node.get("completed_at", 0) or node.get("updated_at", 0) or 0)
            if cm > max_completed:
                max_completed = cm

            for child in node.get("children", []):
                _collect(child)

        _collect(tree)
        duration = max(0.0, round(max_completed - min_created, 3)) if min_created < float("inf") else 0.0

        return {
            "total_sessions": total_sessions,
            "total_tokens": total_tokens,
            "total_steps": total_steps,
            "total_duration": duration,
            "completed_count": completed_count,
            "failed_count": failed_count,
        }

    async def get_session_tree(self, session_id: str) -> dict[str, Any] | None:
        """Recursively build hierarchical session execution tree with all child sessions and metrics."""
        session = await self.store.get(session_id)
        if not session:
            return None

        tree = session.to_dict()
        children: list[dict[str, Any]] = []
        for child_id in session.children_session_ids:
            child_tree = await self.get_session_tree(child_id)
            if child_tree:
                children.append(child_tree)

        tree["children"] = children

        # Compute rollups
        total_subtree_tokens = tree.get("total_tokens", 0)
        total_subtree_steps = len(tree.get("steps", []))
        for c in children:
            sub = c.get("subtree_metrics", {})
            total_subtree_tokens += sub.get("total_tokens", c.get("total_tokens", 0))
            total_subtree_steps += sub.get("total_steps", len(c.get("steps", [])))

        tree["subtree_metrics"] = {
            "total_tokens": total_subtree_tokens,
            "total_steps": total_subtree_steps,
            "child_count": len(children),
        }
        return tree

    async def get_tree_snapshot(self, session_id: str) -> SessionTreeSnapshot | None:
        """Construct an immutable, slotted SessionTreeSnapshot for a session hierarchy."""
        session = await self.store.get(session_id)
        if not session:
            return None

        total_sessions = 0
        total_tokens = 0
        total_steps = 0
        completed_count = 0
        failed_count = 0
        min_created = float("inf")
        max_completed = 0.0
        max_depth = 0

        async def _build_node(sess: AgentSession, current_depth: int) -> SessionTreeNode:
            nonlocal total_sessions, total_tokens, total_steps, completed_count, failed_count, min_created, max_completed, max_depth
            total_sessions += 1
            if current_depth > max_depth:
                max_depth = current_depth

            sess_tokens = int(sess.total_tokens or 0)
            sess_steps = len(sess.steps or [])
            total_tokens += sess_tokens
            total_steps += sess_steps

            if sess.status == "completed":
                completed_count += 1
            elif sess.status in ("error", "failed", "max_steps_reached"):
                failed_count += 1

            if sess.created_at and sess.created_at < min_created:
                min_created = sess.created_at
            end_t = sess.completed_at or sess.updated_at or sess.created_at
            if end_t and end_t > max_completed:
                max_completed = end_t

            children_nodes: list[SessionTreeNode] = []
            sub_tokens = sess_tokens
            sub_steps = sess_steps

            for child_id in sess.children_session_ids:
                child_sess = await self.store.get(child_id)
                if child_sess:
                    child_node = await _build_node(child_sess, current_depth + 1)
                    children_nodes.append(child_node)
                    sub_tokens += child_node.subtree_tokens
                    sub_steps += child_node.subtree_steps

            return SessionTreeNode(
                session_id=sess.session_id,
                task=sess.task,
                status=sess.status,
                created_at=sess.created_at,
                updated_at=sess.updated_at,
                completed_at=sess.completed_at,
                final_answer=sess.final_answer,
                total_tokens=sess_tokens,
                steps_count=sess_steps,
                role=sess.role,
                node_id=sess.node_id,
                parent_session_id=sess.parent_session_id,
                children=tuple(children_nodes),
                depth=current_depth,
                subtree_tokens=sub_tokens,
                subtree_steps=sub_steps,
            )

        root_node = await _build_node(session, 0)
        duration = max(0.0, round(max_completed - min_created, 3)) if min_created < float("inf") else 0.0

        metrics = {
            "total_sessions": total_sessions,
            "total_tokens": total_tokens,
            "total_steps": total_steps,
            "total_duration": duration,
            "max_depth": max_depth,
            "completed_count": completed_count,
            "failed_count": failed_count,
        }

        return SessionTreeSnapshot(
            root=root_node,
            total_sessions=total_sessions,
            total_tokens=total_tokens,
            total_steps=total_steps,
            total_duration=duration,
            max_depth=max_depth,
            completed_count=completed_count,
            failed_count=failed_count,
            metrics=metrics,
        )


    async def list_root_sessions(
        self,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AgentSession]:
        """List root-level sessions (excluding child sub-agent executions)."""
        all_sessions = await self.store.list(status=status, limit=1000)
        root_sessions = [s for s in all_sessions if s.parent_session_id is None]
        return root_sessions[offset : offset + limit]

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
