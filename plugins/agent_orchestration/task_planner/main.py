"""Hierarchical DAG Task Planner and Milestone Tracker plugin for Brain Harness."""

from __future__ import annotations

import uuid
from typing import Any

# In-memory plan store
_PLANS: dict[str, dict[str, Any]] = {}


def plan_decompose_goal(
    goal: str,
    subtasks: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Create a new DAG plan for a goal with task dependencies."""
    plan_id = f"plan_{uuid.uuid4().hex[:8]}"

    tasks_dict: dict[str, dict[str, Any]] = {}
    if subtasks:
        for idx, task in enumerate(subtasks, start=1):
            t_id = str(task.get("id") or f"task_{idx}")
            tasks_dict[t_id] = {
                "id": t_id,
                "title": str(task.get("title", f"Task {idx}")),
                "description": str(task.get("description", "")),
                "depends_on": list(task.get("depends_on", [])),
                "status": "pending",
                "result": None,
            }
    else:
        # Default 3-phase decomposition
        tasks_dict = {
            "task_1_research": {
                "id": "task_1_research",
                "title": "Analyze and Research",
                "description": f"Gather context and constraints for: {goal}",
                "depends_on": [],
                "status": "pending",
                "result": None,
            },
            "task_2_execute": {
                "id": "task_2_execute",
                "title": "Implement Changes",
                "description": "Execute the primary modifications",
                "depends_on": ["task_1_research"],
                "status": "pending",
                "result": None,
            },
            "task_3_verify": {
                "id": "task_3_verify",
                "title": "Verify and Validate",
                "description": "Run tests and verify acceptance criteria",
                "depends_on": ["task_2_execute"],
                "status": "pending",
                "result": None,
            },
        }

    _PLANS[plan_id] = {
        "id": plan_id,
        "goal": goal,
        "tasks": tasks_dict,
        "status": "active",
    }

    return {
        "status": "ok",
        "plan_id": plan_id,
        "goal": goal,
        "tasks_count": len(tasks_dict),
        "tasks": list(tasks_dict.values()),
    }


def plan_get_next_milestone(plan_id: str) -> dict[str, Any]:
    """Identify tasks whose dependencies are fully completed and are ready to execute."""
    if plan_id not in _PLANS:
        return {"status": "error", "error": f"Plan '{plan_id}' not found."}

    plan = _PLANS[plan_id]
    tasks = plan["tasks"]

    completed_ids = {t_id for t_id, t in tasks.items() if t["status"] == "completed"}
    ready_tasks: list[dict[str, Any]] = []

    for t in tasks.values():
        if t["status"] == "pending":
            # Check if all dependencies are completed
            deps = t.get("depends_on", [])
            if all(dep in completed_ids for dep in deps):
                ready_tasks.append(t)

    all_completed = len(completed_ids) == len(tasks)
    has_failures = any(t["status"] == "failed" for t in tasks.values())

    return {
        "status": "ok",
        "plan_id": plan_id,
        "unblocked_count": len(ready_tasks),
        "ready_tasks": ready_tasks,
        "all_completed": all_completed,
        "has_failures": has_failures,
    }


def plan_update_status(
    plan_id: str,
    task_id: str,
    status: str,
    result: str | None = None,
) -> dict[str, Any]:
    """Update task status in the plan."""
    if plan_id not in _PLANS:
        return {"status": "error", "error": f"Plan '{plan_id}' not found."}

    plan = _PLANS[plan_id]
    tasks = plan["tasks"]

    if task_id not in tasks:
        return {"status": "error", "error": f"Task '{task_id}' not found in plan '{plan_id}'."}

    valid_statuses = ("pending", "in_progress", "completed", "failed")
    new_status = status.lower()
    if new_status not in valid_statuses:
        return {"status": "error", "error": f"Invalid status: {status}. Must be one of {valid_statuses}."}

    tasks[task_id]["status"] = new_status
    if result is not None:
        tasks[task_id]["result"] = result

    # Check overall plan completion
    if all(t["status"] == "completed" for t in tasks.values()):
        plan["status"] = "completed"
    elif any(t["status"] == "failed" for t in tasks.values()):
        plan["status"] = "failed"
    else:
        plan["status"] = "active"

    return {
        "status": "ok",
        "plan_id": plan_id,
        "task_id": task_id,
        "new_status": new_status,
        "plan_status": plan["status"],
    }


def plan_export_dag(plan_id: str) -> dict[str, Any]:
    """Export the DAG plan in structured JSON and Mermaid graph format."""
    if plan_id not in _PLANS:
        return {"status": "error", "error": f"Plan '{plan_id}' not found."}

    plan = _PLANS[plan_id]
    tasks = plan["tasks"]

    mermaid_lines = ["graph TD"]
    for t_id, t in tasks.items():
        title = t.get("title", t_id).replace('"', "'")
        st = t["status"]
        shape = f'["{t_id}: {title} ({st})"]'
        mermaid_lines.append(f"  {t_id}{shape}")

        for dep in t.get("depends_on", []):
            mermaid_lines.append(f"  {dep} --> {t_id}")

    return {
        "status": "ok",
        "plan_id": plan_id,
        "goal": plan["goal"],
        "plan_status": plan["status"],
        "tasks": list(tasks.values()),
        "mermaid": "\n".join(mermaid_lines),
    }
