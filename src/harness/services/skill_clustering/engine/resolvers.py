"""Single-seam IoC resolver factory for SkillClusteringEngine (Rule 58)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from harness.kernel.context import ServiceKey

if TYPE_CHECKING:
    from harness.services.skill_clustering.engine.core import SkillClusteringEngine

SKILL_CLUSTERING_ENGINE_KEY: ServiceKey[SkillClusteringEngine] = ServiceKey(
    "service.skill_clustering_engine"
)


def resolve_skill_clustering_engine(target: Any = None) -> SkillClusteringEngine:
    """Resolve or construct SkillClusteringEngine instance via single seam (Rule 58)."""
    from harness.kernel.context import ServiceContext
    from harness.services.skill_clustering.engine.core import SkillClusteringEngine

    if target is not None:
        if isinstance(target, SkillClusteringEngine):
            return target
        if isinstance(target, ServiceContext):
            if target.has(SKILL_CLUSTERING_ENGINE_KEY):
                return target.require(SKILL_CLUSTERING_ENGINE_KEY)
            engine = SkillClusteringEngine()
            target.provide(SKILL_CLUSTERING_ENGINE_KEY, engine)
            return engine
        if hasattr(target, "clustering_engine") and isinstance(
            target.clustering_engine, SkillClusteringEngine
        ):
            return target.clustering_engine

    return SkillClusteringEngine()
