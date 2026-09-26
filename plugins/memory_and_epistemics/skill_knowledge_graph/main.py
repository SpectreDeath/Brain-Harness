"""Entrypoint module and HarnessPlugin implementation for Skill Knowledge Graph & Registry."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.plugins.tool_mount import ToolMountMixin
from harness.services.skill_clustering import (
    SKILL_CLUSTERING_KEY,
    CrossClusterBridge,
    EmergentCapability,
    SkillCluster,
    SkillClusteringEngine,
    SkillSelectionPlan,
)
from harness.services.skill_graph import (
    SKILL_GRAPH_KEY,
    SKILL_INTELLIGENCE_KEY,
    SKILL_REGISTRY_KEY,
    ActionGateResult,
    AntiPatternViolation,
    SkillCardDefinition,
    SkillChainResult,
    SkillExecutionGuidance,
    SkillTopologyReport,
    get_default_skill_registry,
)
from harness.services.tools import TOOL_REGISTRY_KEY, ToolSpec

from .graph import SkillKnowledgeGraph
from .visualizer import SkillGraphVisualizer

# Global cached graph and clustering engine instances
_GRAPH_INSTANCE = SkillKnowledgeGraph()
_CLUSTERING_ENGINE: SkillClusteringEngine | None = None


def get_clustering_engine() -> SkillClusteringEngine:
    """Retrieve or lazily initialize the singleton SkillClusteringEngine."""
    global _CLUSTERING_ENGINE
    graph = _ensure_indexed()
    if _CLUSTERING_ENGINE is None:
        _CLUSTERING_ENGINE = graph._registry._get_clustering_engine()
    return _CLUSTERING_ENGINE


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
    reg = registry if registry is not None else plugin._get_registry()
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
    closure = plugin.get_prerequisite_closure(skill_name)
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
    guidance = plugin.compile_execution_guidance(task=task, max_skills=max_skills)
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
    violations = plugin.intercept_action(
        action_name=action_name,
        action_input=action_input,
        active_skills=active_skills,
    )
    from harness.services.skill_graph import AntiPatternGuard

    obs = AntiPatternGuard.format_self_repair_observation(violations)
    return {
        "status": obs.get("status", "ok"),
        "violations": [v.model_dump() for v in violations],
        "observation": obs,
    }


# --- Service Protocol & HarnessPlugin Implementation ---



class SkillGraphPlugin(ToolMountMixin, HarnessPlugin):
    """In-process Harness plugin providing SkillGraphService, SkillRegistryService, and SkillClusteringService."""

    name = "plugin.skill_knowledge_graph"
    version = "1.0.0"
    description = "Knowledge graph indexer, semantic router, cluster capability discovery, and skill selector"
    trusted = True

    def __init__(self) -> None:
        self._registry = get_default_skill_registry()
        self._graph = SkillKnowledgeGraph(registry=self._registry)

    def _get_registry(self) -> Any:
        return self._registry

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [
            SKILL_GRAPH_KEY,
            SKILL_REGISTRY_KEY,
            SKILL_CLUSTERING_KEY,
            SKILL_INTELLIGENCE_KEY,
        ]

    async def on_load(self, ctx: ServiceContext) -> None:
        ctx.provide(SKILL_GRAPH_KEY, self, allow_override=True)
        ctx.provide(SKILL_REGISTRY_KEY, self._registry, allow_override=True)
        ctx.provide(SKILL_CLUSTERING_KEY, self._registry, allow_override=True)
        ctx.provide(SKILL_INTELLIGENCE_KEY, self._registry, allow_override=True)
        self.setup_tool_mount(ctx, self.name)

        # Synchronize invalidation with BuiltinSkillRegistryService
        if hasattr(self._registry, "add_invalidation_listener"):
            self._registry.add_invalidation_listener(invalidate_skill_catalog)

        try:
            from harness.events.bus import EVENT_BUS_KEY
            from harness.events.types import EventType

            bus = ctx.optional(EVENT_BUS_KEY)
            if bus:
                ctx.subscribe(EventType.FILE_MODIFIED, self._on_skill_file_changed)
                ctx.subscribe(EventType.FILE_CREATED, self._on_skill_file_changed)
                ctx.subscribe(EventType.FILE_DELETED, self._on_skill_file_changed)
        except Exception:
            pass

    def _on_skill_file_changed(self, event: Any) -> None:
        """Handle EventBus file change events by invalidating graph and registry caches."""
        payload = getattr(event, "payload", {}) or {}
        path = str(payload.get("path", ""))
        if "SKILL.md" in path or "CARD.md" in path:
            invalidate_skill_catalog()

    async def on_enable(self) -> None:
        index_skill_catalog(".")
        if self._mount_ctx and self._mount_ctx.has(TOOL_REGISTRY_KEY):
            tools = [
                ToolSpec(
                    name="select_skills",
                    description=(
                        "Intelligently select agent skills and compile a prerequisite-aware "
                        "topological execution plan for a given task using the skill knowledge graph."
                    ),
                    executor=lambda task, max_skills=5, include_verifier=True: (
                        select_skills_for_task(
                            task,
                            max_skills=max_skills,
                            include_verifier=include_verifier,
                        )
                    ),
                ),
                ToolSpec(
                    name="cluster_skills",
                    description=(
                        "Cluster workspace skills into cohesive capability domains and uncover "
                        "emergent macro-capabilities."
                    ),
                    executor=lambda min_cluster_size=2, min_size=None, **kwargs: (
                        cluster_skill_graph(
                            min_cluster_size=min_size
                            if min_size is not None
                            else min_cluster_size
                        )
                    ),
                ),
                ToolSpec(
                    name="discover_capabilities",
                    description=(
                        "Search novel emergent capabilities formed by composite multi-skill "
                        "pipelines in the knowledge graph."
                    ),
                    executor=lambda query="": discover_emergent_capabilities(
                        query=query or None
                    ),
                ),
                ToolSpec(
                    name="get_skill_topology",
                    description=(
                        "Retrieve upstream prerequisites, downstream handoffs, invariants, and "
                        "mitigated anti-patterns for a given skill."
                    ),
                    executor=lambda skill_name: get_skill_topology(skill_name),
                ),
            ]
            await self.mount_tools(tools)

    async def on_disable(self) -> None:
        await self.unmount_tools()

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

    async def cluster_skills(self, min_cluster_size: int = 2) -> list[dict[str, Any]]:
        res = cluster_skill_graph(min_cluster_size=min_cluster_size)
        return list(res.get("clusters", []))

    async def discover_emergent_capabilities(
        self, query: str | None = None
    ) -> list[dict[str, Any]]:
        res = discover_emergent_capabilities(query=query)
        return list(res.get("capabilities", []))

    async def select_skills_for_task(
        self, task: str, max_skills: int = 5, include_verifier: bool = True
    ) -> dict[str, Any]:
        res = select_skills_for_task(
            task=task, max_skills=max_skills, include_verifier=include_verifier
        )
        return dict(res.get("plan", {}))

    # --- SkillRegistryService Protocol Implementation ---
    def discover_all(self, root_dir: str = ".") -> list[SkillCardDefinition]:
        graph = _ensure_indexed(root_dir)
        return list(graph.nodes.values())

    def get_skill(self, name: str) -> SkillCardDefinition | None:
        graph = _ensure_indexed()
        return graph.nodes.get(name)

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

    def get_topology(self, skill_name: str) -> SkillTopologyReport:
        return self._get_registry().get_topology(skill_name)

    def link_knowledge_vault(self, vault_dir: Path | str = ".harness/knowledge") -> int:
        return self._get_registry().link_knowledge_vault(vault_dir)

    def get_prerequisite_closure(self, skill_name: str) -> list[str]:
        return self._get_registry().get_prerequisite_closure(skill_name)

    def evaluate_chain_feasibility(
        self, chain: list[str], context: Any = None
    ) -> tuple[bool, list[str]]:
        return self._get_registry().evaluate_chain_feasibility(chain, context)

    # --- SkillClusteringService Protocol Implementation ---
    def cluster_skills_sync(self, min_cluster_size: int = 2) -> list[SkillCluster]:
        return get_clustering_engine().cluster_skills(min_cluster_size=min_cluster_size)

    def discover_emergent_capabilities_sync(
        self, query: str | None = None
    ) -> list[EmergentCapability]:
        return get_clustering_engine().discover_emergent_capabilities(query=query)

    def get_cross_cluster_bridges(self) -> list[CrossClusterBridge]:
        return get_clustering_engine().get_cross_cluster_bridges()

    def select_skills_for_task_sync(
        self,
        task: str,
        max_skills: int = 5,
        include_verifier: bool = True,
    ) -> SkillSelectionPlan:
        return get_clustering_engine().select_skills_for_task(
            task=task, max_skills=max_skills, include_verifier=include_verifier
        )

    # --- SkillIntelligenceService Protocol Implementation ---
    def compile_execution_guidance(
        self, task: str, max_skills: int = 4, include_verifier: bool = True
    ) -> SkillExecutionGuidance:
        return self._get_registry().compile_execution_guidance(
            task=task, max_skills=max_skills, include_verifier=include_verifier
        )

    def intercept_action(
        self,
        action_name: str,
        action_input: dict[str, Any],
        active_skills: list[str] | None = None,
    ) -> list[AntiPatternViolation]:
        return self._get_registry().intercept_action(
            action_name=action_name,
            action_input=action_input,
            active_skills=active_skills,
        )

    def evaluate_action_gate(
        self,
        action_name: str,
        action_input: dict[str, Any],
        active_skills: list[str] | None = None,
    ) -> ActionGateResult:
        return self._get_registry().evaluate_action_gate(
            action_name=action_name,
            action_input=action_input,
            active_skills=active_skills,
        )


# Authoritative instantiated plugin singleton (Rule 45)
plugin = SkillGraphPlugin()
