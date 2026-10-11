"""Task graph representation and DAG cycle validation for Goal-Directed Loop Engine."""

from __future__ import annotations

import sys
from plugins.agent_orchestration.loop_engine.loop_core.models import Status, Task

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


class TaskGraph:
    """Directed Acyclic Graph (DAG) of task execution nodes with dependency verification."""

    def __init__(self, tasks: list[Task]) -> None:
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
        """Check if all direct dependencies of a task have completed successfully."""
        return all(self.tasks[d].status == Status.DONE for d in task.depends_on)

    def blocked_dependency(self, task: Task) -> str | None:
        """Return the identifier of any dependency in a terminal failure/deadlock state."""
        for d in task.depends_on:
            dep = self.tasks[d]
            if dep.status in (Status.FAILED, Status.DEADLOCKED):
                return d
        return None

    def counts(self) -> dict[str, int]:
        """Return counts of tasks partitioned by Status name."""
        out: dict[str, int] = {}
        for t in self.tasks.values():
            out[t.status.name] = out.get(t.status.name, 0) + 1
        return out

    def is_terminal(self) -> bool:
        """Check if all tasks have reached a terminal state (DONE, FAILED, DEADLOCKED)."""
        return all(
            t.status in (Status.DONE, Status.FAILED, Status.DEADLOCKED)
            for t in self.tasks.values()
        )


__all__ = [
    "TaskGraph",
]
