"""Slotted domain models and tree representations for agent execution sessions.

Adheres to:
- Rule 12: Slotted & frozen dataclasses (slots=True, frozen=True where appropriate).
- Rule 33: Safe dict null-field fallbacks.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any

from harness.agent.base import AgentStep, AgentTaskResult, AgentTrajectory


@dataclass(slots=True)
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
                **(self.metadata or {}),
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
                **(self.metadata or {}),
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
            "steps": [s.to_dict() for s in (self.steps or [])],
            "metadata": self.metadata or {},
            "parent_session_id": self.parent_session_id,
            "children_session_ids": list(self.children_session_ids or []),
            "node_id": self.node_id,
            "role": self.role,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AgentSession:
        """Reconstitute an AgentSession from a dictionary."""
        raw_steps = data.get("steps") or []
        steps = [
            s if isinstance(s, AgentStep) else AgentStep(
                step_number=s.get("step_number", 0),
                thought=s.get("thought", ""),
                action=s.get("action"),
                action_input=s.get("action_input") or {},
                observation=s.get("observation"),
            )
            for s in raw_steps
        ]
        return cls(
            session_id=data["session_id"],
            task=data["task"],
            status=data.get("status", "running"),
            created_at=data.get("created_at") or time.time(),
            updated_at=data.get("updated_at") or time.time(),
            completed_at=data.get("completed_at"),
            final_answer=data.get("final_answer") or "",
            total_tokens=data.get("total_tokens") or 0,
            steps=steps,
            metadata=data.get("metadata") or {},
            parent_session_id=data.get("parent_session_id"),
            children_session_ids=list(data.get("children_session_ids") or []),
            node_id=data.get("node_id"),
            role=data.get("role"),
        )

    def to_markdown(self) -> str:
        """Render session execution history as a clean markdown document."""
        from harness.agent.session.exporter import SessionTreeExporter
        return SessionTreeExporter.to_markdown(self)


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
            "children": [c.to_dict() for c in (self.children or ())],
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
            "metrics": dict(self.metrics or {}),
        }
