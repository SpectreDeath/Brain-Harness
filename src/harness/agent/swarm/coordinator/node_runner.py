"""Single node execution runner with session binding, context compaction, and token tracking."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
import time
from typing import Any

import structlog

from harness.agent.base import AgentTaskResult
from harness.services.context_optimizer import (
    AGENT_CONTEXT_OPTIMIZER_KEY,
    AgentContextOptimizer,
)
from harness.agent.session import AgentSessionManager
from harness.agent.swarm.governor import TokenGovernor
from harness.agent.swarm.models import SwarmDAG, SwarmNode
from harness.kernel.context import ServiceContext
from harness.services.agent_graph import (
    AgentExecutionGraphService,
    ThreadSpawnStatus,
)

logger = structlog.get_logger()


async def _register_child_session(
    session_mgr: AgentSessionManager | None,
    graph_svc: AgentExecutionGraphService | None,
    actual_run_id: str,
    child_sid: str,
    node: SwarmNode,
) -> None:
    if session_mgr is not None:
        await session_mgr.create_child_session(
            parent_session_id=actual_run_id,
            task=node.task,
            session_id=child_sid,
            node_id=node.id,
            role=node.role,
            metadata={"dependencies": list(node.dependencies), "allocated_tokens": node.allocated_tokens},
        )
    elif graph_svc is not None:
        graph_svc.register_thread(
            node_id=child_sid,
            role=node.role,
            task=node.task,
            parent_id=actual_run_id,
            metadata={"node_id": node.id, "dependencies": list(node.dependencies), "allocated_tokens": node.allocated_tokens},
        )


async def _fail_child_session(
    session_mgr: AgentSessionManager | None,
    graph_svc: AgentExecutionGraphService | None,
    actual_run_id: str,
    child_sid: str,
    error: str,
) -> None:
    if session_mgr is not None:
        await session_mgr.fail_session(child_sid, error)
    elif graph_svc is not None:
        graph_svc.update_thread_status(node_id=child_sid, status="failed", completed=True)
        graph_svc.close_spawn_edge(parent_id=actual_run_id, child_id=child_sid, status=ThreadSpawnStatus.FAILED)


async def _complete_child_session(
    session_mgr: AgentSessionManager | None,
    graph_svc: AgentExecutionGraphService | None,
    actual_run_id: str,
    child_sid: str,
    result: Any,
    tokens: int,
) -> None:
    if session_mgr is not None:
        await session_mgr.complete_session(child_sid, final_answer=str(result), total_tokens=tokens)
    elif graph_svc is not None:
        graph_svc.update_thread_status(node_id=child_sid, status="completed", tokens_used=tokens, completed=True)
        graph_svc.close_spawn_edge(parent_id=actual_run_id, child_id=child_sid, status=ThreadSpawnStatus.COMPLETED)


async def execute_swarm_node(
    node_id: str,
    dag: SwarmDAG,
    actual_run_id: str,
    governor: TokenGovernor,
    accumulated_results: dict[str, Any],
    context: ServiceContext,
    session_mgr: AgentSessionManager | None,
    graph_svc: AgentExecutionGraphService | None,
    custom_executor: Callable[[SwarmNode, dict[str, Any]], Any] | None = None,
) -> tuple[str, Any, int, str | None, float, float]:
    """Execute a single swarm node within a dedicated child session and token boundary."""
    node = dag.nodes[node_id]
    node.status = "running"
    child_sid = f"{actual_run_id}_{node_id}"
    n_start = time.time()

    await _register_child_session(session_mgr, graph_svc, actual_run_id, child_sid, node)

    if governor.is_exhausted():
        node.status = "failed"
        node.error = "Token budget exhausted before execution"
        n_end = time.time()
        await _fail_child_session(session_mgr, graph_svc, actual_run_id, child_sid, node.error)
        return node_id, None, 0, node.error, n_start, n_end

    context_opt: AgentContextOptimizer | None = context.optional(AGENT_CONTEXT_OPTIMIZER_KEY)
    upstream_ctx: dict[str, Any] = {}
    for dep in node.dependencies:
        if dep in accumulated_results:
            raw = accumulated_results[dep]
            upstream_ctx[dep] = context_opt.compact_observation(f"upstream_{dep}", raw) if context_opt else raw

    enriched_prompt = node.task
    if upstream_ctx:
        summary = "\n".join(f"- Upstream {k}: {v}" for k, v in upstream_ctx.items())
        enriched_prompt = f"{node.task}\n\n[Prerequisite Context]:\n{summary}"

    tokens_used = 100
    try:
        if custom_executor is not None:
            res = custom_executor(node, upstream_ctx)
            if asyncio.iscoroutine(res):
                res = await res
            node.result = res
            node.status = "completed"
        else:
            from harness.agent.base import AGENT_LOOP_KEY

            agent_loop = context.optional(AGENT_LOOP_KEY)
            if agent_loop is not None:
                agent_res: AgentTaskResult = await agent_loop.run_task(
                    enriched_prompt,
                    max_steps=6,
                    context=upstream_ctx,
                    session_id=child_sid,
                    parent_session_id=actual_run_id,
                )
                node.result = agent_res.final_answer or agent_res.status
                tokens_used = agent_res.total_tokens or 150
                node.status = "completed" if agent_res.status == "completed" else "failed"
            else:
                node.result = f"Completed {node.role} task: {node.task}"
                node.status = "completed"

        node.tokens_used = tokens_used
        governor.record_usage(node.id, tokens_used)
        n_end = time.time()

        if node.status == "completed":
            await _complete_child_session(session_mgr, graph_svc, actual_run_id, child_sid, node.result, tokens_used)
        else:
            await _fail_child_session(session_mgr, graph_svc, actual_run_id, child_sid, node.error or "Execution failed")

        return node_id, node.result, tokens_used, None, n_start, n_end
    except Exception as e:
        node.status = "failed"
        node.error = str(e)
        n_end = time.time()
        logger.error("Swarm node execution failed", run_id=actual_run_id, node=node_id, error=str(e))
        await _fail_child_session(session_mgr, graph_svc, actual_run_id, child_sid, str(e))
        return node_id, None, tokens_used, str(e), n_start, n_end
