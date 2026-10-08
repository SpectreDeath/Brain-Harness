"""Authoritative in-memory caching Skill Registry, Knowledge Graph, and IoC coordinator."""

from __future__ import annotations

import collections
from pathlib import Path
import threading
import time
from typing import Any

import structlog

from harness.kernel.context import ServiceContext
from harness.services.skill_clustering import (
    CrossClusterBridge,
    EmergentCapability,
    SkillCluster,
    SkillClusteringEngine,
    SkillSelectionPlan,
)
from harness.services.skill_graph.adapter import SkillIntelligenceAdapter
from harness.services.skill_graph.guidance import (
    compile_execution_guidance_plan,
    export_html_brief as _export_html_brief,
)
from harness.services.skill_graph.guard import AntiPatternGuard
from harness.services.skill_graph.intent import route_skill_intent
from harness.services.skill_graph.models import (
    ActionGateResult,
    AntiPatternViolation,
    EdgeType,
    SkillCardDefinition,
    SkillChainResult,
    SkillEdge,
    SkillExecutionGuidance,
    SkillTopologyReport,
)
from harness.services.skill_graph.plugin import SkillRegistryPlugin
from harness.services.skill_graph.protocols import (
    SKILL_GRAPH_KEY,
    SKILL_INTELLIGENCE_KEY,
    SKILL_REGISTRY_KEY,
    SkillGraphService,
    SkillIntelligenceService,
    SkillRegistryService,
)
from harness.services.skill_graph.scanner import (
    link_knowledge_vault_items,
    scan_skills_catalog,
)
from harness.services.skill_graph.topology import (
    compute_prerequisite_closure as _compute_prereqs,
    compute_skill_chain,
    compute_topology_report,
    evaluate_chain_feasibility as _eval_feasibility,
)

logger = structlog.get_logger()


class BuiltinSkillRegistryService(SkillIntelligenceService):
    """Authoritative in-memory caching Skill Registry and Knowledge Graph engine.

    Parses SKILL.md and CARD.md specifications, builds directed dependency DAGs,
    calculates BFS shortest execution chains, and performs semantic token routing.
    """

    def __init__(self, default_root: str = ".") -> None:
        self._default_root = default_root
        self._skills_cache: dict[str, SkillCardDefinition] = {}
        self._adjacency: dict[str, set[str]] = collections.defaultdict(set)
        self._synthetic_adjacency: dict[str, set[str]] = collections.defaultdict(set)
        self._categories: set[str] = set()
        self._anti_pattern_map: dict[str, list[Any]] = collections.defaultdict(list)
        self._edges: list[SkillEdge] = []
        self._edge_keys: set[tuple[str, str, EdgeType]] = set()
        self._adj_out: dict[str, list[SkillEdge]] = collections.defaultdict(list)
        self._adj_in: dict[str, list[SkillEdge]] = collections.defaultdict(list)
        self._last_scan_time: float = 0.0
        self._clustering_engine: Any = None
        self._invalidation_listeners: list[Any] = []
        self._is_invalidating: bool = False
        self._scan_lock = threading.Lock()
        self._idf_table: dict[str, float] = {}

    @property
    def edges(self) -> list[SkillEdge]:
        """All directed relationship edges in the skill knowledge graph."""
        self._ensure_scanned(self._default_root)
        return list(self._edges)

    def _add_edge(
        self, source: str, target: str, relation: EdgeType, weight: float = 1.0
    ) -> None:
        """Append directed edge and update bidirectional adjacency indices in O(1) time."""
        edge_key = (source, target, relation)
        if edge_key in self._edge_keys:
            return
        self._edge_keys.add(edge_key)
        edge = SkillEdge(source=source, target=target, relation=relation, weight=weight)
        self._edges.append(edge)
        self._adj_out[source].append(edge)
        self._adj_in[target].append(edge)

    def discover_all(self, root_dir: str = ".") -> list[SkillCardDefinition]:
        """Discover and parse all skill cards across .agents/skills, plugins/, and skills/."""
        self._ensure_scanned(root_dir)
        return list(self._skills_cache.values())

    def get_skill(self, name: str) -> SkillCardDefinition | None:
        """Retrieve parsed skill card definition by canonical or normalized name."""
        self._ensure_scanned(self._default_root)
        clean = name.strip().lower().replace("_", "-")
        return self._skills_cache.get(clean)

    def get_nodes(self) -> dict[str, SkillCardDefinition]:
        """Retrieve copy of all registered skill card nodes."""
        self._ensure_scanned(self._default_root)
        return dict(self._skills_cache)

    def get_categories(self) -> set[str]:
        """Retrieve set of unique domain category names."""
        self._ensure_scanned(self._default_root)
        return set(self._categories)

    def get_outgoing_edges(self, skill_name: str) -> list[SkillEdge]:
        """Retrieve outgoing directed edges originated from a skill."""
        self._ensure_scanned(self._default_root)
        clean = skill_name.strip().lower().replace("_", "-")
        return list(self._adj_out.get(clean, []))

    def get_incoming_edges(self, skill_name: str) -> list[SkillEdge]:
        """Retrieve incoming directed edges targeting a skill."""
        self._ensure_scanned(self._default_root)
        clean = skill_name.strip().lower().replace("_", "-")
        return list(self._adj_in.get(clean, []))

    def check_anti_patterns(
        self, skill_name: str, proposed_text: str
    ) -> list[AntiPatternViolation]:
        """Verify proposed action or text against anti-patterns for a given skill."""
        skill = self.get_skill(skill_name)
        if not skill:
            return []
        return AntiPatternGuard.check_proposal(skill, proposed_text)

    def intercept_action(
        self,
        action_name: str,
        action_input: dict[str, Any],
        active_skills: list[str] | None = None,
    ) -> list[AntiPatternViolation]:
        """Intercept proposed tool invocation and parameters against anti-patterns and blocked AST calls."""
        self._ensure_scanned(self._default_root)
        return AntiPatternGuard.evaluate_action(
            action_name=action_name,
            action_input=action_input,
            active_skills=active_skills,
            skill_lookup=self.get_skill,
        )

    def evaluate_action_gate(
        self,
        action_name: str,
        action_input: dict[str, Any],
        active_skills: list[str] | None = None,
    ) -> ActionGateResult:
        """Evaluate proposed tool invocation and parameters against anti-patterns and blocked AST calls."""
        self._ensure_scanned(self._default_root)
        return AntiPatternGuard.evaluate_action_gate(
            action_name=action_name,
            action_input=action_input,
            active_skills=active_skills,
            skill_lookup=self.get_skill,
        )

    def compile_execution_guidance(
        self, task: str, max_skills: int = 4, include_verifier: bool = True
    ) -> SkillExecutionGuidance:
        """Compile an end-to-end execution guidance plan for an agent task with multi-tier fallback."""
        self._ensure_scanned(self._default_root)
        return compile_execution_guidance_plan(
            task=task,
            skills_cache=self._skills_cache,
            select_skills_fn=self.select_skills_for_task,
            route_intent_fn=self.route_intent,
            get_skill_fn=self.get_skill,
            max_skills=max_skills,
            include_verifier=include_verifier,
        )

    def get_prerequisite_closure(self, skill_name: str) -> list[str]:
        """Compute the full transitive prerequisite closure for a skill in topological execution order."""
        self._ensure_scanned(self._default_root)
        return _compute_prereqs(skill_name, self._skills_cache, self._adj_out, self._adj_in)

    def export_html_brief(self, output_path: str | None = None) -> str:
        """Generate and save interactive HTML visual brief synchronously."""
        return _export_html_brief(self, output_path=output_path)

    def add_invalidation_listener(self, callback: Any) -> None:
        """Register a callback invoked when the skills cache is invalidated."""
        if callback not in self._invalidation_listeners:
            self._invalidation_listeners.append(callback)

    def register_invalidation_listener(self, callback: Any) -> None:
        """Alias for add_invalidation_listener."""
        self.add_invalidation_listener(callback)

    def remove_invalidation_listener(self, callback: Any) -> None:
        """Unregister an invalidation callback."""
        if callback in self._invalidation_listeners:
            self._invalidation_listeners.remove(callback)

    def invalidate_cache(self) -> None:
        """Invalidate scanned skills cache to force immediate re-scan on next query."""
        if getattr(self, "_is_invalidating", False):
            return
        self._is_invalidating = True
        try:
            self._last_scan_time = 0.0
            self._skills_cache.clear()
            self._categories.clear()
            self._adjacency.clear()
            self._synthetic_adjacency.clear()
            self._anti_pattern_map.clear()
            self._edges.clear()
            self._edge_keys.clear()
            self._adj_out.clear()
            self._adj_in.clear()
            self._clustering_engine = None
            for listener in list(self._invalidation_listeners):
                try:
                    listener()
                except Exception:
                    pass
        finally:
            self._is_invalidating = False

    def _get_clustering_engine(self) -> SkillClusteringEngine:
        self._ensure_scanned(self._default_root)
        if self._clustering_engine is None:
            self._clustering_engine = SkillClusteringEngine(
                self._skills_cache, registry=self
            )
        return self._clustering_engine

    def cluster_skills(self, min_cluster_size: int = 2) -> list[SkillCluster]:
        """Cluster workspace skills into functional capability domains."""
        return self._get_clustering_engine().cluster_skills(
            min_cluster_size=min_cluster_size
        )

    def discover_emergent_capabilities(
        self, query: str | None = None
    ) -> list[EmergentCapability]:
        """Discover novel macro-capabilities revealed by the graph clusters."""
        return self._get_clustering_engine().discover_emergent_capabilities(
            query=query
        )

    def get_cross_cluster_bridges(self) -> list[CrossClusterBridge]:
        """Discover cross-domain macro-bridges connecting distinct clusters."""
        return self._get_clustering_engine().get_cross_cluster_bridges()

    def select_skills_for_task(
        self,
        task: str,
        max_skills: int = 5,
        include_verifier: bool = True,
    ) -> SkillSelectionPlan:
        """Select skills and generate an execution plan for an agent task."""
        return self._get_clustering_engine().select_skills_for_task(
            task=task, max_skills=max_skills, include_verifier=include_verifier
        )

    def _get_neighbors(
        self, node: str, *, include_synthetic: bool = False
    ) -> set[str]:
        """Retrieve adjacent nodes, optionally including synthetic precedence edges."""
        neighbors = set(self._adjacency.get(node, set()))
        if include_synthetic:
            neighbors.update(self._synthetic_adjacency.get(node, set()))
        return neighbors

    def evaluate_chain_feasibility(
        self,
        chain: list[str],
        context: Any = None,
        *,
        verify_prerequisites: bool = False,
    ) -> tuple[bool, list[str]]:
        """Check whether all declared service preconditions and prerequisite dependencies are satisfied."""
        self._ensure_scanned(self._default_root)
        return _eval_feasibility(
            chain=chain,
            skills_cache=self._skills_cache,
            prereq_closure_fn=self.get_prerequisite_closure,
            context=context,
            verify_prerequisites=verify_prerequisites,
        )

    def get_topology(self, skill_name: str) -> SkillTopologyReport:
        """Inspect topological dependencies, upstream prerequisites, downstream handoffs, and anti-patterns."""
        self._ensure_scanned(self._default_root)
        return compute_topology_report(
            skill_name=skill_name,
            skills_cache=self._skills_cache,
            adj_out=self._adj_out,
            adj_in=self._adj_in,
        )

    def route_intent(
        self, intent: str, top_k: int = 3, min_confidence: float = 0.20
    ) -> dict[str, Any]:
        """Route natural language task intent to candidate skills with confidence scores."""
        self._ensure_scanned(self._default_root)
        return route_skill_intent(
            intent=intent,
            skills_cache=self._skills_cache,
            idf_table=self._idf_table,
            chain_fn=self.get_chain,
            top_k=top_k,
            min_confidence=min_confidence,
        )

    def get_chain(
        self,
        start_skill: str,
        target_skill: str,
        *,
        fallback_direct: bool = False,
        include_synthetic: bool = False,
    ) -> SkillChainResult:
        """Calculate the shortest directed execution path between two skills using BFS."""
        self._ensure_scanned(self._default_root)
        return compute_skill_chain(
            start_skill=start_skill,
            target_skill=target_skill,
            skills_cache=self._skills_cache,
            neighbors_fn=self._get_neighbors,
            fallback_direct=fallback_direct,
            include_synthetic=include_synthetic,
        )

    def _ensure_scanned(self, root_dir: str) -> None:
        """Scan workspace directories if not yet populated or if 30s elapsed (Rule 52)."""
        now = time.time()
        if self._skills_cache and (now - self._last_scan_time) < 30.0:
            return

        with self._scan_lock:
            if self._skills_cache and (time.time() - self._last_scan_time) < 30.0:
                return

            disc, cats, adj, synth, edges, idf = scan_skills_catalog(root_dir)

            self._edges.clear()
            self._edge_keys.clear()
            self._adj_out.clear()
            self._adj_in.clear()

            for edge in edges:
                self._add_edge(edge.source, edge.target, edge.relation, edge.weight)

            self._skills_cache = disc
            self._categories = cats
            self._adjacency = adj
            self._synthetic_adjacency = synth
            self._idf_table = idf
            self._last_scan_time = now

    def _parse_skill_directory(self, skill_dir: Path) -> SkillCardDefinition | None:
        """Parse SKILL.md and companion CARD.md from a skill directory via authoritative SkillCardParser."""
        from harness.services.skill_parser import SkillCardParser

        return SkillCardParser.parse_directory(skill_dir)

    def link_knowledge_vault(self, vault_dir: Path | str = ".harness/knowledge") -> int:
        """Scan dual-file on-disk knowledge vault and link matching KIs to registered skills."""
        self._ensure_scanned(self._default_root)
        return link_knowledge_vault_items(self._skills_cache, vault_dir=vault_dir)


class BuiltinSkillGraphService(SkillGraphService):
    """Authoritative Skill Graph service implementation fulfilling SkillGraphService protocol."""

    def __init__(self, registry: BuiltinSkillRegistryService | None = None) -> None:
        self._registry = registry or BuiltinSkillRegistryService()

    @property
    def registry(self) -> BuiltinSkillRegistryService:
        return self._registry

    async def index(self, root_dir: str = ".") -> int:
        """Scan and index all skill cards in the workspace."""
        skills = self._registry.discover_all(root_dir)
        return len(skills)

    async def find_chain(
        self, start_skill: str, target_skill: str, fallback_direct: bool = False
    ) -> list[str]:
        """Compute execution path between two skills."""
        res = self._registry.get_chain(
            start_skill, target_skill, fallback_direct=fallback_direct
        )
        return list(res.chain)

    async def query_router(self, intent: str, top_k: int = 3) -> dict[str, Any]:
        """Route natural language task intent to matching skills."""
        return self._registry.route_intent(intent, top_k=top_k)

    async def get_topology(self, skill_name: str) -> dict[str, Any]:
        """Inspect topological dependencies, handoffs, and anti-patterns for a skill."""
        try:
            topo = self._registry.get_topology(skill_name)
            return {
                "status": "ok",
                "skill": skill_name,
                "topology": {
                    "skill": {"name": topo.skill.name, "category": topo.skill.category},
                    "prerequisites": list(topo.prerequisites),
                    "downstream_handoffs": list(topo.downstream_handoffs),
                    "complements": list(topo.complements),
                    "mitigated_anti_patterns": list(topo.mitigated_anti_patterns),
                },
            }
        except KeyError as e:
            return {"status": "error", "message": str(e)}

    async def export_html_brief(self, output_path: str | None = None) -> str:
        """Generate and save interactive HTML visual brief."""
        return self._registry.export_html_brief(output_path=output_path)

    async def link_knowledge_vault(self, vault_dir: str = ".harness/knowledge") -> int:
        """Cross-link knowledge vault items to skills."""
        return self._registry.link_knowledge_vault(vault_dir=vault_dir)

    async def cluster_skills(self, min_cluster_size: int = 2) -> list[dict[str, Any]]:
        """Cluster workspace skills into functional capability domains."""
        clusters = self._registry.cluster_skills(min_cluster_size=min_cluster_size)
        return [
            c.model_dump() if hasattr(c, "model_dump") else {
                "cluster_id": c.cluster_id,
                "name": c.name,
                "skills": list(c.skills),
            }
            for c in clusters
        ]

    async def discover_emergent_capabilities(
        self, query: str | None = None
    ) -> list[dict[str, Any]]:
        """Discover novel emergent capabilities across skill clusters."""
        caps = self._registry.discover_emergent_capabilities(query=query)
        return [
            c.model_dump() if hasattr(c, "model_dump") else {
                "capability_id": getattr(c, "capability_id", getattr(c, "id", "")),
                "title": getattr(c, "title", getattr(c, "name", "")),
                "primary_skills": list(getattr(c, "primary_skills", [])),
            }
            for c in caps
        ]

    async def get_cross_cluster_bridges(self) -> list[dict[str, Any]]:
        """Discover cross-domain macro-bridges connecting distinct clusters."""
        bridges = self._registry.get_cross_cluster_bridges()
        return [
            b.model_dump() if hasattr(b, "model_dump") else {
                "source_cluster": b.source_cluster,
                "target_cluster": b.target_cluster,
                "bridge_skills": list(getattr(b, "bridge_skills", [])),
            }
            for b in bridges
        ]

    async def select_skills_for_task(
        self, task: str, max_skills: int = 5, include_verifier: bool = True
    ) -> dict[str, Any]:
        """Select skills and generate an execution plan for an agent task."""
        plan = self._registry.select_skills_for_task(
            task, max_skills=max_skills, include_verifier=include_verifier
        )
        if hasattr(plan, "model_dump"):
            return plan.model_dump()
        return {
            "task": plan.task,
            "selected_skills": list(plan.selected_skills),
            "ordered_pipeline": list(plan.ordered_pipeline),
            "execution_pipeline": list(plan.execution_pipeline),
            "confidence": plan.confidence,
            "rationale": plan.rationale,
            "stages": [
                {
                    "skill": s.skill,
                    "stage_num": s.stage_num,
                    "name": s.name,
                    "completion_gate": s.completion_gate,
                }
                for s in plan.stages
            ],
        }

    async def get_prerequisite_closure(self, skill_name: str) -> list[str]:
        """Compute the full transitive prerequisite closure for a skill in topological execution order."""
        return self._registry.get_prerequisite_closure(skill_name)

    async def compile_execution_guidance(
        self, task: str, max_skills: int = 4
    ) -> SkillExecutionGuidance:
        """Compile an end-to-end execution guidance plan for an agent task."""
        return self._registry.compile_execution_guidance(task, max_skills=max_skills)

    def get_edges(self, skill_name: str | None = None) -> list[SkillEdge]:
        """Retrieve graph relationship edges, optionally filtered by skill name."""
        if skill_name:
            out_edges = self._registry.get_outgoing_edges(skill_name)
            in_edges = self._registry.get_incoming_edges(skill_name)
            seen: set[tuple[str, str, Any]] = set()
            result: list[SkillEdge] = []
            for e in out_edges + in_edges:
                key = (e.source, e.target, e.relation)
                if key not in seen:
                    seen.add(key)
                    result.append(e)
            return result
        return self._registry.edges

    def find_shortest_chain(
        self, start_skill: str, target_skill: str, fallback_direct: bool = False
    ) -> SkillChainResult:
        """Synchronous wrapper for finding shortest execution chain between two skills."""
        return self._registry.get_chain(
            start_skill, target_skill, fallback_direct=fallback_direct
        )

    def evaluate_chain_feasibility(
        self, chain: list[str], context: Any = None
    ) -> tuple[bool, list[str]]:
        """Synchronously check whether all declared service preconditions are satisfied."""
        return self._registry.evaluate_chain_feasibility(chain, context=context)

    def intercept_action(
        self,
        action_name: str,
        action_input: dict[str, Any],
        active_skills: list[str] | None = None,
    ) -> list[AntiPatternViolation]:
        """Intercept proposed tool invocation and parameters against anti-patterns."""
        return self._registry.intercept_action(
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
        """Evaluate proposed tool invocation against anti-patterns and AST gates."""
        return self._registry.evaluate_action_gate(
            action_name=action_name,
            action_input=action_input,
            active_skills=active_skills,
        )


_DEFAULT_REGISTRY: BuiltinSkillRegistryService | None = None
_DEFAULT_GRAPH: BuiltinSkillGraphService | None = None
_INIT_LOCK = threading.Lock()


def get_default_skill_registry(root_dir: str = ".") -> BuiltinSkillRegistryService:
    """Retrieve or construct the process-level default BuiltinSkillRegistryService singleton."""
    global _DEFAULT_REGISTRY
    if _DEFAULT_REGISTRY is None:
        with _INIT_LOCK:
            if _DEFAULT_REGISTRY is None:
                _DEFAULT_REGISTRY = BuiltinSkillRegistryService(default_root=root_dir)
    return _DEFAULT_REGISTRY


def get_default_skill_graph(root_dir: str = ".") -> BuiltinSkillGraphService:
    """Retrieve or construct the process-level default BuiltinSkillGraphService singleton."""
    global _DEFAULT_GRAPH
    if _DEFAULT_GRAPH is None:
        with _INIT_LOCK:
            if _DEFAULT_GRAPH is None:
                reg = get_default_skill_registry(root_dir=root_dir)
                _DEFAULT_GRAPH = BuiltinSkillGraphService(registry=reg)
    return _DEFAULT_GRAPH


def resolve_skill_intelligence(
    context: Any = None, root_dir: str = "."
) -> SkillIntelligenceService:
    """Authoritative single-source factory seam to resolve SkillIntelligenceService (Rule 58)."""
    if context is not None and hasattr(context, "optional"):
        intel = context.optional(SKILL_INTELLIGENCE_KEY)
        if intel is not None:
            if isinstance(intel, SkillIntelligenceService):
                return intel
            return SkillIntelligenceAdapter(intel)
        reg = context.optional(SKILL_REGISTRY_KEY)
        if reg is not None:
            if isinstance(reg, SkillIntelligenceService):
                return reg
            return SkillIntelligenceAdapter(reg)
        from harness.services.skill_clustering import SKILL_CLUSTERING_KEY

        clust = context.optional(SKILL_CLUSTERING_KEY)
        if clust is not None:
            if isinstance(clust, SkillIntelligenceService):
                return clust
            return SkillIntelligenceAdapter(clust)

    return get_default_skill_registry(root_dir=root_dir)


__all__ = [
    "BuiltinSkillGraphService",
    "BuiltinSkillRegistryService",
    "SkillIntelligenceAdapter",
    "SkillRegistryPlugin",
    "get_default_skill_graph",
    "get_default_skill_registry",
    "resolve_skill_intelligence",
]
