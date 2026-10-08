"""Topology inspection, chain discovery, feasibility checking, and clustering commands."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from harness.commands.skills.seams import get_skill_registry


def cluster_skills_cmd(
    min_cluster_size: int = 2,
    root_path: str | Path = ".",
    context: Any = None,
) -> dict[str, Any]:
    """Cluster workspace skills into functional domains and discover emergent capabilities."""
    registry = get_skill_registry(root_path, context=context)
    clusters = registry.cluster_skills(min_cluster_size=min_cluster_size)
    return {
        "status": "ok",
        "total_clusters": len(clusters),
        "clusters": [c.model_dump() for c in clusters],
    }


def discover_capabilities_cmd(
    query: str | None = None,
    root_path: str | Path = ".",
    context: Any = None,
) -> dict[str, Any]:
    """Discover novel emergent capabilities across skill graph clusters."""
    registry = get_skill_registry(root_path, context=context)
    caps = registry.discover_emergent_capabilities(query=query)
    return {
        "status": "ok",
        "total_capabilities": len(caps),
        "query": query or "",
        "capabilities": [c.model_dump() for c in caps],
    }


def find_skill_chain_cmd(
    start_skill: str, target_skill: str, context: Any = None
) -> dict[str, Any]:
    """Find directed execution path between two skills."""
    registry = get_skill_registry(context=context)
    res = registry.get_chain(start_skill, target_skill)
    return {
        "status": res.status,
        "start": res.start_skill,
        "target": res.target_skill,
        "start_skill": res.start_skill,
        "target_skill": res.target_skill,
        "chain": res.chain,
        "length": res.length,
    }


def get_prerequisite_closure_cmd(
    skill_name: str,
    root_path: str | Path = ".",
    context: Any = None,
) -> dict[str, Any]:
    """Compute the transitive prerequisite closure for a skill in topological execution order."""
    registry = get_skill_registry(root_path, context=context)
    closure = registry.get_prerequisite_closure(skill_name)
    return {
        "status": "ok",
        "skill": skill_name,
        "prerequisites": closure,
        "count": len(closure),
    }


def check_chain_feasibility_cmd(
    chain: list[str],
    root_path: str | Path = ".",
    verify_prerequisites: bool = True,
    context: Any = None,
) -> dict[str, Any]:
    """Check whether declared service preconditions and prerequisite dependencies for a skill chain are satisfied (Rule 10)."""
    registry = get_skill_registry(root_path, context=context)
    feasible, missing = registry.evaluate_chain_feasibility(
        chain=chain,
        context=context,
        verify_prerequisites=verify_prerequisites,
    )
    return {
        "status": "ok" if feasible else "error",
        "feasible": feasible,
        "chain": chain,
        "length": len(chain),
        "missing_items": missing,
        "missing_count": len(missing),
    }


def get_skill_topology_cmd(
    skill_name: str, context: Any = None
) -> dict[str, Any]:
    """Inspect topological dependencies, prerequisites, and anti-patterns for a skill."""
    registry = get_skill_registry(context=context)
    try:
        topo = registry.get_topology(skill_name)
        skill = topo.skill
        return {
            "status": "ok",
            "topology": {
                "skill": {
                    "name": skill.name,
                    "version": skill.version,
                    "category": skill.category,
                    "invocation": skill.invocation,
                    "target": skill.target,
                    "description": skill.target,
                    "stages": [s.model_dump() for s in skill.stages],
                    "anti_patterns": [ap.model_dump() for ap in skill.anti_patterns],
                    "invariants": [inv.model_dump() for inv in skill.invariants],
                },
                "prerequisites": topo.prerequisites,
                "downstream_handoffs": topo.downstream_handoffs,
                "complements": topo.complements,
                "mitigated_anti_patterns": topo.mitigated_anti_patterns,
            },
        }
    except KeyError as e:
        return {"status": "error", "reason": str(e)}
