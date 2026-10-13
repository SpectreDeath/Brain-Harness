"""Data structure converters between engine results and service report models."""

from __future__ import annotations

from typing import Any

from harness.services.uncertainty_guard import (
    BoundaryReportData,
    DocDebtClusterData,
    EscalationTicketData,
    LogprobReportData,
    PipelineReportData,
    RetrievalReportData,
    ScoredChunkData,
)


def to_boundary_report(res: Any) -> BoundaryReportData:
    """Convert raw boundary verification result to BoundaryReportData."""
    return BoundaryReportData(
        is_valid=res.is_valid,
        score=res.score,
        matched_domain=res.matched_domain,
        latency_ms=res.latency_ms,
        reason=res.reason,
    )


def to_retrieval_report(res: Any) -> RetrievalReportData:
    """Convert raw retrieval scoring result to RetrievalReportData."""
    return RetrievalReportData(
        has_sufficient_context=res.has_sufficient_context,
        top_score=res.top_score,
        min_threshold=res.min_threshold,
        scored_chunks=[
            ScoredChunkData(
                chunk_id=c.chunk_id,
                content=c.content,
                score=c.score,
            )
            for c in res.scored_chunks
        ],
        action=res.action,
    )


def to_logprob_report(res: Any) -> LogprobReportData:
    """Convert raw logprob validation result to LogprobReportData."""
    return LogprobReportData(
        is_confident=res.is_confident,
        avg_logprob=res.avg_logprob,
        perplexity=res.perplexity,
        threshold=res.threshold,
        token_count=res.token_count,
        action=res.action,
    )


def to_escalation_ticket(ticket: Any) -> EscalationTicketData | None:
    """Convert raw escalation ticket to EscalationTicketData."""
    if not ticket:
        return None
    return EscalationTicketData(
        ticket_id=ticket.ticket_id,
        timestamp=ticket.timestamp,
        query=ticket.query,
        failure_gate=ticket.failure_gate,
        reason=ticket.reason,
        metadata=ticket.metadata,
    )


def to_pipeline_report(res: Any) -> PipelineReportData:
    """Convert raw request interception result to PipelineReportData."""
    ret_rep = to_retrieval_report(res.retrieval_result) if res.retrieval_result else None
    lp_rep = to_logprob_report(res.logprob_result) if res.logprob_result else None
    ticket = to_escalation_ticket(res.escalation_ticket)

    return PipelineReportData(
        state=res.state,
        gate_passed=res.gate_passed,
        total_latency_ms=res.total_latency_ms,
        boundary_result=to_boundary_report(res.boundary_result),
        retrieval_result=ret_rep,
        logprob_result=lp_rep,
        escalation_ticket=ticket,
        response_text=res.response_text,
    )


def to_doc_debt_clusters(clusters: list[Any]) -> list[DocDebtClusterData]:
    """Convert raw documentation debt clusters to DocDebtClusterData list."""
    return [
        DocDebtClusterData(
            cluster_id=c.cluster_id,
            representative_topic=c.representative_topic,
            query_count=c.query_count,
            sample_queries=list(c.sample_queries),
            severity=c.severity,
        )
        for c in clusters
    ]
