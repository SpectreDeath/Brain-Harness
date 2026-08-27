"""Main entrypoint and typed tool registrations for Goal-Directed Loop Engine plugin."""

from __future__ import annotations

from typing import Any

import structlog

from harness.kernel.context import ServiceKey
from plugins.agent_orchestration.loop_engine.loop_core import (
    DecisionFixture,
    LoopController,
    ResourceStore,
    Task,
    TaskGraph,
    build_scenario,
    run_linear,
)

logger = structlog.get_logger()


def _dict_to_task(d: dict[str, Any]) -> Task:
    return Task.from_dict(d)


def run_loop(
    tasks: list[dict[str, Any]],
    available_resources: dict[str, Any] | None = None,
    eventually_available_resources: dict[str, int] | None = None,
    decision_answers: dict[str, Any] | None = None,
    max_iterations: int = 100,
    initial_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Execute a goal-directed task DAG loop with tri-state resource polling and deadlock isolation.

    Args:
        tasks: List of task definitions (task_id, depends_on, requires_resource, requires_decision, max_retries).
        available_resources: Dictionary of immediately available resources.
        eventually_available_resources: Dictionary mapping resource keys to polling attempts required.
        decision_answers: Predefined decision lookup table.
        max_iterations: Maximum iteration safety budget.
        initial_context: Initial execution context dictionary.

    Returns:
        Structured LoopResult dictionary with trace, snapshots, completed count, and recoveries.
    """
    if not tasks:
        return {"status": "error", "error": "Task list cannot be empty"}

    try:
        task_objs = [_dict_to_task(t) for t in tasks]
        graph = TaskGraph(task_objs)
    except Exception as e:
        logger.error("invalid_task_dag", error=str(e))
        return {"status": "error", "error": f"Invalid task graph: {e}"}

    resources = ResourceStore(
        available=dict(available_resources or {}),
        eventually_available=dict(eventually_available_resources or {}),
    )
    decisions = DecisionFixture(answers=dict(decision_answers or {}))

    controller = LoopController(
        graph=graph,
        resources=resources,
        decisions=decisions,
        max_iterations=max_iterations,
    )

    result = controller.run(context=dict(initial_context or {}))
    return {
        "status": "ok",
        "result": result.to_dict(),
        "task_states": {t.task_id: t.to_dict() for t in graph.tasks.values()},
        "checkpoint": controller.export_checkpoint(),
    }


def step_loop(
    checkpoint: dict[str, Any],
    context: dict[str, Any] | None = None,
    new_tasks: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Execute a single iteration step on an existing loop checkpoint, optionally injecting dynamic tasks.

    Args:
        checkpoint: Serialized loop checkpoint dictionary.
        context: Context variables to supply or update.
        new_tasks: Optional list of dynamic tasks to inject before the step.

    Returns:
        Step execution summary, updated checkpoint, and terminal status.
    """
    try:
        controller = LoopController.restore_checkpoint(checkpoint)
        if new_tasks:
            for nt in new_tasks:
                controller.graph.add_dynamic_task(_dict_to_task(nt))

        iter_num, summary, is_term = controller.step(context=context)
        return {
            "status": "ok",
            "iteration": iter_num,
            "summary": summary,
            "is_terminal": is_term,
            "checkpoint": controller.export_checkpoint(),
        }
    except Exception as e:
        logger.error("step_loop_failed", error=str(e))
        return {"status": "error", "error": str(e)}


def export_loop_checkpoint(
    tasks: list[dict[str, Any]],
    available_resources: dict[str, Any] | None = None,
    eventually_available_resources: dict[str, int] | None = None,
    decision_answers: dict[str, Any] | None = None,
    max_iterations: int = 100,
) -> dict[str, Any]:
    """Initialize and export a pristine loop state checkpoint without running it."""
    try:
        task_objs = [_dict_to_task(t) for t in tasks]
        graph = TaskGraph(task_objs)
        resources = ResourceStore(
            available=dict(available_resources or {}),
            eventually_available=dict(eventually_available_resources or {}),
        )
        decisions = DecisionFixture(answers=dict(decision_answers or {}))
        controller = LoopController(
            graph=graph,
            resources=resources,
            decisions=decisions,
            max_iterations=max_iterations,
        )
        return {
            "status": "ok",
            "checkpoint": controller.export_checkpoint(),
        }
    except Exception as e:
        logger.error("export_checkpoint_failed", error=str(e))
        return {"status": "error", "error": str(e)}


def validate_task_dag(tasks: list[dict[str, Any]]) -> dict[str, Any]:
    """Validate task DAG for cyclic dependencies, missing task IDs, and structural correctness.

    Args:
        tasks: List of task definitions to validate.

    Returns:
        Validation status, task counts, and any detected errors.
    """
    if not tasks:
        return {"status": "error", "error": "Task list is empty"}

    try:
        task_objs = [_dict_to_task(t) for t in tasks]
        graph = TaskGraph(task_objs)
        return {
            "status": "ok",
            "valid": True,
            "total_tasks": len(graph.tasks),
            "task_ids": list(graph.tasks.keys()),
        }
    except Exception as e:
        return {
            "status": "ok",
            "valid": False,
            "error": str(e),
        }


def benchmark_loop_vs_linear(
    num_scenarios: int = 10,
    seed: int = 42,
    max_iterations: int = 100,
) -> dict[str, Any]:
    """Benchmark goal-directed LoopController against one-shot linear baseline across failure topologies.

    Args:
        num_scenarios: Number of seeded scenarios to evaluate.
        seed: Base random seed.
        max_iterations: Maximum iteration budget per scenario.

    Returns:
        Aggregated comparative metrics for loop controller vs linear baseline.
    """
    loop_completed = 0
    linear_completed = 0
    total_tasks = 0
    total_recoveries = 0
    total_skipped_work_saved = 0

    for i in range(num_scenarios):
        sc_seed = seed + i
        tasks_l, res_l, dec_l = build_scenario(num_branches=4, tasks_per_branch=3, seed=sc_seed)
        tasks_lin, res_lin, dec_lin = build_scenario(num_branches=4, tasks_per_branch=3, seed=sc_seed)

        total_tasks += len(tasks_l)

        # Run Loop Controller
        g_l = TaskGraph(tasks_l)
        ctrl = LoopController(g_l, res_l, dec_l, max_iterations=max_iterations)
        l_res = ctrl.run()
        loop_completed += l_res.completed
        total_recoveries += l_res.total_recoveries
        total_skipped_work_saved += l_res.skipped_work_avoided

        # Run Linear Baseline
        g_lin = TaskGraph(tasks_lin)
        lin_res = run_linear(g_lin, res_lin, dec_lin)
        linear_completed += lin_res["completed"]

    loop_rate = round(100.0 * loop_completed / total_tasks, 2) if total_tasks else 0.0
    linear_rate = round(100.0 * linear_completed / total_tasks, 2) if total_tasks else 0.0

    return {
        "status": "ok",
        "scenarios_evaluated": num_scenarios,
        "total_tasks": total_tasks,
        "loop_controller": {
            "completed_tasks": loop_completed,
            "completion_rate_pct": loop_rate,
            "total_recoveries": total_recoveries,
            "skipped_work_saved": total_skipped_work_saved,
        },
        "linear_baseline": {
            "completed_tasks": linear_completed,
            "completion_rate_pct": linear_rate,
        },
        "relative_improvement_pct": round(loop_rate - linear_rate, 2),
    }


def create_scenario_graph(
    num_branches: int = 4,
    tasks_per_branch: int = 3,
    seed: int = 42,
    failure_mix: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Generate a synthetic task graph scenario with controlled failure and latency injection.

    Args:
        num_branches: Number of independent workflow branches.
        tasks_per_branch: Number of sequential tasks per branch.
        seed: Random seed for deterministic generation.
        failure_mix: Custom probability weights for failure modes.

    Returns:
        Structured scenario dictionary with tasks, resources, and decision fixtures.
    """
    tasks, resources, decisions = build_scenario(
        num_branches=num_branches,
        tasks_per_branch=tasks_per_branch,
        seed=seed,
        failure_mix=failure_mix,
    )
    return {
        "status": "ok",
        "total_tasks": len(tasks),
        "tasks": [t.to_dict() for t in tasks],
        "available_resources": resources.available,
        "eventually_available_resources": resources.eventually_available,
        "decision_answers": decisions.answers,
    }


class LoopEngineService:
    """Service provider for Goal-Directed Loop Engineering."""

    def run(
        self,
        tasks: list[dict[str, Any]],
        available_resources: dict[str, Any] | None = None,
        eventually_available_resources: dict[str, int] | None = None,
        decision_answers: dict[str, Any] | None = None,
        max_iterations: int = 100,
        initial_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return run_loop(
            tasks,
            available_resources=available_resources,
            eventually_available_resources=eventually_available_resources,
            decision_answers=decision_answers,
            max_iterations=max_iterations,
            initial_context=initial_context,
        )

    def step(
        self,
        checkpoint: dict[str, Any],
        context: dict[str, Any] | None = None,
        new_tasks: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        return step_loop(checkpoint, context=context, new_tasks=new_tasks)

    def export_checkpoint(
        self,
        tasks: list[dict[str, Any]],
        available_resources: dict[str, Any] | None = None,
        eventually_available_resources: dict[str, int] | None = None,
        decision_answers: dict[str, Any] | None = None,
        max_iterations: int = 100,
    ) -> dict[str, Any]:
        return export_loop_checkpoint(
            tasks=tasks,
            available_resources=available_resources,
            eventually_available_resources=eventually_available_resources,
            decision_answers=decision_answers,
            max_iterations=max_iterations,
        )

    def validate(self, tasks: list[dict[str, Any]]) -> dict[str, Any]:
        return validate_task_dag(tasks)

    def benchmark(self, num_scenarios: int = 10, seed: int = 42, max_iterations: int = 100) -> dict[str, Any]:
        return benchmark_loop_vs_linear(num_scenarios=num_scenarios, seed=seed, max_iterations=max_iterations)

    def generate_scenario(
        self,
        num_branches: int = 4,
        tasks_per_branch: int = 3,
        seed: int = 42,
        failure_mix: dict[str, float] | None = None,
    ) -> dict[str, Any]:
        return create_scenario_graph(
            num_branches=num_branches,
            tasks_per_branch=tasks_per_branch,
            seed=seed,
            failure_mix=failure_mix,
        )


LOOP_ENGINE_SERVICE_KEY = ServiceKey[LoopEngineService]("domain.loop_engine")
