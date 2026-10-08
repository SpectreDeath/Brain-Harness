"""Data models, slotted guidance structures, and constants for Skill Knowledge Graph."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


@dataclass(slots=True, frozen=True)
class SkillExecutionGuidance:
    """Slotted and frozen execution guidance plan synthesized from skill graph (Rule 12 & Rule 43)."""

    task: str
    selected_skills: tuple[str, ...] = field(default_factory=tuple)
    execution_pipeline: tuple[str, ...] = field(default_factory=tuple)
    stages: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    active_anti_patterns: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    confidence: float = 0.0

    def __post_init__(self) -> None:
        assert isinstance(self.task, str), "task must be a string"

    @property
    def should_inject(self) -> bool:
        """Whether this guidance plan has sufficient confidence and pipeline steps for injection."""
        return self.confidence > 0.20 and len(self.execution_pipeline) > 0

    def format_system_prompt_block(self) -> str:
        """Render formatted system prompt Markdown block for ReAct / autonomous agent context injection."""
        if not self.should_inject:
            return ""
        lines = [
            "\n\n## Active Skill Knowledge Guidance",
            f"Recommended Pipeline: {' -> '.join(self.execution_pipeline)}",
        ]
        if self.stages:
            lines.append("Key Stage Gates:")
            for st in self.stages[:4]:
                gate = st.get("completion_gate", "")
                skill_name = st.get("skill", "")
                stage_name = st.get("name", "")
                lines.append(f" - [{skill_name}] {stage_name}: {gate}")
        if self.active_anti_patterns:
            lines.append("Guarded Anti-Patterns:")
            for ap in self.active_anti_patterns[:3]:
                ap_name = ap.get("anti_pattern", "")
                skill_name = ap.get("skill", "")
                lines.append(f" - {ap_name} ({skill_name})")
        return "\n".join(lines)

    def inject_into_message(self, message: Any) -> Any:
        """Inject execution guidance into an LLMMessage system prompt cleanly without caller string munging."""
        block = self.format_system_prompt_block()
        if not block:
            return message
        if hasattr(message, "content"):
            from harness.services.llm import LLMMessage

            return LLMMessage(
                role=getattr(message, "role", "system"),
                content=message.content + block,
            )
        return message


class SkillStageDefinition(BaseModel):
    """Execution stage within an agent skill."""

    stage_num: int = Field(..., description="Stage sequence number (1-indexed)")
    name: str = Field(..., description="Stage title")
    completion_gate: str = Field(default="", description="Crisp completion criterion")
    objective: str = Field(default="", description="Stage objective summary")
    primary_artifact: str = Field(
        default="", description="Artifact produced by this stage"
    )
    consumes: list[str] = Field(
        default_factory=list, description="Artifact types this stage requires as input"
    )

    @property
    def title(self) -> str:
        """Alias for name."""
        return self.name


class SkillAntiPatternDefinition(BaseModel):
    """Guarded failure mode within a skill."""

    name: str = Field(..., description="Anti-pattern identifier")
    symptom: str = Field(default="", description="Telltale failure symptom")
    remedy: str = Field(default="", description="Prescribed corrective pattern")

    @property
    def description(self) -> str:
        """Alias for symptom."""
        return self.symptom

    @property
    def mitigation(self) -> str:
        """Alias for remedy."""
        return self.remedy


class AntiPatternViolation(BaseModel):
    """Identified anti-pattern violation within an execution proposal."""

    skill_name: str = Field(
        ..., description="Skill declaring the violated anti-pattern"
    )
    anti_pattern: str = Field(..., description="Anti-pattern name")
    symptom: str = Field(default="", description="Declared failure symptom")
    remedy: str = Field(default="", description="Prescribed corrective action")
    matched_phrase: str = Field(
        default="", description="Phrase or token triggering the violation"
    )


class InvariantViolation(BaseModel):
    """Identified invariant violation within an execution proposal."""

    skill_name: str = Field(
        ..., description="Skill declaring the violated invariant"
    )
    rule: str = Field(..., description="Invariant rule description or assertion")
    matched_phrase: str = Field(
        default="", description="Phrase or token triggering the violation"
    )
    is_blocking: bool = Field(
        default=True, description="Whether violation blocks execution"
    )
    remedy: str = Field(
        default="Adhere strictly to the skill invariant rule",
        description="Prescribed corrective action",
    )

    @property
    def anti_pattern(self) -> str:
        """Alias for anti_pattern to provide unified polymorphism with AntiPatternViolation."""
        return f"Invariant Violation: {self.rule}"

    @property
    def symptom(self) -> str:
        """Alias for symptom."""
        return f"Violation of mandatory invariant: {self.rule}"


@dataclass(slots=True, frozen=True)
class ActionGateResult:
    """Slotted and frozen action gate evaluation result (Rule 12)."""

    action_name: str
    is_blocked: bool = False
    violations: tuple[Any, ...] = field(default_factory=tuple)
    observation: dict[str, Any] = field(default_factory=dict)

    def to_observation(self) -> dict[str, Any]:
        """Return the actionable ReAct observation dictionary for in-flight self-repair."""
        return dict(self.observation) if self.observation else {"status": "ok"}


class SkillInvariantDefinition(BaseModel):
    """Guarded non-negotiable invariant rule within a skill."""

    rule: str = Field(..., description="Invariant rule description or assertion")
    is_blocking: bool = Field(
        default=True, description="Whether violation blocks execution"
    )


class SkillCardDefinition(BaseModel):
    """Parsed and validated Skill Card model."""

    name: str = Field(..., description="Skill kebab-case identifier")
    category: str = Field(default="general", description="Domain classification")
    invocation: str = Field(
        default="", description="Command / trigger format e.g. /deepen-architecture"
    )
    triggers: list[str] = Field(
        default_factory=list, description="Natural language trigger phrases"
    )
    version: str = Field(default="1.0.0", description="Semantic version")
    target: str = Field(default="", description="Operational target summary")
    stages: list[SkillStageDefinition] = Field(
        default_factory=list, description="Execution progression"
    )
    anti_patterns: list[SkillAntiPatternDefinition] = Field(
        default_factory=list, description="Guarded anti-patterns"
    )
    invariants: list[SkillInvariantDefinition] = Field(
        default_factory=list, description="Guarded invariants"
    )
    dependencies: list[str] = Field(
        default_factory=list, description="Referenced peer skills"
    )
    knowledge_items: list[str] = Field(
        default_factory=list,
        description="Linked Knowledge Item IDs from Knowledge Vault",
    )
    services: list[str] = Field(
        default_factory=list, description="Required micro-kernel ServiceKey identifiers"
    )
    tools: list[str] = Field(default_factory=list, description="Required tool names")
    card_path: str = Field(default="", description="Path to companion CARD.md")
    skill_path: str = Field(default="", description="Path to authoritative SKILL.md")

    @property
    def references(self) -> list[str]:
        """Alias for dependencies to provide model interop."""
        return self.dependencies

    @property
    def description(self) -> str:
        """Alias for target to provide model interop."""
        return self.target


class EdgeType(str, Enum):
    """Semantic relationship types between skills and graph entities."""

    PRECEDES = "PRECEDES"
    REQUIRES = "REQUIRES"
    MITIGATES = "MITIGATES"
    BELONGS_TO = "BELONGS_TO"
    MANDATES = "MANDATES"
    ACTIVATES = "ACTIVATES"
    COMPLEMENTS = "COMPLEMENTS"
    FEEDS = "FEEDS"


class SkillEdge(BaseModel):
    """Directed relation between two nodes in the skill knowledge graph."""

    source: str = Field(..., description="Source node identifier")
    target: str = Field(..., description="Target node identifier")
    relation: EdgeType = Field(..., description="Semantic edge type")
    weight: float = Field(1.0, description="Graph edge traversal weight")
    metadata: dict[str, str] = Field(
        default_factory=dict, description="Additional relation metadata"
    )


class SkillTopologyReport(BaseModel):
    """Topological inspection report for a single skill."""

    skill: SkillCardDefinition
    prerequisites: list[str] = Field(
        default_factory=list, description="Upstream skills required"
    )
    downstream_handoffs: list[str] = Field(
        default_factory=list, description="Downstream skills enabled"
    )
    complements: list[str] = Field(
        default_factory=list, description="Complementary companion skills"
    )
    mitigated_anti_patterns: list[str] = Field(
        default_factory=list, description="Failure modes mitigated"
    )


class SkillChainResult(BaseModel):
    """Topological execution chain between skills."""

    status: str = Field(default="ok", description="ok or no_path")
    start_skill: str = Field(..., description="Origin skill")
    target_skill: str = Field(..., description="Destination skill")
    chain: list[str] = Field(default_factory=list, description="Ordered skill names")
    length: int = Field(default=0, description="Step count")


# Backward-compatible model aliases for plugins, swarms, and tests (Rule 49 & Deepening Seam)
SkillNode = SkillCardDefinition
StageNode = SkillStageDefinition
AntiPatternNode = SkillAntiPatternDefinition
InvariantNode = SkillInvariantDefinition

# Canonical pipeline precedence pairs (single source of truth for graph routing and synthetic DAG edges)
CANONICAL_PIPELINE_PRECEDENCE: list[tuple[str, str]] = [
    ("structured-data-scout", "data-topology-mapper"),
    ("data-topology-mapper", "epistemic-isnad-audit"),
    ("epistemic-isnad-audit", "questio-reflection"),
    ("codebase-design", "deepen-architecture"),
    ("questio-reflection", "deepen-architecture"),
    ("crafting-skills", "questio-reflection"),
    ("repo-reader", "repo-to-plugin-forge"),
    ("repo-to-plugin-forge", "deepen-architecture"),
    ("mind-reader", "repo-to-plugin-forge"),
    ("mind-reader", "harness-reflector"),
    ("deepen-architecture", "crafting-skills"),
]

__all__ = [
    "CANONICAL_PIPELINE_PRECEDENCE",
    "ActionGateResult",
    "AntiPatternNode",
    "AntiPatternViolation",
    "EdgeType",
    "InvariantNode",
    "InvariantViolation",
    "SkillAntiPatternDefinition",
    "SkillCardDefinition",
    "SkillChainResult",
    "SkillEdge",
    "SkillExecutionGuidance",
    "SkillInvariantDefinition",
    "SkillNode",
    "SkillStageDefinition",
    "SkillTopologyReport",
    "StageNode",
]
