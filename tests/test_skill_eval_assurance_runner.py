"""Contract tests for skill-eval-assurance-runner skill and SkillEvalAssuranceEngine (Rule 43)."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from harness.services.skill_eval_assurance import (
    SKILL_EVAL_ASSURANCE_SERVICE_KEY,
    ActionSequenceGrade,
    ConfidenceIntervalResult,
    PreflightBoundaryFinding,
    SealedEnvelopeCheck,
    SkillEvalAssuranceEngine,
    SkillEvalAssuranceProtocol,
    ToolConstraintGrade,
)


@pytest.mark.unit
class TestSkillEvalAssuranceModelsAndEngine:
    def test_frozen_slotted_immutability(self) -> None:
        ci = ConfidenceIntervalResult(0.8, 0.37, 0.96, 0.95, 5)
        grade = ActionSequenceGrade(True, "in_order_match", 1.0, 1.0, 1.0, ("a",), ("a",))
        tc = ToolConstraintGrade(True, 1.0)
        pf = PreflightBoundaryFinding("boundary.post_run", "unresolved", "post-run-grader", "s", "r")
        sc = SealedEnvelopeCheck(True, "abc", "abc", "digest_verified")

        with pytest.raises((AttributeError, TypeError)):
            ci.mean = 0.5  # type: ignore[misc]
        with pytest.raises((AttributeError, TypeError)):
            grade.passed = False  # type: ignore[misc]
        with pytest.raises((AttributeError, TypeError)):
            tc.score = 0.0  # type: ignore[misc]
        with pytest.raises((AttributeError, TypeError)):
            pf.state = "valid"  # type: ignore[misc]
        with pytest.raises((AttributeError, TypeError)):
            sc.valid = False  # type: ignore[misc]

    def test_small_n_statistics_and_hake_gain(self) -> None:
        engine = SkillEvalAssuranceEngine()

        # Small N (3/3): upper clamped at 1.0, lower strictly < 1.0
        ci = engine.compute_wilson_ci(3, 3)
        assert ci.mean == pytest.approx(1.0)
        assert 0.0 < ci.lower < 1.0
        assert ci.upper == pytest.approx(1.0)

        # Unbiased pass^k: C(3,2)/C(4,2) = 3/6 = 0.5 (unlike (3/4)^2 = 0.5625)
        assert engine.compute_pass_hat_k(3, 4, 2) == pytest.approx(0.5)
        assert engine.compute_pass_hat_k(1, 4, 2) == pytest.approx(0.0)

        # Hake normalized gain: (0.95 - 0.90) / (1.0 - 0.90) = 0.5
        assert engine.compute_hake_normalized_gain(0.90, 0.95) == pytest.approx(0.5)
        assert engine.compute_hake_normalized_gain(1.0, 1.0) == pytest.approx(0.0)

    def test_trajectory_and_tool_constraint_graders(self) -> None:
        engine = SkillEvalAssuranceEngine()

        exact = engine.grade_action_sequence(
            ("a", "b"), ("a", "b"), matching_mode="exact_match"
        )
        assert exact.passed is True
        assert exact.f1 == pytest.approx(1.0)

        in_order_fail = engine.grade_action_sequence(
            ("b", "a"), ("a", "b"), matching_mode="in_order_match"
        )
        assert in_order_fail.passed is False

        any_order = engine.grade_action_sequence(
            ("b", "a"), ("a", "b"), matching_mode="any_order_match"
        )
        assert any_order.passed is True

        tc_fail = engine.grade_tool_constraints(
            ("read_file", "shell_exec"),
            expect_tools=("read_file",),
            reject_tools=("shell_.*",),
        )
        assert tc_fail.passed is False
        assert any("rejected_tool:shell_exec" in v for v in tc_fail.violations)

    def test_preflight_boundary_honesty_and_sealed_envelopes(self) -> None:
        engine = SkillEvalAssuranceEngine()
        findings = engine.audit_preflight_boundary(
            requested_tools=("read_file",), has_post_run_boundary_grader=True
        )
        assert len(findings) == 2
        assert all(f.state == "unresolved" for f in findings)

        envelope = {"kind": "waza.release-policy", "accepted": True, "score": 0.9}
        digest = engine.seal_json_envelope(envelope)
        assert engine.verify_sealed_envelope({**envelope, "digest": digest}).valid is True
        assert (
            engine.verify_sealed_envelope({**envelope, "score": 0.1, "digest": digest}).valid
            is False
        )

        assert isinstance(engine, SkillEvalAssuranceProtocol)
        assert SKILL_EVAL_ASSURANCE_SERVICE_KEY.name == "service.skill_eval_assurance_runner"

    def test_cli_subcommands(self) -> None:
        script = (
            Path(__file__).resolve().parent.parent
            / ".agents"
            / "skills"
            / "skill-eval-assurance-runner"
            / "scripts"
            / "skill_eval_assurance_engine.py"
        )
        spec = importlib.util.spec_from_file_location("skill_eval_assurance_cli", script)
        assert spec is not None and spec.loader is not None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        assert mod.main(["wilson", "--successes", "4", "--trials", "5"]) == 0
        assert mod.main(["pass-hat-k", "--successes", "3", "--trials", "4", "--k", "2"]) == 0
        assert mod.main(["hake-gain", "--pre", "0.9", "--post", "0.95"]) == 0
        assert mod.main(["grade-actions", "--actual", "a,b", "--expected", "a,b", "--mode", "exact_match"]) == 0
        assert mod.main(["grade-tools", "--observed", "read_file", "--expect", "read_file"]) == 0
        assert mod.main(["preflight-boundary", "--requested-tools", "read_file", "--post-run-grader"]) == 0
        assert mod.main(["seal-check", "--payload-json", json.dumps({"ok": True}), "--seal"]) == 0

    def test_skill_package_validation(self) -> None:
        from harness.creator.skills import SkillValidator

        skill_dir = (
            Path(__file__).resolve().parent.parent
            / ".agents"
            / "skills"
            / "skill-eval-assurance-runner"
        )
        report = SkillValidator().validate(skill_dir)
        assert report.valid, f"Skill validation failed: {[c.message for c in report.checks if not c.passed]}"
