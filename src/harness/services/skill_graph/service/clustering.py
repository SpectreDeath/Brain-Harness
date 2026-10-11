"""Clustering and emergent capability delegation for BuiltinSkillRegistryService."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from harness.services.skill_clustering import (
    CrossClusterBridge,
    EmergentCapability,
    SkillCluster,
    SkillClusteringEngine,
    SkillSelectionPlan,
)

if TYPE_CHECKING:
    from harness.services.skill_graph.service.registry import BuiltinSkillRegistryService


class RegistryClusteringMixin:
    """Clustering, bridges, emergent capabilities, and task skill selection."""

    def _get_clustering_engine(self: BuiltinSkillRegistryService) -> SkillClusteringEngine:
        self._ensure_scanned(self._default_root)
        if self._clustering_engine is None:
            self._clustering_engine = SkillClusteringEngine(self._skills_cache, registry=self)
        return self._clustering_engine

    def cluster_skills(self: BuiltinSkillRegistryService, min_cluster_size: int = 2) -> list[SkillCluster]:
        return self._get_clustering_engine().cluster_skills(min_cluster_size=min_cluster_size)

    def discover_emergent_capabilities(
        self: BuiltinSkillRegistryService, query: str | None = None
    ) -> list[EmergentCapability]:
        return self._get_clustering_engine().discover_emergent_capabilities(query=query)

    def get_cross_cluster_bridges(self: BuiltinSkillRegistryService) -> list[CrossClusterBridge]:
        return self._get_clustering_engine().get_cross_cluster_bridges()

    def select_skills_for_task(
        self: BuiltinSkillRegistryService,
        task: str,
        max_skills: int = 5,
        include_verifier: bool = True,
    ) -> SkillSelectionPlan:
        return self._get_clustering_engine().select_skills_for_task(
            task=task, max_skills=max_skills, include_verifier=include_verifier
        )
