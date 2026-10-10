"""Core algorithmic engine package for knowledge graph clustering and capability synthesis."""

from __future__ import annotations

from harness.services.skill_clustering.engine.affinity import compute_affinity_matrix
from harness.services.skill_clustering.engine.bridges import detect_cross_cluster_bridges
from harness.services.skill_clustering.engine.clusterer import cluster_skills
from harness.services.skill_clustering.engine.core import SkillClusteringEngine
from harness.services.skill_clustering.engine.emergent import (
    discover_emergent_capabilities,
    synthesize_cluster_capabilities,
)
from harness.services.skill_clustering.engine.planner import select_skills_for_task
from harness.services.skill_clustering.engine.resolvers import (
    SKILL_CLUSTERING_ENGINE_KEY,
    resolve_skill_clustering_engine,
)
from harness.services.skill_clustering.engine.scoring import score_skills_for_task
from harness.services.skill_clustering.engine.tokens import tokenize

__all__ = [
    "SKILL_CLUSTERING_ENGINE_KEY",
    "SkillClusteringEngine",
    "cluster_skills",
    "compute_affinity_matrix",
    "detect_cross_cluster_bridges",
    "discover_emergent_capabilities",
    "resolve_skill_clustering_engine",
    "score_skills_for_task",
    "select_skills_for_task",
    "synthesize_cluster_capabilities",
    "tokenize",
]
