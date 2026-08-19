"""Pydantic data schemas for the Skill Knowledge Graph plugin."""

from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, Field


class EdgeType(str, Enum):
    """Semantic relationship types between skills and graph entities."""

    PRECEDES = "PRECEDES"
    REQUIRES = "REQUIRES"
    MITIGATES = "MITIGATES"
    BELONGS_TO = "BELONGS_TO"
    MANDATES = "MANDATES"
    ACTIVATES = "ACTIVATES"
    COMPLEMENTS = "COMPLEMENTS"


class StageNode(BaseModel):
    """A discrete execution stage within a skill."""

    stage_num: int = Field(..., description="Stage sequence number (1-indexed)")
    name: str = Field(..., description="Short stage title")
    objective: str = Field("", description="Stage objective summary")
    primary_artifact: str = Field("", description="Artifact produced by this stage")
    completion_gate: str = Field("", description="Binary checkable completion criterion")


class AntiPatternNode(BaseModel):
    """A named failure mode guarded against by a skill."""

    name: str = Field(..., description="Named anti-pattern (e.g. 'Context Flooding')")
    description: str = Field("", description="Description of the failure mode")
    mitigation: str = Field("", description="Positive corrective action required")


class InvariantNode(BaseModel):
    """A non-negotiable architectural invariant or quality checklist item."""

    rule: str = Field(..., description="Rule assertion text")
    is_blocking: bool = Field(True, description="Whether this invariant halts execution if violated")


class SkillNode(BaseModel):
    """Core skill node representing an agent capability."""

    name: str = Field(..., description="Unique kebab-case skill identifier")
    category: str = Field("general", description="Skill category classification")
    version: str = Field("1.0.0", description="Skill semantic version")
    invocation: str = Field("", description="Slash command invocation (e.g. /questio-reflection)")
    triggers: list[str] = Field(default_factory=list, description="Trigger phrases and keywords")
    target: str = Field("", description="Target objective summary from CARD.md")
    description: str = Field("", description="Frontmatter description from SKILL.md")
    card_path: str = Field("", description="Path to companion CARD.md")
    skill_path: str = Field("", description="Path to authoritative SKILL.md")
    stages: list[StageNode] = Field(default_factory=list, description="Ordered execution stages")
    anti_patterns: list[AntiPatternNode] = Field(default_factory=list, description="Guarded anti-patterns")
    invariants: list[InvariantNode] = Field(default_factory=list, description="Mandatory invariants")
    references: list[str] = Field(default_factory=list, description="Referenced cross-skill names")


class SkillEdge(BaseModel):
    """Directed relation between two nodes in the skill knowledge graph."""

    source: str = Field(..., description="Source node identifier")
    target: str = Field(..., description="Target node identifier")
    relation: EdgeType = Field(..., description="Semantic edge type")
    weight: float = Field(1.0, description="Graph edge traversal weight")
    metadata: dict[str, str] = Field(default_factory=dict, description="Additional relation metadata")


class SkillTopologyReport(BaseModel):
    """Topological inspection report for a single skill."""

    skill: SkillNode
    prerequisites: list[str] = Field(default_factory=list, description="Upstream skills required")
    downstream_handoffs: list[str] = Field(default_factory=list, description="Downstream skills enabled")
    complements: list[str] = Field(default_factory=list, description="Complementary companion skills")
    mitigated_anti_patterns: list[str] = Field(default_factory=list, description="Failure modes mitigated")


class SkillMatch(BaseModel):
    """Ranked skill match from the semantic router."""

    skill_name: str
    category: str
    confidence: float
    matched_triggers: list[str] = Field(default_factory=list)
    reasoning: str = ""


class SkillRouterResult(BaseModel):
    """Result from query_skill_router."""

    query: str
    matches: list[SkillMatch] = Field(default_factory=list)
    recommended_chain: list[str] = Field(default_factory=list)


class SkillGraphSnapshot(BaseModel):
    """Full snapshot of the skill knowledge graph."""

    total_skills: int
    categories: list[str] = Field(default_factory=list)
    nodes: dict[str, SkillNode] = Field(default_factory=dict)
    edges: list[SkillEdge] = Field(default_factory=list)
