"""Standalone tool handlers and functional query entrypoints for Skill Knowledge Graph."""

from __future__ import annotations

from typing import Any

from harness.services.skill_clustering import (
    SkillClusteringEngine,
)
from harness.services.skill_graph import (
    SkillCardDefinition,
    get_default_skill_registry,
)

from .clustering_tools import (
    cluster_skill_graph,
    compile_execution_guidance,
    discover_emergent_capabilities,
    get_clustering_engine,
    get_cross_cluster_bridges,
    intercept_skill_action,
    select_skills_for_task,
)
from .graph import SkillKnowledgeGraph
from .visualizer import SkillGraphVisualizer

# Global cached graph and clustering engine instances
_GRAPH_INSTANCE = SkillKnowledgeGraph()
_CLUSTERING_ENGINE: SkillClusteringEngine | None = None


def _node_to_card_def(node: Any) -> SkillCardDefinition:
    """Convert an internal SkillNode AST into the canonical SkillCardDefinition model."""
    if isinstance(node, SkillCardDefinition):
        return node
    return SkillCardDefinition(**node.model_dump())


def _ensure_indexed(root_path: str = ".") -> SkillKnowledgeGraph:
    """Helper to lazily index workspace skills if graph is empty."""
    if not _GRAPH_INSTANCE.nodes:
        index_skill_catalog(root_path=root_path)
    return _GRAPH_INSTANCE


def index_skill_catalog(root_path: str = ".") -> dict[str, Any]:
    """Scan workspace (.agents/skills, plugins) and construct the knowledge graph."""
    global _GRAPH_INSTANCE, _CLUSTERING_ENGINE
    reg = get_default_skill_registry(root_dir=root_path)
    reg.discover_all(root_path)
    _GRAPH_INSTANCE = SkillKnowledgeGraph(registry=reg)
    _CLUSTERING_ENGINE = None

    return {
        "status": "ok",
        "indexed_skills": len(reg._skills_cache),
        "categories": sorted(reg._categories),
        "total_nodes": len(reg._skills_cache),
        "total_edges": len(reg.edges),
    }


def invalidate_skill_catalog() -> None:
    """Invalidate global graph instance and clustering engine to force re-indexing."""
    global _GRAPH_INSTANCE, _CLUSTERING_ENGINE
    reg = get_default_skill_registry()
    reg.invalidate_cache()
    _GRAPH_INSTANCE = SkillKnowledgeGraph(registry=reg)
    _CLUSTERING_ENGINE = None


def query_skill_router(
    intent: str, top_k: int = 3, registry: Any = None
) -> dict[str, Any]:
    """Route natural language task intent to matching skills and recommended chains."""
    graph = _ensure_indexed()
    reg = registry if registry is not None else get_default_skill_registry()
    result = graph.query_router(intent=intent, top_k=top_k, registry=reg)
    return {
        "status": "ok",
        "query": result.query,
        "matches": [m.model_dump() for m in result.matches],
        "recommended_chain": result.recommended_chain,
    }


def find_skill_chain(start_skill: str, target_skill: str) -> dict[str, Any]:
    """Find shortest directed execution chain between two skills."""
    graph = _ensure_indexed()
    chain = graph.find_chain(start_skill=start_skill, target_skill=target_skill)
    return {
        "status": "ok" if chain else "no_path",
        "start_skill": start_skill,
        "target_skill": target_skill,
        "chain": chain,
        "length": len(chain),
    }


def get_skill_topology(skill_name: str) -> dict[str, Any]:
    """Retrieve full topological inspection for a specific skill."""
    graph = _ensure_indexed()
    try:
        topo = graph.get_topology(skill_name=skill_name)
        return {
            "status": "ok",
            "topology": topo.model_dump(),
        }
    except KeyError as e:
        return {
            "status": "error",
            "reason": str(e),
        }


def get_prerequisite_closure(skill_name: str) -> dict[str, Any]:
    """Compute the transitive prerequisite closure for a skill in topological execution order."""
    closure = get_default_skill_registry().get_prerequisite_closure(skill_name)
    return {
        "status": "ok",
        "skill": skill_name,
        "prerequisites": closure,
        "count": len(closure),
    }


def export_skill_graph_visual(output_path: str | None = None) -> dict[str, Any]:
    """Generate an interactive HTML visual brief in %TEMP%."""
    graph = _ensure_indexed()
    path = SkillGraphVisualizer.render_html(graph, output_path=output_path)
    return {
        "status": "ok",
        "html_path": path,
        "total_skills": len(graph.nodes),
        "total_edges": len(graph.edges),
    }


__all__ = [
    "_CLUSTERING_ENGINE",
    "_GRAPH_INSTANCE",
    "_ensure_indexed",
    "_node_to_card_def",
    "cluster_skill_graph",
    "compile_execution_guidance",
    "discover_emergent_capabilities",
    "export_skill_graph_visual",
    "find_skill_chain",
    "get_clustering_engine",
    "get_cross_cluster_bridges",
    "get_prerequisite_closure",
    "get_skill_topology",
    "index_skill_catalog",
    "intercept_skill_action",
    "invalidate_skill_catalog",
    "query_skill_router",
    "select_skills_for_task",
]
