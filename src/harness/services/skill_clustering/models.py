"""Domain models for Skill Knowledge Graph clustering, capabilities, and selection."""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class EmergentCapability(BaseModel):
    """A novel macro-capability revealed by a composition or cluster of skills."""

    id: str = Field(..., description="Unique slug for this emergent capability")
    title: str = Field(..., description="Human-readable title")
    description: str = Field(..., description="Comprehensive description of the capability")
    cluster_id: str = Field(..., description="Associated cluster identifier")
    primary_skills: list[str] = Field(
        default_factory=list, description="Constituent skills forming the capability"
    )
    recommended_pipeline: list[str] = Field(
        default_factory=list, description="Topological execution order of skills"
    )
    novelty_rationale: str = Field(
        ..., description="Explanation of why this composite capability transcends individual skills"
    )
    guarded_anti_patterns: list[str] = Field(
        default_factory=list, description="Aggregated anti-patterns defended across the pipeline"
    )
    guaranteed_invariants: list[str] = Field(
        default_factory=list, description="Key invariants guaranteed by the composition"
    )
    keywords: list[str] = Field(
        default_factory=list, description="Target trigger keywords for capability routing"
    )
    target_outcomes: list[str] = Field(
        default_factory=list, description="Tangible artifacts and business outcomes produced"
    )

    @property
    def name(self) -> str:
        """Alias for title."""
        return self.title

    @property
    def composed_skills(self) -> list[str]:
        """Alias for primary_skills."""
        return self.primary_skills

    @property
    def synergy_score(self) -> float:
        """Emergent synergy confidence score."""
        return 0.85

    @property
    def novelty_type(self) -> str:
        """Emergent capability novelty classification."""
        return "cluster-synthesis" if "synth" in self.id else "canonical-pipeline"


class SkillCluster(BaseModel):
    """A functionally cohesive cluster of skills discovered from the knowledge graph."""

    cluster_id: str = Field(..., description="Unique identifier (e.g. cluster_repo_modernization)")
    name: str = Field(..., description="Human-readable cluster name")
    domain: str = Field(..., description="Primary domain / capability classification")
    skills: list[str] = Field(default_factory=list, description="List of member skill names")
    central_hub_skill: str = Field(
        ..., description="The most central / highly-referenced skill in the cluster"
    )
    categories: list[str] = Field(
        default_factory=list, description="Underlying skill categories in this cluster"
    )
    internal_edge_count: int = Field(
        default=0, description="Number of intra-cluster dependency / precedence edges"
    )
    cohesion_score: float = Field(
        default=0.0, description="Internal structural cohesion metric (0.0 - 1.0)"
    )
    emergent_capabilities: list[EmergentCapability] = Field(
        default_factory=list, description="Novel capabilities unlocked by this cluster"
    )

    @property
    def dominant_category(self) -> str:
        """Alias for domain."""
        return self.domain


class CrossClusterBridge(BaseModel):
    """A directed bridge between two clusters unlocking a cross-domain macro-capability."""

    source_cluster: str = Field(..., description="Originating cluster ID")
    target_cluster: str = Field(..., description="Destination cluster ID")
    bridge_skills: list[tuple[str, str]] = Field(
        default_factory=list, description="Pairs of (source_skill, target_skill) forming the link"
    )
    synergy_description: str = Field(
        ..., description="Cross-domain capability enabled by this bridge"
    )

    @property
    def source_skill(self) -> str:
        return self.bridge_skills[0][0] if self.bridge_skills else ""

    @property
    def target_skill(self) -> str:
        return self.bridge_skills[0][1] if self.bridge_skills else ""

    @property
    def bridge_weight(self) -> float:
        return float(len(self.bridge_skills))


class SkillSelectionPlan(BaseModel):
    """A fully compiled, prerequisite-aware skill selection plan for an agent task."""

    task: str = Field(..., description="The original task intent or user prompt")
    selected_skills: list[str] = Field(
        default_factory=list, description="Core skills directly selected to solve the task"
    )
    execution_pipeline: list[str] = Field(
        default_factory=list, description="Topological sequence of skills respecting direct prerequisites"
    )
    emergent_capability: EmergentCapability | None = Field(
        default=None, description="Matching emergent capability, if applicable"
    )
    primary_cluster: str | None = Field(
        default=None, description="Primary matching skill cluster ID"
    )
    prerequisites: list[str] = Field(
        default_factory=list, description="Immediate prerequisite skills needed before execution"
    )
    stages: list[dict[str, Any]] = Field(
        default_factory=list, description="Ordered stages with crisp completion gates"
    )
    active_anti_patterns: list[dict[str, str]] = Field(
        default_factory=list, description="Guarded failure modes across selected skills"
    )
    active_invariants: list[dict[str, Any]] = Field(
        default_factory=list, description="Invariants and checklist rules enforced"
    )
    recommended_verifier: str | None = Field(
        default="adversarial-agent-verifier",
        description="Tail verifier skill recommended to assert contract satisfaction",
    )
    confidence: float = Field(default=0.0, description="Selection match confidence (0.0 - 1.0)")
    rationale: str = Field(
        ..., description="Detailed architectural rationale for this skill selection"
    )

    @property
    def ordered_pipeline(self) -> list[str]:
        """Convenience alias for execution_pipeline."""
        return self.execution_pipeline

    @property
    def matched_skills(self) -> list[str]:
        """Convenience alias for selected_skills."""
        return self.selected_skills

    @property
    def clusters_involved(self) -> list[str]:
        """Convenience property returning involved clusters."""
        return [self.primary_cluster] if self.primary_cluster else []

    @property
    def tail_verifier(self) -> str | None:
        """Alias for recommended_verifier."""
        return self.recommended_verifier


__all__ = [
    "CrossClusterBridge",
    "EmergentCapability",
    "SkillCluster",
    "SkillSelectionPlan",
]
