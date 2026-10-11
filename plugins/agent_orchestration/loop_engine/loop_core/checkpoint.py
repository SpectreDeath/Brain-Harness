"""State serialization, checkpoint export, and resurrection for LoopController."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any

from plugins.agent_orchestration.loop_engine.loop_core.graph import TaskGraph
from plugins.agent_orchestration.loop_engine.loop_core.models import (
    IterationSnapshot,
    Task,
)
from plugins.agent_orchestration.loop_engine.loop_core.resources import (
    DecisionFixture,
    ResourceStore,
)

if TYPE_CHECKING:
    from plugins.agent_orchestration.loop_engine.loop_core.controller import LoopController

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


def export_controller_checkpoint(ctrl: LoopController) -> dict[str, Any]:
    """Export serialized snapshot of the entire loop controller state."""
    return {
        "iteration": ctrl.iteration,
        "max_iterations": ctrl.max_iterations,
        "total_recoveries": ctrl.total_recoveries,
        "skipped_work_avoided": ctrl.skipped_work_avoided,
        "tasks": [t.to_dict() for t in ctrl.graph.tasks.values()],
        "resources": ctrl.resources.to_dict(),
        "decisions": ctrl.decisions.to_dict(),
        "trace": list(ctrl.trace),
        "snapshots": [s.to_dict() for s in ctrl.snapshots],
    }


def restore_controller_checkpoint(
    cls: type[LoopController],
    data: dict[str, Any],
) -> LoopController:
    """Reconstruct a LoopController from an exported checkpoint dictionary."""
    tasks = [Task.from_dict(t) for t in data["tasks"]]
    graph = TaskGraph(tasks)
    resources = ResourceStore.from_dict(data["resources"])
    decisions = DecisionFixture.from_dict(data["decisions"])
    ctrl = cls(
        graph=graph,
        resources=resources,
        decisions=decisions,
        max_iterations=data.get("max_iterations", 100),
    )
    ctrl.iteration = data.get("iteration", 0)
    ctrl.total_recoveries = data.get("total_recoveries", 0)
    ctrl.skipped_work_avoided = data.get("skipped_work_avoided", 0)
    ctrl.trace = list(data.get("trace", []))
    ctrl.snapshots = [IterationSnapshot.from_dict(s) for s in data.get("snapshots", [])]
    return ctrl


__all__ = [
    "export_controller_checkpoint",
    "restore_controller_checkpoint",
]
