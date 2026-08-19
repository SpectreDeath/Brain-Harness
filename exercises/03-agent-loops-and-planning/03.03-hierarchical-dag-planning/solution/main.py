"""Exercise 03.03: Hierarchical DAG Task Planning (Solution)."""

from __future__ import annotations

from typing import Any

try:
    from plugins.agent_orchestration.task_planner.main import (
        plan_decompose_goal,
        plan_get_next_milestone,
        plan_update_status,
    )
except ImportError:
    from plugins.task_planner.main import (
        plan_decompose_goal,
        plan_get_next_milestone,
        plan_update_status,
    )


def run_dag_milestones() -> dict[str, Any]:
    subtasks = [
        {"id": "task_a", "title": "Task A", "depends_on": []},
        {"id": "task_b", "title": "Task B", "depends_on": []},
        {"id": "task_c", "title": "Task C", "depends_on": ["task_a", "task_b"]},
    ]

    res = plan_decompose_goal("Parallel build goal", subtasks=subtasks)
    plan_id = res["plan_id"]

    # Initial ready tasks
    init_milestone = plan_get_next_milestone(plan_id)

    # Complete task a and b
    plan_update_status(plan_id, "task_a", "completed")
    plan_update_status(plan_id, "task_b", "completed")

    # Second milestone (task c is now unblocked)
    second_milestone = plan_get_next_milestone(plan_id)

    # Complete task c
    plan_update_status(plan_id, "task_c", "completed")
    final_milestone = plan_get_next_milestone(plan_id)

    return {
        "plan_id": plan_id,
        "initial_unblocked": init_milestone["unblocked_count"],
        "second_unblocked": second_milestone["unblocked_count"],
        "all_completed": final_milestone["all_completed"],
    }
