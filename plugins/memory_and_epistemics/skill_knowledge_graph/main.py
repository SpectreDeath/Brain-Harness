"""Entrypoint module and HarnessPlugin implementation for Skill Knowledge Graph & Registry."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.skill_graph import (
    SKILL_GRAPH_KEY,
    SKILL_REGISTRY_KEY,
    SkillAntiPatternDefinition,
    SkillCardDefinition,
    SkillChainResult,
    SkillInvariantDefinition,
    SkillStageDefinition,
)

from .graph import SkillKnowledgeGraph
from .models import SkillNode
from .parser import SkillCardParser
from .visualizer import SkillGraphVisualizer

# Global cached graph instance
_GRAPH_INSTANCE = SkillKnowledgeGraph()


def _node_to_card_def(node: SkillNode) -> SkillCardDefinition:
    """Convert an internal SkillNode AST into the canonical SkillCardDefinition model."""
    return SkillCardDefinition(
        name=node.name,
        category=node.category,
        invocation=node.invocation,
        triggers=list(node.triggers),
        version=node.version,
        target=node.target,
        stages=[
            SkillStageDefinition(
                stage_num=s.stage_num,
                name=s.name,
                completion_gate=s.completion_gate or s.objective,
            )
            for s in node.stages
        ],
        anti_patterns=[
            SkillAntiPatternDefinition(
                name=ap.name,
                symptom=ap.description,
                remedy=ap.mitigation,
            )
            for ap in node.anti_patterns
        ],
        invariants=[
            SkillInvariantDefinition(
                rule=inv.rule,
                is_blocking=inv.is_blocking,
            )
            for inv in node.invariants
        ],
        dependencies=list(node.references),
        services=[],
        tools=[],
        card_path=node.card_path,
        skill_path=node.skill_path,
    )


def _ensure_indexed(root_path: str = ".") -> SkillKnowledgeGraph:
    """Helper to lazily index workspace skills if graph is empty."""
    global _GRAPH_INSTANCE
    if not _GRAPH_INSTANCE.nodes:
        index_skill_catalog(root_path=root_path)
    return _GRAPH_INSTANCE


def index_skill_catalog(root_path: str = ".") -> dict[str, Any]:
    """Scan workspace (.agents/skills, plugins) and construct the knowledge graph."""
    global _GRAPH_INSTANCE
    _GRAPH_INSTANCE = SkillKnowledgeGraph()

    p = Path(root_path)
    # Search .agents/skills/ and plugins/
    paths_to_scan = [p / ".agents" / "skills", p / "plugins", p]
    indexed_count = 0

    for scan_dir in paths_to_scan:
        if scan_dir.exists():
            discovered = SkillCardParser.scan_root(scan_dir)
            for skill_name, node in discovered.items():
                if skill_name not in _GRAPH_INSTANCE.nodes:
                    _GRAPH_INSTANCE.add_skill(node)
                    indexed_count += 1

    _GRAPH_INSTANCE.build_derived_edges()

    return {
        "status": "ok",
        "indexed_skills": indexed_count,
        "categories": sorted(_GRAPH_INSTANCE.categories),
        "total_nodes": len(_GRAPH_INSTANCE.nodes),
        "total_edges": len(_GRAPH_INSTANCE.edges),
    }


def query_skill_router(intent: str, top_k: int = 3) -> dict[str, Any]:
    """Route natural language task intent to matching skills and recommended chains."""
    graph = _ensure_indexed()
    result = graph.query_router(intent=intent, top_k=top_k)
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


# --- Service Protocol & HarnessPlugin Implementation ---

class SkillGraphPlugin(HarnessPlugin):
    """In-process Harness plugin providing SkillGraphService and SkillRegistryService."""

    name = "plugin.skill_knowledge_graph"
    version = "1.0.0"
    description = "Knowledge graph indexer, semantic router, and authoritative workspace skill registry"
    trusted = True

    def __init__(self) -> None:
        self._graph = SkillKnowledgeGraph()

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [SKILL_GRAPH_KEY, SKILL_REGISTRY_KEY]

    async def on_load(self, ctx: ServiceContext) -> None:
        ctx.provide(SKILL_GRAPH_KEY, self)
        ctx.provide(SKILL_REGISTRY_KEY, self)

    async def on_enable(self) -> None:
        index_skill_catalog(".")

    async def on_disable(self) -> None:
        pass

    async def on_unload(self) -> None:
        pass

    # --- SkillGraphService Protocol Implementation ---
    async def index(self, root_dir: str = ".") -> int:
        res = index_skill_catalog(root_dir)
        return int(res.get("indexed_skills", 0))

    async def find_chain(self, start_skill: str, target_skill: str) -> list[str]:
        res = find_skill_chain(start_skill, target_skill)
        return list(res.get("chain", []))

    async def query_router(self, intent: str, top_k: int = 3) -> dict[str, Any]:
        return query_skill_router(intent, top_k=top_k)

    async def export_html_brief(self, output_path: str | None = None) -> str:
        res = export_skill_graph_visual(output_path)
        return str(res.get("html_path", ""))

    # --- SkillRegistryService Protocol Implementation ---
    def discover_all(self, root_dir: str = ".") -> list[SkillCardDefinition]:
        graph = _ensure_indexed(root_dir)
        return [_node_to_card_def(node) for node in graph.nodes.values()]

    def get_skill(self, name: str) -> SkillCardDefinition | None:
        graph = _ensure_indexed()
        node = graph.nodes.get(name)
        return _node_to_card_def(node) if node is not None else None

    def route_intent(self, intent: str, top_k: int = 3) -> dict[str, Any]:
        return query_skill_router(intent, top_k=top_k)

    def get_chain(self, start_skill: str, target_skill: str) -> SkillChainResult:
        res = find_skill_chain(start_skill, target_skill)
        return SkillChainResult(
            status=str(res.get("status", "no_path")),
            start_skill=start_skill,
            target_skill=target_skill,
            chain=list(res.get("chain", [])),
            length=int(res.get("length", 0)),
        )
