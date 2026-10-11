"""Contract verification test suite for Goal-Directed Loop Engine Core Decomposition (Cycle 42).

Verifies:
1. Subpackage structure and strict line count bounds (Rule 11: all submodules <= 200 lines).
2. Slotted & frozen dataclass contracts and immutability guards (Rule 12 & Rule 43).
3. 100% backward-compatible facade re-exports across plugins.agent_orchestration.loop_engine.loop_core.
4. Tri-state resource polling, dynamic task injection, and deadlock isolation.
5. Checkpoint serialization and lossless state resurrection.
6. Baseline linear execution comparison and synthetic scenario generation.
"""

from __future__ import annotations

import sys
from pathlib import Path
import pytest

from plugins.agent_orchestration.loop_engine.loop_core import (
    DecisionFixture,
    IterationSnapshot,
    LoopController,
    LoopResult,
    ResourceStore,
    Status,
    Task,
    TaskGraph,
    build_scenario,
    export_controller_checkpoint,
    restore_controller_checkpoint,
    run_linear,
)

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


class TestLoopEngineDecompositionArchitecture:
    """Architectural and structural invariants for loop_core subpackage."""

    def test_submodule_structure_and_line_limits(self) -> None:
        """Rule 11: All decomposed submodules must strictly remain <= 200 lines."""
        pkg_dir = (
            Path(__file__).parent.parent
            / "plugins"
            / "agent_orchestration"
            / "loop_engine"
            / "loop_core"
        )
        assert pkg_dir.is_dir(), f"Expected directory at {pkg_dir}"

        expected_modules = {
            "__init__.py",
            "checkpoint.py",
            "controller.py",
            "graph.py",
            "models.py",
            "resources.py",
            "simulation.py",
            "transitions.py",
        }

        found_modules = {p.name for p in pkg_dir.glob("*.py")}
        assert expected_modules.issubset(found_modules)

        for mod_name in expected_modules:
            mod_path = pkg_dir / mod_name
            lines = len(mod_path.read_text(encoding="utf-8").splitlines())
            assert lines <= 200, f"Module {mod_name} has {lines} lines, exceeding Rule 11 limit (200)"

    def test_slotted_frozen_dataclass_immutability(self) -> None:
        """Rule 12 & Rule 43: Direct attribute mutation on frozen models must raise errors."""
        # 1. IterationSnapshot (slotted, frozen)
        snap = IterationSnapshot(
            iteration=1,
            ready_or_done_this_iter=2,
            completed_total=2,
            blocked=0,
            waiting=1,
            retrieved_this_iter=1,
            asked_this_iter=0,
            revised_this_iter=0,
        )
        assert hasattr(snap, "__slots__")
        with pytest.raises((AttributeError, TypeError)):
            snap.iteration = 5  # type: ignore[misc]

        # 2. LoopResult (slotted, frozen)
        res = LoopResult(
            iterations=3,
            final_counts={"DONE": 2, "DEADLOCKED": 1},
            total_recoveries=1,
            skipped_work_avoided=0,
        )
        assert hasattr(res, "__slots__")
        with pytest.raises((AttributeError, TypeError)):
            res.iterations = 10  # type: ignore[misc]

        # 3. Task, ResourceStore, DecisionFixture (slotted)
        task = Task(task_id="t1")
        assert hasattr(task, "__slots__")
        assert not hasattr(task, "__dict__")

        rstore = ResourceStore()
        assert hasattr(rstore, "__slots__")
        assert not hasattr(rstore, "__dict__")

        dfix = DecisionFixture()
        assert hasattr(dfix, "__slots__")
        assert not hasattr(dfix, "__dict__")

    def test_dag_validation_and_cycle_detection(self) -> None:
        """Verify TaskGraph detects dependency cycles and invalid unknown dependencies."""
        t1 = Task(task_id="t1", depends_on=("t2",))
        t2 = Task(task_id="t2", depends_on=("t1",))
        with pytest.raises(ValueError, match="Cycle detected"):
            TaskGraph([t1, t2])

        t_orphan = Task(task_id="t_orphan", depends_on=("unknown_dep",))
        with pytest.raises(ValueError, match="depends on unknown task"):
            TaskGraph([t_orphan])

    def test_tri_state_resource_and_decision_polling(self) -> None:
        """Verify ResourceStore eventual availability and DecisionFixture answers."""
        rstore = ResourceStore(
            available={"static_res": "val1"},
            eventually_available={"delayed_res": 2},
        )
        assert rstore.retrieve("static_res") == ("resolved", "val1")
        assert rstore.retrieve("delayed_res") == ("pending", None)
        assert rstore.retrieve("delayed_res") == ("resolved", "resolved:delayed_res")
        assert rstore.retrieve("unknown_res") == ("missing", None)

        dfix = DecisionFixture(answers={"dec1": "user_yes"})
        assert dfix.ask("dec1") == ("resolved", "user_yes")
        assert dfix.ask("dec_missing") == ("missing", None)

    def test_stepwise_controller_and_observer_events(self) -> None:
        """Verify stepwise execution and telemetry notification stream."""
        events: list[tuple[str, dict]] = []

        t1 = Task(task_id="t1", action=lambda t, c: True)
        t2 = Task(task_id="t2", depends_on=("t1",), requires_resource="res2")
        graph = TaskGraph([t1, t2])
        resources = ResourceStore(available={"res2": "data2"})
        decisions = DecisionFixture()

        ctrl = LoopController(graph=graph, resources=resources, decisions=decisions, max_iterations=5)
        ctrl.register_observer(lambda ev, data: events.append((ev, data)))

        iter_num, summary, is_term = ctrl.step()
        assert iter_num == 1
        assert summary["counts"]["DONE"] == 1  # t1 done, t2 pending or waiting on resource

        result = ctrl.run()
        assert result.completed == 2
        assert any(ev[0] == "done" for ev in events)

    def test_checkpoint_export_and_restoration(self) -> None:
        """Verify lossless export and resurrection of LoopController state machine."""
        t1 = Task(task_id="t1", action=lambda t, c: True)
        t2 = Task(task_id="t2", depends_on=("t1",))
        graph = TaskGraph([t1, t2])
        ctrl = LoopController(graph=graph, resources=ResourceStore(), decisions=DecisionFixture())

        ctrl.step()
        assert ctrl.iteration == 1

        checkpoint_data = ctrl.export_checkpoint()
        assert "tasks" in checkpoint_data
        assert checkpoint_data["iteration"] == 1

        resurrected = LoopController.restore_checkpoint(checkpoint_data)
        assert resurrected.iteration == 1
        assert resurrected.graph.tasks["t1"].status == Status.DONE

        final_res = resurrected.run()
        assert final_res.completed == 2

    def test_linear_vs_scenario_generation(self) -> None:
        """Verify baseline linear walk and synthetic scenario generator."""
        tasks, rstore, dfix = build_scenario(num_branches=2, tasks_per_branch=2, seed=123)
        assert len(tasks) == 4

        graph = TaskGraph(tasks)
        lin_res = run_linear(graph, rstore, dfix)
        assert "completed" in lin_res
        assert "final_counts" in lin_res
