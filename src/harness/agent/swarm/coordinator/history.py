"""Swarm run history caching, analytics inspection, and persistent query integration."""

from __future__ import annotations

from typing import Any, cast

from harness.agent.session import AGENT_SESSION_MANAGER_KEY, AgentSessionManager
from harness.agent.swarm.models import SwarmTaskResult
from harness.kernel.context import ServiceContext


def get_run_from_cache(
    run_history: dict[str, SwarmTaskResult],
    run_id: str,
) -> SwarmTaskResult | None:
    """Fetch a completed or archived swarm run by ID from in-memory cache."""
    return run_history.get(run_id)


async def get_run_async_with_fallback(
    run_history: dict[str, SwarmTaskResult],
    context: ServiceContext,
    run_id: str,
) -> SwarmTaskResult | dict[str, Any] | None:
    """Fetch a completed swarm run by ID, falling back to persistent session store."""
    if run_id in run_history:
        return run_history[run_id]

    session_mgr: AgentSessionManager | None = context.optional(
        AGENT_SESSION_MANAGER_KEY
    )
    if session_mgr is not None:
        sess = await session_mgr.get_session(run_id)
        if sess and "swarm_run" in sess.metadata:
            return cast(dict[str, Any], sess.metadata["swarm_run"])
        if sess:
            return sess.to_dict()
    return None


def analyze_run_metrics(
    run_history: dict[str, SwarmTaskResult],
    run_id: str,
) -> dict[str, Any] | None:
    """Fetch post-flight execution analytics and critical path breakdown for a run."""
    run = get_run_from_cache(run_history, run_id)
    if not run:
        return None
    if run.execution_tree is not None:
        return run.execution_tree.to_dict()
    return run.to_dict()


async def get_run_session_tree_hierarchy(
    run_history: dict[str, SwarmTaskResult],
    context: ServiceContext,
    run_id: str,
) -> dict[str, Any] | None:
    """Retrieve full hierarchical execution session tree for a swarm run."""
    session_mgr: AgentSessionManager | None = context.optional(
        AGENT_SESSION_MANAGER_KEY
    )
    if session_mgr is not None:
        return await session_mgr.get_session_tree(run_id)
    run = get_run_from_cache(run_history, run_id)
    return run.to_dict() if run else None


def list_runs_cached(
    run_history: dict[str, SwarmTaskResult],
    limit: int = 50,
) -> list[SwarmTaskResult]:
    """List historical swarm execution outcomes from in-memory cache."""
    runs = list(run_history.values())
    return runs[-limit:] if limit > 0 else runs


async def list_runs_async_with_fallback(
    run_history: dict[str, SwarmTaskResult],
    context: ServiceContext,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """List historical swarm execution outcomes from memory and persistent session store."""
    results: list[dict[str, Any]] = [
        r.to_dict() for r in run_history.values()
    ]
    seen_ids = {r["run_id"] for r in results if "run_id" in r}

    session_mgr: AgentSessionManager | None = context.optional(
        AGENT_SESSION_MANAGER_KEY
    )
    if session_mgr is not None:
        sessions = await session_mgr.list_sessions(limit=limit * 2)
        for s in sessions:
            if s.session_id not in seen_ids and s.metadata.get("is_swarm"):
                swarm_payload = s.metadata.get("swarm_run")
                if swarm_payload:
                    results.append(swarm_payload)
                    seen_ids.add(s.session_id)
                else:
                    results.append(s.to_dict())
                    seen_ids.add(s.session_id)

    return results[-limit:] if limit > 0 else results


def build_status_summary(
    run_history: dict[str, SwarmTaskResult],
    active_runs: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Return status report of the swarm coordinator."""
    last_run = (
        list(run_history.values())[-1].to_dict()
        if run_history
        else None
    )
    return {
        "status": "ready",
        "active_swarms": len(active_runs),
        "total_runs": len(run_history),
        "last_run": last_run,
        "coordinator_available": True,
    }
