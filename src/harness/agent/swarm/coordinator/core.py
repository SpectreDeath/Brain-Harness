"""Authoritative Swarm Coordinator orchestrating multi-agent DAGs with token governance."""

from __future__ import annotations

from collections.abc import Callable
import time
from typing import Any
import uuid

import structlog

from harness.agent.swarm.governor import TokenGovernor
from harness.agent.swarm.models import (
    SwarmDAG,
    SwarmNode,
    SwarmNodeExecution,
    SwarmTaskResult,
    SwarmWaveMetrics,
)
from harness.events.bus import EventBus
from harness.events.types import EventType, HarnessEvent
from harness.kernel.context import ServiceContext, ServiceKey

from .decomposition import decompose_objective, decompose_objective_with_skills
from .history import (
    analyze_run_metrics,
    build_status_summary,
    get_run_async_with_fallback,
    get_run_from_cache,
    get_run_session_tree_hierarchy,
    list_runs_async_with_fallback,
    list_runs_cached,
)
from .outcome import finalize_swarm_outcome
from .wave_runner import execute_swarm_wave, init_swarm_session

logger = structlog.get_logger()

SWARM_COORDINATOR_KEY: ServiceKey[SwarmCoordinator] = ServiceKey("agent.swarm")


class SwarmCoordinator:
    """Authoritative coordinator executing multi-agent swarm DAGs with token governance."""

    def __init__(self, context: ServiceContext, event_bus: EventBus | None = None) -> None:
        self.context = context
        self.event_bus = event_bus
        self._active_runs: dict[str, dict[str, Any]] = {}
        self._run_history: dict[str, SwarmTaskResult] = {}

    def _emit(self, event_type: EventType | str, payload: dict[str, Any]) -> None:
        if self.event_bus is not None:
            et = event_type if isinstance(event_type, EventType) else EventType.CUSTOM
            self.event_bus.emit_sync(HarnessEvent(event_type=et, source="agent.swarm", payload=payload))

    def decompose(self, objective: str, agents: list[dict[str, Any]] | None = None) -> SwarmDAG:
        """Decompose a high-level objective into a structured SwarmDAG."""
        return decompose_objective(objective, agents)

    def decompose_with_skills(
        self,
        objective: str,
        skill_names: list[str] | None = None,
        top_k: int = 3,
        include_verifier: bool = True,
    ) -> SwarmDAG:
        """Decompose a high-level objective into a structured SwarmDAG derived from agent skills."""
        return decompose_objective_with_skills(
            context=self.context,
            objective=objective,
            skill_names=skill_names,
            top_k=top_k,
            include_verifier=include_verifier,
        )

    async def dispatch_skill_swarm(
        self,
        objective: str,
        skill_names: list[str] | None = None,
        *,
        max_total_tokens: int = 100_000,
        context: dict[str, Any] | None = None,
        custom_executor: Callable[[SwarmNode, dict[str, Any]], Any] | None = None,
        run_id: str | None = None,
        consensus_threshold: float = 0.66,
        include_verifier: bool = True,
    ) -> SwarmTaskResult:
        """Decompose objective into a skill-driven SwarmDAG and execute with token governance."""
        dag = self.decompose_with_skills(objective, skill_names=skill_names, include_verifier=include_verifier)
        return await self.run_swarm(
            dag=dag, objective=objective, max_total_tokens=max_total_tokens,
            context=context, custom_executor=custom_executor, run_id=run_id,
            consensus_threshold=consensus_threshold,
        )

    async def run_swarm(
        self,
        dag_or_objective: SwarmDAG | str | None = None,
        *,
        objective: str | None = None,
        dag: SwarmDAG | None = None,
        max_total_tokens: int = 100_000,
        max_tokens: int | None = None,
        context: dict[str, Any] | None = None,
        custom_executor: Callable[[SwarmNode, dict[str, Any]], Any] | None = None,
        run_id: str | None = None,
        consensus_threshold: float = 0.66,
    ) -> SwarmTaskResult:
        """Execute all nodes in the Swarm DAG in topological dependency waves."""
        target = dag_or_objective if dag_or_objective is not None else (dag if dag is not None else objective)
        if target is None:
            raise ValueError("Either dag or objective must be provided to run_swarm")

        effective_max = max_tokens if max_tokens is not None else max_total_tokens
        actual_id = run_id or f"swarm_{uuid.uuid4().hex[:8]}"

        if isinstance(target, str):
            dag = self.decompose(target)
            objective = target
        else:
            dag = target
            objective = objective or "Custom Swarm DAG Execution"

        governor = TokenGovernor(max_tokens=effective_max)
        plan = dag.get_execution_plan()
        accumulated: dict[str, Any] = {}

        session_mgr, graph_svc = await init_swarm_session(self.context, actual_id, objective, dag, plan, context)
        self._active_runs[actual_id] = {
            "run_id": actual_id, "objective": objective, "status": "running",
            "nodes_total": len(dag.nodes), "waves_total": len(plan),
        }
        self._emit(EventType.AGENT_TASK_STARTED, {
            "run_id": actual_id, "objective": objective, "waves": len(plan), "nodes": len(dag.nodes),
        })

        all_ok, t0 = True, time.time()
        node_execs: dict[str, SwarmNodeExecution] = {}
        wave_metrics: list[SwarmWaveMetrics] = []

        try:
            for w_idx, w_nodes in enumerate(plan, start=1):
                logger.info("Executing swarm wave", run_id=actual_id, wave=w_idx, nodes=w_nodes)
                wave_ok = await execute_swarm_wave(
                    w_idx, w_nodes, dag, actual_id, governor, accumulated,
                    node_execs, wave_metrics, self.context, session_mgr, graph_svc, custom_executor,
                )
                if not wave_ok:
                    all_ok = False

            result = await finalize_swarm_outcome(
                actual_id, objective, governor, accumulated, node_execs,
                wave_metrics, t0, all_ok, session_mgr, graph_svc,
            )
            evt = EventType.AGENT_TASK_COMPLETED if all_ok else EventType.AGENT_TASK_FAILED
            self._emit(evt, result.to_dict())
            self._run_history[actual_id] = result
            return result
        finally:
            self._active_runs.pop(actual_id, None)

    execute_dag = run_swarm

    def get_run(self, run_id: str) -> SwarmTaskResult | None:
        """Fetch a completed or archived swarm run by ID from in-memory cache."""
        return get_run_from_cache(self._run_history, run_id)

    async def get_run_async(self, run_id: str) -> SwarmTaskResult | dict[str, Any] | None:
        """Fetch a completed swarm run by ID, falling back to persistent session store."""
        return await get_run_async_with_fallback(self._run_history, self.context, run_id)

    def analyze_run(self, run_id: str) -> dict[str, Any] | None:
        """Fetch post-flight execution analytics and critical path breakdown for a run."""
        return analyze_run_metrics(self._run_history, run_id)

    async def get_run_session_tree(self, run_id: str) -> dict[str, Any] | None:
        """Retrieve full hierarchical execution session tree for a swarm run."""
        return await get_run_session_tree_hierarchy(self._run_history, self.context, run_id)

    def list_runs(self, limit: int = 50) -> list[SwarmTaskResult]:
        """List historical swarm execution outcomes from in-memory cache."""
        return list_runs_cached(self._run_history, limit)

    async def list_runs_async(self, limit: int = 50) -> list[dict[str, Any]]:
        """List historical swarm execution outcomes from memory and persistent session store."""
        return await list_runs_async_with_fallback(self._run_history, self.context, limit)

    async def get_status(self) -> dict[str, Any]:
        """Return status report of the swarm coordinator."""
        return build_status_summary(self._run_history, self._active_runs)
