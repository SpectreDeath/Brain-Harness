"""Service-layer skill catalog, routing, chain, and topology operations (Rule 49)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from harness.services.skill_graph.protocols import SKILL_REGISTRY_KEY
from harness.services.skill_graph.service import (
    BuiltinSkillRegistryService,
    get_default_skill_registry,
)


def resolve_skill_registry(
    root_path: str | Path = ".",
    context: Any = None,
) -> BuiltinSkillRegistryService:
    """Resolve BuiltinSkillRegistryService from IoC context or process default."""
    if context is not None and hasattr(context, "optional"):
        reg = context.optional(SKILL_REGISTRY_KEY)
        if reg is not None and isinstance(reg, BuiltinSkillRegistryService):
            return reg
    return get_default_skill_registry(root_dir=str(root_path))


def index_skills_catalog(
    root_path: str | Path = ".",
    context: Any = None,
) -> dict[str, Any]:
    """Scan workspace (.agents/skills, plugins) and summarize indexed skill graph."""
    registry = resolve_skill_registry(root_path, context=context)
    skills = registry.discover_all(str(root_path))
    categories = sorted({s.category for s in skills})
    total_edges = sum(len(s.dependencies) for s in skills)
    return {
        "status": "ok",
        "indexed_skills": len(skills),
        "categories": categories,
        "total_nodes": len(skills),
        "total_edges": total_edges,
    }


def route_skills_catalog(
    intent: str,
    top_k: int = 3,
    root_path: str | Path = ".",
    context: Any = None,
) -> dict[str, Any]:
    """Route natural language task intent to matching skills and recommended chains."""
    registry = resolve_skill_registry(root_path, context=context)
    return registry.route_intent(intent, top_k=top_k)


def find_skill_chain(
    start_skill: str,
    target_skill: str,
    context: Any = None,
) -> dict[str, Any]:
    """Find directed execution path between two skills."""
    registry = resolve_skill_registry(context=context)
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


def get_skill_topology_payload(
    skill_name: str,
    context: Any = None,
) -> dict[str, Any]:
    """Inspect topological dependencies, prerequisites, and anti-patterns for a skill."""
    registry = resolve_skill_registry(context=context)
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
    except KeyError as exc:
        return {"status": "error", "reason": str(exc)}


__all__ = [
    "find_skill_chain",
    "get_skill_topology_payload",
    "index_skills_catalog",
    "resolve_skill_registry",
    "route_skills_catalog",
]
