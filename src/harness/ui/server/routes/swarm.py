"""Multi-agent swarm execution, DAG trees, and dispatching endpoints."""

from __future__ import annotations

from typing import Any, cast

from fastapi import APIRouter, Request
import structlog

from harness.agent.swarm import SWARM_COORDINATOR_KEY
from harness.services.agent_graph import AGENT_GRAPH_STORE_KEY
from harness.ui.server.models import (
    SwarmRunRequest,
    SwarmSkillDispatchRequest,
)
from harness.ui.server.swarm_graph import build_swarm_mermaid_graph

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.get("/api/swarm/status")
async def get_swarm_status(request: Request) -> dict[str, Any]:
    adapter = request.app.state.adapter
    swarm_coord = adapter.context.optional(SWARM_COORDINATOR_KEY)
    if swarm_coord is not None and hasattr(swarm_coord, "get_status"):
        return cast(dict[str, Any], await swarm_coord.get_status())

    return {
        "status": "ready",
        "active_swarms": 0,
        "coordinator_available": swarm_coord is not None,
    }


@router.get("/api/swarm/runs")
async def list_swarm_runs(request: Request, limit: int = 50) -> dict[str, Any]:
    adapter = request.app.state.adapter
    swarm_coord = adapter.context.optional(SWARM_COORDINATOR_KEY)
    if swarm_coord is None:
        return {"runs": [], "total": 0}

    if hasattr(swarm_coord, "list_runs_async"):
        runs = await swarm_coord.list_runs_async(limit=limit)
    else:
        raw_runs = swarm_coord.list_runs(limit=limit)
        runs = [r.to_dict() if hasattr(r, "to_dict") else r for r in raw_runs]

    return {"runs": runs, "total": len(runs)}


@router.get("/api/swarm/runs/{run_id}")
async def get_swarm_run_endpoint(run_id: str, request: Request) -> dict[str, Any]:
    adapter = request.app.state.adapter
    swarm_coord = adapter.context.optional(SWARM_COORDINATOR_KEY)
    if swarm_coord is None:
        return {"status": "error", "error": "SwarmCoordinator service not available"}

    if hasattr(swarm_coord, "get_run_async"):
        run_data = await swarm_coord.get_run_async(run_id)
    else:
        raw_run = swarm_coord.get_run(run_id)
        run_data = raw_run.to_dict() if raw_run and hasattr(raw_run, "to_dict") else raw_run

    if run_data is None:
        return {"status": "error", "error": f"Swarm run '{run_id}' not found"}

    return {"status": "ok", "run": run_data if isinstance(run_data, dict) else run_data.to_dict()}


@router.get("/api/swarm/runs/{run_id}/tree")
async def get_swarm_run_tree_endpoint(run_id: str, request: Request) -> dict[str, Any]:
    adapter = request.app.state.adapter
    swarm_coord = adapter.context.optional(SWARM_COORDINATOR_KEY)
    if swarm_coord is None:
        return {"status": "error", "error": "SwarmCoordinator service not available"}

    # 1. Direct run lookup
    run_data = None
    if hasattr(swarm_coord, "get_run"):
        run_data = swarm_coord.get_run(run_id)
    if run_data is None and hasattr(swarm_coord, "get_run_async"):
        run_data = await swarm_coord.get_run_async(run_id)

    if run_data is not None:
        if hasattr(run_data, "execution_tree") and run_data.execution_tree is not None:
            return {"status": "ok", "tree": run_data.execution_tree.to_dict()}
        if isinstance(run_data, dict) and run_data.get("execution_tree"):
            return {"status": "ok", "tree": run_data["execution_tree"]}

    # 2. analyze_run
    if hasattr(swarm_coord, "analyze_run"):
        analytics = swarm_coord.analyze_run(run_id)
        if analytics is not None:
            return {"status": "ok", "tree": analytics}

    # 3. get_run_session_tree
    if hasattr(swarm_coord, "get_run_session_tree"):
        tree = await swarm_coord.get_run_session_tree(run_id)
        if tree is not None:
            return {"status": "ok", "tree": tree}

    # 4. AgentExecutionGraphService fallback
    graph_svc = adapter.context.optional(AGENT_GRAPH_STORE_KEY)
    if graph_svc is not None:
        export = graph_svc.export_graph(run_id)
        if export and export.nodes:
            nodes_map = {}
            for nid, n in export.nodes.items():
                nodes_map[nid] = {
                    "id": nid,
                    "role": n.role,
                    "status": n.status,
                    "tokens_used": n.tokens_used,
                    "duration": 0.0,
                    "dependencies": [n.parent_id] if n.parent_id else [],
                }
            fallback_tree = {
                "run_id": run_id,
                "objective": f"Execution DAG {run_id}",
                "status": "completed",
                "total_tokens": export.total_tokens_rollup,
                "nodes": nodes_map,
                "critical_path": list(nodes_map.keys()),
                "bottlenecks": [],
            }
            return {"status": "ok", "tree": fallback_tree}

    return {"status": "error", "error": f"Execution tree for '{run_id}' not found"}


@router.get("/api/swarm/runs/{run_id}/mermaid")
async def get_swarm_run_mermaid_endpoint(run_id: str, request: Request) -> dict[str, Any]:
    adapter = request.app.state.adapter
    swarm_coord = adapter.context.optional(SWARM_COORDINATOR_KEY)
    tree_dict: dict[str, Any] | None = None

    if swarm_coord is not None:
        run_data = None
        if hasattr(swarm_coord, "get_run"):
            run_data = swarm_coord.get_run(run_id)
        if run_data is None and hasattr(swarm_coord, "get_run_async"):
            run_data = await swarm_coord.get_run_async(run_id)

        if run_data is not None:
            if hasattr(run_data, "execution_tree") and run_data.execution_tree is not None:
                tree_dict = run_data.execution_tree.to_dict()
            elif isinstance(run_data, dict) and run_data.get("execution_tree"):
                tree_dict = run_data["execution_tree"]

        if tree_dict is None and hasattr(swarm_coord, "analyze_run"):
            tree_dict = swarm_coord.analyze_run(run_id)

        if tree_dict is None and hasattr(swarm_coord, "get_run_session_tree"):
            sess_tree = await swarm_coord.get_run_session_tree(run_id)
            if isinstance(sess_tree, dict):
                tree_dict = sess_tree

    # Fallback to AgentExecutionGraphService
    if tree_dict is None:
        graph_svc = adapter.context.optional(AGENT_GRAPH_STORE_KEY)
        if graph_svc is not None:
            export = graph_svc.export_graph(run_id)
            if export and export.nodes:
                nodes_map = {}
                for nid, n in export.nodes.items():
                    nodes_map[nid] = {
                        "id": nid,
                        "role": n.role,
                        "status": n.status,
                        "tokens_used": n.tokens_used,
                        "duration": 0.0,
                        "dependencies": [n.parent_id] if n.parent_id else [],
                    }
                tree_dict = {
                    "run_id": run_id,
                    "objective": f"Execution DAG {run_id}",
                    "status": "completed",
                    "total_tokens": export.total_tokens_rollup,
                    "nodes": nodes_map,
                    "critical_path": list(nodes_map.keys()),
                    "bottlenecks": [],
                }

    if tree_dict is None:
        return {"status": "error", "error": f"Execution data for run '{run_id}' not found"}

    mermaid_code = build_swarm_mermaid_graph(run_id, tree_dict)
    return {
        "status": "ok",
        "run_id": run_id,
        "mermaid": mermaid_code,
        "tree": tree_dict,
    }


@router.post("/api/swarm/run")
async def run_swarm_endpoint(req: SwarmRunRequest, request: Request) -> dict[str, Any]:
    adapter = request.app.state.adapter
    projection_engine = request.app.state.projection_engine
    swarm_coord = adapter.context.optional(SWARM_COORDINATOR_KEY)
    if swarm_coord is None:
        return {"status": "error", "error": "SwarmCoordinator service not available"}

    try:
        if hasattr(swarm_coord, "run_swarm"):
            res = await swarm_coord.run_swarm(
                objective=req.objective,
                max_tokens=req.max_tokens,
                consensus_threshold=req.consensus_threshold,
                run_id=req.run_id,
            )
        else:
            return {"status": "error", "error": "run_swarm execution method not supported on coordinator"}

        payload = res.to_dict() if hasattr(res, "to_dict") else res
        if adapter.event_bus is not None and projection_engine is not None:
            await projection_engine.broadcast(
                channel="agent",
                message={
                    "type": "swarm_task_completed",
                    "data": payload,
                },
            )
        return {"status": "ok", "result": payload}
    except Exception as e:
        logger.error("Swarm run execution failed from API", error=str(e))
        return {"status": "error", "error": str(e)}


@router.post("/api/swarm/dispatch-skill")
async def dispatch_skill_swarm_endpoint(req: SwarmSkillDispatchRequest, request: Request) -> dict[str, Any]:
    adapter = request.app.state.adapter
    projection_engine = request.app.state.projection_engine
    swarm_coord = adapter.context.optional(SWARM_COORDINATOR_KEY)
    if swarm_coord is None:
        return {"status": "error", "error": "SwarmCoordinator service not available"}

    try:
        if hasattr(swarm_coord, "dispatch_skill_swarm"):
            res = await swarm_coord.dispatch_skill_swarm(
                objective=req.objective,
                skill_names=req.skills,
                max_total_tokens=req.max_tokens,
                include_verifier=req.include_verifier,
                consensus_threshold=req.consensus_threshold,
                run_id=req.run_id,
            )
        else:
            return {
                "status": "error",
                "error": "dispatch_skill_swarm execution method not supported on coordinator",
            }

        payload = res.to_dict() if hasattr(res, "to_dict") else res
        if adapter.event_bus is not None and projection_engine is not None:
            await projection_engine.broadcast(
                channel="agent",
                message={
                    "type": "swarm_task_completed",
                    "data": payload,
                },
            )
        return {"status": "ok", "result": payload}
    except Exception as e:
        logger.error("Skill-driven swarm dispatch failed from API", error=str(e))
        return {"status": "error", "error": str(e)}


__all__ = ["router"]
