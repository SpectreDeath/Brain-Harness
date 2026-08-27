"""Tests for Domain: Loop Engine plugin (Goal-Directed Task DAG Controller)."""

from __future__ import annotations

from pathlib import Path

import pytest

from harness.creator.validator import PluginValidator
from plugins.agent_orchestration.loop_engine.loop_core import (
    DecisionFixture,
    LoopController,
    ResourceStore,
    Status,
    Task,
    TaskGraph,
)
from plugins.agent_orchestration.loop_engine.main import (
    LOOP_ENGINE_SERVICE_KEY,
    LoopEngineService,
    benchmark_loop_vs_linear,
    create_scenario_graph,
    export_loop_checkpoint,
    run_loop,
    step_loop,
    validate_task_dag,
)


@pytest.mark.unit
class TestLoopEnginePlugin:
    def test_dag_cycle_detection(self) -> None:
        cyclic_tasks = [
            {"task_id": "a", "depends_on": ["b"]},
            {"task_id": "b", "depends_on": ["a"]},
        ]
        res = validate_task_dag(cyclic_tasks)
        assert res["status"] == "ok"
        assert res["valid"] is False
        assert "Cycle detected" in res["error"]

    def test_run_loop_branch_isolation_and_recovery(self) -> None:
        tasks = [
            {"task_id": "b1_task", "requires_resource": "nonexistent_resource"},
            {"task_id": "b1_downstream", "depends_on": ["b1_task"]},
            {"task_id": "b2_task", "requires_resource": "delayed_res"},
            {"task_id": "b3_clean"},
        ]

        res = run_loop(
            tasks=tasks,
            eventually_available_resources={"delayed_res": 2},
            max_iterations=10,
        )

        assert res["status"] == "ok"
        result = res["result"]
        assert result["completed"] == 2
        final_counts = result["final_counts"]
        assert final_counts.get("DEADLOCKED", 0) == 2
        assert final_counts.get("DONE", 0) == 2
        assert result["total_recoveries"] >= 1
        assert "checkpoint" in res

    def test_stepwise_execution_and_checkpoint_resume(self) -> None:
        tasks = [
            {"task_id": "t1", "requires_resource": "db_conn"},
            {"task_id": "t2", "depends_on": ["t1"]},
        ]
        exp = export_loop_checkpoint(tasks, eventually_available_resources={"db_conn": 2})
        assert exp["status"] == "ok"
        chk = exp["checkpoint"]

        # Step 1: polls db_conn -> pending
        step1 = step_loop(chk)
        assert step1["status"] == "ok"
        assert step1["iteration"] == 1
        assert step1["is_terminal"] is False

        # Step 2: polls db_conn -> resolved! t1 becomes ready and done
        step2 = step_loop(step1["checkpoint"])
        assert step2["status"] == "ok"
        assert step2["iteration"] == 2

        # Step 3: t2 runs -> done -> terminal!
        step3 = step_loop(step2["checkpoint"])
        assert step3["status"] == "ok"
        assert step3["is_terminal"] is True

    def test_dynamic_task_injection(self) -> None:
        tasks = [{"task_id": "root_task"}]
        exp = export_loop_checkpoint(tasks)
        chk = exp["checkpoint"]

        # Inject child task at step 1
        new_child = {"task_id": "dynamic_child", "depends_on": ["root_task"]}
        step_res = step_loop(chk, new_tasks=[new_child])
        assert step_res["status"] == "ok"
        # Both root and dynamic child will be processed
        chk_after = step_res["checkpoint"]
        task_ids = [t["task_id"] for t in chk_after["tasks"]]
        assert "dynamic_child" in task_ids

    def test_benchmark_tool(self) -> None:
        bench = benchmark_loop_vs_linear(num_scenarios=5, seed=42, max_iterations=50)
        assert bench["status"] == "ok"
        assert bench["scenarios_evaluated"] == 5
        assert bench["loop_controller"]["completion_rate_pct"] >= bench["linear_baseline"]["completion_rate_pct"]

    def test_create_scenario_graph(self) -> None:
        sc = create_scenario_graph(num_branches=3, tasks_per_branch=2, seed=123)
        assert sc["status"] == "ok"
        assert sc["total_tasks"] == 6

    def test_service_facade_and_service_key(self) -> None:
        svc = LoopEngineService()
        val = svc.validate([{"task_id": "t1"}])
        assert val["valid"] is True
        assert LOOP_ENGINE_SERVICE_KEY.name == "domain.loop_engine"

    @pytest.mark.asyncio
    async def test_plugin_validator_compliance(self) -> None:
        plugin_dir = Path("plugins/agent_orchestration/loop_engine")
        report = await PluginValidator.validate(plugin_dir)
        assert report.valid, f"Validation errors: {report.errors}"
        assert len(report.errors) == 0
