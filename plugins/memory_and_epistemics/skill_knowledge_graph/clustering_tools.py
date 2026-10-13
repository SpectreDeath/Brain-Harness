"""Clustering, capability discovery, and execution guidance tool implementations."""

from __future__ import annotations

from typing import Any

from harness.services.skill_clustering import (
    SkillClusteringEngine,
)
from harness.services.skill_graph import (
    AntiPatternGuard,
    get_default_skill_registry,
)


def get_clustering_engine() -> SkillClusteringEngine:
    """Retrieve or lazily initialize the singleton SkillClusteringEngine."""
    from .tools import _ensure_indexed
    import plugins.memory_and_epistemics.skill_knowledge_graph.tools as t_mod

    graph = _ensure_indexed()
    if t_mod._CLUSTERING_ENGINE is None:
        t_mod._CLUSTERING_ENGINE = graph._registry._get_clustering_engine()
    return t_mod._CLUSTERING_ENGINE


def cluster_skill_graph(min_cluster_size: int = 2) -> dict[str, Any]:
    """Cluster workspace skills into functional domains and discover novel capabilities."""
    engine = get_clustering_engine()
    clusters = engine.cluster_skills(min_cluster_size=min_cluster_size)
    return {
        "status": "ok",
        "total_clusters": len(clusters),
        "clusters": [c.model_dump() for c in clusters],
    }


def discover_emergent_capabilities(query: str | None = None) -> dict[str, Any]:
    """Retrieve emergent macro-capabilities revealed by the graph clusters."""
    engine = get_clustering_engine()
    caps = engine.discover_emergent_capabilities(query=query)
    return {
        "status": "ok",
        "total_capabilities": len(caps),
        "query": query or "",
        "capabilities": [c.model_dump() for c in caps],
    }


def select_skills_for_task(
    task: str, max_skills: int = 5, include_verifier: bool = True
) -> dict[str, Any]:
    """Analyze natural language task intent and compile a prerequisite-aware execution plan."""
    engine = get_clustering_engine()
    plan = engine.select_skills_for_task(
        task=task, max_skills=max_skills, include_verifier=include_verifier
    )
    return {
        "status": "ok",
        "plan": plan.model_dump(),
    }


def get_cross_cluster_bridges() -> dict[str, Any]:
    """Discover cross-domain macro-bridges connecting distinct clusters."""
    engine = get_clustering_engine()
    bridges = engine.get_cross_cluster_bridges()
    return {
        "status": "ok",
        "total_bridges": len(bridges),
        "bridges": [b.model_dump() for b in bridges],
    }


def compile_execution_guidance(
    task: str, max_skills: int = 4
) -> dict[str, Any]:
    """Compile an execution guidance plan for an agent task."""
    guidance = get_default_skill_registry().compile_execution_guidance(task=task, max_skills=max_skills)
    return {
        "status": "ok",
        "task": guidance.task,
        "selected_skills": list(guidance.selected_skills),
        "execution_pipeline": list(guidance.execution_pipeline),
        "stages": list(guidance.stages),
        "active_anti_patterns": list(guidance.active_anti_patterns),
        "confidence": guidance.confidence,
    }


def intercept_skill_action(
    action_name: str,
    action_input: dict[str, Any],
    active_skills: list[str] | None = None,
) -> dict[str, Any]:
    """Intercept proposed tool invocation and parameters against anti-patterns and blocked AST calls."""
    violations = get_default_skill_registry().intercept_action(
        action_name=action_name,
        action_input=action_input,
        active_skills=active_skills,
    )
    obs = AntiPatternGuard.format_self_repair_observation(violations)
    return {
        "status": obs.get("status", "ok"),
        "violations": [v.model_dump() for v in violations],
        "observation": obs,
    }
