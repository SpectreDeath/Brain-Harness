"""Service mixin implementations for Skill Knowledge Graph protocols."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from harness.services.skill_clustering import (
    CrossClusterBridge,
    EmergentCapability,
    SkillCluster,
    SkillSelectionPlan,
)
from harness.services.skill_graph import (
    ActionGateResult,
    AntiPatternViolation,
    SkillCardDefinition,
    SkillChainResult,
    SkillExecutionGuidance,
    SkillTopologyReport,
)

from .tools import (
    _ensure_indexed,
    cluster_skill_graph,
    discover_emergent_capabilities,
    export_skill_graph_visual,
    find_skill_chain,
    get_clustering_engine,
    get_skill_topology,
    index_skill_catalog,
    query_skill_router,
    select_skills_for_task,
)


class GraphServiceMixin:
    """Implements SkillGraphService protocol methods."""

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


class RegistryServiceMixin:
    """Implements SkillRegistryService protocol methods."""

    _registry: Any

    def _get_registry(self) -> Any:
        return self._registry

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


class ClusteringServiceMixin:
    """Implements SkillClusteringService protocol methods."""

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


class IntelligenceServiceMixin:
    """Implements SkillIntelligenceService protocol methods."""

    _registry: Any

    def _get_registry(self) -> Any:
        return self._registry

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
