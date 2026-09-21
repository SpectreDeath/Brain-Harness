"""UncertaintyGuard service protocol, typed models, and ServiceKey.

Elevates the 3-layer deterministic uncertainty interception architecture (Chidiebere Njoku 2026,
ki_njoku_uncertainty_aware_systems) into a first-class micro-kernel IoC service seam.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, Field

from harness.kernel.context import ServiceKey


class BoundaryReportData(BaseModel):
    """Payload representing Layer 1 input domain boundary evaluation."""

    is_valid: bool = Field(
        ..., description="Whether query aligns with operational domain"
    )
    score: float = Field(..., description="Cosine similarity alignment score")
    matched_domain: str = Field(
        default="", description="Closest operational domain centroid"
    )
    latency_ms: float = Field(
        ..., description="Gating execution latency in milliseconds"
    )
    reason: str = Field(..., description="Human-readable decision explanation")


class ScoredChunkData(BaseModel):
    """Payload for individual scored retrieval chunks."""

    chunk_id: str = Field(..., description="Unique chunk identifier")
    content: str = Field(..., description="Chunk text content")
    score: float = Field(..., description="Computed cosine relevance score")


class RetrievalReportData(BaseModel):
    """Payload representing Layer 2 retrieval quality & semantic distance scoring."""

    has_sufficient_context: bool = Field(
        ..., description="Whether top relevance score meets threshold"
    )
    top_score: float = Field(
        ..., description="Maximum relevance score across retrieved chunks"
    )
    min_threshold: float = Field(
        ..., description="Calibrated sufficiency threshold (default 0.60)"
    )
    scored_chunks: list[ScoredChunkData] = Field(
        default_factory=list, description="All scored chunks sorted by relevance"
    )
    action: str = Field(
        ...,
        description="Gating action: INJECT_CONTEXT | BLOCK_CONTEXT_AND_ESCALATE",
    )


class LogprobReportData(BaseModel):
    """Payload representing Layer 3 probabilistic logit analysis & output validation."""

    is_confident: bool = Field(
        ..., description="Whether average logprob meets threshold"
    )
    avg_logprob: float = Field(..., description="Sequence mean token log probability")
    perplexity: float = Field(
        ..., description="Text sequence perplexity exp(-avg_logprob)"
    )
    threshold: float = Field(
        ..., description="Calibrated logprob threshold (default -0.35)"
    )
    token_count: int = Field(..., description="Number of evaluated tokens")
    action: str = Field(
        ...,
        description="Gating action: DELIVER_RESPONSE | ACTIVATE_CALIBRATED_FALLBACK",
    )


class EscalationTicketData(BaseModel):
    """Payload representing an intentional HITL escalation ticket."""

    ticket_id: str = Field(..., description="Unique ticket identifier")
    timestamp: str = Field(..., description="UTC ISO-8601 creation timestamp")
    query: str = Field(..., description="User input query")
    failure_gate: str = Field(
        ...,
        description="Interception gate that triggered escalation: BOUNDARY_GATE | RETRIEVAL_GATE | LOGPROB_GATE",
    )
    reason: str = Field(..., description="Escalation rationale")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Contextual scoring metrics"
    )


class PipelineReportData(BaseModel):
    """Payload representing unified end-to-end 3-layer request interception outcome."""

    state: str = Field(
        ...,
        description="Lifecycle state: PASSED_VERIFIED | REJECTED_OUT_OF_DOMAIN | ESCALATED_LOW_CONTEXT | FALLBACK_UNCERTAIN_LOGPROBS",
    )
    gate_passed: int = Field(..., description="Highest gate successfully cleared (0-3)")
    total_latency_ms: float = Field(
        ..., description="Total execution latency in milliseconds"
    )
    boundary_result: BoundaryReportData = Field(
        ..., description="Layer 1 boundary evaluation"
    )
    retrieval_result: RetrievalReportData | None = Field(
        default=None, description="Layer 2 retrieval scoring"
    )
    logprob_result: LogprobReportData | None = Field(
        default=None, description="Layer 3 logprob audit"
    )
    escalation_ticket: EscalationTicketData | None = Field(
        default=None, description="Escalation ticket if triggered"
    )
    response_text: str = Field(..., description="Delivered or fallback response text")


class DocDebtClusterData(BaseModel):
    """Payload representing clustered documentation debt mined from repeated misses."""

    cluster_id: str = Field(..., description="Unique debt cluster identifier")
    representative_topic: str = Field(
        ..., description="Extracted common topic keywords"
    )
    query_count: int = Field(..., description="Number of failed queries in cluster")
    sample_queries: list[str] = Field(
        default_factory=list, description="Sample failed queries"
    )
    severity: str = Field(
        ..., description="Debt priority: LOW | MEDIUM | HIGH | CRITICAL"
    )


@runtime_checkable
class UncertaintyGuardService(Protocol):
    """Protocol for 3-layer deterministic uncertainty interception and overconfidence mitigation."""

    def verify_boundary(
        self,
        query: str,
        target_domains: list[str] | tuple[str, ...] | None = None,
        threshold: float | None = None,
    ) -> BoundaryReportData:
        """Evaluate Layer 1 input domain boundary gating (<1ms)."""
        ...

    def score_retrieval(
        self,
        user_query: str,
        retrieved_chunks: list[str] | list[dict[str, str]],
        minimum_relevance: float | None = None,
    ) -> RetrievalReportData:
        """Evaluate Layer 2 retrieval relevance and context sufficiency (default tau = 0.60)."""
        ...

    def validate_logprobs(
        self,
        token_logprobs: list[float],
        logprob_threshold: float | None = None,
    ) -> LogprobReportData:
        """Evaluate Layer 3 token generation log probabilities and perplexity (default tau = -0.35)."""
        ...

    def intercept_request(
        self,
        query: str,
        target_domains: list[str] | None = None,
        retrieved_chunks: list[str] | list[dict[str, str]] | None = None,
        token_logprobs: list[float] | None = None,
        draft_response: str = "",
        escalate_on_failure: bool = True,
    ) -> PipelineReportData:
        """Execute unified 3-layer request interception lifecycle with deterministic routing."""
        ...

    def mine_documentation_debt(
        self, failed_queries: list[str] | None = None
    ) -> list[DocDebtClusterData]:
        """Cluster under-retrieved queries to uncover missing or outdated documentation."""
        ...

    def generate_visual_brief(
        self,
        pipeline_result: PipelineReportData | dict[str, Any],
        output_path: str | Path | None = None,
    ) -> Path:
        """Generate interactive HTML visual brief in %TEMP% summarizing uncertainty interception."""
        ...


UNCERTAINTY_GUARD_SERVICE_KEY: ServiceKey[UncertaintyGuardService] = ServiceKey(
    "service.uncertainty_guard"
)
