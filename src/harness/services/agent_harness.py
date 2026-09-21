"""AgentHarnessArchitect service protocol, typed models, and ServiceKey."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, Field

from harness.kernel.context import ServiceKey


class HarnessComponentStatusData(BaseModel):
    """Audit status of an individual harness component within the 5-Part Architecture."""

    name: str = Field(..., description="Name of the harness component")
    present: bool = Field(default=False, description="Whether the component is detected")
    score: float = Field(default=0.0, description="Component readiness score 0.0 to 1.0")
    details: str = Field(..., description="Diagnostic rationale or findings")


class FivePartHarnessAuditData(BaseModel):
    """Aggregate audit covering the Core 5-Part Harness Architecture."""

    model_core: HarnessComponentStatusData
    tool_router: HarnessComponentStatusData
    memory_context: HarnessComponentStatusData
    planning_gate: HarnessComponentStatusData
    sandbox_boundary: HarnessComponentStatusData
    overall_score: float = Field(default=0.0, description="Mean 5-part architecture score")
    passed: bool = Field(default=False, description="Whether overall score >= 0.80")


class MechanismReliabilityScoreData(BaseModel):
    """Scorecard assessment of an individual reliability mechanism across Level 0 to Level 2."""

    name: str = Field(..., description="Name of the reliability mechanism")
    level: int = Field(default=0, description="Scored level: 0 (Toy), 1 (Intermediate), 2 (Production)")
    level_name: str = Field(..., description="Descriptive label for scored level")
    rationale: str = Field(..., description="Diagnostic explanation for level classification")
    passed_l2_gate: bool = Field(default=False, description="Whether mechanism achieves Level 2 gate")


class FourMechanismReliabilityGateData(BaseModel):
    """Assessment of the 4 Reliability Mechanisms (Planning, Sandbox, Subagents, Compression)."""

    planning: MechanismReliabilityScoreData
    sandbox: MechanismReliabilityScoreData
    subagents: MechanismReliabilityScoreData
    compression: MechanismReliabilityScoreData
    observability: MechanismReliabilityScoreData
    overall_level: int = Field(default=0, description="Minimum mechanism level")
    meets_l2_production_gate: bool = Field(
        default=False, description="Whether production reliability gate is fully met"
    )


class FourLayerStackAuditData(BaseModel):
    """Decoupling verification across the 4-Layer Agent Stack."""

    layer1_mcp: bool = Field(default=True, description="Protocol layer decoupling (MCP)")
    layer2_harness: bool = Field(default=True, description="Single-agent ReAct harness loop")
    layer3_orchestration: bool = Field(default=True, description="Multi-agent orchestration graphs")
    layer4_observability_sandbox: bool = Field(
        default=True, description="Observability & disposable sandbox execution"
    )
    clean_boundaries: bool = Field(
        default=True, description="Whether 4-layer boundaries are strictly decoupled"
    )
    details: dict[str, str] = Field(default_factory=dict, description="Per-layer verification notes")


class ArchitecturalBetRecommendationData(BaseModel):
    """Strategic recommendation matching team operational bottleneck to one of four 2026 harness bets."""

    recommended_bet: str = Field(..., description="Archetype bet: modularity, fixed_reliability, compounding_memory, radical_minimalism")
    archetype_name: str = Field(..., description="Representative harness name (e.g. dsh, claude-code)")
    rationale: str = Field(..., description="Diagnostic justification for selection")
    tradeoffs: list[str] = Field(default_factory=list, description="Accepted architectural tradeoffs")
    adoption_profile: str = Field(default="compounding_production", description="Team adoption profile")


class HarnessAuditReportData(BaseModel):
    """Authoritative comprehensive harness evaluation report."""

    target_path: str = Field(..., description="Scanned directory or workspace path")
    five_part_audit: FivePartHarnessAuditData
    reliability_gate: FourMechanismReliabilityGateData
    stack_audit: FourLayerStackAuditData
    bet_recommendation: ArchitecturalBetRecommendationData
    triple_budget_enforced: bool = Field(
        default=False, description="Whether max_turns, cost cap, and subprocess timeouts are configured"
    )
    summary: str = Field(..., description="High-level evaluation narrative")
    timestamp: str = Field(..., description="ISO 8601 evaluation timestamp")


@runtime_checkable
class AgentHarnessArchitectService(Protocol):
    """Protocol for 5-part harness auditing, 4-mechanism reliability scoring, and stack boundary verification."""

    def audit(
        self,
        target_path: str | Path | None = None,
    ) -> HarnessAuditReportData | Any:
        """Execute comprehensive 5-part architecture and 4-layer boundary audit."""
        ...

    def evaluate_reliability(
        self,
        config_or_path: dict[str, Any] | str | Path | None = None,
    ) -> FourMechanismReliabilityGateData | Any:
        """Evaluate planning, sandbox, subagent, compression, and observability across Level 0 to Level 2."""
        ...

    def classify_bet(
        self,
        bottleneck: str | None = None,
        requirements: list[str] | None = None,
    ) -> ArchitecturalBetRecommendationData | Any:
        """Classify operational bottleneck into one of four architectural harness bets."""
        ...

    def visual_brief(
        self,
        audit_report: Any | None = None,
        target_path: str | Path | None = None,
        output_path: str | Path | None = None,
    ) -> Path:
        """Render interactive HTML visual brief with Mermaid topology and reliability scorecard."""
        ...


AGENT_HARNESS_ARCHITECT_SERVICE_KEY: ServiceKey[AgentHarnessArchitectService] = (
    ServiceKey("service.agent_harness_architect")
)
