"""UncertaintyGuard Plugin — 3-Layer Deterministic Uncertainty Interception Engine.

Synthesized from Chidiebere Njoku (freeCodeCamp, 2026), grounded in ki_njoku_uncertainty_aware_systems.
Provides in-memory micro-kernel IoC service implementation (Rule 45 & Rule 49).
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import structlog

# Rule 23: Windows UTF-8 Stream Codec Entrypoint Invariant
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

# Dynamically ensure skill scripts directory and harness src are on sys.path
_PLUGIN_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _PLUGIN_DIR.parents[2]
_SKILL_SCRIPTS = (
    _REPO_ROOT / ".agents" / "skills" / "uncertainty-aware-ai-architect" / "scripts"
)
_HARNESS_SRC = _REPO_ROOT / "src"

for _p in [_SKILL_SCRIPTS, _HARNESS_SRC]:
    if _p.exists() and str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from uncertainty_guard_engine import (  # type: ignore
    UncertaintyGuardEngine,
)

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.uncertainty_guard import (
    UNCERTAINTY_GUARD_SERVICE_KEY,
    BoundaryReportData,
    DocDebtClusterData,
    EscalationTicketData,
    LogprobReportData,
    PipelineReportData,
    RetrievalReportData,
    ScoredChunkData,
    UncertaintyGuardService,
)

logger = structlog.get_logger(__name__)


class UncertaintyGuardPlugin(HarnessPlugin, UncertaintyGuardService):
    """Plugin providing 3-layer deterministic uncertainty interception & overconfidence prevention."""

    def __init__(self, root_dir: Path | str | None = None) -> None:
        super().__init__()
        self._root = Path(root_dir or _REPO_ROOT).resolve()
        self._engine = UncertaintyGuardEngine()

    @property
    def name(self) -> str:
        return "plugin.uncertainty_guard"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return (
            "3-layer deterministic uncertainty interception, semantic distance gating, "
            "token logprob entropy analysis, and intentional HITL escalation (Njoku 2026)"
        )

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [UNCERTAINTY_GUARD_SERVICE_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, context: ServiceContext) -> None:
        """Register the service singleton in the IoC container (Rule 45)."""
        context.provide(UNCERTAINTY_GUARD_SERVICE_KEY, self)
        logger.info(
            "uncertainty_guard_plugin_loaded",
            provides=[k.name for k in self.provides],
        )

    async def on_unload(self, context: ServiceContext) -> None:
        """Clean up resources on unload."""
        logger.info("uncertainty_guard_plugin_unloaded")

    def verify_boundary(
        self,
        query: str,
        target_domains: list[str] | tuple[str, ...] | None = None,
        threshold: float | None = None,
    ) -> BoundaryReportData:
        """Evaluate Layer 1 input domain boundary gating (<1ms)."""
        res = self._engine.verify_boundary(
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
        """Evaluate Layer 2 retrieval relevance and context sufficiency (default tau = 0.60)."""
        res = self._engine.score_retrieval(
            user_query, retrieved_chunks, minimum_relevance=minimum_relevance
        )
        return RetrievalReportData(
            has_sufficient_context=res.has_sufficient_context,
            top_score=res.top_score,
            min_threshold=res.min_threshold,
            scored_chunks=[
                ScoredChunkData(chunk_id=c.chunk_id, content=c.content, score=c.score)
                for c in res.scored_chunks
            ],
            action=res.action,
        )

    def validate_logprobs(
        self,
        token_logprobs: list[float],
        logprob_threshold: float | None = None,
    ) -> LogprobReportData:
        """Evaluate Layer 3 token generation log probabilities and perplexity (default tau = -0.35)."""
        res = self._engine.validate_logprobs(
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
        """Execute unified 3-layer request interception lifecycle with deterministic routing."""
        res = self._engine.intercept_request(
            query=query,
            target_domains=target_domains,
            retrieved_chunks=retrieved_chunks,
            token_logprobs=token_logprobs,
            draft_response=draft_response,
            escalate_on_failure=escalate_on_failure,
        )

        boundary_data = BoundaryReportData(
            is_valid=res.boundary_result.is_valid,
            score=res.boundary_result.score,
            matched_domain=res.boundary_result.matched_domain,
            latency_ms=res.boundary_result.latency_ms,
            reason=res.boundary_result.reason,
        )

        retrieval_data = None
        if res.retrieval_result is not None:
            retrieval_data = RetrievalReportData(
                has_sufficient_context=res.retrieval_result.has_sufficient_context,
                top_score=res.retrieval_result.top_score,
                min_threshold=res.retrieval_result.min_threshold,
                scored_chunks=[
                    ScoredChunkData(
                        chunk_id=c.chunk_id, content=c.content, score=c.score
                    )
                    for c in res.retrieval_result.scored_chunks
                ],
                action=res.retrieval_result.action,
            )

        logprob_data = None
        if res.logprob_result is not None:
            logprob_data = LogprobReportData(
                is_confident=res.logprob_result.is_confident,
                avg_logprob=res.logprob_result.avg_logprob,
                perplexity=res.logprob_result.perplexity,
                threshold=res.logprob_result.threshold,
                token_count=res.logprob_result.token_count,
                action=res.logprob_result.action,
            )

        ticket_data = None
        if res.escalation_ticket is not None:
            ticket_data = EscalationTicketData(
                ticket_id=res.escalation_ticket.ticket_id,
                timestamp=res.escalation_ticket.timestamp,
                query=res.escalation_ticket.query,
                failure_gate=res.escalation_ticket.failure_gate,
                reason=res.escalation_ticket.reason,
                metadata=res.escalation_ticket.metadata,
            )

        return PipelineReportData(
            state=res.state,
            gate_passed=res.gate_passed,
            total_latency_ms=res.total_latency_ms,
            boundary_result=boundary_data,
            retrieval_result=retrieval_data,
            logprob_result=logprob_data,
            escalation_ticket=ticket_data,
            response_text=res.response_text,
        )

    def mine_documentation_debt(
        self, failed_queries: list[str] | None = None
    ) -> list[DocDebtClusterData]:
        """Cluster under-retrieved queries to uncover missing or outdated documentation."""
        clusters = self._engine.mine_documentation_debt(failed_queries=failed_queries)
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
        """Generate interactive HTML visual brief in %TEMP% summarizing uncertainty interception."""
        if isinstance(pipeline_result, PipelineReportData):
            raw = {
                "state": pipeline_result.state,
                "gate_passed": pipeline_result.gate_passed,
                "latency_ms": pipeline_result.total_latency_ms,
                "boundary_score": pipeline_result.boundary_result.score,
                "boundary_valid": pipeline_result.boundary_result.is_valid,
                "retrieval_score": (
                    pipeline_result.retrieval_result.top_score
                    if pipeline_result.retrieval_result
                    else 0.0
                ),
                "retrieval_valid": (
                    pipeline_result.retrieval_result.has_sufficient_context
                    if pipeline_result.retrieval_result
                    else False
                ),
                "logprob_avg": (
                    pipeline_result.logprob_result.avg_logprob
                    if pipeline_result.logprob_result
                    else 0.0
                ),
                "perplexity": (
                    pipeline_result.logprob_result.perplexity
                    if pipeline_result.logprob_result
                    else 0.0
                ),
                "logprob_valid": (
                    pipeline_result.logprob_result.is_confident
                    if pipeline_result.logprob_result
                    else False
                ),
                "response_text": pipeline_result.response_text,
                "ticket_id": (
                    pipeline_result.escalation_ticket.ticket_id
                    if pipeline_result.escalation_ticket
                    else None
                ),
            }
        else:
            raw = pipeline_result
        return self._engine.generate_visual_brief(raw, output_path=output_path)


# Module-level singleton provider required by Rule 45
plugin = UncertaintyGuardPlugin()
