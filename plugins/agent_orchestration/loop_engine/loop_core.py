"""Core Goal-Directed Loop Engine: Task Graph DAG, Tri-State Polling, Stepwise Control, and Checkpointing."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable


class Status(Enum):
    PENDING = auto()         # not yet attempted or waiting on upstream
    NEEDS_RESOURCE = auto()  # blocked on a missing resource, retrieve() may help
    NEEDS_INPUT = auto()     # blocked on ambiguity, ask() may help
    READY = auto()           # dependencies satisfied, can attempt action
    DONE = auto()            # completed and validated
    FAILED = auto()          # exhausted retries, permanently failed
    DEADLOCKED = auto()      # unresolvable block (missing resource/decision or deadlocked upstream)


@dataclass
class Task:
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


class TaskGraph:
    def __init__(self, tasks: list[Task]):
        self.tasks: dict[str, Task] = {t.task_id: t for t in tasks}
        self._validate_dag()

    def _validate_dag(self) -> None:
        visiting, visited = set(), set()

        def dfs(tid: str) -> None:
            if tid in visited:
                return
            if tid in visiting:
                raise ValueError(f"Cycle detected involving task {tid!r}")
            visiting.add(tid)
            for dep in self.tasks[tid].depends_on:
                if dep not in self.tasks:
                    raise ValueError(f"Task {tid!r} depends on unknown task {dep!r}")
                dfs(dep)
            visiting.remove(tid)
            visited.add(tid)

        for tid in self.tasks:
            dfs(tid)

    def add_dynamic_task(self, task: Task) -> None:
        """Dynamically register a new task into the graph during execution."""
        if task.task_id in self.tasks:
            raise ValueError(f"Task {task.task_id!r} already exists in graph")
        self.tasks[task.task_id] = task
        self._validate_dag()

    def add_dependency(self, task_id: str, depends_on_id: str) -> None:
        """Dynamically add a dependency edge."""
        if task_id not in self.tasks:
            raise ValueError(f"Task {task_id!r} not found")
        if depends_on_id not in self.tasks:
            raise ValueError(f"Dependency task {depends_on_id!r} not found")
        task = self.tasks[task_id]
        if depends_on_id not in task.depends_on:
            task.depends_on = (*task.depends_on, depends_on_id)
            self._validate_dag()

    def dependencies_satisfied(self, task: Task) -> bool:
        return all(self.tasks[d].status == Status.DONE for d in task.depends_on)

    def blocked_dependency(self, task: Task) -> str | None:
        for d in task.depends_on:
            dep = self.tasks[d]
            if dep.status in (Status.FAILED, Status.DEADLOCKED):
                return d
        return None

    def counts(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for t in self.tasks.values():
            out[t.status.name] = out.get(t.status.name, 0) + 1
        return out

    def is_terminal(self) -> bool:
        return all(
            t.status in (Status.DONE, Status.FAILED, Status.DEADLOCKED)
            for t in self.tasks.values()
        )


@dataclass
class ResourceStore:
    available: dict[str, Any] = field(default_factory=dict)
    eventually_available: dict[str, int] = field(default_factory=dict)
    _poll_counts: dict[str, int] = field(default_factory=dict)

    def retrieve(self, key: str) -> tuple[str, Any]:
        if key in self.available:
            return "resolved", self.available[key]
        if key in self.eventually_available:
            self._poll_counts[key] = self._poll_counts.get(key, 0) + 1
            if self._poll_counts[key] >= self.eventually_available[key]:
                value = f"resolved:{key}"
                self.available[key] = value
                return "resolved", value
            return "pending", None
        return "missing", None

    def to_dict(self) -> dict[str, Any]:
        return {
            "available": dict(self.available),
            "eventually_available": dict(self.eventually_available),
            "poll_counts": dict(self._poll_counts),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> ResourceStore:
        return cls(
            available=dict(d.get("available", {})),
            eventually_available=dict(d.get("eventually_available", {})),
            _poll_counts=dict(d.get("poll_counts", {})),
        )


@dataclass
class DecisionFixture:
    answers: dict[str, Any] = field(default_factory=dict)

    def ask(self, key: str) -> tuple[str, Any]:
        if key in self.answers:
            return "resolved", self.answers[key]
        return "missing", None

    def to_dict(self) -> dict[str, Any]:
        return {"answers": dict(self.answers)}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> DecisionFixture:
        return cls(answers=dict(d.get("answers", {})))


@dataclass
class IterationSnapshot:
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


@dataclass
class LoopResult:
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


class LoopController:
    """Goal-directed agent loop state machine with stepwise execution, checkpointing, and dynamic task injection."""

    def __init__(
        self,
        graph: TaskGraph,
        resources: ResourceStore,
        decisions: DecisionFixture,
        max_iterations: int = 100,
    ):
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
        """Execute a single iteration of the loop state machine.

        Returns:
            (iteration_number, step_summary_dict, is_terminal_or_exhausted)
        """
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
        blocked_dep = self.graph.blocked_dependency(task)
        if blocked_dep is not None:
            task.status = Status.DEADLOCKED
            task.log(f"deadlocked: dependency {blocked_dep!r} never resolved")
            trace.append(f"[{task.task_id}] DEADLOCKED (blocked by {blocked_dep})")
            self._notify("deadlock", {"task_id": task.task_id, "blocked_by": blocked_dep})
            return None

        if not self.graph.dependencies_satisfied(task):
            task.status = Status.PENDING
            return None

        if task.requires_resource is not None:
            rstatus, value = self.resources.retrieve(task.requires_resource)
            if rstatus == "resolved":
                context[task.requires_resource] = value
                task.log(f"retrieved resource {task.requires_resource!r}")
                task.requires_resource = None
                self._notify("recovery", {"task_id": task.task_id, "resource": task.requires_resource})
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
            dstatus, value = self.decisions.ask(task.requires_decision)
            if dstatus == "resolved":
                context[task.requires_decision] = value
                task.log(f"resolved decision {task.requires_decision!r}")
                task.requires_decision = None
                self._notify("recovery", {"task_id": task.task_id, "decision": task.requires_decision})
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
            self._notify("done", {"task_id": task.task_id, "attempts": task.attempts})
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

    def export_checkpoint(self) -> dict[str, Any]:
        """Export serialized snapshot of the entire loop controller state."""
        return {
            "iteration": self.iteration,
            "max_iterations": self.max_iterations,
            "total_recoveries": self.total_recoveries,
            "skipped_work_avoided": self.skipped_work_avoided,
            "tasks": [t.to_dict() for t in self.graph.tasks.values()],
            "resources": self.resources.to_dict(),
            "decisions": self.decisions.to_dict(),
            "trace": list(self.trace),
            "snapshots": [s.to_dict() for s in self.snapshots],
        }

    @classmethod
    def restore_checkpoint(cls, data: dict[str, Any]) -> LoopController:
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


def run_linear(graph: TaskGraph, resources: ResourceStore, decisions: DecisionFixture, context: dict[str, Any] | None = None) -> dict[str, Any]:
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
