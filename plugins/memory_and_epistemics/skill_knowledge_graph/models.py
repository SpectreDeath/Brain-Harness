"""Pydantic data schemas for the Skill Knowledge Graph plugin.

Re-exports unified canonical models from harness.services.skill_graph while
preserving backward-compatible model aliases for external callers.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from harness.services.skill_graph import (
    EdgeType,
    SkillAntiPatternDefinition,
    SkillCardDefinition,
    SkillEdge,
    SkillInvariantDefinition,
    SkillStageDefinition,
    SkillTopologyReport,
)

# Canonical model aliases for plugin backward compatibility
SkillNode = SkillCardDefinition
StageNode = SkillStageDefinition
AntiPatternNode = SkillAntiPatternDefinition
InvariantNode = SkillInvariantDefinition

__all__ = [
    "AntiPatternNode",
    "EdgeType",
    "InvariantNode",
    "SkillCardDefinition",
    "SkillEdge",
    "SkillGraphSnapshot",
    "SkillMatch",
    "SkillNode",
    "SkillRouterResult",
    "SkillTopologyReport",
    "StageNode",
]


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
    nodes: dict[str, SkillCardDefinition] = Field(default_factory=dict)
    edges: list[SkillEdge] = Field(default_factory=list)
