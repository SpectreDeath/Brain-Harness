"""Skill Knowledge Graph service protocol, typed models, and ServiceKey."""

from __future__ import annotations

from typing import Any, Protocol
from pydantic import BaseModel, Field

from harness.kernel.context import ServiceKey


class SkillStageDefinition(BaseModel):
    """Execution stage within an agent skill."""

    stage_num: int = Field(..., description="Stage sequence number (1-indexed)")
    name: str = Field(..., description="Stage title")
    completion_gate: str = Field(default="", description="Crisp completion criterion")


class SkillAntiPatternDefinition(BaseModel):
    """Guarded failure mode within a skill."""

    name: str = Field(..., description="Anti-pattern identifier")
    symptom: str = Field(default="", description="Telltale failure symptom")
    remedy: str = Field(default="", description="Prescribed corrective pattern")


class SkillCardDefinition(BaseModel):
    """Parsed and validated Skill Card model."""

    name: str = Field(..., description="Skill kebab-case identifier")
    category: str = Field(default="general", description="Domain classification")
    invocation: str = Field(default="", description="Command / trigger format e.g. /deepen-architecture")
    triggers: list[str] = Field(default_factory=list, description="Natural language trigger phrases")
    version: str = Field(default="1.0.0", description="Semantic version")
    target: str = Field(default="", description="Operational target summary")
    stages: list[SkillStageDefinition] = Field(default_factory=list, description="Execution progression")
    anti_patterns: list[SkillAntiPatternDefinition] = Field(default_factory=list, description="Guarded anti-patterns")
    dependencies: list[str] = Field(default_factory=list, description="Referenced peer skills")


class SkillChainResult(BaseModel):
    """Topological execution chain between skills."""

    status: str = Field(default="ok", description="ok or no_path")
    start_skill: str = Field(..., description="Origin skill")
    target_skill: str = Field(..., description="Destination skill")
    chain: list[str] = Field(default_factory=list, description="Ordered skill names")
    length: int = Field(default=0, description="Step count")


class SkillGraphService(Protocol):
    """Protocol for the Skill Knowledge Graph service."""

    async def index(self, root_dir: str = ".") -> int:
        """Scan and index all skill cards in the workspace."""
        ...

    async def find_chain(self, start_skill: str, target_skill: str) -> list[str]:
        """Compute execution path between two skills."""
        ...

    async def query_router(self, intent: str, top_k: int = 3) -> dict[str, Any]:
        """Route natural language task intent to matching skills."""
        ...

    async def export_html_brief(self, output_path: str | None = None) -> str:
        """Generate and save interactive HTML visual brief."""
        ...


SKILL_GRAPH_KEY: ServiceKey[SkillGraphService] = ServiceKey("service.skill_knowledge_graph")

