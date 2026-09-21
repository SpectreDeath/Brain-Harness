"""AiNativeHarness service protocol, typed models, and ServiceKey."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, Field

from harness.kernel.context import ServiceKey


class BehavioralGateResultData(BaseModel):
    """Audit status of an individual behavioral verification gate."""

    name: str = Field(..., description="Name of the behavioral gate")
    gate_number: int = Field(..., description="Gate number 1 to 4")
    passed: bool = Field(default=False, description="Whether the gate criteria was met")
    score: float = Field(default=0.0, description="Gate score 0.0 to 1.0")
    metrics: dict[str, Any] = Field(default_factory=dict, description="Diagnostic metrics")
    details: str = Field(..., description="Diagnostic rationale or findings")
    duration_ms: float = Field(default=0.0, description="Execution duration in milliseconds")


class PartialPayloadOmissionAuditData(BaseModel):
    """Verification that partial payload updates do not quietly reset unmentioned fields."""

    passed: bool = Field(default=True, description="Whether omission test passed")
    tested_endpoints_count: int = Field(default=0, description="Number of inspected endpoints")
    unmentioned_fields_preserved: bool = Field(default=True, description="Unmentioned scopes preserved")
    details: str = Field(..., description="Diagnostic audit findings")


class FourGatesEvaluationData(BaseModel):
    """Comprehensive evaluation across the 4 Behavioral Verification Gates."""

    gate1_typecheck: BehavioralGateResultData
    gate2_coverage: BehavioralGateResultData
    gate3_e2e_simulation: BehavioralGateResultData
    gate4_live_demo: BehavioralGateResultData
    payload_omission_audit: PartialPayloadOmissionAuditData
    overall_score: float = Field(default=0.0, description="Composite four-gate score")
    all_passed: bool = Field(default=False, description="Whether all 4 gates and omission checks pass")
    disallowed_lint_budget: bool = Field(
        default=True, description="Whether gate budget was reserved for behavior instead of syntax linting"
    )


class DocDriftItemData(BaseModel):
    """Code-to-Doc drift item measuring commits modifying code path P since doc D(P) was updated."""

    doc_slug: str = Field(..., description="Document identifier slug")
    doc_path: str = Field(..., description="Relative path to documentation file")
    code_paths: list[str] = Field(default_factory=list, description="Associated code paths")
    commits_since_doc_update: int = Field(default=0, description="Number of commits since doc edit")
    drift_count: int = Field(default=0, description="Calculated drift count")
    status_badge: str = Field(default="green", description="Badge indicator: green or amber")
    last_commit_hash: str | None = Field(default=None, description="Last commit hash modifying code")


class HarnessDocDriftReportData(BaseModel):
    """Collection of code-to-doc drift metrics across repository assets."""

    items: list[DocDriftItemData] = Field(default_factory=list, description="Monitored doc items")
    total_drift_count: int = Field(default=0, description="Sum of all drift counts")
    has_drift: bool = Field(default=False, description="True if any asset is drifted")
    amber_count: int = Field(default=0, description="Count of amber drifted docs")
    green_count: int = Field(default=0, description="Count of synchronized green docs")


class McpSecurityCheckData(BaseModel):
    """Verification of credential-free enterprise MCP server posture."""

    zero_stored_credentials: bool = Field(default=True, description="Holds 0 DB credentials")
    forward_user_tokens: bool = Field(default=True, description="Forwards user PAT on every invocation")
    dynamic_rbac_enabled: bool = Field(default=True, description="Enforces dynamic live RBAC checks")
    sanitized_403_forbidden: bool = Field(default=True, description="Returns sanitized 403 error payloads")
    identical_404_leak_defense: bool = Field(
        default=True, description="Returns identical 404 responses to eliminate enumeration"
    )
    human_sme_workflow_markers: bool = Field(
        default=True, description="Enforces [!VERIFY] uncertainty and [!SME] approval gates"
    )
    passed: bool = Field(default=True, description="Overall MCP security pass status")
    score: float = Field(default=1.0, description="Security score 0.0 to 1.0")
    details: dict[str, str] = Field(default_factory=dict, description="Audit check details")


class NegativeQueryDemandItemData(BaseModel):
    """Clustered unanswered question indicating documentation or capability demand."""

    query_cluster: str = Field(..., description="Subject category of unanswered questions")
    demand_count: int = Field(default=1, description="Frequency of unanswered questions in cluster")
    priority: str = Field(default="medium", description="Priority tier: high, medium, low")
    suggested_doc_slug: str = Field(..., description="Target documentation slug to author or update")
    sample_queries: list[str] = Field(default_factory=list, description="Representative sample questions")


class NegativeBacklogReportData(BaseModel):
    """Automated documentation backlog synthesized from negative assistant telemetry."""

    items: list[NegativeQueryDemandItemData] = Field(default_factory=list, description="Demand clusters")
    total_unanswered_queries: int = Field(default=0, description="Total unanswered query count")
    total_clusters: int = Field(default=0, description="Distinct topic clusters")


class AiNativeHarnessAuditReportData(BaseModel):
    """Comprehensive AI-native harness governance report."""

    target_path: str = Field(..., description="Workspace root path audited")
    gates_evaluation: FourGatesEvaluationData
    doc_drift_report: HarnessDocDriftReportData
    mcp_security_check: McpSecurityCheckData
    negative_backlog: NegativeBacklogReportData
    operational_budgets_enforced: bool = Field(
        default=True, description="Whether max_turns and cost bounds are enforced"
    )
    summary: str = Field(..., description="Executive narrative summary")
    timestamp: str = Field(..., description="ISO 8601 audit timestamp")


@runtime_checkable
class AiNativeHarnessService(Protocol):
    """Protocol for 4 behavioral gates, credential-free MCP security, drift calculus, and demand mining."""

    def evaluate_gates(
        self,
        workspace_root: str | Path | None = None,
        config: dict[str, Any] | None = None,
    ) -> FourGatesEvaluationData | Any:
        """Execute and score the 4 Behavioral Verification Gates."""
        ...

    def calculate_code_to_doc_drift(
        self,
        workspace_root: str | Path | None = None,
        mappings: list[dict[str, Any]] | None = None,
    ) -> HarnessDocDriftReportData | Any:
        """Calculate Git code-to-doc commit drift across tracked assets."""
        ...

    def audit_mcp_security(
        self,
        mcp_config_or_path: dict[str, Any] | str | Path | None = None,
    ) -> McpSecurityCheckData | Any:
        """Audit MCP server configuration and endpoints for zero credentials and leak defense."""
        ...

    def mine_negative_backlog(
        self,
        queries: list[str] | None = None,
        logs_path: str | Path | None = None,
    ) -> NegativeBacklogReportData | Any:
        """Cluster and rank unanswered assistant queries into prioritized documentation demand."""
        ...

    def audit(
        self,
        workspace_root: str | Path | None = None,
    ) -> AiNativeHarnessAuditReportData | Any:
        """Execute full composite audit across all 3 pillars."""
        ...

    def visual_brief(
        self,
        audit_report: Any | None = None,
        workspace_root: str | Path | None = None,
        output_path: str | Path | None = None,
    ) -> Path:
        """Render interactive HTML visual brief with Mermaid topology and telemetry tables."""
        ...


AI_NATIVE_HARNESS_SERVICE_KEY: ServiceKey[AiNativeHarnessService] = (
    ServiceKey("service.ai_native_harness")
)
