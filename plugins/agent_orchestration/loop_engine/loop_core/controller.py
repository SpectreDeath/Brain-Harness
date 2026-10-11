"""Goal-directed agent loop state machine with stepwise execution and telemetry observers."""

from __future__ import annotations

import sys
from typing import Any, Callable

from plugins.agent_orchestration.loop_engine.loop_core.checkpoint import (
    export_controller_checkpoint,
    restore_controller_checkpoint,
)
from plugins.agent_orchestration.loop_engine.loop_core.graph import TaskGraph
from plugins.agent_orchestration.loop_engine.loop_core.models import (
    IterationSnapshot,
    LoopResult,
    Status,
    Task,
)
from plugins.agent_orchestration.loop_engine.loop_core.resources import (
    DecisionFixture,
    ResourceStore,
)
from plugins.agent_orchestration.loop_engine.loop_core.transitions import evaluate_task_step

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


class LoopController:
    """Goal-directed agent loop state machine with stepwise execution, checkpointing, and dynamic task injection."""

    def __init__(
        self,
        graph: TaskGraph,
        resources: ResourceStore,
        decisions: DecisionFixture,
        max_iterations: int = 100,
    ) -> None:
        self.graph = graph
        self.resources = resources
        self.decisions = decisions
        self.max_iterations = max_iterations
        self.iteration = 0
        self.trace: list[str] = []
        self.snapshots: list[IterationSnapshot] = []
        self.total_recoveries = 0
        self.first_deadlock_completed: int | None = None
        self.skipped_work_avoided = 0
        self._observers: list[Callable[[str, dict[str, Any]], None]] = []

    def register_observer(self, observer: Callable[[str, dict[str, Any]], None]) -> None:
        """Register a callback for telemetry events ('step', 'recovery', 'deadlock', 'done')."""
        self._observers.append(observer)

    def _notify(self, event: str, data: dict[str, Any]) -> None:
        for obs in self._observers:
            try:
                obs(event, data)
            except Exception:
                pass

    def step(self, context: dict[str, Any] | None = None) -> tuple[int, dict[str, Any], bool]:
        """Execute a single iteration of the loop state machine."""
        context = context if context is not None else {}
        if self.graph.is_terminal() or self.iteration >= self.max_iterations:
            return self.iteration, {"status": "exhausted_or_terminal", "counts": self.graph.counts()}, True

        self.iteration += 1
        retrieved = asked = revised = 0

        for task in list(self.graph.tasks.values()):
            if task.status in (Status.DONE, Status.FAILED, Status.DEADLOCKED):
                continue

            outcome = self._step(task, context, self.trace)
            if outcome == "retrieved":
                retrieved += 1
            elif outcome == "asked":
                asked += 1
            elif outcome == "revised":
                revised += 1

        recoveries_this_iter = retrieved + asked
        self.total_recoveries += recoveries_this_iter
        counts = self.graph.counts()
        blocked = counts.get("DEADLOCKED", 0)
        waiting = (
            counts.get("PENDING", 0)
            + counts.get("NEEDS_RESOURCE", 0)
            + counts.get("NEEDS_INPUT", 0)
        )

        if blocked > 0 and self.first_deadlock_completed is None:
            self.first_deadlock_completed = counts.get("DONE", 0)
        if self.first_deadlock_completed is not None:
            self.skipped_work_avoided = counts.get("DONE", 0) - self.first_deadlock_completed

        snapshot = IterationSnapshot(
            iteration=self.iteration,
            ready_or_done_this_iter=counts.get("DONE", 0),
            completed_total=counts.get("DONE", 0),
            blocked=blocked,
            waiting=waiting,
            retrieved_this_iter=retrieved,
            asked_this_iter=asked,
            revised_this_iter=revised,
        )
        self.snapshots.append(snapshot)

        is_term = self.graph.is_terminal() or (self.iteration >= self.max_iterations)
        summary = {
            "iteration": self.iteration,
            "retrieved": retrieved,
            "asked": asked,
            "revised": revised,
            "counts": counts,
            "is_terminal": self.graph.is_terminal(),
        }

        self._notify("step", summary)
        return self.iteration, summary, is_term

    def run(self, context: dict[str, Any] | None = None) -> LoopResult:
        """Run the controller until terminal completion or max_iterations budget exhaustion."""
        context = context if context is not None else {}
        while not self.graph.is_terminal() and self.iteration < self.max_iterations:
            _, _, _ = self.step(context)

        if not self.graph.is_terminal():
            for task in self.graph.tasks.values():
                if task.status not in (Status.DONE, Status.FAILED, Status.DEADLOCKED):
                    task.log("budget exhausted before task could resolve")
                    self.trace.append(f"[{task.task_id}] BUDGET EXHAUSTED (still {task.status.name})")

        return LoopResult(
            iterations=self.iteration,
            final_counts=self.graph.counts(),
            trace=self.trace,
            snapshots=self.snapshots,
            total_recoveries=self.total_recoveries,
            skipped_work_avoided=max(self.skipped_work_avoided, 0),
        )

    def _step(self, task: Task, context: dict[str, Any], trace: list[str]) -> str | None:
        return evaluate_task_step(
            task=task,
            graph=self.graph,
            resources=self.resources,
            decisions=self.decisions,
            context=context,
            trace=trace,
            notifier=self._notify,
        )

    def export_checkpoint(self) -> dict[str, Any]:
        """Export serialized snapshot of the entire loop controller state."""
        return export_controller_checkpoint(self)

    @classmethod
    def restore_checkpoint(cls, data: dict[str, Any]) -> LoopController:
        """Reconstruct a LoopController from an exported checkpoint dictionary."""
        return restore_controller_checkpoint(cls, data)


__all__ = [
    "LoopController",
]
