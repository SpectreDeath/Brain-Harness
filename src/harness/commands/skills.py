"""Skill commands — pure async and sync programmatic entry points for skill knowledge and authoring.

Provides an authoritative seam for indexing, routing, chain discovery, topology inspection,
scaffolding, and validation across agent skills. Delegates to BuiltinSkillRegistryService.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import structlog

from harness.creator.skills import (
    SkillOptions,
    SkillResult,
    SkillScaffoldEngine,
    SkillValidator,
)
from harness.creator.validator import ValidationReport
from harness.services.skill_graph import (
    BuiltinSkillGraphService,
    BuiltinSkillRegistryService,
    SkillCardDefinition,
)

logger = structlog.get_logger()

# Global default registry instance
_DEFAULT_REGISTRY = BuiltinSkillRegistryService()
_DEFAULT_GRAPH = BuiltinSkillGraphService(registry=_DEFAULT_REGISTRY)


def index_skills_cmd(root_path: str | Path = ".") -> dict[str, Any]:
    """Scan workspace (.agents/skills, plugins) and construct the skill knowledge graph."""
    registry = BuiltinSkillRegistryService(default_root=str(root_path))
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


def export_skill_graph_visual_cmd(output_path: str | Path | None = None) -> dict[str, Any]:
    """Generate an interactive HTML visual brief of the skill graph."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            html_path = pool.submit(asyncio.run, _DEFAULT_GRAPH.export_html_brief(str(output_path) if output_path else None)).result()
    else:
        html_path = asyncio.run(_DEFAULT_GRAPH.export_html_brief(str(output_path) if output_path else None))

    skills = _DEFAULT_REGISTRY.discover_all()
    return {
        "status": "ok",
        "html_path": html_path,
        "total_skills": len(skills),
        "node_count": len(skills),
    }


def route_skills_cmd(intent: str, top_k: int = 3, root_path: str | Path = ".") -> dict[str, Any]:
    """Route natural language task intent to matching skills and recommended chains."""
    registry = BuiltinSkillRegistryService(default_root=str(root_path))
    return registry.route_intent(intent, top_k=top_k)


def find_skill_chain_cmd(start_skill: str, target_skill: str) -> dict[str, Any]:
    """Find directed execution path between two skills."""
    res = _DEFAULT_REGISTRY.get_chain(start_skill, target_skill)
    return {
        "status": res.status,
        "start": res.start_skill,
        "target": res.target_skill,
        "start_skill": res.start_skill,
        "target_skill": res.target_skill,
        "chain": res.chain,
        "length": res.length,
    }


def get_skill_topology_cmd(skill_name: str) -> dict[str, Any]:
    """Inspect topological dependencies, prerequisites, and anti-patterns for a skill."""
    skill = _DEFAULT_REGISTRY.get_skill(skill_name)
    if not skill:
        return {"status": "error", "reason": f"Skill '{skill_name}' not found"}

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
            "prerequisites": skill.dependencies,
            "downstream_handoffs": [],
            "mitigated_anti_patterns": [ap.name for ap in skill.anti_patterns],
        },
    }


def list_skills_cmd(root_path: str | Path = ".") -> list[SkillCardDefinition]:
    """List all discovered skill cards."""
    registry = BuiltinSkillRegistryService(default_root=str(root_path))
    return registry.discover_all(str(root_path))


def scaffold_skill_cmd(
    name: str,
    *,
    description: str = "",
    category: str = "engineering / meta-skills",
    target_dir: str | Path | None = None,
    triggers: list[str] | tuple[str, ...] | None = None,
    auto_validate: bool = False,
) -> SkillResult:
    """Scaffold a high-precision agent skill with SKILL.md and CARD.md specifications."""
    clean_name = name.strip().lower().replace("_", "-")
    out_dir = Path(target_dir) if target_dir else Path(".agents") / "skills" / clean_name

    opts = SkillOptions(
        name=clean_name,
        description=description,
        category=category,
        triggers=list(triggers) if triggers else [],
        auto_validate=auto_validate,
    )
    return SkillScaffoldEngine.scaffold(out_dir, options=opts)


def validate_skill_cmd(skill_dir: str | Path = ".") -> ValidationReport:
    """Validate an agent skill package against deep-module craft standards."""
    target = Path(skill_dir).resolve()
    return SkillValidator.validate(target)


__all__ = [
    "export_skill_graph_visual_cmd",
    "find_skill_chain_cmd",
    "get_skill_topology_cmd",
    "index_skills_cmd",
    "list_skills_cmd",
    "route_skills_cmd",
    "scaffold_skill_cmd",
    "validate_skill_cmd",
]
