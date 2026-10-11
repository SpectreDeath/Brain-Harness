"""Domain models, Status enum, Task, IterationSnapshot, and LoopResult for Goal-Directed Loop Engine."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


class Status(Enum):
    """Tri-state polling and lifecycle states for goal-directed tasks."""

    PENDING = auto()         # not yet attempted or waiting on upstream
    NEEDS_RESOURCE = auto()  # blocked on a missing resource, retrieve() may help
    NEEDS_INPUT = auto()     # blocked on ambiguity, ask() may help
    READY = auto()           # dependencies satisfied, can attempt action
    DONE = auto()            # completed and validated
    FAILED = auto()          # exhausted retries, permanently failed
    DEADLOCKED = auto()      # unresolvable block (missing resource/decision or deadlocked upstream)


@dataclass(slots=True)
class Task:
    """Task node within the goal-directed execution graph (Rule 12)."""

    task_id: str
    depends_on: tuple[str, ...] = ()
    requires_resource: str | None = None
    requires_decision: str | None = None
    action: Callable[[Task, dict], bool] | None = None
    max_retries: int = 2

    status: Status = Status.PENDING
    attempts: int = 0
    history: list[str] = field(default_factory=list)

    def log(self, event: str) -> None:
        self.history.append(event)

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "depends_on": list(self.depends_on),
            "requires_resource": self.requires_resource,
            "requires_decision": self.requires_decision,
            "status": self.status.name,
            "attempts": self.attempts,
            "history": list(self.history),
            "max_retries": self.max_retries,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Task:
        task = cls(
            task_id=d["task_id"],
            depends_on=tuple(d.get("depends_on", ())),
            requires_resource=d.get("requires_resource"),
            requires_decision=d.get("requires_decision"),
            max_retries=d.get("max_retries", 2),
        )
        if "status" in d:
            task.status = Status[d["status"]]
        task.attempts = int(d.get("attempts", 0))
        task.history = list(d.get("history", []))
        return task


@dataclass(slots=True, frozen=True)
class IterationSnapshot:
    """Slotted, frozen iteration progress snapshot (Rule 12 & Rule 43)."""

    iteration: int
    ready_or_done_this_iter: int
    completed_total: int
    blocked: int
    waiting: int
    retrieved_this_iter: int
    asked_this_iter: int
    revised_this_iter: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "iteration": self.iteration,
            "completed_total": self.completed_total,
            "blocked": self.blocked,
            "waiting": self.waiting,
            "retrieved_this_iter": self.retrieved_this_iter,
            "asked_this_iter": self.asked_this_iter,
            "revised_this_iter": self.revised_this_iter,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> IterationSnapshot:
        return cls(
            iteration=d["iteration"],
            ready_or_done_this_iter=d.get("ready_or_done_this_iter", d.get("completed_total", 0)),
            completed_total=d["completed_total"],
            blocked=d["blocked"],
            waiting=d["waiting"],
            retrieved_this_iter=d["retrieved_this_iter"],
            asked_this_iter=d["asked_this_iter"],
            revised_this_iter=d["revised_this_iter"],
        )


@dataclass(slots=True, frozen=True)
class LoopResult:
    """Slotted, frozen evaluation result of a complete goal-directed loop execution run (Rule 12 & Rule 43)."""

    iterations: int
    final_counts: dict[str, int]
    trace: list[str] = field(default_factory=list)
    snapshots: list[IterationSnapshot] = field(default_factory=list)
    total_recoveries: int = 0
    skipped_work_avoided: int = 0

    @property
    def completed(self) -> int:
        return self.final_counts.get("DONE", 0)

    @property
    def progress_efficiency(self) -> float:
        return self.completed / self.iterations if self.iterations else 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "iterations": self.iterations,
            "completed": self.completed,
            "final_counts": self.final_counts,
            "total_recoveries": self.total_recoveries,
            "skipped_work_avoided": self.skipped_work_avoided,
            "progress_efficiency": round(self.progress_efficiency, 3),
            "trace": self.trace,
            "snapshots": [s.to_dict() for s in self.snapshots],
        }


__all__ = [
    "IterationSnapshot",
    "LoopResult",
    "Status",
    "Task",
]
