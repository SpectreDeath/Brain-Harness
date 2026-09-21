"""Comprehensive tests for deepened self-evaluating AI pipeline architecture.

Covers:
- Slotted frozen dataclass immutability (Rule 12 & Rule 43)
- Sub-millisecond Layer 1 deterministic guardrails (schema, bounds, URLs, refusals, AST)
- Layer 2 anchored 1-to-5 rubric semantic judge & median consensus
- Layer 3 Cohen's Kappa human agreement (kappa > 0.6) & judge drift audit
- Layer 4 golden dataset regression pipeline execution
- Layer 5 paired Student's t-test statistical significance gating (p < 0.05 & delta > 0)
- Micro-kernel IoC service key registration & resolution (Rule 2 & Rule 49)
- PluginValidator compliance (Rule 34 & Rule 38)
- Headless Click CLI subcommands via CliRunner (Rule 6, Rule 10, Rule 23)
- Standalone HTML visual brief generation in %TEMP% (Rule 51)
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import pytest
from click.testing import CliRunner

_ws_root = Path(__file__).resolve().parent.parent
_skill_scripts = (
    _ws_root / ".agents" / "skills" / "self-evaluating-ai-pipeline" / "scripts"
)
for _p in [_ws_root / "src", _skill_scripts, _ws_root]:
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from self_evaluating_pipeline_engine import (
    DeterministicCheckResult,
    GoldenTestCase,
    HumanAnnotationRecord,
    InterAnnotatorAgreementReport,
    JudgeScoreResult,
    MultiJudgeConsensusResult,
    RegressionRunResult,
    RubricAnchor,
    SelfEvaluatingPipelineEngine,
    StatisticalGatingDecision,
)

from harness.commands.self_eval import eval_group
from harness.creator.validator import PluginValidator
from harness.kernel.context import ServiceContext
from harness.services.self_evaluating_pipeline import (
    SELF_EVALUATING_PIPELINE_SERVICE_KEY,
    Layer1ReportData,
    SelfEvaluatingPipelineService,
)
from plugins.agent_orchestration.self_evaluating_pipeline.main import (
    plugin as eval_plugin,
)


@pytest.fixture
def engine() -> SelfEvaluatingPipelineEngine:
    return SelfEvaluatingPipelineEngine()


@pytest.fixture
def golden_dataset_path() -> Path:
    p = (
        _ws_root
        / ".agents"
        / "skills"
        / "self-evaluating-ai-pipeline"
        / "resources"
        / "golden_dataset.json"
    )
    assert p.exists(), f"Missing golden dataset: {p}"
    return p


# --- 1. Slotted & Frozen Dataclass Immutability (Rule 12 & Rule 43) ---


def test_frozen_dataclass_immutability():
    """Verify slotted & frozen dataclasses prevent attribute mutation (Rule 12 & Rule 43)."""
    check = DeterministicCheckResult(
        name="test_check",
        passed=True,
        latency_ms=0.1,
        message="OK",
    )
    with pytest.raises((AttributeError, TypeError)):
        check.passed = False  # type: ignore

    anchor = RubricAnchor(
        score=4,
        label="Accurate",
        description="Helpful answer",
        criteria=("criterion 1",),
    )
    with pytest.raises((AttributeError, TypeError)):
        anchor.score = 5  # type: ignore

    judge_res = JudgeScoreResult(
        judge_id="j1",
        score=4,
        reasoning="Good",
        duration_ms=10.0,
    )
    with pytest.raises((AttributeError, TypeError)):
        judge_res.score = 3  # type: ignore

    consensus = MultiJudgeConsensusResult(
        median_score=4.0,
        mean_score=4.0,
        scores=(4, 4, 4),
        judge_results=(judge_res,),
        passed=True,
        threshold=3.5,
    )
    with pytest.raises((AttributeError, TypeError)):
        consensus.passed = False  # type: ignore

    annotation = HumanAnnotationRecord(
        annotation_id="ann_1",
        sample_id="s_1",
        annotator_id="usr_1",
        score=5,
    )
    with pytest.raises((AttributeError, TypeError)):
        annotation.score = 4  # type: ignore

    agreement = InterAnnotatorAgreementReport(
        cohens_kappa=0.85,
        observed_agreement=0.9,
        expected_chance_agreement=0.3,
        is_acceptable=True,
        interpretation="Near perfect",
        paired_samples_count=20,
    )
    with pytest.raises((AttributeError, TypeError)):
        agreement.cohens_kappa = 0.5  # type: ignore

    gate = StatisticalGatingDecision(
        p_value=0.01,
        t_statistic=3.2,
        mean_difference=0.45,
        sample_size=50,
        is_significant=True,
        is_improvement=True,
        decision="APPROVED",
        justification="Statistically significant",
    )
    with pytest.raises((AttributeError, TypeError)):
        gate.decision = "BLOCKED_NOISE"  # type: ignore


# --- 2. Sub-Millisecond Layer 1 Deterministic Sanity Checks ---


def test_layer1_deterministic_guardrails(engine: SelfEvaluatingPipelineEngine):
    """Verify Layer 1 catches schema errors, bounds, refusals, and hallucinated URLs in <10ms."""
    # Passing check
    good_text = '{"status": "success", "result": "The answer is 42", "url": "https://docs.python.org/3/"}'
    rep_good = engine.evaluate_layer1(
        good_text,
        expected_schema="json",
        min_len=10,
        max_len=5000,
        allowed_domains=["docs.python.org"],
    )
    assert rep_good.passed is True
    assert rep_good.refusal_detected is False
    assert len(rep_good.hallucinated_urls) == 0
    assert rep_good.total_latency_ms < 50.0  # sub-millisecond to few milliseconds

    # Failing Schema Check
    bad_json = '{"status": "incomplete", "result": '
    rep_bad_schema = engine.evaluate_layer1(bad_json, expected_schema="json")
    assert rep_bad_schema.passed is False
    assert rep_bad_schema.syntax_valid is False
    schema_check = next(c for c in rep_bad_schema.checks if c.name == "schema_syntax")
    assert schema_check.passed is False

    # Length Boundary Failure
    rep_too_short = engine.evaluate_layer1("Hi", min_len=10)
    assert rep_too_short.passed is False
    len_check = next(c for c in rep_too_short.checks if c.name == "length_boundary")
    assert len_check.passed is False

    # Refusal Phrase Detection
    refusal_text = (
        "I apologize, but as an AI language model, I cannot fulfill this request."
    )
    rep_refusal = engine.evaluate_layer1(refusal_text)
    assert rep_refusal.refusal_detected is True
    assert rep_refusal.passed is False

    # Hallucinated URL Detection
    unauthorized_link_text = (
        "Visit https://fabricated-fake-domain.xyz/docs for details."
    )
    rep_url = engine.evaluate_layer1(
        unauthorized_link_text,
        allowed_domains=["wikipedia.org", "github.com"],
    )
    assert rep_url.passed is False
    assert "https://fabricated-fake-domain.xyz/docs" in rep_url.hallucinated_urls

    # Python AST Syntax Check
    python_code = "def add(a, b):\n    return a + b\n"
    rep_py_ok = engine.evaluate_layer1(python_code, syntax_lang="python")
    assert rep_py_ok.passed is True

    bad_python = "def add(a, b\n    return a +"
    rep_py_bad = engine.evaluate_layer1(bad_python, syntax_lang="python")
    assert rep_py_bad.passed is False
    assert rep_py_bad.syntax_valid is False


# --- 3. Layer 2 Anchored Rubric & Median Consensus ---


def test_layer2_anchored_judge_and_consensus(engine: SelfEvaluatingPipelineEngine):
    """Verify Layer 2 semantic judging enforces observable 1-5 anchors and median consensus."""
    prompt = "Explain quicksort algorithm"
    response = (
        "Quicksort is an efficient divide-and-conquer sorting algorithm. "
        "It selects a pivot element and partitions the array into elements less than and greater than the pivot. "
        "The average time complexity is O(n log n), while worst-case is O(n^2)."
    )

    consensus = engine.evaluate_layer2_judge(
        prompt, response, num_judges=3, threshold=3.5
    )
    assert consensus.passed is True
    assert consensus.median_score >= 3.5
    assert len(consensus.scores) == 3
    assert all(1 <= s <= 5 for s in consensus.scores)

    # Custom evaluator callback simulating deterministic variance
    def _mock_judge(p: str, r: str, seed: int) -> tuple[int, str]:
        scores = [3, 5, 4]
        return scores[seed], f"Reasoning for score {scores[seed]}"

    var_consensus = engine.evaluate_layer2_judge(
        prompt, response, num_judges=3, custom_evaluator=_mock_judge
    )
    assert var_consensus.scores == (3, 5, 4)
    assert var_consensus.median_score == 4.0  # median of [3, 4, 5] is 4.0
    assert var_consensus.mean_score == 4.0


# --- 4. Layer 3 Cohen's Kappa & Judge Drift Audit ---


def test_layer3_cohens_kappa_calculation(engine: SelfEvaluatingPipelineEngine):
    """Verify Cohen's Kappa inter-annotator agreement and acceptance gating."""
    # Substantial/Near-Perfect agreement (kappa > 0.6)
    ann_a = [
        HumanAnnotationRecord("1", "s1", "user_a", 4),
        HumanAnnotationRecord("2", "s2", "user_a", 5),
        HumanAnnotationRecord("3", "s3", "user_a", 3),
        HumanAnnotationRecord("4", "s4", "user_a", 2),
        HumanAnnotationRecord("5", "s5", "user_a", 5),
    ]
    ann_b = [
        HumanAnnotationRecord("6", "s1", "user_b", 4),
        HumanAnnotationRecord("7", "s2", "user_b", 5),
        HumanAnnotationRecord("8", "s3", "user_b", 3),
        HumanAnnotationRecord("9", "s4", "user_b", 2),
        HumanAnnotationRecord("10", "s5", "user_b", 4),  # minor difference
    ]

    rep = engine.calculate_cohens_kappa(ann_a, ann_b)
    assert rep.is_acceptable is True
    assert rep.cohens_kappa > 0.6
    assert rep.observed_agreement == 0.8  # 4 out of 5 match
    assert rep.paired_samples_count == 5

    # Poor agreement (kappa <= 0.6)
    ann_c = [
        HumanAnnotationRecord("11", "s1", "user_c", 1),
        HumanAnnotationRecord("12", "s2", "user_c", 2),
        HumanAnnotationRecord("13", "s3", "user_c", 5),
        HumanAnnotationRecord("14", "s4", "user_c", 5),
        HumanAnnotationRecord("15", "s5", "user_c", 1),
    ]
    rep_poor = engine.calculate_cohens_kappa(ann_a, ann_c)
    assert rep_poor.is_acceptable is False
    assert rep_poor.cohens_kappa <= 0.6


def test_layer3_judge_drift_audit(engine: SelfEvaluatingPipelineEngine):
    """Verify automated judge drift audit flags MAD > 0.5 points."""
    # Stable ratings (MAD <= 0.5)
    human_scores = [4, 5, 3, 4, 5]
    judge_scores = [4, 5, 3, 4, 4]  # MAD = 1/5 = 0.2
    rep_stable = engine.audit_judge_drift(
        human_scores, judge_scores, max_allowed_drift=0.5
    )
    assert rep_stable.drift_detected is False
    assert pytest.approx(rep_stable.mean_absolute_deviation, 0.01) == 0.2

    # Drifting ratings (MAD > 0.5)
    judge_scores_drift = [2, 3, 1, 2, 3]  # MAD = 2.0
    rep_drift = engine.audit_judge_drift(
        human_scores, judge_scores_drift, max_allowed_drift=0.5
    )
    assert rep_drift.drift_detected is True
    assert rep_drift.mean_absolute_deviation == 2.0


# --- 5. Layer 4 Golden Dataset CI/CD Regression Suite ---


def test_layer4_golden_regression_suite(
    engine: SelfEvaluatingPipelineEngine, golden_dataset_path: Path
):
    """Verify regression suite executes across golden dataset with zero Layer 1 errors."""
    raw = json.loads(golden_dataset_path.read_text(encoding="utf-8"))
    cases = [
        GoldenTestCase(
            test_id=c["test_id"],
            prompt=c["prompt"],
            expected_category=c.get("expected_category", "general"),
            difficulty=c.get("difficulty", "medium"),
            pre_change_score=c.get("pre_change_score"),
        )
        for c in raw[:10]  # run across first 10 for fast unit test
    ]

    result = engine.run_golden_regression(cases, min_judge_score=3.5)
    assert result.total_cases == 10
    assert result.layer1_pass_rate == 1.0  # zero deterministic failures
    assert result.pass_rate >= 0.8
    assert len(result.scores) == 10


# --- 6. Layer 5 Paired Student's t-Test Gating ---


def test_layer5_statistical_significance_gate(engine: SelfEvaluatingPipelineEngine):
    """Verify Paired Student's t-test release gate decisions."""
    # Case 1: Significant Improvement (p < 0.05, delta > 0) -> APPROVED
    scores_before = [3.0, 3.2, 3.1, 2.9, 3.3, 3.0, 3.1, 3.2, 3.0, 3.1]
    scores_after = [4.5, 4.6, 4.4, 4.5, 4.7, 4.4, 4.6, 4.5, 4.6, 4.5]
    gate_app = engine.evaluate_statistical_significance_gate(
        scores_before, scores_after, alpha=0.05
    )
    assert gate_app.decision == "APPROVED"
    assert gate_app.is_significant is True
    assert gate_app.is_improvement is True
    assert gate_app.p_value < 0.05
    assert gate_app.mean_difference > 0

    # Case 2: Indistinguishable Noise (p >= 0.05, delta > 0) -> BLOCKED_NOISE
    scores_noise_after = [3.05, 3.2, 3.12, 2.9, 3.32, 3.01, 3.1, 3.21, 3.0, 3.1]
    gate_noise = engine.evaluate_statistical_significance_gate(
        scores_before, scores_noise_after, alpha=0.05
    )
    assert gate_noise.decision == "BLOCKED_NOISE"
    assert gate_noise.is_significant is False

    # Case 3: System Regression (delta <= 0) -> BLOCKED_REGRESSION
    scores_reg_after = [2.5, 2.7, 2.6, 2.4, 2.8, 2.5, 2.6, 2.5, 2.4, 2.6]
    gate_reg = engine.evaluate_statistical_significance_gate(
        scores_before, scores_reg_after, alpha=0.05
    )
    assert gate_reg.decision == "BLOCKED_REGRESSION"
    assert gate_reg.is_improvement is False


# --- 7. Micro-Kernel IoC Registration & Resolution ---


@pytest.mark.asyncio
async def test_ioc_service_registration():
    """Verify SelfEvaluatingPipelinePlugin registers into IoC container via typed key."""
    ctx = ServiceContext()
    await eval_plugin.on_load(ctx)

    svc = ctx.require(SELF_EVALUATING_PIPELINE_SERVICE_KEY)
    assert svc is not None
    assert isinstance(svc, SelfEvaluatingPipelineService)

    # Invoke method through resolved interface
    rep = svc.evaluate_layer1("Testing the micro-kernel service seam.")
    assert isinstance(rep, Layer1ReportData)
    assert rep.passed is True

    await eval_plugin.on_unload(ctx)


# --- 8. PluginValidator Compliance (Rule 34 & Rule 38) ---


def test_plugin_validator_compliance():
    """Verify plugin conforms to PluginValidator requirements."""
    plugin_dir = (
        _ws_root / "plugins" / "agent_orchestration" / "self_evaluating_pipeline"
    )
    assert plugin_dir.exists(), f"Plugin directory missing: {plugin_dir}"

    report = PluginValidator.validate_sync(plugin_dir)
    assert report.valid is True, f"PluginValidator errors: {report.errors}"
    assert len(report.warnings) == 0, f"Unexpected warnings: {report.warnings}"


# --- 9. Headless Click CLI Execution via CliRunner ---


def test_click_cli_subcommands(golden_dataset_path: Path):
    """Verify headless Click CLI commands (Rule 6, Rule 10, Rule 23)."""
    runner = CliRunner()

    # 1. layer1
    r_l1 = runner.invoke(eval_group, ["layer1", '{"valid": true}', "--schema", "json"])
    assert r_l1.exit_code == 0
    assert "Layer 1 Status: PASS" in r_l1.output

    # 2. judge
    response_text = "2 plus 2 equals 4. In standard integer arithmetic, adding two units to two units yields four."
    r_j = runner.invoke(eval_group, ["judge", "What is 2+2?", response_text])
    assert r_j.exit_code == 0
    assert "Layer 2 Judge Status: PASS" in r_j.output

    # 3. kappa
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tf:
        json.dump(
            {
                "rater_a": [
                    {
                        "annotation_id": "1",
                        "sample_id": "s1",
                        "annotator_id": "a",
                        "score": 4,
                    }
                ],
                "rater_b": [
                    {
                        "annotation_id": "2",
                        "sample_id": "s1",
                        "annotator_id": "b",
                        "score": 4,
                    }
                ],
            },
            tf,
        )
        tmp_file = tf.name

    r_k = runner.invoke(eval_group, ["kappa", tmp_file])
    assert r_k.exit_code == 0
    assert "Cohen's Kappa:" in r_k.output

    # 4. gate
    scores_b = json.dumps([3.0, 3.1, 3.2, 3.0, 3.1])
    scores_a = json.dumps([4.5, 4.6, 4.7, 4.5, 4.6])
    r_g = runner.invoke(eval_group, ["gate", "--before", scores_b, "--after", scores_a])
    assert r_g.exit_code == 0
    assert "APPROVED" in r_g.output


# --- 10. Standalone HTML Visual Brief Generation (Rule 51) ---


def test_visual_brief_generation(engine: SelfEvaluatingPipelineEngine):
    """Verify standalone HTML visual brief generation in %TEMP%."""
    run_res = RegressionRunResult(
        run_id="test_run_123",
        total_cases=10,
        passed_cases=9,
        pass_rate=0.9,
        layer1_pass_rate=1.0,
        mean_score=4.2,
        scores=(4.0, 4.5, 4.0, 5.0, 4.0, 4.5, 4.0, 4.0, 4.0, 4.0),
        failures=(),
    )
    gate_res = StatisticalGatingDecision(
        p_value=0.001,
        t_statistic=4.5,
        mean_difference=0.8,
        sample_size=10,
        is_significant=True,
        is_improvement=True,
        decision="APPROVED",
        justification="Statistically significant improvement.",
    )

    out_file = engine.generate_visual_brief(run_res, gate_res)
    assert out_file.exists()
    content = out_file.read_text(encoding="utf-8")
    assert "Self-Evaluating AI Pipeline Visual Brief" in content
    assert "APPROVED" in content
    assert "test_run_123" in content
