"""Simulation scenarios and linear execution baselines for Goal-Directed Loop Engine."""

from __future__ import annotations

import random
import sys
from typing import Any

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


def run_linear(
    graph: TaskGraph,
    resources: ResourceStore,
    decisions: DecisionFixture,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Execute a baseline linear walk of the task graph without retries or recovery loops."""
    context = context if context is not None else {}
    trace: list[str] = []

    visited = set()
    order = []

    def visit(tid: str) -> None:
        if tid in visited:
            return
        visited.add(tid)
        for dep in graph.tasks[tid].depends_on:
            visit(dep)
        order.append(tid)

    for tid in graph.tasks:
        visit(tid)

    for tid in order:
        task = graph.tasks[tid]
        if not graph.dependencies_satisfied(task):
            task.status = Status.DEADLOCKED
            trace.append(f"[{task.task_id}] skipped: dependencies unsatisfied")
            continue

        if task.requires_resource is not None:
            rstatus, val = resources.retrieve(task.requires_resource)
            if rstatus != "resolved":
                task.status = Status.DEADLOCKED
                trace.append(f"[{task.task_id}] linear fail: resource not immediately available")
                continue
            context[task.requires_resource] = val

        if task.requires_decision is not None:
            dstatus, val = decisions.ask(task.requires_decision)
            if dstatus != "resolved":
                task.status = Status.DEADLOCKED
                trace.append(f"[{task.task_id}] linear fail: decision missing")
                continue
            context[task.requires_decision] = val

        task.attempts += 1
        try:
            valid = task.action(task, context) if task.action else True
        except Exception:
            valid = False

        if valid:
            task.status = Status.DONE
            trace.append(f"[{task.task_id}] DONE")
        else:
            task.status = Status.FAILED
            trace.append(f"[{task.task_id}] FAILED (no retry in linear mode)")

    return {
        "completed": graph.counts().get("DONE", 0),
        "final_counts": graph.counts(),
        "trace": trace,
    }


def build_scenario(
    num_branches: int = 4,
    tasks_per_branch: int = 3,
    seed: int = 42,
    failure_mix: dict[str, float] | None = None,
) -> tuple[list[Task], ResourceStore, DecisionFixture]:
    """Generate a synthetic multi-branch task DAG with deterministic failure/recovery distribution."""
    rng = random.Random(seed)
    mix = failure_mix or {
        "clean": 0.35,
        "flaky": 0.20,
        "resource_delay": 0.20,
        "missing_resource": 0.10,
        "decision_ok": 0.10,
        "decision_missing": 0.05,
    }

    tasks: list[Task] = []
    res_avail: dict[str, Any] = {}
    res_eventual: dict[str, int] = {}
    decisions: dict[str, Any] = {}

    for b in range(num_branches):
        prev_id = None
        for step in range(tasks_per_branch):
            tid = f"b{b}_t{step}"
            depends = (prev_id,) if prev_id else ()
            prev_id = tid

            roll = rng.random()
            cum = 0.0
            chosen = "clean"
            for k, prob in mix.items():
                cum += prob
                if roll <= cum:
                    chosen = k
                    break

            req_res = None
            req_dec = None
            action = None

            if chosen == "flaky":
                action = lambda t, c: t.attempts > 1
            elif chosen == "resource_delay":
                rkey = f"res_{tid}"
                req_res = rkey
                res_eventual[rkey] = rng.randint(2, 4)
            elif chosen == "missing_resource":
                req_res = f"missing_{tid}"
            elif chosen == "decision_ok":
                dkey = f"dec_{tid}"
                req_dec = dkey
                decisions[dkey] = f"ans_{tid}"
            elif chosen == "decision_missing":
                req_dec = f"unanswerable_{tid}"

            tasks.append(
                Task(
                    task_id=tid,
                    depends_on=depends,
                    requires_resource=req_res,
                    requires_decision=req_dec,
                    action=action,
                    max_retries=2,
                )
            )

    return tasks, ResourceStore(available=res_avail, eventually_available=res_eventual), DecisionFixture(answers=decisions)


__all__ = [
    "build_scenario",
    "run_linear",
]
