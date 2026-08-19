"""Abstract agent loop interface.

In accordance with the "everything is a plugin" design ethos, the agent's
reasoning/execution loop itself is an swappable service.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from harness.kernel.context import ServiceKey

AGENT_LOOP_KEY: ServiceKey[AgentLoopService] = ServiceKey("agent.loop")


@dataclass
class AgentStep:
    """A single thought/action/observation step in the agent trajectory."""

    step_number: int
    thought: str = ""
    action: str | None = None
    action_input: dict[str, Any] = field(default_factory=dict)
    observation: Any = None

    def to_dict(self) -> dict[str, Any]:
        """Convert AgentStep to standard dictionary representation."""
        return {
            "step_number": self.step_number,
            "thought": self.thought,
            "action": self.action,
            "action_input": self.action_input,
            "observation": self.observation,
        }


@dataclass
class AgentTaskResult:
    """Outcome of an autonomous agent task run."""

    task: str
    status: str  # "completed", "max_steps_reached", "error"
    final_answer: str = ""
    steps: list[AgentStep] = field(default_factory=list)
    total_tokens: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    session_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert AgentTaskResult to standard dictionary representation."""
        res = {
            "task": self.task,
            "status": self.status,
            "final_answer": self.final_answer,
            "steps": [s.to_dict() for s in self.steps],
            "total_tokens": self.total_tokens,
            "metadata": self.metadata,
        }
        if self.session_id:
            res["session_id"] = self.session_id
        return res


@dataclass
class AgentTrajectory:
    """Stateful execution record for an agent task run.

    Encapsulates message history, step records, token counts, status,
    and metadata across reasoning and tool execution iterations.
    """

    task: str
    messages: list[Any] = field(default_factory=list)
    steps: list[AgentStep] = field(default_factory=list)
    status: str = "running"  # "running", "completed", "max_steps_reached", "error"
    final_answer: str = ""
    total_tokens: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    session_id: str | None = None

    def add_step(self, step: AgentStep) -> None:
        """Append a step to the trajectory."""
        self.steps.append(step)

    def mark_completed(self, answer: str) -> None:
        """Mark task as successfully completed with final answer."""
        self.status = "completed"
        self.final_answer = answer

    def mark_error(self, error_message: str) -> None:
        """Mark task as stopped with error."""
        self.status = "error"
        self.final_answer = error_message

    def mark_max_steps(self, fallback_answer: str = "") -> None:
        """Mark task as reaching max step limit."""
        self.status = "max_steps_reached"
        self.final_answer = fallback_answer or (
            self.steps[-1].thought if self.steps else "Max steps reached without answer"
        )

    def to_result(self) -> AgentTaskResult:
        """Convert trajectory into an immutable AgentTaskResult snapshot."""
        return AgentTaskResult(
            task=self.task,
            status=self.status,
            final_answer=self.final_answer,
            steps=list(self.steps),
            total_tokens=self.total_tokens,
            metadata=dict(self.metadata),
            session_id=self.session_id,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert AgentTrajectory to standard dictionary representation."""
        res = {
            "task": self.task,
            "status": self.status,
            "final_answer": self.final_answer,
            "steps": [s.to_dict() for s in self.steps],
            "total_tokens": self.total_tokens,
            "metadata": self.metadata,
            "messages_count": len(self.messages),
        }
        if self.session_id:
            res["session_id"] = self.session_id
        return res

    def to_summary(self) -> dict[str, Any]:
        """Lightweight summary snapshot of current trajectory state."""
        res = {
            "task": self.task,
            "status": self.status,
            "steps_count": len(self.steps),
            "final_answer": self.final_answer,
        }
        if self.session_id:
            res["session_id"] = self.session_id
        return res


class AgentLoopService(ABC):
    """Abstract interface for agent execution loops."""

    @abstractmethod
    async def run_task(
        self,
        task: str,
        *,
        max_steps: int = 10,
        context: dict[str, Any] | None = None,
    ) -> AgentTaskResult:
        """Execute an autonomous task."""
