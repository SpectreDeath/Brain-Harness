"""Uncertainty-Aware AI Pipeline CLI commands.

Provides headless Click CLI introspection for 3-layer deterministic uncertainty interception,
semantic distance gating, token logprob validation, and HITL escalation.
"""

from __future__ import annotations

import json as _json
import sys
from pathlib import Path
from typing import Any

import click
import structlog

from harness.kernel.context import ServiceContext
from harness.services.uncertainty_guard import (
    UNCERTAINTY_GUARD_SERVICE_KEY,
    BoundaryReportData,
    DocDebtClusterData,
    LogprobReportData,
    PipelineReportData,
    RetrievalReportData,
    UncertaintyGuardService,
)

logger = structlog.get_logger(__name__)


def get_uncertainty_service(
    context: ServiceContext | None = None,
) -> UncertaintyGuardService:
    """Resolve UncertaintyGuardService from context or fall back to plugin singleton."""
    if context is not None:
        svc = context.optional(UNCERTAINTY_GUARD_SERVICE_KEY)
        if svc is not None:
            return svc

    # Fallback to plugin singleton
    _ws_root = Path.cwd()
    if str(_ws_root) not in sys.path:
        sys.path.insert(0, str(_ws_root))
    if str(_ws_root / "src") not in sys.path:
        sys.path.insert(0, str(_ws_root / "src"))

    try:
        from plugins.agent_orchestration.uncertainty_guard.main import (
            plugin as guard_plugin,
        )

        return guard_plugin
    except Exception as exc:
        logger.warning("uncertainty_guard_plugin_fallback_failed", error=str(exc))
        skill_scripts = (
            _ws_root
            / ".agents"
            / "skills"
            / "uncertainty-aware-ai-architect"
            / "scripts"
        )
        if str(skill_scripts) not in sys.path:
            sys.path.insert(0, str(skill_scripts))
        from uncertainty_guard_engine import (  # type: ignore
            UncertaintyGuardEngine,
        )

        class _EngineAdapter(UncertaintyGuardService):
            def __init__(self) -> None:
                self._eng = UncertaintyGuardEngine()

            def verify_boundary(
                self,
                query: str,
                target_domains: list[str] | tuple[str, ...] | None = None,
                threshold: float | None = None,
            ) -> BoundaryReportData:
                res = self._eng.verify_boundary(
                    query, target_domains=target_domains, threshold=threshold
                )
                return BoundaryReportData(
                    is_valid=res.is_valid,
                    score=res.score,
                    matched_domain=res.matched_domain,
                    latency_ms=res.latency_ms,
                    reason=res.reason,
                )

            def score_retrieval(
                self,
                user_query: str,
                retrieved_chunks: list[str] | list[dict[str, str]],
                minimum_relevance: float | None = None,
            ) -> RetrievalReportData:
                res = self._eng.score_retrieval(
                    user_query,
                    retrieved_chunks,
                    minimum_relevance=minimum_relevance,
                )
                from harness.services.uncertainty_guard import ScoredChunkData

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

            def validate_logprobs(
                self,
                token_logprobs: list[float],
                logprob_threshold: float | None = None,
            ) -> LogprobReportData:
                res = self._eng.validate_logprobs(
                    token_logprobs, logprob_threshold=logprob_threshold
                )
                return LogprobReportData(
                    is_confident=res.is_confident,
                    avg_logprob=res.avg_logprob,
                    perplexity=res.perplexity,
                    threshold=res.threshold,
                    token_count=res.token_count,
                    action=res.action,
                )

            def intercept_request(
                self,
                query: str,
                target_domains: list[str] | None = None,
                retrieved_chunks: list[str] | list[dict[str, str]] | None = None,
                token_logprobs: list[float] | None = None,
                draft_response: str = "",
                escalate_on_failure: bool = True,
            ) -> PipelineReportData:
                res = self._eng.intercept_request(
                    query=query,
                    target_domains=target_domains,
                    retrieved_chunks=retrieved_chunks,
                    token_logprobs=token_logprobs,
                    draft_response=draft_response,
                    escalate_on_failure=escalate_on_failure,
                )
                from harness.services.uncertainty_guard import (
                    EscalationTicketData,
                    ScoredChunkData,
                )

                ticket = (
                    EscalationTicketData(
                        ticket_id=res.escalation_ticket.ticket_id,
                        timestamp=res.escalation_ticket.timestamp,
                        query=res.escalation_ticket.query,
                        failure_gate=res.escalation_ticket.failure_gate,
                        reason=res.escalation_ticket.reason,
                        metadata=res.escalation_ticket.metadata,
                    )
                    if res.escalation_ticket
                    else None
                )

                ret_rep = (
                    RetrievalReportData(
                        has_sufficient_context=res.retrieval_result.has_sufficient_context,
                        top_score=res.retrieval_result.top_score,
                        min_threshold=res.retrieval_result.min_threshold,
                        scored_chunks=[
                            ScoredChunkData(
                                chunk_id=c.chunk_id,
                                content=c.content,
                                score=c.score,
                            )
                            for c in res.retrieval_result.scored_chunks
                        ],
                        action=res.retrieval_result.action,
                    )
                    if res.retrieval_result
                    else None
                )

                lp_rep = (
                    LogprobReportData(
                        is_confident=res.logprob_result.is_confident,
                        avg_logprob=res.logprob_result.avg_logprob,
                        perplexity=res.logprob_result.perplexity,
                        threshold=res.logprob_result.threshold,
                        token_count=res.logprob_result.token_count,
                        action=res.logprob_result.action,
                    )
                    if res.logprob_result
                    else None
                )

                return PipelineReportData(
                    state=res.state,
                    gate_passed=res.gate_passed,
                    total_latency_ms=res.total_latency_ms,
                    boundary_result=BoundaryReportData(
                        is_valid=res.boundary_result.is_valid,
                        score=res.boundary_result.score,
                        matched_domain=res.boundary_result.matched_domain,
                        latency_ms=res.boundary_result.latency_ms,
                        reason=res.boundary_result.reason,
                    ),
                    retrieval_result=ret_rep,
                    logprob_result=lp_rep,
                    escalation_ticket=ticket,
                    response_text=res.response_text,
                )

            def mine_documentation_debt(
                self, failed_queries: list[str] | None = None
            ) -> list[DocDebtClusterData]:
                clusters = self._eng.mine_documentation_debt(failed_queries)
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

            def generate_visual_brief(
                self,
                pipeline_result: PipelineReportData | dict[str, Any],
                output_path: str | Path | None = None,
            ) -> Path:
                return self._eng.generate_visual_brief(pipeline_result, output_path)

        return _EngineAdapter()


# ---------------------------------------------------------------------------
# Click Command Group
# ---------------------------------------------------------------------------


@click.group("uncertainty")
def uncertainty_group() -> None:
    """Uncertainty-Aware AI Pipeline — 3-Layer Interception & Overconfidence Mitigation."""
    # Ensure Windows UTF-8 stream codec entrypoint invariant (Rule 23)
    if sys.platform == "win32":
        try:
            if hasattr(sys.stdout, "reconfigure"):
                sys.stdout.reconfigure(encoding="utf-8")
            if hasattr(sys.stderr, "reconfigure"):
                sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass


@uncertainty_group.command("gate")
@click.option("--query", "-q", required=True, help="User input query")
@click.option(
    "--threshold",
    "-t",
    type=float,
    default=0.45,
    help="Cosine boundary threshold (default: 0.45)",
)
@click.option(
    "--domain", "-d", multiple=True, help="Custom operational domain centroid"
)
def gate_cmd(query: str, threshold: float, domain: tuple[str, ...]) -> None:
    """Evaluate Layer 1 input domain boundary gating."""
    svc = get_uncertainty_service()
    domains = list(domain) if domain else None
    res = svc.verify_boundary(query, target_domains=domains, threshold=threshold)
    click.echo(
        _json.dumps(
            {
                "is_valid": res.is_valid,
                "score": res.score,
                "matched_domain": res.matched_domain,
                "latency_ms": res.latency_ms,
                "reason": res.reason,
            },
            indent=2,
        )
    )


@uncertainty_group.command("retrieval")
@click.option("--query", "-q", required=True, help="User input query")
@click.option(
    "--chunk",
    "-c",
    multiple=True,
    required=True,
    help="Retrieved document chunks to score",
)
@click.option(
    "--threshold",
    "-t",
    type=float,
    default=0.60,
    help="Minimum context relevance threshold (default: 0.60)",
)
def retrieval_cmd(query: str, chunk: tuple[str, ...], threshold: float) -> None:
    """Evaluate Layer 2 retrieval relevance and context sufficiency."""
    svc = get_uncertainty_service()
    res = svc.score_retrieval(query, list(chunk), minimum_relevance=threshold)
    click.echo(
        _json.dumps(
            {
                "has_sufficient_context": res.has_sufficient_context,
                "top_score": res.top_score,
                "min_threshold": res.min_threshold,
                "action": res.action,
                "scored_chunks": [
                    {"id": c.chunk_id, "score": c.score, "content": c.content}
                    for c in res.scored_chunks
                ],
            },
            indent=2,
        )
    )


@uncertainty_group.command("logprobs")
@click.option(
    "--logprob",
    "-l",
    multiple=True,
    type=float,
    required=True,
    help="Sequence of token log probabilities",
)
@click.option(
    "--threshold",
    "-t",
    type=float,
    default=-0.35,
    help="Logprob safety threshold (default: -0.35)",
)
def logprobs_cmd(logprob: tuple[float, ...], threshold: float) -> None:
    """Evaluate Layer 3 token log probabilities and sequence perplexity."""
    svc = get_uncertainty_service()
    res = svc.validate_logprobs(list(logprob), logprob_threshold=threshold)
    click.echo(
        _json.dumps(
            {
                "is_confident": res.is_confident,
                "avg_logprob": res.avg_logprob,
                "perplexity": res.perplexity,
                "threshold": res.threshold,
                "token_count": res.token_count,
                "action": res.action,
            },
            indent=2,
        )
    )


@uncertainty_group.command("pipeline")
@click.option("--query", "-q", required=True, help="User input query")
@click.option("--chunk", "-c", multiple=True, help="Retrieved context chunks")
@click.option(
    "--logprob",
    "-l",
    multiple=True,
    type=float,
    help="Token log probabilities",
)
@click.option(
    "--response", "-r", default="Verified response", help="Draft LLM generation"
)
def pipeline_cmd(
    query: str,
    chunk: tuple[str, ...],
    logprob: tuple[float, ...],
    response: str,
) -> None:
    """Execute end-to-end 3-layer request interception lifecycle."""
    svc = get_uncertainty_service()
    res = svc.intercept_request(
        query=query,
        retrieved_chunks=list(chunk) if chunk else None,
        token_logprobs=list(logprob) if logprob else None,
        draft_response=response,
    )
    click.echo(
        _json.dumps(
            {
                "state": res.state,
                "gate_passed": res.gate_passed,
                "latency_ms": res.total_latency_ms,
                "boundary_score": res.boundary_result.score,
                "boundary_valid": res.boundary_result.is_valid,
                "retrieval_sufficient": (
                    res.retrieval_result.has_sufficient_context
                    if res.retrieval_result
                    else False
                ),
                "logprob_confident": (
                    res.logprob_result.is_confident if res.logprob_result else False
                ),
                "ticket_id": (
                    res.escalation_ticket.ticket_id if res.escalation_ticket else None
                ),
                "response": res.response_text,
            },
            indent=2,
        )
    )


@uncertainty_group.command("calibrate")
@click.option(
    "--query",
    "-q",
    multiple=True,
    required=True,
    help="Under-retrieved or failing queries to cluster",
)
def calibrate_cmd(query: tuple[str, ...]) -> None:
    """Cluster under-retrieved queries to uncover missing documentation debt."""
    svc = get_uncertainty_service()
    clusters = svc.mine_documentation_debt(failed_queries=list(query))
    click.echo(
        _json.dumps(
            [
                {
                    "cluster_id": c.cluster_id,
                    "representative_topic": c.representative_topic,
                    "query_count": c.query_count,
                    "severity": c.severity,
                    "sample_queries": c.sample_queries,
                }
                for c in clusters
            ],
            indent=2,
        )
    )


@uncertainty_group.command("brief")
@click.option("--query", "-q", default="Configure internal VPN", help="Query")
@click.option(
    "--output",
    "-o",
    type=click.Path(dir_okay=False, writable=True),
    help="Custom output HTML path",
)
def brief_cmd(query: str, output: str | None) -> None:
    """Generate interactive HTML visual brief in %TEMP%."""
    svc = get_uncertainty_service()
    res = svc.intercept_request(
        query=query,
        retrieved_chunks=["VPN client configuration for remote staff..."],
        token_logprobs=[-0.1, -0.05, -0.2],
        draft_response="Follow the corporate VPN guide.",
    )
    path = svc.generate_visual_brief(res, output_path=output)
    click.echo(f"Visual Brief generated: {path}")
