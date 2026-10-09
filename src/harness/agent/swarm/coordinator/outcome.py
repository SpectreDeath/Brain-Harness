"""Outcome synthesis, consensus tallying, execution tree analysis, and session finalization."""

from __future__ import annotations

import time
from typing import Any

from harness.agent.session import AgentSessionManager
from harness.agent.swarm.consensus import ConsensusEngine
from harness.agent.swarm.governor import TokenGovernor
from harness.agent.swarm.models import (
    SwarmExecutionTree,
    SwarmNodeExecution,
    SwarmTaskResult,
    SwarmWaveMetrics,
)
from harness.services.agent_graph import AgentExecutionGraphService


async def finalize_swarm_outcome(
    actual_run_id: str,
    objective: str,
    governor: TokenGovernor,
    accumulated_results: dict[str, Any],
    node_executions: dict[str, SwarmNodeExecution],
    wave_metrics_list: list[SwarmWaveMetrics],
    swarm_start_time: float,
    all_success: bool,
    session_mgr: AgentSessionManager | None,
    graph_svc: AgentExecutionGraphService | None,
) -> SwarmTaskResult:
    """Synthesize final output, calculate execution critical path, and finalize session."""
    swarm_end_time = time.time()
    total_duration = max(0.0, swarm_end_time - swarm_start_time)

    # Synthesize final output
    final_synthesis = ""
    if "synthesizer" in accumulated_results:
        final_synthesis = str(accumulated_results["synthesizer"])
    elif accumulated_results:
        last_node = list(accumulated_results.keys())[-1]
        final_synthesis = str(accumulated_results[last_node])

    # Check if any critic/debater node results contain consensus votes
    consensus_data: dict[str, Any] | None = None
    votes_collected: list[dict[str, Any]] = []
    for _nid, res in accumulated_results.items():
        if isinstance(res, dict) and "vote" in res:
            votes_collected.append(res)
        elif isinstance(res, list):
            for item in res:
                if isinstance(item, dict) and "vote" in item:
                    votes_collected.append(item)

    if votes_collected:
        consensus_data = ConsensusEngine.tally(votes_collected)

    task_status = "completed" if all_success else "partial"

    # Construct execution tree
    exec_tree = SwarmExecutionTree(
        run_id=actual_run_id,
        objective=objective,
        status=task_status,
        start_time=swarm_start_time,
        end_time=swarm_end_time,
        duration=total_duration,
        total_tokens=governor.tokens_consumed,
        nodes=node_executions,
        waves=wave_metrics_list,
    )
    exec_tree.calculate_critical_path()
    exec_tree.calculate_bottlenecks()

    task_result = SwarmTaskResult(
        run_id=actual_run_id,
        objective=objective,
        status=task_status,
        final_synthesis=final_synthesis,
        node_results=accumulated_results,
        total_tokens=governor.tokens_consumed,
        consensus=consensus_data,
        metadata=governor.get_stats(),
        execution_tree=exec_tree,
    )

    # Store swarm task result in root session metadata and complete in session manager
    if session_mgr is not None:
        root_session = await session_mgr.get_session(actual_run_id)
        if root_session is not None:
            root_session.metadata["swarm_run"] = task_result.to_dict()
            root_session.metadata["is_swarm"] = True
            await session_mgr.store.save(root_session)

        if all_success:
            await session_mgr.complete_session(
                actual_run_id,
                final_answer=final_synthesis,
                total_tokens=governor.tokens_consumed,
            )
        else:
            await session_mgr.fail_session(
                actual_run_id,
                error_message=f"Swarm completed with partial failures: {task_status}",
            )
    elif graph_svc is not None:
        st = "completed" if all_success else "failed"
        graph_svc.update_thread_status(
            node_id=actual_run_id,
            status=st,
            tokens_used=governor.tokens_consumed,
            completed=True,
        )

    return task_result
