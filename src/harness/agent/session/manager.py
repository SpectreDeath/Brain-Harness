"""Authoritative lifecycle and persistence orchestrator for agent sessions."""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import structlog

from harness.agent.base import AgentStep
from harness.agent.session.exporter import SessionTreeExporter
from harness.agent.session.models import AgentSession, SessionTreeNode, SessionTreeSnapshot
from harness.agent.session.scope import AgentSessionScope
from harness.agent.session.store import AgentSessionStore, InMemoryAgentSessionStore
from harness.events.bus import EventBus
from harness.events.types import EventType, agent_event
from harness.kernel.context import ServiceContext, ServiceKey
from harness.services.agent_graph import (
    AGENT_GRAPH_STORE_KEY,
    AgentExecutionGraphService,
    ThreadSpawnStatus,
)

logger = structlog.get_logger()

AGENT_SESSION_MANAGER_KEY: ServiceKey[AgentSessionManager] = ServiceKey("agent.session_manager")


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

            for child in (node.get("children") or []):
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

        if format.lower() in ("markdown", "md"):
            return SessionTreeExporter.to_markdown(session)
        return SessionTreeExporter.to_json(session)
