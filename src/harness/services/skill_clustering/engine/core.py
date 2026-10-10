"""SkillClusteringEngine coordinator class orchestrating affinity, clustering, and planning."""

from __future__ import annotations

from typing import Any

from harness.services.skill_clustering.engine.affinity import compute_affinity_matrix
from harness.services.skill_clustering.engine.bridges import detect_cross_cluster_bridges
from harness.services.skill_clustering.engine.clusterer import cluster_skills
from harness.services.skill_clustering.engine.emergent import discover_emergent_capabilities
from harness.services.skill_clustering.engine.planner import select_skills_for_task
from harness.services.skill_clustering.engine.tokens import tokenize
from harness.services.skill_clustering.models import (
    CrossClusterBridge,
    EmergentCapability,
    SkillCluster,
    SkillSelectionPlan,
)
from harness.services.skill_clustering.patterns import CANONICAL_EMERGENT_PATTERNS


class SkillClusteringEngine:
    """Core algorithmic engine for knowledge graph clustering and capability synthesis."""

    # Canonical high-order capability patterns recognized across the Brain Harness ecosystem
    CANONICAL_EMERGENT_PATTERNS = CANONICAL_EMERGENT_PATTERNS

    def __init__(
        self,
        skills_input: dict[str, Any] | list[Any] | None = None,
        registry: Any = None,
    ) -> None:
        """Initialize engine with a dictionary, list, or authoritative SkillRegistryService."""
        self._registry = registry
        if skills_input is None and registry is not None:
            if hasattr(registry, "_skills_cache") and registry._skills_cache:
                self._skills = dict(registry._skills_cache)
            elif hasattr(registry, "discover_all"):
                self._skills = {s.name: s for s in registry.discover_all()}
            else:
                self._skills = {}
        elif isinstance(skills_input, list):
            self._skills = {
                getattr(s, "name", str(s)): s for s in skills_input
            }
        elif isinstance(skills_input, dict):
            self._skills = dict(skills_input)
        else:
            self._skills = {}

        self._clusters_cache: list[SkillCluster] | None = None
        self._bridges_cache: list[CrossClusterBridge] | None = None

    @classmethod
    def _tokenize(cls, text: str) -> set[str]:
        """Tokenize string into normalized keyword set, filtering common English stopwords."""
        return tokenize(text)

    def compute_affinity_matrix(self) -> dict[str, dict[str, float]]:
        """Compute pairwise structural and semantic affinity weights between skills with degree normalization."""
        return compute_affinity_matrix(self._skills, registry=self._registry, tokenize_fn=self._tokenize)

    def build_clusters(self, min_cluster_size: int = 2) -> list[SkillCluster]:
        """Alias for cluster_skills."""
        return self.cluster_skills(min_cluster_size=min_cluster_size)

    def cluster_skills(self, min_cluster_size: int = 2) -> list[SkillCluster]:
        """Cluster skills into functional domains using modular community detection."""
        if self._clusters_cache is not None:
            return self._clusters_cache

        adj = self.compute_affinity_matrix()
        clusters = cluster_skills(
            self._skills,
            adj,
            min_cluster_size=min_cluster_size,
            tokenize_fn=self._tokenize,
        )
        self._clusters_cache = clusters
        return clusters

    def discover_emergent_capabilities(
        self, query: str | None = None
    ) -> list[EmergentCapability]:
        """Retrieve all emergent capabilities across clusters, optionally filtered by query."""
        clusters = self.cluster_skills()
        return discover_emergent_capabilities(
            self._skills,
            clusters,
            query=query,
            tokenize_fn=self._tokenize,
        )

    def get_cross_cluster_bridges(self) -> list[CrossClusterBridge]:
        """Detect cross-cluster bridges where directed edges connect distinct capability clusters."""
        if self._bridges_cache is not None:
            return self._bridges_cache

        clusters = self.cluster_skills()
        bridges = detect_cross_cluster_bridges(self._skills, clusters)
        self._bridges_cache = bridges
        return bridges

    def detect_cross_cluster_bridges(self) -> list[CrossClusterBridge]:
        """Alias for get_cross_cluster_bridges."""
        return self.get_cross_cluster_bridges()

    def select_skills_for_task(
        self,
        task: str,
        max_skills: int = 5,
        include_verifier: bool = True,
    ) -> SkillSelectionPlan:
        """Analyze task intent and synthesize a prerequisite-aware execution plan."""
        return select_skills_for_task(
            skills=self._skills,
            registry=self._registry,
            task=task,
            max_skills=max_skills,
            include_verifier=include_verifier,
            tokenize_fn=self._tokenize,
            emergent_discover_fn=self.discover_emergent_capabilities,
        )
