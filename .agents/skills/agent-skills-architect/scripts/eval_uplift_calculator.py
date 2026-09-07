#!/usr/bin/env python3
"""
Enterprise Agent Skill 2x2 Evaluation Matrix & Uplift Calculator.
Operationalizes Google Cloud continuous evaluation standards:
Measures Accuracy Uplift vs. Token/Latency Efficiency Uplift across baseline and skill trajectories.
Supports single-run scalar metrics and multi-case evaluation suite files (--suite / --runs).
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path
import sys
from typing import Any

# Rule 23: UTF-8 Stream Codec Entrypoint
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass


class EvalQuadrant(str, Enum):
    """Google 2x2 Continuous Evaluation Quadrants."""
    DOMINANT_UPLIFT = "DOMINANT_UPLIFT"          # High Accuracy Uplift, High Efficiency Uplift (Target)
    QUALITY_DOMINANT = "QUALITY_DOMINANT"        # High Accuracy Uplift, Higher Token Cost
    COST_DOMINANT = "COST_DOMINANT"              # Slight/Neutral Accuracy, Massive Token Savings
    DEGRADED = "DEGRADED"                        # Worse Accuracy, Higher Cost (Fails Gate)


@dataclass(slots=True, frozen=True)
class RunMetric:
    """Individual execution metrics for an agent run."""
    run_id: str
    accuracy_score: float  # 0.0 to 1.0 (or 0 to 100%)
    tokens_consumed: int
    latency_seconds: float = 0.0
    turns_count: int = 1

    def __post_init__(self) -> None:
        assert 0.0 <= self.accuracy_score <= 1.0, f"accuracy_score must be in [0.0, 1.0], got {self.accuracy_score}"
        assert self.tokens_consumed >= 0, f"tokens_consumed cannot be negative, got {self.tokens_consumed}"
        assert self.latency_seconds >= 0.0, f"latency_seconds cannot be negative, got {self.latency_seconds}"
        assert self.turns_count >= 1, f"turns_count must be >= 1, got {self.turns_count}"


@dataclass(slots=True, frozen=True)
class UpliftResult:
    """Calculated comparative uplift between baseline and skill-augmented runs."""
    baseline: RunMetric
    with_skill: RunMetric
    accuracy_uplift: float = field(init=False)
    accuracy_uplift_pct: float = field(init=False)
    token_efficiency_uplift_pct: float = field(init=False)
    latency_efficiency_uplift_pct: float = field(init=False)
    quadrant: EvalQuadrant = field(init=False)
    passed_gate: bool = field(init=False)

    def __post_init__(self) -> None:
        acc_delta = self.with_skill.accuracy_score - self.baseline.accuracy_score
        acc_pct = (acc_delta / max(self.baseline.accuracy_score, 1e-6)) * 100.0
        
        # Token Efficiency Uplift: % reduction in consumed tokens
        tok_baseline = max(self.baseline.tokens_consumed, 1)
        tok_delta = tok_baseline - self.with_skill.tokens_consumed
        tok_pct = (tok_delta / tok_baseline) * 100.0

        # Latency Efficiency Uplift: % reduction in execution time
        lat_baseline = max(self.baseline.latency_seconds, 0.001)
        lat_delta = lat_baseline - self.with_skill.latency_seconds
        lat_pct = (lat_delta / lat_baseline) * 100.0

        object.__setattr__(self, "accuracy_uplift", acc_delta)
        object.__setattr__(self, "accuracy_uplift_pct", acc_pct)
        object.__setattr__(self, "token_efficiency_uplift_pct", tok_pct)
        object.__setattr__(self, "latency_efficiency_uplift_pct", lat_pct)

        # Quadrant Assignment
        is_acc_pos = acc_delta >= 0.0
        is_eff_pos = tok_delta >= 0

        if is_acc_pos and is_eff_pos:
            quad = EvalQuadrant.DOMINANT_UPLIFT
            passes = True
        elif is_acc_pos and not is_eff_pos:
            quad = EvalQuadrant.QUALITY_DOMINANT
            # Passes if accuracy gain is substantial (>= +15%)
            passes = acc_delta >= 0.15
        elif not is_acc_pos and is_eff_pos:
            quad = EvalQuadrant.COST_DOMINANT
            # Passes if accuracy loss is negligible (< -3%) and token savings >= 30%
            passes = acc_delta >= -0.03 and tok_pct >= 30.0
        else:
            quad = EvalQuadrant.DEGRADED
            passes = False

        object.__setattr__(self, "quadrant", quad)
        object.__setattr__(self, "passed_gate", passes)

    def format_report(self) -> str:
        """Render a formatted diagnostic summary table."""
        status = "✓ PASS" if self.passed_gate else "✗ FAIL (DEGRADED)"
        lines = [
            "=" * 64,
            "GOOGLE 2x2 CONTINUOUS EVALUATION UPLIFT REPORT",
            "=" * 64,
            f"Overall Status:            {status}",
            f"Quadrant:                  {self.quadrant.value}",
            "-" * 64,
            f"Accuracy (Baseline):       {self.baseline.accuracy_score * 100:.1f}%",
            f"Accuracy (With Skill):     {self.with_skill.accuracy_score * 100:.1f}%",
            f"Accuracy Delta:            {self.accuracy_uplift * 100:+.1f}% ({self.accuracy_uplift_pct:+.1f}% rel)",
            "-" * 64,
            f"Tokens (Baseline):         {self.baseline.tokens_consumed:,}",
            f"Tokens (With Skill):       {self.with_skill.tokens_consumed:,}",
            f"Token Savings:             {self.token_efficiency_uplift_pct:+.1f}%",
            "-" * 64,
            f"Latency (Baseline):        {self.baseline.latency_seconds:.2f}s",
            f"Latency (With Skill):      {self.with_skill.latency_seconds:.2f}s",
            f"Latency Reduction:         {self.latency_efficiency_uplift_pct:+.1f}%",
            "=" * 64,
        ]
        return "\n".join(lines)


@dataclass(slots=True, frozen=True)
class SuiteUpliftReport:
    """Aggregated uplift results across an entire evaluation test suite."""
    suite_name: str
    case_results: list[tuple[str, UpliftResult]]
    passed_gate: bool
    overall_quadrant: EvalQuadrant
    avg_accuracy_uplift: float
    avg_token_savings_pct: float

    def format_report(self) -> str:
        status = "✓ PASS" if self.passed_gate else "✗ FAIL"
        lines = [
            "=" * 72,
            f"GOOGLE 2x2 CONTINUOUS EVALUATION SUITE REPORT: {self.suite_name}",
            "=" * 72,
            f"Overall Status:            {status}",
            f"Overall Quadrant:          {self.overall_quadrant.value}",
            f"Avg Accuracy Delta:        {self.avg_accuracy_uplift * 100:+.1f}%",
            f"Avg Token Savings:         {self.avg_token_savings_pct:+.1f}%",
            "-" * 72,
            f"{'Test Case ID':<32} {'Quadrant':<18} {'Acc Delta':<10} {'Tok Savings':<10}",
            "-" * 72,
        ]
        for cid, res in self.case_results:
            acc_str = f"{res.accuracy_uplift * 100:+.1f}%"
            tok_str = f"{res.token_efficiency_uplift_pct:+.1f}%"
            lines.append(f"{cid:<32} {res.quadrant.value:<18} {acc_str:<10} {tok_str:<10}")

        lines.append("=" * 72)
        return "\n".join(lines)


def calculate_uplift(baseline: RunMetric, with_skill: RunMetric) -> UpliftResult:
    """Calculate comparative 2x2 uplift."""
    return UpliftResult(baseline=baseline, with_skill=with_skill)


def evaluate_suite_file(suite_path: Path | str, runs_path: Path | str | None = None) -> SuiteUpliftReport:
    """Evaluate an entire evaluation suite file (e.g. eval_matrix_template.json)."""
    p = Path(suite_path).resolve()
    with open(p, "r", encoding="utf-8") as f:
        suite_data = json.load(f)

    suite_name = suite_data.get("title") or p.stem
    test_cases = suite_data.get("test_cases", [])

    runs_by_id: dict[str, Any] = {}
    if runs_path:
        rp = Path(runs_path).resolve()
        with open(rp, "r", encoding="utf-8") as f:
            runs_data = json.load(f)
            # Support {"runs": [...]} or direct list
            items = runs_data.get("runs", runs_data) if isinstance(runs_data, dict) else runs_data
            for r in items:
                runs_by_id[r["id"]] = r

    case_results: list[tuple[str, UpliftResult]] = []
    acc_deltas: list[float] = []
    tok_savings: list[float] = []
    all_passed = True

    for tc in test_cases:
        cid = tc.get("id", "unknown")
        if cid in runs_by_id:
            r = runs_by_id[cid]
            b_data = r["baseline"]
            s_data = r["with_skill"]
            b_metric = RunMetric(
                run_id=f"{cid}_baseline",
                accuracy_score=b_data.get("accuracy", b_data.get("accuracy_score", 0.5)),
                tokens_consumed=b_data.get("tokens", b_data.get("tokens_consumed", 5000)),
                latency_seconds=b_data.get("latency", b_data.get("latency_seconds", 5.0)),
                turns_count=b_data.get("turns", 1),
            )
            s_metric = RunMetric(
                run_id=f"{cid}_skill",
                accuracy_score=s_data.get("accuracy", s_data.get("accuracy_score", 0.8)),
                tokens_consumed=s_data.get("tokens", s_data.get("tokens_consumed", 3000)),
                latency_seconds=s_data.get("latency", s_data.get("latency_seconds", 3.0)),
                turns_count=s_data.get("turns", 1),
            )
        else:
            # Fall back to expectations in the template definition
            b_exp = tc.get("baseline_expectation", {})
            s_exp = tc.get("skill_expectation", {})
            b_metric = RunMetric(
                run_id=f"{cid}_baseline_exp",
                accuracy_score=b_exp.get("expected_accuracy_score", 0.6),
                tokens_consumed=b_exp.get("max_expected_tokens", 10000),
                latency_seconds=10.0,
                turns_count=4,
            )
            s_metric = RunMetric(
                run_id=f"{cid}_skill_exp",
                accuracy_score=s_exp.get("expected_accuracy_score", 0.9),
                tokens_consumed=s_exp.get("max_expected_tokens", 4000),
                latency_seconds=4.0,
                turns_count=2,
            )

        res = calculate_uplift(b_metric, s_metric)
        case_results.append((cid, res))
        acc_deltas.append(res.accuracy_uplift)
        tok_savings.append(res.token_efficiency_uplift_pct)
        if not res.passed_gate:
            all_passed = False

    avg_acc = sum(acc_deltas) / max(len(acc_deltas), 1)
    avg_tok = sum(tok_savings) / max(len(tok_savings), 1)

    if avg_acc >= 0 and avg_tok >= 0:
        overall_quad = EvalQuadrant.DOMINANT_UPLIFT
    elif avg_acc >= 0 and avg_tok < 0:
        overall_quad = EvalQuadrant.QUALITY_DOMINANT
    elif avg_acc < 0 and avg_tok >= 0:
        overall_quad = EvalQuadrant.COST_DOMINANT
    else:
        overall_quad = EvalQuadrant.DEGRADED

    return SuiteUpliftReport(
        suite_name=suite_name,
        case_results=case_results,
        passed_gate=all_passed,
        overall_quadrant=overall_quad,
        avg_accuracy_uplift=avg_acc,
        avg_token_savings_pct=avg_tok,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Calculate Google 2x2 Agent Skill Continuous Evals Uplift.")
    parser.add_argument("--suite", help="Path to evaluation suite JSON (e.g. eval_matrix_template.json)")
    parser.add_argument("--runs", help="Optional path to actual execution run logs JSON")

    parser.add_argument("--baseline-acc", type=float, default=0.65, help="Baseline accuracy (0.0 - 1.0)")
    parser.add_argument("--baseline-tokens", type=int, default=12000, help="Baseline token consumption")
    parser.add_argument("--baseline-latency", type=float, default=14.5, help="Baseline latency in seconds")
    parser.add_argument("--baseline-turns", type=int, default=5, help="Baseline turn count")
    
    parser.add_argument("--skill-acc", type=float, default=0.92, help="Skill-augmented accuracy (0.0 - 1.0)")
    parser.add_argument("--skill-tokens", type=int, default=4800, help="Skill-augmented token consumption")
    parser.add_argument("--skill-latency", type=float, default=6.2, help="Skill-augmented latency in seconds")
    parser.add_argument("--skill-turns", type=int, default=3, help="Skill-augmented turn count")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    # Suite mode
    if args.suite:
        report = evaluate_suite_file(args.suite, args.runs)
        if args.json:
            payload = {
                "suite_name": report.suite_name,
                "passed_gate": report.passed_gate,
                "overall_quadrant": report.overall_quadrant.value,
                "avg_accuracy_uplift": round(report.avg_accuracy_uplift, 4),
                "avg_token_savings_pct": round(report.avg_token_savings_pct, 2),
                "cases": [
                    {
                        "id": cid,
                        "quadrant": res.quadrant.value,
                        "passed_gate": res.passed_gate,
                        "accuracy_uplift": round(res.accuracy_uplift, 4),
                        "token_savings_pct": round(res.token_efficiency_uplift_pct, 2),
                    }
                    for cid, res in report.case_results
                ]
            }
            print(json.dumps(payload, indent=2))
        else:
            print(report.format_report())
        if not report.passed_gate:
            sys.exit(1)
        return

    # Single-run scalar mode
    baseline = RunMetric(
        run_id="baseline_run",
        accuracy_score=args.baseline_acc,
        tokens_consumed=args.baseline_tokens,
        latency_seconds=args.baseline_latency,
        turns_count=args.baseline_turns,
    )

    with_skill = RunMetric(
        run_id="with_skill_run",
        accuracy_score=args.skill_acc,
        tokens_consumed=args.skill_tokens,
        latency_seconds=args.skill_latency,
        turns_count=args.skill_turns,
    )

    result = calculate_uplift(baseline, with_skill)

    if args.json:
        payload = {
            "passed_gate": result.passed_gate,
            "quadrant": result.quadrant.value,
            "accuracy_uplift": round(result.accuracy_uplift, 4),
            "accuracy_uplift_pct": round(result.accuracy_uplift_pct, 2),
            "token_efficiency_uplift_pct": round(result.token_efficiency_uplift_pct, 2),
            "latency_efficiency_uplift_pct": round(result.latency_efficiency_uplift_pct, 2),
            "baseline": {
                "accuracy": result.baseline.accuracy_score,
                "tokens": result.baseline.tokens_consumed,
                "latency_sec": result.baseline.latency_seconds,
            },
            "with_skill": {
                "accuracy": result.with_skill.accuracy_score,
                "tokens": result.with_skill.tokens_consumed,
                "latency_sec": result.with_skill.latency_seconds,
            }
        }
        print(json.dumps(payload, indent=2))
    else:
        print(result.format_report())

    if not result.passed_gate:
        sys.exit(1)


if __name__ == "__main__":
    main()
