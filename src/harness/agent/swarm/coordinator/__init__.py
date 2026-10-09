"""Swarm Coordinator subpackage — multi-agent DAG orchestration with token governance."""

from __future__ import annotations

from .core import SWARM_COORDINATOR_KEY, SwarmCoordinator
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
from .node_runner import execute_swarm_node
from .outcome import finalize_swarm_outcome
from .resolvers import resolve_swarm_coordinator
from .wave_runner import execute_swarm_wave

__all__ = [
    "SWARM_COORDINATOR_KEY",
    "SwarmCoordinator",
    "analyze_run_metrics",
    "build_status_summary",
    "decompose_objective",
    "decompose_objective_with_skills",
    "execute_swarm_node",
    "execute_swarm_wave",
    "finalize_swarm_outcome",
    "get_run_async_with_fallback",
    "get_run_from_cache",
    "get_run_session_tree_hierarchy",
    "list_runs_async_with_fallback",
    "list_runs_cached",
    "resolve_swarm_coordinator",
]
