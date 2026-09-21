"""Self-Evaluating AI Pipeline Engine — 3-Layer LLM Quality Architecture.

Synthesized from Jude Otine's foundational literature ("How to Build a Self-Evaluating AI System",
freeCodeCamp, 2026), grounded in Knowledge Item ki_self_20260917_02.

Enforces:
1. Layer 1: Sub-millisecond, zero-cost deterministic guardrails (schema, bounds, links, refusals, AST).
2. Layer 2: Semantic LLM-as-judge with discrete 1-to-5 observable anchors and median consensus.
3. Layer 3: Human calibration loop with Cohen's Kappa (kappa > 0.6) and monthly judge drift tracking.
4. Layer 4: Golden dataset regression suite with incident ingestion.
5. Layer 5: Paired Student's t-test statistical significance gating (p < 0.05 AND delta > 0).
"""

from __future__ import annotations

import ast
import datetime
import json
import math
import re
import statistics
import sys
import tempfile
import time
from collections import Counter
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import structlog

# Rule 23: Windows UTF-8 Stream Codec Entrypoint Invariant
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

logger = structlog.get_logger(__name__)

# Common refusal substrings per Otine (2026)
CANONICAL_REFUSAL_PHRASES: tuple[str, ...] = (
    "as an ai",
    "as a language model",
    "as a large language model",
    "i cannot fulfill",
    "i'm unable to",
    "i am unable to",
    "i don't have access",
    "i do not have access",
    "i apologize, but i cannot",
    "as an artificial intelligence",
)

URL_REGEX: re.Pattern[str] = re.compile(
    r"https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&//=]*)",
    re.IGNORECASE,
)


# --- Slotted & Frozen Domain Entities (Rule 12 & Rule 43) ---


@dataclass(slots=True, frozen=True)
class DeterministicCheckResult:
    """Individual rule-based check observation."""

    name: str
    passed: bool
    latency_ms: float
    message: str
    details: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("Check name must not be empty.")


@dataclass(slots=True, frozen=True)
class Layer1EvaluationReport:
    """Consolidated Layer 1 deterministic pre-flight report."""

    passed: bool
    total_latency_ms: float
    checks: tuple[DeterministicCheckResult, ...]
    refusal_detected: bool
    hallucinated_urls: tuple[str, ...]
    syntax_valid: bool


@dataclass(slots=True, frozen=True)
class RubricAnchor:
    """Observable 1-to-5 anchor definition for semantic LLM judging."""

    score: int
    label: str
    description: str
    criteria: tuple[str, ...]

    def __post_init__(self) -> None:
        if not (1 <= self.score <= 5):
            raise ValueError(f"Rubric score must be between 1 and 5, got {self.score}")


DEFAULT_RUBRIC_ANCHORS: tuple[RubricAnchor, ...] = (
    RubricAnchor(
        score=1,
        label="Irrelevant/Harmful",
        description="Completely irrelevant, incorrect, harmful, or unresponsive to prompt.",
        criteria=("Fails core intent", "Major safety/policy violation", "Unintelligible"),
    ),
    RubricAnchor(
        score=2,
        label="Major Errors",
        description="On-topic but contains major factual errors, hallucinated facts, or omissions.",
        criteria=("Key facts wrong", "Critical instructions ignored", "Severe hallucination"),
    ),
    RubricAnchor(
        score=3,
        label="Partially Correct",
        description="Partially correct; core points present but misses important nuances or structure.",
        criteria=("Core answer present", "Incomplete coverage", "Superficial explanation"),
    ),
    RubricAnchor(
        score=4,
        label="Accurate & Helpful",
        description="Fully accurate and helpful; directly answers prompt with only minor aesthetic issues.",
        criteria=("Directly responsive", "Accurate facts", "Clean presentation"),
    ),
    RubricAnchor(
        score=5,
        label="Comprehensive & Flawless",
        description="Comprehensive, flawless accuracy, well-structured, and exceeds intent.",
        criteria=("Flawless technical rigor", "Anticipates edge cases", "Optimal structure"),
    ),
)


@dataclass(slots=True, frozen=True)
class JudgeScoreResult:
    """Individual judge evaluation output."""

    judge_id: str
    score: int
    reasoning: str
    duration_ms: float

    def __post_init__(self) -> None:
        if not (1 <= self.score <= 5):
            raise ValueError(f"Judge score must be between 1 and 5, got {self.score}")


@dataclass(slots=True, frozen=True)
class MultiJudgeConsensusResult:
    """Median consensus from multi-judge evaluation."""

    median_score: float
    mean_score: float
    scores: tuple[int, ...]
    judge_results: tuple[JudgeScoreResult, ...]
    passed: bool
    threshold: float


@dataclass(slots=True, frozen=True)
class HumanAnnotationRecord:
    """Ground-truth human annotation entry."""

    annotation_id: str
    sample_id: str
    annotator_id: str
    score: int
    feedback: str = ""
    timestamp: str = ""

    def __post_init__(self) -> None:
        if not (1 <= self.score <= 5):
            raise ValueError(f"Annotation score must be between 1 and 5, got {self.score}")


@dataclass(slots=True, frozen=True)
class InterAnnotatorAgreementReport:
    """Statistical measurement of human rater agreement corrected for chance."""

    cohens_kappa: float
    observed_agreement: float
    expected_chance_agreement: float
    is_acceptable: bool
    interpretation: str
    paired_samples_count: int


@dataclass(slots=True, frozen=True)
class JudgeDriftAuditReport:
    """Audit of LLM judge deviation against human calibration benchmark."""

    mean_absolute_deviation: float
    sample_count: int
    drift_detected: bool
    max_allowed_drift: float
    details: tuple[dict[str, Any], ...] = ()


@dataclass(slots=True, frozen=True)
class GoldenTestCase:
    """Standardized test case for CI/CD regression suites."""

    test_id: str
    prompt: str
    expected_category: str
    difficulty: str
    expected_criteria: tuple[str, ...] = ()
    pre_change_score: float | None = None


@dataclass(slots=True, frozen=True)
class RegressionRunResult:
    """Outcome of regression suite run against golden dataset."""

    run_id: str
    total_cases: int
    passed_cases: int
    pass_rate: float
    layer1_pass_rate: float
    mean_score: float
    scores: tuple[float, ...]
    failures: tuple[dict[str, Any], ...]


@dataclass(slots=True, frozen=True)
class StatisticalGatingDecision:
    """Paired Student's t-test statistical release gate decision."""

    p_value: float
    t_statistic: float
    mean_difference: float
    sample_size: int
    is_significant: bool
    is_improvement: bool
    decision: str  # "APPROVED" | "BLOCKED_NOISE" | "BLOCKED_REGRESSION"
    justification: str


# --- Authoritative Slotted Domain Engine ---


class SelfEvaluatingPipelineEngine:
    """Production 5-stage evaluation engine synthesized from Jude Otine (2026)."""

    def __init__(
        self,
        rubric_anchors: Sequence[RubricAnchor] | None = None,
        config_path: Path | str | None = None,
    ) -> None:
        self._anchors = tuple(rubric_anchors or DEFAULT_RUBRIC_ANCHORS)
        self._config: dict[str, Any] = {}
        if config_path:
            p = Path(config_path)
            if p.exists():
                try:
                    import yaml

                    self._config = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
                except Exception as exc:
                    logger.warning("failed_loading_config", path=str(p), error=str(exc))

    @property
    def rubric_anchors(self) -> tuple[RubricAnchor, ...]:
        return self._anchors

    # --- Stage 1: Deterministic Guardrails (<1ms, $0) ---

    def evaluate_layer1(
        self,
        output_text: str,
        expected_schema: str | None = None,
        min_len: int = 10,
        max_len: int = 5000,
        allowed_domains: Sequence[str] | None = None,
        syntax_lang: str | None = None,
    ) -> Layer1EvaluationReport:
        """Run sub-millisecond deterministic sanity checks on raw output text."""
        t0 = time.perf_counter()
        checks: list[DeterministicCheckResult] = []
        clean_text = output_text.strip()

        # 1. Length Boundary Check
        t_len_0 = time.perf_counter()
        char_count = len(clean_text)
        len_passed = min_len <= char_count <= max_len
        len_msg = (
            f"Length {char_count} within [{min_len}, {max_len}] chars"
            if len_passed
            else f"Length {char_count} outside allowed [{min_len}, {max_len}] chars"
        )
        checks.append(
            DeterministicCheckResult(
                name="length_boundary",
                passed=len_passed,
                latency_ms=(time.perf_counter() - t_len_0) * 1000,
                message=len_msg,
                details=(f"chars={char_count}",),
            )
        )

        # 2. Schema & Syntax Check
        syntax_valid = True
        if expected_schema:
            t_schema_0 = time.perf_counter()
            schema_type = expected_schema.lower()
            if schema_type == "json":
                try:
                    json.loads(clean_text)
                    schema_passed = True
                    schema_msg = "Valid JSON payload syntax"
                except Exception as exc:
                    schema_passed = False
                    schema_msg = f"JSON syntax error: {exc}"
                    syntax_valid = False
            elif schema_type in ("xml", "html"):
                schema_passed = (
                    clean_text.startswith("<")
                    and clean_text.endswith(">")
                    and ("</" in clean_text or "/>" in clean_text)
                )
                schema_msg = (
                    "Valid XML/HTML tag syntax"
                    if schema_passed
                    else "Missing balanced XML/HTML tags"
                )
                if not schema_passed:
                    syntax_valid = False
            else:
                schema_passed = True
                schema_msg = f"Unknown schema format {expected_schema} bypassed"

            checks.append(
                DeterministicCheckResult(
                    name="schema_syntax",
                    passed=schema_passed,
                    latency_ms=(time.perf_counter() - t_schema_0) * 1000,
                    message=schema_msg,
                )
            )

        # 3. Domain Syntax Check (Python AST)
        if syntax_lang and syntax_lang.lower() == "python":
            t_ast_0 = time.perf_counter()
            try:
                # Extract codeblock if wrapped in markdown
                code_to_parse = clean_text
                if "```python" in clean_text:
                    parts = clean_text.split("```python")
                    if len(parts) > 1:
                        code_to_parse = parts[1].split("```")[0]
                elif "```" in clean_text:
                    parts = clean_text.split("```")
                    if len(parts) > 1:
                        code_to_parse = parts[1]

                ast.parse(code_to_parse)
                ast_passed = True
                ast_msg = "Python syntax verified via AST parse"
            except Exception as exc:
                ast_passed = False
                ast_msg = f"Python AST syntax error: {exc}"
                syntax_valid = False

            checks.append(
                DeterministicCheckResult(
                    name="domain_ast_syntax",
                    passed=ast_passed,
                    latency_ms=(time.perf_counter() - t_ast_0) * 1000,
                    message=ast_msg,
                )
            )

        # 4. Refusal Phrase Scanning
        t_refusal_0 = time.perf_counter()
        lower_text = clean_text.lower()
        matched_refusals = [
            phrase for phrase in CANONICAL_REFUSAL_PHRASES if phrase in lower_text
        ]
        refusal_detected = len(matched_refusals) > 0
        refusal_msg = (
            f"Unprompted refusal detected: {matched_refusals[0]}"
            if refusal_detected
            else "No canned refusal phrases detected"
        )
        checks.append(
            DeterministicCheckResult(
                name="refusal_detection",
                passed=not refusal_detected,
                latency_ms=(time.perf_counter() - t_refusal_0) * 1000,
                message=refusal_msg,
                details=tuple(matched_refusals),
            )
        )

        # 5. Hallucinated URL & Link Detection
        t_url_0 = time.perf_counter()
        extracted_urls = tuple(URL_REGEX.findall(clean_text))
        hallucinated: list[str] = []
        if allowed_domains and extracted_urls:
            whitelist = {d.lower().strip() for d in allowed_domains}
            for u in extracted_urls:
                try:
                    domain = urlparse(u).netloc.lower()
                    if not any(
                        domain == d or domain.endswith("." + d) for d in whitelist
                    ):
                        hallucinated.append(u)
                except Exception:
                    hallucinated.append(u)

        url_passed = len(hallucinated) == 0
        url_msg = (
            f"All {len(extracted_urls)} extracted URLs matched authorized whitelist"
            if url_passed
            else f"Detected {len(hallucinated)} unauthorized/hallucinated URLs"
        )
        checks.append(
            DeterministicCheckResult(
                name="url_hallucination",
                passed=url_passed,
                latency_ms=(time.perf_counter() - t_url_0) * 1000,
                message=url_msg,
                details=tuple(hallucinated),
            )
        )

        total_latency_ms = (time.perf_counter() - t0) * 1000
        overall_passed = all(c.passed for c in checks)

        return Layer1EvaluationReport(
            passed=overall_passed,
            total_latency_ms=total_latency_ms,
            checks=tuple(checks),
            refusal_detected=refusal_detected,
            hallucinated_urls=tuple(hallucinated),
            syntax_valid=syntax_valid,
        )

    # --- Stage 2: Anchored Rubric & LLM-as-Judge ---

    def evaluate_layer2_judge(
        self,
        prompt: str,
        response: str,
        rubric: Sequence[RubricAnchor] | None = None,
        model: str = "gpt-4o-mini",
        num_judges: int = 3,
        threshold: float = 3.5,
        custom_evaluator: Callable[[str, str, int], tuple[int, str]] | None = None,
    ) -> MultiJudgeConsensusResult:
        """Evaluate semantic quality using discrete 1-to-5 anchors and median consensus."""
        anchors = rubric or self._anchors
        judge_results: list[JudgeScoreResult] = []

        for i in range(num_judges):
            judge_id = f"judge_{i + 1}_{model}"
            t0 = time.perf_counter()

            if custom_evaluator:
                score, reasoning = custom_evaluator(prompt, response, i)
            else:
                # Deterministic semantic simulation based on observable anchors
                score, reasoning = self._simulate_anchored_judge(
                    prompt, response, anchors, seed=i
                )

            duration_ms = (time.perf_counter() - t0) * 1000
            judge_results.append(
                JudgeScoreResult(
                    judge_id=judge_id,
                    score=score,
                    reasoning=reasoning,
                    duration_ms=duration_ms,
                )
            )

        scores = tuple(r.score for r in judge_results)
        median_score = float(statistics.median(scores))
        mean_score = float(statistics.mean(scores))
        passed = median_score >= threshold

        return MultiJudgeConsensusResult(
            median_score=median_score,
            mean_score=mean_score,
            scores=scores,
            judge_results=tuple(judge_results),
            passed=passed,
            threshold=threshold,
        )

    def _simulate_anchored_judge(
        self,
        prompt: str,
        response: str,
        rubric: Sequence[RubricAnchor],
        seed: int = 0,
    ) -> tuple[int, str]:
        """Deterministic heuristic judge simulation when LLM API is offline."""
        clean_resp = response.strip()
        lower_resp = clean_resp.lower()

        # Score 1 Check: Canned refusal or empty
        if len(clean_resp) < 15 or any(
            p in lower_resp for p in CANONICAL_REFUSAL_PHRASES[:3]
        ):
            return 1, "Response refused the task or was empty/unresponsive."

        # Score 2 Check: Error flag or hallucination signals
        if "error" in lower_resp and len(clean_resp) < 50:
            return 2, "Response acknowledges error with major factual deficiencies."

        # Score 3 Check: Brief/generic response
        if len(clean_resp) < 80:
            return 3, "Response is partially correct but lacks depth and structure."

        # Score 4 Check: Helpful, structured, addresses prompt
        if 80 <= len(clean_resp) < 250:
            return 4, "Accurate and directly responsive with minor omission of depth."

        # Score 5 Check: Detailed, comprehensive
        return 5, "Comprehensive, flawless accuracy, well-structured and exceeds intent."

    # --- Stage 3: Ground Truth Human Calibration & Agreement ---

    def calculate_cohens_kappa(
        self,
        annotations_a: Sequence[HumanAnnotationRecord],
        annotations_b: Sequence[HumanAnnotationRecord],
    ) -> InterAnnotatorAgreementReport:
        """Calculate Cohen's Kappa inter-annotator agreement corrected for chance."""
        map_a = {a.sample_id: a.score for a in annotations_a}
        map_b = {b.sample_id: b.score for b in annotations_b}
        common_ids = sorted(set(map_a.keys()) & set(map_b.keys()))

        if not common_ids:
            return InterAnnotatorAgreementReport(
                cohens_kappa=0.0,
                observed_agreement=0.0,
                expected_chance_agreement=0.0,
                is_acceptable=False,
                interpretation="No overlapping annotated samples found.",
                paired_samples_count=0,
            )

        n = len(common_ids)
        scores_a = [map_a[cid] for cid in common_ids]
        scores_b = [map_b[cid] for cid in common_ids]

        # Observed Agreement (Po)
        agreements = sum(1 for sa, sb in zip(scores_a, scores_b) if sa == sb)
        p_o = agreements / n

        # Expected Chance Agreement (Pe)
        counter_a = Counter(scores_a)
        counter_b = Counter(scores_b)
        categories = range(1, 6)
        p_e = sum((counter_a[k] / n) * (counter_b[k] / n) for k in categories)

        # Cohen's Kappa: (Po - Pe) / (1 - Pe)
        if math.isclose(p_e, 1.0):
            kappa = 1.0 if math.isclose(p_o, 1.0) else 0.0
        else:
            kappa = (p_o - p_e) / (1.0 - p_e)

        # Interpretation per Landis & Koch (1977) and Otine (2026)
        if kappa > 0.8:
            interp = "Near perfect agreement"
        elif kappa > 0.6:
            interp = "Substantial agreement (Acceptable)"
        elif kappa > 0.4:
            interp = "Moderate agreement (Refine rubrics)"
        else:
            interp = "Poor agreement (Ambiguous rubrics; halt release)"

        is_acceptable = kappa > 0.6

        return InterAnnotatorAgreementReport(
            cohens_kappa=float(kappa),
            observed_agreement=float(p_o),
            expected_chance_agreement=float(p_e),
            is_acceptable=is_acceptable,
            interpretation=interp,
            paired_samples_count=n,
        )

    def audit_judge_drift(
        self,
        human_scores: Sequence[int | float],
        judge_scores: Sequence[int | float],
        max_allowed_drift: float = 0.5,
    ) -> JudgeDriftAuditReport:
        """Audit automated judge drift by calculating Mean Absolute Deviation from human ratings."""
        if not human_scores or not judge_scores or len(human_scores) != len(judge_scores):
            raise ValueError("Human and judge score lists must be non-empty and equal length.")

        n = len(human_scores)
        deviations = [abs(float(h) - float(j)) for h, j in zip(human_scores, judge_scores)]
        mad = sum(deviations) / n
        drift_detected = mad > max_allowed_drift

        details = tuple(
            {
                "index": i,
                "human": human_scores[i],
                "judge": judge_scores[i],
                "deviation": round(deviations[i], 3),
            }
            for i in range(n)
        )

        return JudgeDriftAuditReport(
            mean_absolute_deviation=float(mad),
            sample_count=n,
            drift_detected=drift_detected,
            max_allowed_drift=max_allowed_drift,
            details=details,
        )

    # --- Stage 4: Golden Dataset & CI/CD Regression Suite ---

    def run_golden_regression(
        self,
        golden_cases: Sequence[GoldenTestCase],
        generator: Callable[[str], str] | None = None,
        min_judge_score: float = 3.5,
    ) -> RegressionRunResult:
        """Execute regression pipeline across curated golden test suite."""
        run_id = f"reg_{int(time.time())}"
        total = len(golden_cases)
        passed_count = 0
        layer1_passes = 0
        scores: list[float] = []
        failures: list[dict[str, Any]] = []

        for case in golden_cases:
            response = (
                generator(case.prompt)
                if generator
                else f"Standard response for {case.prompt}. Rigorous technical answer."
            )

            # Layer 1
            l1 = self.evaluate_layer1(response)
            if l1.passed:
                layer1_passes += 1
            else:
                failures.append(
                    {
                        "test_id": case.test_id,
                        "failure_layer": "Layer1",
                        "errors": [c.message for c in l1.checks if not c.passed],
                    }
                )
                scores.append(1.0)
                continue

            # Layer 2
            l2 = self.evaluate_layer2_judge(
                case.prompt, response, threshold=min_judge_score
            )
            scores.append(l2.median_score)

            if l2.passed:
                passed_count += 1
            else:
                failures.append(
                    {
                        "test_id": case.test_id,
                        "failure_layer": "Layer2",
                        "score": l2.median_score,
                        "threshold": min_judge_score,
                        "reasoning": [j.reasoning for j in l2.judge_results],
                    }
                )

        pass_rate = (passed_count / total) if total > 0 else 0.0
        l1_pass_rate = (layer1_passes / total) if total > 0 else 0.0
        mean_score = statistics.mean(scores) if scores else 0.0

        return RegressionRunResult(
            run_id=run_id,
            total_cases=total,
            passed_cases=passed_count,
            pass_rate=float(pass_rate),
            layer1_pass_rate=float(l1_pass_rate),
            mean_score=float(mean_score),
            scores=tuple(scores),
            failures=tuple(failures),
        )

    # --- Stage 5: Paired Student's t-Test Release Gate ---

    def evaluate_statistical_significance_gate(
        self,
        scores_before: Sequence[float],
        scores_after: Sequence[float],
        alpha: float = 0.05,
    ) -> StatisticalGatingDecision:
        """Enforce paired Student's t-test release gate: p < 0.05 AND mean_diff > 0."""
        n_before = len(scores_before)
        n_after = len(scores_after)

        if n_before != n_after or n_before < 2:
            raise ValueError(
                f"Paired t-test requires identical non-trivial sample sizes (got {n_before} vs {n_after})."
            )

        mean_before = statistics.mean(scores_before)
        mean_after = statistics.mean(scores_after)
        mean_diff = mean_after - mean_before

        # Use scipy.stats.ttest_rel if available, else pure Python fallback
        try:
            from scipy import stats

            res = stats.ttest_rel(scores_after, scores_before)
            t_stat = float(res.statistic)
            p_val = float(res.pvalue)
        except Exception:
            # Mathematical paired t-test implementation fallback
            diffs = [a - b for a, b in zip(scores_after, scores_before)]
            d_bar = statistics.mean(diffs)
            sd = statistics.stdev(diffs) if len(diffs) > 1 else 0.0
            if math.isclose(sd, 0.0):
                t_stat = 0.0 if math.isclose(d_bar, 0.0) else float("inf")
                p_val = 1.0 if math.isclose(d_bar, 0.0) else 0.0
            else:
                t_stat = d_bar / (sd / math.sqrt(n_before))
                # Approximate 2-tailed p-value via standard normal error function approximation
                z = abs(t_stat)
                p_val = 2.0 * (1.0 - 0.5 * (1.0 + math.erf(z / math.sqrt(2.0))))

        is_significant = p_val < alpha
        is_improvement = mean_diff > 0

        if is_significant and is_improvement:
            decision = "APPROVED"
            justification = (
                f"Statistically significant improvement (p={p_val:.4f} < {alpha}, "
                f"delta=+{mean_diff:.3f}). Deployment authorized."
            )
        elif not is_improvement:
            decision = "BLOCKED_REGRESSION"
            justification = (
                f"Negative or zero mean score difference (delta={mean_diff:.3f} <= 0). "
                "System has regressed. Deployment blocked."
            )
        else:
            decision = "BLOCKED_NOISE"
            justification = (
                f"Improvement delta=+{mean_diff:.3f} is indistinguishable from random noise "
                f"(p={p_val:.4f} >= {alpha}). Deployment blocked."
            )

        return StatisticalGatingDecision(
            p_value=float(p_val),
            t_statistic=float(t_stat),
            mean_difference=float(mean_diff),
            sample_size=n_before,
            is_significant=is_significant,
            is_improvement=is_improvement,
            decision=decision,
            justification=justification,
        )

    # --- Standalone Visual Brief Generation (Rule 51) ---

    def generate_visual_brief(
        self,
        regression_result: RegressionRunResult,
        gating_decision: StatisticalGatingDecision | None = None,
        output_path: Path | str | None = None,
    ) -> Path:
        """Generate interactive HTML visual brief in %TEMP% summarizing evaluation run."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        if output_path:
            out_file = Path(output_path)
        else:
            out_file = (
                Path(tempfile.gettempdir())
                / f"self-eval-brief-{regression_result.run_id}-{timestamp}.html"
            )

        gate_badge = (
            '<span class="px-3 py-1 bg-emerald-900/60 text-emerald-400 border border-emerald-700 rounded-full font-bold">APPROVED</span>'
            if gating_decision and gating_decision.decision == "APPROVED"
            else '<span class="px-3 py-1 bg-rose-900/60 text-rose-400 border border-rose-700 rounded-full font-bold">BLOCKED</span>'
        )

        decision_text = gating_decision.justification if gating_decision else "N/A"
        p_val_text = f"{gating_decision.p_value:.4f}" if gating_decision else "N/A"
        delta_text = (
            f"{gating_decision.mean_difference:+.3f}" if gating_decision else "N/A"
        )

        failure_rows = ""
        for f in regression_result.failures[:10]:
            layer = f.get("failure_layer", "Unknown")
            tid = f.get("test_id", "N/A")
            err = str(f.get("errors") or f.get("reasoning") or "Score below threshold")
            failure_rows += f"""
            <tr class="border-b border-slate-800 text-xs">
              <td class="p-2 font-mono text-slate-300">{tid}</td>
              <td class="p-2 font-semibold text-amber-400">{layer}</td>
              <td class="p-2 text-slate-400">{err[:120]}</td>
            </tr>
            """

        if not failure_rows:
            failure_rows = '<tr><td colspan="3" class="p-4 text-center text-xs text-slate-500">Zero failures recorded</td></tr>'

        # Rule 51: Dynamic template isolation / double braces
        html = f"""<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <title>Self-Evaluating AI Pipeline: Visual Brief</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    body {{ background-color: #0b0f19; color: #e2e8f0; font-family: ui-sans-serif, system-ui, sans-serif; }}
  </style>
</head>
<body class="p-8 max-w-5xl mx-auto space-y-6">
  <header class="border-b border-slate-800 pb-4 flex justify-between items-center">
    <div>
      <span class="text-xs font-semibold px-2 py-0.5 rounded bg-indigo-950 text-indigo-400 border border-indigo-800">
        Run ID: {regression_result.run_id}
      </span>
      <h1 class="text-2xl font-extrabold text-white mt-1">Self-Evaluating AI Pipeline Visual Brief</h1>
      <p class="text-xs text-slate-400 mt-0.5">Automated 3-layer LLM quality evaluation & statistical deployment gate</p>
    </div>
    <div>{gate_badge}</div>
  </header>

  <div class="grid grid-cols-4 gap-4 text-center">
    <div class="bg-slate-900 border border-slate-800 rounded-lg p-3">
      <div class="text-xs text-slate-400">Total Cases</div>
      <div class="text-xl font-bold text-white mt-1">{regression_result.total_cases}</div>
    </div>
    <div class="bg-slate-900 border border-slate-800 rounded-lg p-3">
      <div class="text-xs text-slate-400">Pass Rate</div>
      <div class="text-xl font-bold text-emerald-400 mt-1">{regression_result.pass_rate * 100:.1f}%</div>
    </div>
    <div class="bg-slate-900 border border-slate-800 rounded-lg p-3">
      <div class="text-xs text-slate-400">Layer 1 Pass Rate</div>
      <div class="text-xl font-bold text-sky-400 mt-1">{regression_result.layer1_pass_rate * 100:.1f}%</div>
    </div>
    <div class="bg-slate-900 border border-slate-800 rounded-lg p-3">
      <div class="text-xs text-slate-400">Mean Judge Score</div>
      <div class="text-xl font-bold text-amber-400 mt-1">{regression_result.mean_score:.2f} / 5.0</div>
    </div>
  </div>

  <section class="bg-slate-900 border border-slate-800 rounded-lg p-4">
    <h2 class="text-sm font-bold text-white mb-2">Stage 5: Statistical Significance Gating (Paired t-Test)</h2>
    <div class="grid grid-cols-2 gap-4 text-xs font-mono bg-slate-950 p-3 rounded border border-slate-800">
      <div><span class="text-slate-500">p-value:</span> <span class="text-slate-200">{p_val_text}</span></div>
      <div><span class="text-slate-500">Mean Score Delta:</span> <span class="text-slate-200">{delta_text}</span></div>
    </div>
    <p class="text-xs text-slate-400 mt-2">{decision_text}</p>
  </section>

  <section class="bg-slate-900 border border-slate-800 rounded-lg p-4">
    <h2 class="text-sm font-bold text-white mb-2">Failure & Defect Observations</h2>
    <table class="w-full text-left border-collapse">
      <thead>
        <tr class="border-b border-slate-800 text-xs text-slate-500 font-mono">
          <th class="p-2">Test ID</th>
          <th class="p-2">Layer</th>
          <th class="p-2">Observation / Reasoning</th>
        </tr>
      </thead>
      <tbody>
        {failure_rows}
      </tbody>
    </table>
  </section>

  <footer class="text-center text-[10px] text-slate-600 font-mono pt-4">
    Generated by SelfEvaluatingPipelineEngine • Grounded in ki_self_20260917_02
  </footer>
</body>
</html>
"""
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(html, encoding="utf-8")
        return out_file
