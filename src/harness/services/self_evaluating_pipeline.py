"""SelfEvaluatingPipeline service protocol, typed models, and ServiceKey.

Elevates the 3-layer LLM quality evaluation architecture (Jude Otine 2026, ki_self_20260917_02)
into a first-class micro-kernel IoC service seam.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, Field

from harness.kernel.context import ServiceKey


class Layer1ReportData(BaseModel):
    """Payload representing Layer 1 deterministic pre-flight checks."""

    passed: bool = Field(..., description="Whether all deterministic checks passed")
    total_latency_ms: float = Field(
        ..., description="Execution latency in milliseconds"
    )
    checks: list[dict[str, Any]] = Field(
        default_factory=list, description="Granular check observations"
    )
    refusal_detected: bool = Field(
        default=False, description="Whether an unprompted canned refusal was caught"
    )
    hallucinated_urls: list[str] = Field(
        default_factory=list, description="Extracted unauthorized or hallucinated URLs"
    )
    syntax_valid: bool = Field(
        default=True, description="Whether schema/AST syntax verification passed"
    )


class JudgeConsensusData(BaseModel):
    """Payload representing Layer 2 anchored LLM-as-judge evaluation."""

    median_score: float = Field(
        ..., description="Median score across judge calls (1-5)"
    )
    mean_score: float = Field(..., description="Mean score across judge calls")
    scores: list[int] = Field(..., description="Individual judge integer scores")
    passed: bool = Field(..., description="Whether median score meets threshold")
    threshold: float = Field(default=3.5, description="Acceptance threshold")
    judge_results: list[dict[str, Any]] = Field(
        default_factory=list, description="Individual judge outputs and reasoning"
    )


class AgreementReportData(BaseModel):
    """Payload representing Layer 3 human inter-annotator agreement."""

    cohens_kappa: float = Field(..., description="Cohen's Kappa coefficient")
    observed_agreement: float = Field(
        ..., description="Observed agreement proportion Po"
    )
    expected_chance_agreement: float = Field(
        ..., description="Expected chance agreement proportion Pe"
    )
    is_acceptable: bool = Field(
        ..., description="Whether agreement exceeds production threshold (kappa > 0.6)"
    )
    interpretation: str = Field(..., description="Qualitative agreement category")
    paired_samples_count: int = Field(
        ..., description="Number of overlapping samples evaluated"
    )


class DriftAuditData(BaseModel):
    """Payload representing automated judge drift against human calibration benchmark."""

    mean_absolute_deviation: float = Field(
        ..., description="Mean absolute deviation between judge and human ratings"
    )
    sample_count: int = Field(..., description="Number of benchmark samples evaluated")
    drift_detected: bool = Field(..., description="Whether deviation exceeds tolerance")
    max_allowed_drift: float = Field(
        default=0.5, description="Maximum permitted drift before recalibration"
    )
    details: list[dict[str, Any]] = Field(
        default_factory=list, description="Per-sample deviations"
    )


class RegressionReportData(BaseModel):
    """Payload representing CI/CD regression suite outcome across golden dataset."""

    run_id: str = Field(..., description="Unique regression execution ID")
    total_cases: int = Field(..., description="Total golden cases executed")
    passed_cases: int = Field(..., description="Number of cases passing all layers")
    pass_rate: float = Field(..., description="Proportion of cases passing all layers")
    layer1_pass_rate: float = Field(
        ..., description="Proportion of cases passing Layer 1"
    )
    mean_score: float = Field(..., description="Average composite score across suite")
    scores: list[float] = Field(
        default_factory=list, description="All individual case scores"
    )
    failures: list[dict[str, Any]] = Field(
        default_factory=list, description="Detailed records for failing cases"
    )


class StatisticalGateData(BaseModel):
    """Payload representing paired Student's t-test release gate decision."""

    p_value: float = Field(..., description="Two-tailed p-value from paired t-test")
    t_statistic: float = Field(..., description="Computed Student's t-statistic")
    mean_difference: float = Field(
        ..., description="Difference in means (after - before)"
    )
    sample_size: int = Field(..., description="Number of paired observations")
    is_significant: bool = Field(..., description="Whether p < alpha (0.05)")
    is_improvement: bool = Field(..., description="Whether mean difference > 0")
    decision: str = Field(
        ..., description="Gating verdict: APPROVED | BLOCKED_NOISE | BLOCKED_REGRESSION"
    )
    justification: str = Field(..., description="Human-readable decision explanation")


@runtime_checkable
class SelfEvaluatingPipelineService(Protocol):
    """Protocol for 3-layer LLM quality evaluation, golden regressions, and statistical gating."""

    def evaluate_layer1(
        self,
        output_text: str,
        expected_schema: str | None = None,
        min_len: int = 10,
        max_len: int = 5000,
        allowed_domains: list[str] | None = None,
        syntax_lang: str | None = None,
    ) -> Layer1ReportData:
        """Execute sub-millisecond Layer 1 deterministic sanity checks."""
        ...

    def evaluate_layer2_judge(
        self,
        prompt: str,
        response: str,
        model: str = "gpt-4o-mini",
        num_judges: int = 3,
        threshold: float = 3.5,
    ) -> JudgeConsensusData:
        """Execute Layer 2 semantic evaluation using anchored 1-to-5 rubric and median consensus."""
        ...

    def calculate_cohens_kappa(
        self,
        annotations_a: list[dict[str, Any]],
        annotations_b: list[dict[str, Any]],
    ) -> AgreementReportData:
        """Calculate Cohen's Kappa inter-annotator agreement corrected for chance."""
        ...

    def audit_judge_drift(
        self,
        human_scores: list[float | int],
        judge_scores: list[float | int],
        max_allowed_drift: float = 0.5,
    ) -> DriftAuditData:
        """Audit LLM judge drift against human ratings with 0.5 threshold."""
        ...

    def run_golden_regression(
        self,
        golden_dataset_path: str | Path,
        generator: Any = None,
        min_judge_score: float = 3.5,
    ) -> RegressionReportData:
        """Execute CI/CD regression suite across curated golden test dataset."""
        ...

    def evaluate_statistical_significance_gate(
        self,
        scores_before: list[float],
        scores_after: list[float],
        alpha: float = 0.05,
    ) -> StatisticalGateData:
        """Enforce paired Student's t-test release gate (p < 0.05 AND mean difference > 0)."""
        ...

    def generate_visual_brief(
        self,
        regression_data: RegressionReportData | dict[str, Any],
        gate_data: StatisticalGateData | dict[str, Any] | None = None,
        output_path: str | Path | None = None,
    ) -> Path:
        """Generate interactive HTML visual brief in %TEMP% summarizing evaluation results."""
        ...


SELF_EVALUATING_PIPELINE_SERVICE_KEY: ServiceKey[SelfEvaluatingPipelineService] = (
    ServiceKey("service.self_evaluating_pipeline")
)
