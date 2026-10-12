"""Engine adapter implementing SelfEvaluatingPipelineService over standalone engine."""

from __future__ import annotations

import json as _json
import sys
from pathlib import Path
from typing import Any

from harness.commands.self_eval.brief_adapter import generate_visual_brief_via_engine
from harness.services.self_evaluating_pipeline import (
    AgreementReportData,
    DriftAuditData,
    JudgeConsensusData,
    Layer1ReportData,
    RegressionReportData,
    SelfEvaluatingPipelineService,
    StatisticalGateData,
)


def _ensure_scripts_path() -> None:
    ws_root = Path.cwd()
    skill_scripts = ws_root / ".agents" / "skills" / "self-evaluating-ai-pipeline" / "scripts"
    if skill_scripts.exists() and str(skill_scripts) not in sys.path:
        sys.path.insert(0, str(skill_scripts))


class SelfEvaluatingPipelineEngineAdapter(SelfEvaluatingPipelineService):
    """Adapter bridging standalone SelfEvaluatingPipelineEngine to typed service protocol."""

    def __init__(self) -> None:
        _ensure_scripts_path()
        from self_evaluating_pipeline_engine import SelfEvaluatingPipelineEngine

        self._eng = SelfEvaluatingPipelineEngine()

    def evaluate_layer1(
        self,
        output_text: str,
        expected_schema: str | None = None,
        min_len: int = 10,
        max_len: int = 5000,
        allowed_domains: list[str] | None = None,
        syntax_lang: str | None = None,
    ) -> Layer1ReportData:
        rep = self._eng.evaluate_layer1(
            output_text,
            expected_schema=expected_schema,
            min_len=min_len,
            max_len=max_len,
            allowed_domains=allowed_domains,
            syntax_lang=syntax_lang,
        )
        checks = [
            {"name": c.name, "passed": c.passed, "latency_ms": c.latency_ms, "message": c.message, "details": list(c.details)}
            for c in rep.checks
        ]
        return Layer1ReportData(
            passed=rep.passed,
            total_latency_ms=rep.total_latency_ms,
            checks=checks,
            refusal_detected=rep.refusal_detected,
            hallucinated_urls=list(rep.hallucinated_urls),
            syntax_valid=rep.syntax_valid,
        )

    def evaluate_layer2_judge(
        self,
        prompt: str,
        response: str,
        model: str = "gpt-4o-mini",
        num_judges: int = 3,
        threshold: float = 3.5,
    ) -> JudgeConsensusData:
        res = self._eng.evaluate_layer2_judge(
            prompt,
            response,
            model=model,
            num_judges=num_judges,
            threshold=threshold,
        )
        judges = [
            {"judge_id": j.judge_id, "score": j.score, "reasoning": j.reasoning, "duration_ms": j.duration_ms}
            for j in res.judge_results
        ]
        return JudgeConsensusData(
            median_score=res.median_score,
            mean_score=res.mean_score,
            scores=list(res.scores),
            passed=res.passed,
            threshold=res.threshold,
            judge_results=judges,
        )

    def calculate_cohens_kappa(
        self,
        annotations_a: list[dict[str, Any]],
        annotations_b: list[dict[str, Any]],
    ) -> AgreementReportData:
        _ensure_scripts_path()
        from self_evaluating_pipeline_engine import HumanAnnotationRecord

        records_a = [HumanAnnotationRecord(**a) for a in annotations_a]
        records_b = [HumanAnnotationRecord(**b) for b in annotations_b]
        rep = self._eng.calculate_cohens_kappa(records_a, records_b)
        return AgreementReportData(
            cohens_kappa=rep.cohens_kappa,
            observed_agreement=rep.observed_agreement,
            expected_chance_agreement=rep.expected_chance_agreement,
            is_acceptable=rep.is_acceptable,
            interpretation=rep.interpretation,
            paired_samples_count=rep.paired_samples_count,
        )

    def audit_judge_drift(
        self,
        human_scores: list[float | int],
        judge_scores: list[float | int],
        max_allowed_drift: float = 0.5,
    ) -> DriftAuditData:
        rep = self._eng.audit_judge_drift(
            human_scores, judge_scores, max_allowed_drift=max_allowed_drift
        )
        return DriftAuditData(
            mean_absolute_deviation=rep.mean_absolute_deviation,
            sample_count=rep.sample_count,
            drift_detected=rep.drift_detected,
            max_allowed_drift=rep.max_allowed_drift,
            details=list(rep.details),
        )

    def run_golden_regression(
        self,
        golden_dataset_path: str | Path,
        generator: Any = None,
        min_judge_score: float = 3.5,
    ) -> RegressionReportData:
        _ensure_scripts_path()
        from self_evaluating_pipeline_engine import GoldenTestCase

        p = Path(golden_dataset_path)
        raw_cases = _json.loads(p.read_text(encoding="utf-8"))
        cases = [
            GoldenTestCase(
                test_id=c["test_id"],
                prompt=c["prompt"],
                expected_category=c.get("expected_category", "general"),
                difficulty=c.get("difficulty", "medium"),
                expected_criteria=tuple(c.get("expected_criteria", ())),
                pre_change_score=c.get("pre_change_score"),
            )
            for c in raw_cases
        ]
        res = self._eng.run_golden_regression(
            cases, generator=generator, min_judge_score=min_judge_score
        )
        return RegressionReportData(
            run_id=res.run_id,
            total_cases=res.total_cases,
            passed_cases=res.passed_cases,
            pass_rate=res.pass_rate,
            layer1_pass_rate=res.layer1_pass_rate,
            mean_score=res.mean_score,
            scores=list(res.scores),
            failures=list(res.failures),
        )

    def evaluate_statistical_significance_gate(
        self,
        scores_before: list[float],
        scores_after: list[float],
        alpha: float = 0.05,
    ) -> StatisticalGateData:
        dec = self._eng.evaluate_statistical_significance_gate(
            scores_before, scores_after, alpha=alpha
        )
        return StatisticalGateData(
            p_value=dec.p_value,
            t_statistic=dec.t_statistic,
            mean_difference=dec.mean_difference,
            sample_size=dec.sample_size,
            is_significant=dec.is_significant,
            is_improvement=dec.is_improvement,
            decision=dec.decision,
            justification=dec.justification,
        )

    def generate_visual_brief(
        self,
        regression_data: RegressionReportData | dict[str, Any],
        gate_data: StatisticalGateData | dict[str, Any] | None = None,
        output_path: str | Path | None = None,
    ) -> Path:
        return generate_visual_brief_via_engine(
            self._eng, regression_data, gate_data=gate_data, output_path=output_path
        )
