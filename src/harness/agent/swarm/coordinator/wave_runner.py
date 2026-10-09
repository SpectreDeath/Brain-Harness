"""Wave execution orchestrator running topological batches concurrently."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
import time
from typing import Any

from harness.agent.session import AGENT_SESSION_MANAGER_KEY, AgentSessionManager
from harness.agent.swarm.governor import TokenGovernor
from harness.agent.swarm.models import (
    SwarmDAG,
    SwarmNode,
    SwarmNodeExecution,
    SwarmWaveMetrics,
)
from harness.kernel.context import ServiceContext
from harness.services.agent_graph import (
    AGENT_GRAPH_STORE_KEY,
    AgentExecutionGraphService,
)

from .node_runner import execute_swarm_node


async def init_swarm_session(
    context: ServiceContext,
    actual_run_id: str,
    objective: str,
    dag: SwarmDAG,
    execution_plan: list[list[str]],
    run_context: dict[str, Any] | None,
) -> tuple[AgentSessionManager | None, AgentExecutionGraphService | None]:
    """Initialize root session in hierarchical session manager or graph store."""
    session_mgr: AgentSessionManager | None = context.optional(AGENT_SESSION_MANAGER_KEY)
    graph_svc: AgentExecutionGraphService | None = context.optional(AGENT_GRAPH_STORE_KEY)
    meta = {
        "is_swarm": True,
        "nodes_total": len(dag.nodes),
        "waves_total": len(execution_plan),
        **(run_context or {}),
    }
    if session_mgr is not None:
        await session_mgr.create_session(task=objective, session_id=actual_run_id, metadata=meta)
    elif graph_svc is not None:
        graph_svc.register_thread(node_id=actual_run_id, role="swarm_coordinator", task=objective, metadata=meta)
    return session_mgr, graph_svc


async def execute_swarm_wave(
    wave_idx: int,
    wave_node_ids: list[str],
    dag: SwarmDAG,
    actual_run_id: str,
    governor: TokenGovernor,
    accumulated_results: dict[str, Any],
    node_executions: dict[str, SwarmNodeExecution],
    wave_metrics_list: list[SwarmWaveMetrics],
    context: ServiceContext,
    session_mgr: AgentSessionManager | None,
    graph_svc: AgentExecutionGraphService | None,
    custom_executor: Callable[[SwarmNode, dict[str, Any]], Any] | None = None,
) -> bool:
    """Execute all nodes in a single topological wave concurrently and record metrics."""
    wave_start_time = time.time()
    wave_tokens_before = governor.tokens_consumed

    results = await asyncio.gather(
        *(
            execute_swarm_node(
                node_id=nid,
                dag=dag,
                actual_run_id=actual_run_id,
                governor=governor,
                accumulated_results=accumulated_results,
                context=context,
                session_mgr=session_mgr,
                graph_svc=graph_svc,
                custom_executor=custom_executor,
            )
            for nid in wave_node_ids
        )
    )

    wave_end_time = time.time()
    wave_duration = max(0.0, wave_end_time - wave_start_time)
    wave_tokens = governor.tokens_consumed - wave_tokens_before

    slowest_node_id: str | None = None
    max_node_dur = 0.0
    wave_success = True

    for nid, res, tokens, err, n_start, n_end in results:
        if err:
            wave_success = False
        accumulated_results[nid] = res
        n_dur = max(0.0, n_end - n_start)
        node_obj = dag.nodes[nid]
        node_executions[nid] = SwarmNodeExecution(
            id=nid,
            role=node_obj.role,
            task=node_obj.task,
            dependencies=list(node_obj.dependencies),
            status=node_obj.status,
            start_time=n_start,
            end_time=n_end,
            duration=n_dur,
            tokens_used=tokens,
            result=res,
            error=err,
        )
        if n_dur > max_node_dur:
            max_node_dur = n_dur
            slowest_node_id = nid

    wave_metrics_list.append(
        SwarmWaveMetrics(
            wave_index=wave_idx,
            node_ids=list(wave_node_ids),
            start_time=wave_start_time,
            end_time=wave_end_time,
            duration=wave_duration,
            total_tokens=wave_tokens,
            bottleneck_node_id=slowest_node_id,
        )
    )

    return wave_success
