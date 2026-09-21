"""Lightweight CLI runner for self-evaluating pipeline skill.

Bifurcated thin wrapper delegating to slotted SelfEvaluatingPipelineEngine.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# UTF-8 streams (Rule 23)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

_scripts_dir = Path(__file__).resolve().parent
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))

from self_evaluating_pipeline_engine import (
    GoldenTestCase,
    HumanAnnotationRecord,
    SelfEvaluatingPipelineEngine,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Self-Evaluating AI Pipeline CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # layer1
    p_l1 = subparsers.add_parser("layer1", help="Run Layer 1 deterministic sanity checks")
    p_l1.add_argument("text", help="Raw model output text to evaluate")
    p_l1.add_argument("--schema", default=None, help="Expected schema: json, xml")
    p_l1.add_argument("--min-len", type=int, default=10, help="Minimum char length")
    p_l1.add_argument("--max-len", type=int, default=5000, help="Maximum char length")
    p_l1.add_argument("--whitelist", nargs="*", default=None, help="Authorized domain list")

    # judge
    p_j = subparsers.add_parser("judge", help="Run Layer 2 anchored semantic judge")
    p_j.add_argument("prompt", help="User input prompt")
    p_j.add_argument("response", help="Model response text")
    p_j.add_argument("--judges", type=int, default=3, help="Number of consensus judges")

    # kappa
    p_k = subparsers.add_parser("kappa", help="Calculate Layer 3 Cohen's Kappa agreement")
    p_k.add_argument("file", help="Path to JSON file containing paired annotations")

    # gate
    p_g = subparsers.add_parser("gate", help="Run Stage 5 paired t-test release gate")
    p_g.add_argument("--before", required=True, help="JSON list of pre-change scores")
    p_g.add_argument("--after", required=True, help="JSON list of post-change scores")
    p_g.add_argument("--alpha", type=float, default=0.05, help="Significance threshold")

    args = parser.parse_args()
    engine = SelfEvaluatingPipelineEngine()

    if args.command == "layer1":
        rep = engine.evaluate_layer1(
            args.text,
            expected_schema=args.schema,
            min_len=args.min_len,
            max_len=args.max_len,
            allowed_domains=args.whitelist,
        )
        print(json.dumps({
            "passed": rep.passed,
            "latency_ms": rep.total_latency_ms,
            "refusal_detected": rep.refusal_detected,
            "hallucinated_urls": rep.hallucinated_urls,
            "checks": [{"name": c.name, "passed": c.passed, "message": c.message} for c in rep.checks],
        }, indent=2))

    elif args.command == "judge":
        res = engine.evaluate_layer2_judge(args.prompt, args.response, num_judges=args.judges)
        print(json.dumps({
            "passed": res.passed,
            "median_score": res.median_score,
            "mean_score": res.mean_score,
            "scores": res.scores,
            "judges": [{"id": j.judge_id, "score": j.score, "reasoning": j.reasoning} for j in res.judge_results],
        }, indent=2))

    elif args.command == "kappa":
        data = json.loads(Path(args.file).read_text(encoding="utf-8"))
        ann_a = [HumanAnnotationRecord(**item) for item in data.get("rater_a", [])]
        ann_b = [HumanAnnotationRecord(**item) for item in data.get("rater_b", [])]
        k_rep = engine.calculate_cohens_kappa(ann_a, ann_b)
        print(json.dumps({
            "cohens_kappa": k_rep.cohens_kappa,
            "observed_agreement": k_rep.observed_agreement,
            "expected_chance_agreement": k_rep.expected_chance_agreement,
            "is_acceptable": k_rep.is_acceptable,
            "interpretation": k_rep.interpretation,
            "paired_samples": k_rep.paired_samples_count,
        }, indent=2))

    elif args.command == "gate":
        sb = json.loads(Path(args.before).read_text(encoding="utf-8")) if Path(args.before).exists() else json.loads(args.before)
        sa = json.loads(Path(args.after).read_text(encoding="utf-8")) if Path(args.after).exists() else json.loads(args.after)
        gate = engine.evaluate_statistical_significance_gate(sb, sa, alpha=args.alpha)
        print(json.dumps({
            "decision": gate.decision,
            "p_value": gate.p_value,
            "t_statistic": gate.t_statistic,
            "mean_difference": gate.mean_difference,
            "is_significant": gate.is_significant,
            "is_improvement": gate.is_improvement,
            "justification": gate.justification,
        }, indent=2))


if __name__ == "__main__":
    main()
