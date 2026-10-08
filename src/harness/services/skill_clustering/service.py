"""Service protocol and default standalone implementation for Skill Clustering."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from harness.services.skill_clustering.engine import SkillClusteringEngine
from harness.services.skill_clustering.models import (
    CrossClusterBridge,
    EmergentCapability,
    SkillCluster,
    SkillSelectionPlan,
)


@runtime_checkable
class SkillClusteringService(Protocol):
    """Service protocol for skill clustering, capability discovery, and execution planning."""

    def cluster_skills(self, min_cluster_size: int = 2) -> list[SkillCluster]:
        """Cluster workspace skills into functional capability domains."""
        ...

    def discover_emergent_capabilities(
        self, query: str | None = None
    ) -> list[EmergentCapability]:
        """Discover novel macro-capabilities revealed by the graph clusters."""
        ...

    def get_cross_cluster_bridges(self) -> list[CrossClusterBridge]:
        """Discover cross-domain macro-bridges connecting distinct clusters."""
        ...

    def select_skills_for_task(
        self,
        task: str,
        max_skills: int = 5,
        include_verifier: bool = True,
    ) -> SkillSelectionPlan:
        """Select skills and generate an execution plan for an agent task."""
        ...


class DefaultSkillClusteringService:
    """Default standalone implementation of SkillClusteringService (Rule 49, Rule 58)."""

    def __init__(
        self,
        skills_input: dict[str, Any] | list[Any] | None = None,
        skills_root: str | Path = ".",
        registry: Any = None,
    ) -> None:
        self._skills_input = skills_input
        self._skills_root = Path(skills_root)
        self._registry = registry
        self._engine: SkillClusteringEngine | None = None

    def _get_engine(self) -> SkillClusteringEngine:
        if self._engine is None:
            skills = self._skills_input
            if skills is None and self._registry is None:
                # Lazy standalone discovery using BuiltinSkillRegistryService if available
                try:
                    from harness.services.skill_graph import BuiltinSkillRegistryService

                    registry = BuiltinSkillRegistryService()
                    skills = {s.name: s for s in registry.discover_all(str(self._skills_root))}
                    self._registry = registry
                except Exception:
                    skills = {}
            self._engine = SkillClusteringEngine(skills_input=skills, registry=self._registry)
        return self._engine

    def cluster_skills(self, min_cluster_size: int = 2) -> list[SkillCluster]:
        """Cluster workspace skills into functional capability domains."""
        return self._get_engine().cluster_skills(min_cluster_size=min_cluster_size)

    def discover_emergent_capabilities(
        self, query: str | None = None
    ) -> list[EmergentCapability]:
        """Discover novel macro-capabilities revealed by the graph clusters."""
        return self._get_engine().discover_emergent_capabilities(query=query)

    def get_cross_cluster_bridges(self) -> list[CrossClusterBridge]:
        """Discover cross-domain macro-bridges connecting distinct clusters."""
        return self._get_engine().get_cross_cluster_bridges()

    def select_skills_for_task(
        self,
        task: str,
        max_skills: int = 5,
        include_verifier: bool = True,
    ) -> SkillSelectionPlan:
        """Select skills and generate an execution plan for an agent task."""
        return self._get_engine().select_skills_for_task(
            task=task, max_skills=max_skills, include_verifier=include_verifier
        )


__all__ = [
    "DefaultSkillClusteringService",
    "SkillClusteringService",
]
