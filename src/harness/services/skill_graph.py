"""Skill Knowledge Graph & Registry service protocol, typed models, and ServiceKey."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable
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


@runtime_checkable
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


@runtime_checkable
class SkillRegistryService(Protocol):
    """Protocol for the authoritative workspace Skill Registry."""

    def discover_all(self, root_dir: str = ".") -> list[SkillCardDefinition]:
        """Discover and parse all skill cards across .agents/skills and skills/."""
        ...

    def get_skill(self, name: str) -> SkillCardDefinition | None:
        """Retrieve a skill definition by kebab-case name."""
        ...

    def route_intent(self, intent: str, top_k: int = 3) -> dict[str, Any]:
        """Route natural language task intent to candidate skills."""
        ...

    def get_chain(self, start_skill: str, target_skill: str) -> SkillChainResult:
        """Calculate execution chain between two skills."""
        ...


SKILL_GRAPH_KEY: ServiceKey[SkillGraphService] = ServiceKey("service.skill_knowledge_graph")
SKILL_REGISTRY_KEY: ServiceKey[SkillRegistryService] = ServiceKey("service.skill_registry")
