"""Thin CLI wrapper delegating to harness.services.skill_eval_assurance (Rule 49, Rule 57)."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

_REPO_ROOT = Path(__file__).resolve().parents[4]
_HARNESS_SRC = _REPO_ROOT / "src"
if _HARNESS_SRC.exists() and str(_HARNESS_SRC) not in sys.path:
    sys.path.insert(0, str(_HARNESS_SRC))

from harness.services.skill_eval_assurance import SkillEvalAssuranceEngine  # noqa: E402


def _split_csv(raw: str) -> tuple[str, ...]:
    return tuple(s.strip() for s in raw.split(",") if s.strip())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Skill Eval Assurance Runner CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    w_p = sub.add_parser("wilson", help="Compute Wilson score confidence interval")
    w_p.add_argument("--successes", type=int, required=True)
    w_p.add_argument("--trials", type=int, required=True)
    w_p.add_argument("--confidence", type=float, default=0.95)

    pk_p = sub.add_parser("pass-hat-k", help="Compute unbiased tau-bench pass^k")
    pk_p.add_argument("--successes", type=int, required=True)
    pk_p.add_argument("--trials", type=int, required=True)
    pk_p.add_argument("--k", type=int, required=True)

    hg_p = sub.add_parser("hake-gain", help="Compute Hake normalized gain")
    hg_p.add_argument("--pre", type=float, required=True)
    hg_p.add_argument("--post", type=float, required=True)

    as_p = sub.add_parser("grade-actions", help="Grade tool action sequence")
    as_p.add_argument("--actual", required=True, help="Comma-separated actual tools")
    as_p.add_argument("--expected", required=True, help="Comma-separated expected tools")
    as_p.add_argument(
        "--mode",
        default="in_order_match",
        choices=("exact_match", "in_order_match", "any_order_match"),
    )

    tc_p = sub.add_parser("grade-tools", help="Evaluate tool usage constraints")
    tc_p.add_argument("--observed", required=True, help="Comma-separated observed tools")
    tc_p.add_argument("--expect", default="")
    tc_p.add_argument("--reject", default="")
    tc_p.add_argument("--allow-only", action="store_true")

    pb_p = sub.add_parser("preflight-boundary", help="Audit static boundary honesty")
    pb_p.add_argument("--requested-tools", default=None)
    pb_p.add_argument("--post-run-grader", action="store_true")

    sc_p = sub.add_parser("seal-check", help="Seal or verify a canonical JSON envelope")
    sc_p.add_argument("--payload-json", required=True)
    sc_p.add_argument("--seal", action="store_true", help="Return sealed digest instead of verifying")

    args = parser.parse_args(argv)
    engine = SkillEvalAssuranceEngine()

    if args.command == "wilson":
        res = engine.compute_wilson_ci(
            args.successes, args.trials, confidence_level=args.confidence
        )
        print(json.dumps(asdict(res), indent=2))
        return 0

    if args.command == "pass-hat-k":
        val = engine.compute_pass_hat_k(args.successes, args.trials, args.k)
        print(json.dumps({"pass_hat_k": val}, indent=2))
        return 0

    if args.command == "hake-gain":
        val = engine.compute_hake_normalized_gain(args.pre, args.post)
        print(json.dumps({"normalized_gain": val}, indent=2))
        return 0

    if args.command == "grade-actions":
        res = engine.grade_action_sequence(
            _split_csv(args.actual), _split_csv(args.expected), matching_mode=args.mode
        )
        print(json.dumps(asdict(res), indent=2))
        return 0

    if args.command == "grade-tools":
        res = engine.grade_tool_constraints(
            _split_csv(args.observed),
            expect_tools=_split_csv(args.expect),
            reject_tools=_split_csv(args.reject),
            allow_only=args.allow_only,
        )
        print(json.dumps(asdict(res), indent=2))
        return 0

    if args.command == "preflight-boundary":
        req_tools = (
            _split_csv(args.requested_tools)
            if args.requested_tools is not None
            else None
        )
        findings = engine.audit_preflight_boundary(
            requested_tools=req_tools,
            has_post_run_boundary_grader=args.post_run_grader,
        )
        print(json.dumps([asdict(f) for f in findings], indent=2))
        return 0

    if args.command == "seal-check":
        payload = json.loads(args.payload_json)
        if args.seal:
            digest = engine.seal_json_envelope(payload)
            print(json.dumps({"digest": digest}, indent=2))
            return 0
        check = engine.verify_sealed_envelope(payload)
        print(json.dumps(asdict(check), indent=2))
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
