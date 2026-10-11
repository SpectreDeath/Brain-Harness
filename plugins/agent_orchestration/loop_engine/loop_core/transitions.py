"""Task transition evaluation, tri-state polling, and retry resolution for LoopController."""

from __future__ import annotations

import sys
from typing import Any, Callable

from plugins.agent_orchestration.loop_engine.loop_core.graph import TaskGraph
from plugins.agent_orchestration.loop_engine.loop_core.models import Status, Task
from plugins.agent_orchestration.loop_engine.loop_core.resources import (
    DecisionFixture,
    ResourceStore,
)

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


def evaluate_task_step(
    task: Task,
    graph: TaskGraph,
    resources: ResourceStore,
    decisions: DecisionFixture,
    context: dict[str, Any],
    trace: list[str],
    notifier: Callable[[str, dict[str, Any]], None],
) -> str | None:
    """Evaluate a single task node's dependencies, resources, decisions, and action execution."""
    blocked_dep = graph.blocked_dependency(task)
    if blocked_dep is not None:
        task.status = Status.DEADLOCKED
        task.log(f"deadlocked: dependency {blocked_dep!r} never resolved")
        trace.append(f"[{task.task_id}] DEADLOCKED (blocked by {blocked_dep})")
        notifier("deadlock", {"task_id": task.task_id, "blocked_by": blocked_dep})
        return None

    if not graph.dependencies_satisfied(task):
        task.status = Status.PENDING
        return None

    if task.requires_resource is not None:
        rstatus, value = resources.retrieve(task.requires_resource)
        if rstatus == "resolved":
            context[task.requires_resource] = value
            task.log(f"retrieved resource {task.requires_resource!r}")
            task.requires_resource = None
            notifier("recovery", {"task_id": task.task_id, "resource": task.requires_resource})
            return "retrieved"
        elif rstatus == "pending":
            task.status = Status.NEEDS_RESOURCE
            trace.append(f"[{task.task_id}] waiting on resource (still resolving)")
            return None
        else:
            task.status = Status.DEADLOCKED
            task.log(f"deadlocked: resource {task.requires_resource!r} does not exist")
            trace.append(f"[{task.task_id}] DEADLOCKED (resource permanently missing)")
            return None

    if task.requires_decision is not None:
        dstatus, value = decisions.ask(task.requires_decision)
        if dstatus == "resolved":
            context[task.requires_decision] = value
            task.log(f"resolved decision {task.requires_decision!r}")
            task.requires_decision = None
            notifier("recovery", {"task_id": task.task_id, "decision": task.requires_decision})
            return "asked"
        else:
            task.status = Status.DEADLOCKED
            task.log("deadlocked: decision has no answer available")
            trace.append(f"[{task.task_id}] DEADLOCKED (decision unanswerable)")
            return None

    task.status = Status.READY
    task.attempts += 1
    try:
        valid = task.action(task, context) if task.action else True
    except Exception as exc:
        valid = False
        task.log(f"action raised: {exc!r}")

    if valid:
        task.status = Status.DONE
        task.log(f"done on attempt {task.attempts}")
        trace.append(f"[{task.task_id}] DONE (attempt {task.attempts})")
        notifier("done", {"task_id": task.task_id, "attempts": task.attempts})
        return None

    if task.attempts <= task.max_retries:
        task.status = Status.PENDING
        task.log(f"validation failed on attempt {task.attempts}, retrying")
        trace.append(f"[{task.task_id}] revise: retry {task.attempts}/{task.max_retries}")
        return "revised"
    else:
        task.status = Status.FAILED
        task.log(f"failed permanently after {task.attempts} attempts")
        trace.append(f"[{task.task_id}] FAILED after {task.attempts} attempts")
        return None


__all__ = [
    "evaluate_task_step",
]
