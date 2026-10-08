"""Skill Knowledge Graph Clustering, Emergent Capabilities, and Intelligent Selection.

Provides functional cluster detection, multi-skill macro-capability synthesis,
cross-cluster bridge discovery, and prerequisite-aware task execution planning.

Enforces:
- Rule 1: Everything is a plugin (registered via IoC container)
- Rule 2: Service keys are typed (SKILL_CLUSTERING_KEY: ServiceKey[SkillClusteringService])
- Rule 12: Slotted & frozen dataclasses / Pydantic models
- Rule 49: Skill-to-IoC micro-kernel seam elevation
- Rule 58: Single-seam resolver factory (resolve_skill_clustering)
"""

from __future__ import annotations

from harness.kernel.context import ServiceContext, ServiceKey
from harness.services.skill_clustering.engine import SkillClusteringEngine
from harness.services.skill_clustering.models import (
    CrossClusterBridge,
    EmergentCapability,
    SkillCluster,
    SkillSelectionPlan,
)
from harness.services.skill_clustering.patterns import CANONICAL_EMERGENT_PATTERNS
from harness.services.skill_clustering.service import (
    DefaultSkillClusteringService,
    SkillClusteringService,
)
from harness.services.skill_clustering.visualizer import generate_clustered_mermaid

SKILL_CLUSTERING_KEY: ServiceKey[SkillClusteringService] = ServiceKey(
    "service.skill_clustering"
)
SKILL_CLUSTERING_SERVICE_KEY = SKILL_CLUSTERING_KEY


def resolve_skill_clustering(
    ctx: ServiceContext | None = None,
) -> SkillClusteringService:
    """Resolve SkillClusteringService from IoC context or fall back to DefaultSkillClusteringService (Rule 58)."""
    if ctx is not None:
        svc = ctx.optional(SKILL_CLUSTERING_KEY)
        if svc is not None and isinstance(svc, SkillClusteringService):
            return svc
    return DefaultSkillClusteringService()


__all__ = [
    "CANONICAL_EMERGENT_PATTERNS",
    "CrossClusterBridge",
    "DefaultSkillClusteringService",
    "EmergentCapability",
    "SKILL_CLUSTERING_KEY",
    "SKILL_CLUSTERING_SERVICE_KEY",
    "SkillCluster",
    "SkillClusteringEngine",
    "SkillClusteringService",
    "SkillSelectionPlan",
    "generate_clustered_mermaid",
    "resolve_skill_clustering",
]
