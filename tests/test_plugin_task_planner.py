"""Tests for task_planner plugin."""

from __future__ import annotations

import pytest

from plugins.agent_orchestration.task_planner.main import (
    plan_decompose_goal,
    plan_export_dag,
    plan_get_next_milestone,
    plan_update_status,
)


@pytest.mark.unit
class TestTaskPlannerPlugin:
    def test_default_plan_lifecycle(self) -> None:
        # Create plan
        res_create = plan_decompose_goal("Implement new authentication system")
        assert res_create["status"] == "ok"
        plan_id = res_create["plan_id"]
        assert res_create["tasks_count"] == 3

        # Next milestone should be task_1_research
        res_next = plan_get_next_milestone(plan_id)
        assert res_next["status"] == "ok"
        assert res_next["unblocked_count"] == 1
        assert res_next["ready_tasks"][0]["id"] == "task_1_research"

        # Complete task 1
        plan_update_status(plan_id, "task_1_research", "completed", result="Research complete")

        # Next milestone should now be task_2_execute
        res_next2 = plan_get_next_milestone(plan_id)
        assert res_next2["unblocked_count"] == 1
        assert res_next2["ready_tasks"][0]["id"] == "task_2_execute"

        # Complete remaining tasks
        plan_update_status(plan_id, "task_2_execute", "completed")
        plan_update_status(plan_id, "task_3_verify", "completed")

        res_final = plan_get_next_milestone(plan_id)
        assert res_final["all_completed"] is True
        assert res_final["unblocked_count"] == 0

    def test_custom_dag_plan_and_export(self) -> None:
        subtasks = [
            {"id": "step_a", "title": "Step A", "depends_on": []},
            {"id": "step_b", "title": "Step B", "depends_on": []},
            {"id": "step_c", "title": "Step C", "depends_on": ["step_a", "step_b"]},
        ]
        res = plan_decompose_goal("Parallel build", subtasks=subtasks)
        plan_id = res["plan_id"]

        # Initially step_a and step_b are both ready in parallel
        ready = plan_get_next_milestone(plan_id)
        assert ready["unblocked_count"] == 2
        ready_ids = {t["id"] for t in ready["ready_tasks"]}
        assert ready_ids == {"step_a", "step_b"}

        # Export Mermaid DAG
        dag = plan_export_dag(plan_id)
        assert dag["status"] == "ok"
        assert "graph TD" in dag["mermaid"]
        assert "step_a --> step_c" in dag["mermaid"]
        assert "step_b --> step_c" in dag["mermaid"]
