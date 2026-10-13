"""Engine adapter for UncertaintyGuardService fallback resolution."""

from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

from harness.services.uncertainty_guard import (
    BoundaryReportData,
    DocDebtClusterData,
    LogprobReportData,
    PipelineReportData,
    RetrievalReportData,
    UncertaintyGuardService,
)

from .converters import (
    to_boundary_report,
    to_doc_debt_clusters,
    to_logprob_report,
    to_pipeline_report,
    to_retrieval_report,
)


def _get_engine_class() -> Any:
    """Dynamically resolve UncertaintyGuardEngine class from skill scripts."""
    _ws_root = Path.cwd()
    if str(_ws_root) not in sys.path:
        sys.path.insert(0, str(_ws_root))
    if str(_ws_root / "src") not in sys.path:
        sys.path.insert(0, str(_ws_root / "src"))

    skill_scripts = (
        _ws_root
        / ".agents"
        / "skills"
        / "uncertainty-aware-ai-architect"
        / "scripts"
    )
    if str(skill_scripts) not in sys.path:
        sys.path.insert(0, str(skill_scripts))
    from uncertainty_guard_engine import UncertaintyGuardEngine  # type: ignore

    return UncertaintyGuardEngine


class UncertaintyEngineAdapter(UncertaintyGuardService):
    """Fallback adapter delegating to underlying UncertaintyGuardEngine."""

    def __init__(self) -> None:
        engine_cls = _get_engine_class()
        self._eng = engine_cls()

    def verify_boundary(
        self,
        query: str,
        target_domains: list[str] | tuple[str, ...] | None = None,
        threshold: float | None = None,
    ) -> BoundaryReportData:
        res = self._eng.verify_boundary(
            query, target_domains=target_domains, threshold=threshold
        )
        return to_boundary_report(res)

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
        return to_retrieval_report(res)

    def validate_logprobs(
        self,
        token_logprobs: list[float],
        logprob_threshold: float | None = None,
    ) -> LogprobReportData:
        res = self._eng.validate_logprobs(
            token_logprobs, logprob_threshold=logprob_threshold
        )
        return to_logprob_report(res)

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
        return to_pipeline_report(res)

    def mine_documentation_debt(
        self, failed_queries: list[str] | None = None
    ) -> list[DocDebtClusterData]:
        clusters = self._eng.mine_documentation_debt(failed_queries)
        return to_doc_debt_clusters(clusters)

    def generate_visual_brief(
        self,
        pipeline_result: PipelineReportData | dict[str, Any],
        output_path: str | Path | None = None,
    ) -> Path:
        return self._eng.generate_visual_brief(pipeline_result, output_path)
