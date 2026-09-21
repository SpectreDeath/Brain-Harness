"""Self-Evaluating AI Pipeline CLI commands.

Provides headless Click CLI introspection for 3-layer LLM quality evaluation,
anchored semantic judging, Cohen's Kappa agreement, golden regressions, and paired t-test release gating.
"""

from __future__ import annotations

import json as _json
import sys
from pathlib import Path
from typing import Any

import click
import structlog

from harness.kernel.context import ServiceContext
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


def get_self_eval_service(
    context: ServiceContext | None = None,
) -> SelfEvaluatingPipelineService:
    """Resolve SelfEvaluatingPipelineService from context or fall back to plugin singleton / engine."""
    if context is not None:
        svc = context.optional(SELF_EVALUATING_PIPELINE_SERVICE_KEY)
        if svc is not None:
            return svc

    # Fallback to plugin singleton
    _ws_root = Path.cwd()
    if str(_ws_root) not in sys.path:
        sys.path.insert(0, str(_ws_root))
    if str(_ws_root / "src") not in sys.path:
        sys.path.insert(0, str(_ws_root / "src"))

    try:
        from plugins.agent_orchestration.self_evaluating_pipeline.main import (
            plugin as eval_plugin,
        )

        return eval_plugin
    except Exception as exc:
        logger.warning(
            "self_evaluating_pipeline_plugin_fallback_failed", error=str(exc)
        )
        skill_scripts = (
            _ws_root / ".agents" / "skills" / "self-evaluating-ai-pipeline" / "scripts"
        )
        if str(skill_scripts) not in sys.path:
            sys.path.insert(0, str(skill_scripts))
        from self_evaluating_pipeline_engine import (  # type: ignore
            GoldenTestCase,
            HumanAnnotationRecord,
            SelfEvaluatingPipelineEngine,
        )

        class _EngineAdapter(SelfEvaluatingPipelineService):
            def __init__(self) -> None:
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
                res = self._eng.evaluate_layer2_judge(
                    prompt,
                    response,
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
                return self._eng.generate_visual_brief(
                    reg_obj, gating_decision=gate_obj, output_path=output_path
                )

        return _EngineAdapter()


@click.group("eval")
def eval_group() -> None:
    """Self-Evaluating AI Pipeline — 3-layer LLM quality evaluation & statistical gating."""


@eval_group.command("layer1")
@click.argument("text")
@click.option("--schema", default=None, help="Expected schema format (json, xml)")
@click.option("--min-len", type=int, default=10, help="Minimum character length")
@click.option("--max-len", type=int, default=5000, help="Maximum character length")
@click.option(
    "--whitelist", default=None, help="Comma-separated authorized URL domains"
)
@click.option("--syntax", default=None, help="Language syntax validator (e.g. python)")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON payload")
def layer1_cmd(
    text: str,
    schema: str | None,
    min_len: int,
    max_len: int,
    whitelist: str | None,
    syntax: str | None,
    json_output: bool,
) -> None:
    """Execute sub-millisecond Layer 1 deterministic sanity checks on raw text."""
    svc = get_self_eval_service()
    allowed_domains = [d.strip() for d in whitelist.split(",")] if whitelist else None

    rep = svc.evaluate_layer1(
        output_text=text,
        expected_schema=schema,
        min_len=min_len,
        max_len=max_len,
        allowed_domains=allowed_domains,
        syntax_lang=syntax,
    )

    if json_output:
        click.echo(_json.dumps(rep.model_dump(), indent=2))
        return

    status_icon = "PASS" if rep.passed else "FAIL"
    click.echo(f"Layer 1 Status: {status_icon} (Latency: {rep.total_latency_ms:.2f}ms)")
    if rep.refusal_detected:
        click.echo("  [WARNING] Unprompted canned refusal detected!")
    if rep.hallucinated_urls:
        click.echo(
            f"  [WARNING] Unauthorized/Hallucinated URLs: {rep.hallucinated_urls}"
        )
    for c in rep.checks:
        c_status = "OK" if c["passed"] else "FAIL"
        click.echo(f"  [{c_status}] {c['name']}: {c['message']}")


@eval_group.command("judge")
@click.argument("prompt")
@click.argument("response")
@click.option("--model", default="gpt-4o-mini", help="Judge model identifier")
@click.option("--judges", type=int, default=3, help="Number of consensus judges")
@click.option("--threshold", type=float, default=3.5, help="Minimum passing score")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON payload")
def judge_cmd(
    prompt: str,
    response: str,
    model: str,
    judges: int,
    threshold: float,
    json_output: bool,
) -> None:
    """Execute Layer 2 anchored semantic evaluation with median consensus."""
    svc = get_self_eval_service()
    res = svc.evaluate_layer2_judge(
        prompt=prompt,
        response=response,
        model=model,
        num_judges=judges,
        threshold=threshold,
    )

    if json_output:
        click.echo(_json.dumps(res.model_dump(), indent=2))
        return

    status_icon = "PASS" if res.passed else "FAIL"
    click.echo(
        f"Layer 2 Judge Status: {status_icon} (Median Score: {res.median_score:.1f} / 5.0, Mean: {res.mean_score:.2f})"
    )
    click.echo(f"  Individual Scores: {res.scores}")
    for j in res.judge_results:
        click.echo(f"  - [{j['judge_id']}] Score: {j['score']} | {j['reasoning']}")


@eval_group.command("kappa")
@click.argument("annotations_file", type=click.Path(exists=True, dir_okay=False))
@click.option("--json", "json_output", is_flag=True, help="Output as JSON payload")
def kappa_cmd(annotations_file: str, json_output: bool) -> None:
    """Calculate Layer 3 Cohen's Kappa human inter-annotator agreement."""
    svc = get_self_eval_service()
    raw = _json.loads(Path(annotations_file).read_text(encoding="utf-8"))
    ann_a = raw.get("rater_a", [])
    ann_b = raw.get("rater_b", [])

    rep = svc.calculate_cohens_kappa(ann_a, ann_b)
    if json_output:
        click.echo(_json.dumps(rep.model_dump(), indent=2))
        return

    verdict = "ACCEPTABLE" if rep.is_acceptable else "UNACCEPTABLE (kappa <= 0.6)"
    click.echo(f"Cohen's Kappa: {rep.cohens_kappa:.3f} ({verdict})")
    click.echo(f"  Observed Agreement: {rep.observed_agreement * 100:.1f}%")
    click.echo(
        f"  Expected Chance Agreement: {rep.expected_chance_agreement * 100:.1f}%"
    )
    click.echo(f"  Paired Samples: {rep.paired_samples_count}")
    click.echo(f"  Interpretation: {rep.interpretation}")


@eval_group.command("drift")
@click.option(
    "--human", "human_path", required=True, help="Path to JSON file of human scores"
)
@click.option(
    "--judge", "judge_path", required=True, help="Path to JSON file of judge scores"
)
@click.option("--max-drift", type=float, default=0.5, help="Maximum allowable drift")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON payload")
def drift_cmd(
    human_path: str,
    judge_path: str,
    max_drift: float,
    json_output: bool,
) -> None:
    """Audit automated LLM judge drift against human calibration ratings."""
    svc = get_self_eval_service()
    h_scores = _json.loads(Path(human_path).read_text(encoding="utf-8"))
    j_scores = _json.loads(Path(judge_path).read_text(encoding="utf-8"))

    rep = svc.audit_judge_drift(h_scores, j_scores, max_allowed_drift=max_drift)
    if json_output:
        click.echo(_json.dumps(rep.model_dump(), indent=2))
        return

    verdict = "DRIFT DETECTED" if rep.drift_detected else "STABLE"
    click.echo(f"Judge Drift Audit: {verdict}")
    click.echo(
        f"  Mean Absolute Deviation: {rep.mean_absolute_deviation:.3f} (Max: {rep.max_allowed_drift:.2f})"
    )
    click.echo(f"  Benchmark Samples: {rep.sample_count}")


@eval_group.command("regression")
@click.option(
    "--golden", "golden_path", required=True, help="Path to golden dataset JSON"
)
@click.option("--min-score", type=float, default=3.5, help="Minimum passing score")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON payload")
def regression_cmd(golden_path: str, min_score: float, json_output: bool) -> None:
    """Execute CI/CD regression suite across curated golden test dataset."""
    svc = get_self_eval_service()
    rep = svc.run_golden_regression(
        golden_dataset_path=golden_path, min_judge_score=min_score
    )

    if json_output:
        click.echo(_json.dumps(rep.model_dump(), indent=2))
        return

    click.echo(f"Regression Suite Run: {rep.run_id}")
    click.echo(
        f"  Total Cases: {rep.total_cases} | Passed: {rep.passed_cases} ({rep.pass_rate * 100:.1f}%)"
    )
    click.echo(f"  Layer 1 Pass Rate: {rep.layer1_pass_rate * 100:.1f}%")
    click.echo(f"  Mean Score: {rep.mean_score:.2f} / 5.0")
    if rep.failures:
        click.echo(f"  Recorded Failures: {len(rep.failures)}")


@eval_group.command("gate")
@click.option(
    "--before",
    "before_path",
    required=True,
    help="Path or JSON string of pre-change scores",
)
@click.option(
    "--after",
    "after_path",
    required=True,
    help="Path or JSON string of post-change scores",
)
@click.option(
    "--alpha", type=float, default=0.05, help="Statistical significance alpha"
)
@click.option("--json", "json_output", is_flag=True, help="Output as JSON payload")
def gate_cmd(
    before_path: str,
    after_path: str,
    alpha: float,
    json_output: bool,
) -> None:
    """Run Stage 5 paired Student's t-test statistical significance deployment gate."""
    svc = get_self_eval_service()
    sb = (
        _json.loads(Path(before_path).read_text(encoding="utf-8"))
        if Path(before_path).exists()
        else _json.loads(before_path)
    )
    sa = (
        _json.loads(Path(after_path).read_text(encoding="utf-8"))
        if Path(after_path).exists()
        else _json.loads(after_path)
    )

    gate = svc.evaluate_statistical_significance_gate(sb, sa, alpha=alpha)
    if json_output:
        click.echo(_json.dumps(gate.model_dump(), indent=2))
        return

    badge = click.style(
        gate.decision, fg="green" if gate.decision == "APPROVED" else "red", bold=True
    )
    click.echo(f"Deployment Gate Verdict: {badge}")
    click.echo(f"  p-value: {gate.p_value:.4f} (alpha: {alpha})")
    click.echo(f"  Student's t-statistic: {gate.t_statistic:.3f}")
    click.echo(f"  Mean Score Delta: {gate.mean_difference:+.3f}")
    click.echo(f"  Justification: {gate.justification}")


@eval_group.command("brief")
@click.option(
    "--result", "result_path", required=True, help="Path to regression JSON result"
)
@click.option(
    "--gate", "gate_path", default=None, help="Optional path to statistical gate JSON"
)
@click.option(
    "--output", "output_path", default=None, help="Destination HTML file path"
)
def brief_cmd(
    result_path: str,
    gate_path: str | None,
    output_path: str | None,
) -> None:
    """Generate standalone interactive HTML visual brief in %TEMP%."""
    svc = get_self_eval_service()
    reg_data = _json.loads(Path(result_path).read_text(encoding="utf-8"))
    gate_data = (
        _json.loads(Path(gate_path).read_text(encoding="utf-8")) if gate_path else None
    )

    out_file = svc.generate_visual_brief(
        regression_data=reg_data,
        gate_data=gate_data,
        output_path=output_path,
    )
    click.echo(f"Visual Brief generated: {out_file.resolve()}")
