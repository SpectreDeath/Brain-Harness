"""Self-Evaluating AI Pipeline Plugin — 3-Layer Quality & Statistical Gating Engine.

Synthesized from Jude Otine (freeCodeCamp, 2026), grounded in ki_self_20260917_02.
Provides in-memory micro-kernel IoC service implementation (Rule 45 & Rule 49).
"""

from __future__ import annotations

import json
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
    _REPO_ROOT / ".agents" / "skills" / "self-evaluating-ai-pipeline" / "scripts"
)
_HARNESS_SRC = _REPO_ROOT / "src"

for _p in [_SKILL_SCRIPTS, _HARNESS_SRC]:
    if _p.exists() and str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from self_evaluating_pipeline_engine import (  # type: ignore
    GoldenTestCase,
    HumanAnnotationRecord,
    SelfEvaluatingPipelineEngine,
)

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.self_evaluating_pipeline import (
    SELF_EVALUATING_PIPELINE_SERVICE_KEY,
    AgreementReportData,
    DriftAuditData,
    JudgeConsensusData,
    Layer1ReportData,
    RegressionReportData,
    SelfEvaluatingPipelineService,
    StatisticalGateData,
)

logger = structlog.get_logger(__name__)


class SelfEvaluatingPipelinePlugin(HarnessPlugin, SelfEvaluatingPipelineService):
    """Plugin providing 3-layer LLM quality evaluation, regressions, and statistical release gating."""

    def __init__(self, root_dir: Path | str | None = None) -> None:
        super().__init__()
        self._root = Path(root_dir or _REPO_ROOT).resolve()
        config_path = _PLUGIN_DIR / "config.default.yaml"
        self._engine = SelfEvaluatingPipelineEngine(
            config_path=config_path if config_path.exists() else None
        )

    @property
    def name(self) -> str:
        return "plugin.self_evaluating_pipeline"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return (
            "3-layer LLM evaluation pipeline, anchored judges, human calibration loops, "
            "golden regression suites, and paired t-test statistical significance release gating"
        )

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [SELF_EVALUATING_PIPELINE_SERVICE_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, context: ServiceContext) -> None:
        """Register the service singleton in the IoC container."""
        context.provide(SELF_EVALUATING_PIPELINE_SERVICE_KEY, self)
        logger.info(
            "self_evaluating_pipeline_plugin_loaded",
            provides=[k.name for k in self.provides],
        )

    async def on_unload(self, context: ServiceContext) -> None:
        """Clean up resources on unload."""
        logger.info("self_evaluating_pipeline_plugin_unloaded")

    # --- SelfEvaluatingPipelineService implementation ---

    def evaluate_layer1(
        self,
        output_text: str,
        expected_schema: str | None = None,
        min_len: int = 10,
        max_len: int = 5000,
        allowed_domains: list[str] | None = None,
        syntax_lang: str | None = None,
    ) -> Layer1ReportData:
        rep = self._engine.evaluate_layer1(
            output_text=output_text,
            expected_schema=expected_schema,
            min_len=min_len,
            max_len=max_len,
            allowed_domains=allowed_domains,
            syntax_lang=syntax_lang,
        )
        return Layer1ReportData(
            passed=rep.passed,
            total_latency_ms=rep.total_latency_ms,
            checks=[
                {
                    "name": c.name,
                    "passed": c.passed,
                    "latency_ms": c.latency_ms,
                    "message": c.message,
                    "details": list(c.details),
                }
                for c in rep.checks
            ],
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
        res = self._engine.evaluate_layer2_judge(
            prompt=prompt,
            response=response,
            model=model,
            num_judges=num_judges,
            threshold=threshold,
        )
        return JudgeConsensusData(
            median_score=res.median_score,
            mean_score=res.mean_score,
            scores=list(res.scores),
            passed=res.passed,
            threshold=res.threshold,
            judge_results=[
                {
                    "judge_id": j.judge_id,
                    "score": j.score,
                    "reasoning": j.reasoning,
                    "duration_ms": j.duration_ms,
                }
                for j in res.judge_results
            ],
        )

    def calculate_cohens_kappa(
        self,
        annotations_a: list[dict[str, Any]],
        annotations_b: list[dict[str, Any]],
    ) -> AgreementReportData:
        records_a = [HumanAnnotationRecord(**a) for a in annotations_a]
        records_b = [HumanAnnotationRecord(**b) for b in annotations_b]
        rep = self._engine.calculate_cohens_kappa(records_a, records_b)
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
        rep = self._engine.audit_judge_drift(
            human_scores=human_scores,
            judge_scores=judge_scores,
            max_allowed_drift=max_allowed_drift,
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
        p = Path(golden_dataset_path)
        if not p.exists():
            raise FileNotFoundError(f"Golden dataset not found: {p}")

        raw_cases = json.loads(p.read_text(encoding="utf-8"))
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
        res = self._engine.run_golden_regression(
            golden_cases=cases,
            generator=generator,
            min_judge_score=min_judge_score,
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
        dec = self._engine.evaluate_statistical_significance_gate(
            scores_before=scores_before,
            scores_after=scores_after,
            alpha=alpha,
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
        from self_evaluating_pipeline_engine import (
            RegressionRunResult,
            StatisticalGatingDecision,
        )

        reg_dict = (
            regression_data.model_dump()
            if isinstance(regression_data, RegressionReportData)
            else regression_data
        )
        reg_obj = RegressionRunResult(
            run_id=reg_dict["run_id"],
            total_cases=reg_dict["total_cases"],
            passed_cases=reg_dict["passed_cases"],
            pass_rate=reg_dict["pass_rate"],
            layer1_pass_rate=reg_dict["layer1_pass_rate"],
            mean_score=reg_dict["mean_score"],
            scores=tuple(reg_dict["scores"]),
            failures=tuple(reg_dict["failures"]),
        )

        gate_obj = None
        if gate_data:
            g_dict = (
                gate_data.model_dump()
                if isinstance(gate_data, StatisticalGateData)
                else gate_data
            )
            gate_obj = StatisticalGatingDecision(
                p_value=g_dict["p_value"],
                t_statistic=g_dict["t_statistic"],
                mean_difference=g_dict["mean_difference"],
                sample_size=g_dict["sample_size"],
                is_significant=g_dict["is_significant"],
                is_improvement=g_dict["is_improvement"],
                decision=g_dict["decision"],
                justification=g_dict["justification"],
            )

        return self._engine.generate_visual_brief(
            regression_result=reg_obj,
            gating_decision=gate_obj,
            output_path=output_path,
        )


# Rule 45: Export module-level singleton instance
plugin = SelfEvaluatingPipelinePlugin()
