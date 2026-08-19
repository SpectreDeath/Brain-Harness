"""Tests for evaluator_critic plugin."""

from __future__ import annotations

import pytest

from plugins.evaluator_critic.main import (
    critic_check_safety,
    critic_evaluate_code,
    critic_review_plan,
)


@pytest.mark.unit
class TestEvaluatorCriticPlugin:
    def test_critic_check_safety_clean(self) -> None:
        res = critic_check_safety("pytest tests/test_engine.py")
        assert res["status"] == "ok"
        assert res["is_safe"] is True
        assert res["risk_level"] == "low"
        assert len(res["violations"]) == 0

    def test_critic_check_safety_destructive(self) -> None:
        res1 = critic_check_safety("rm -rf /")
        assert res1["is_safe"] is False
        assert res1["risk_level"] == "critical"

        res2 = critic_check_safety("git reset --hard HEAD~1")
        assert res2["is_safe"] is False

        res3 = critic_check_safety("git push origin main --force")
        assert res3["is_safe"] is False

    def test_critic_evaluate_python_code(self) -> None:
        valid_code = """
def add(a: int, b: int) -> int:
    \"\"\"Add two numbers.\"\"\"
    return a + b
"""
        res = critic_evaluate_code(valid_code, "python")
        assert res["valid"] is True
        assert res["score"] == 100
        assert len(res["functions"]) == 1
        assert res["functions"][0]["has_docstring"] is True
        assert res["functions"][0]["has_return_type"] is True

        # Incomplete code with missing annotations and docstrings
        untyped_code = "def bad_func(x): return x * 2"
        res_untyped = critic_evaluate_code(untyped_code, "python")
        assert res_untyped["valid"] is True
        assert res_untyped["score"] < 100
        assert len(res_untyped["issues"]) >= 2

        # Syntax error
        syntax_err_code = "def oops(: return"
        res_err = critic_evaluate_code(syntax_err_code, "python")
        assert res_err["valid"] is False
        assert res_err["score"] == 0

    def test_critic_evaluate_json(self) -> None:
        res_ok = critic_evaluate_code('{"key": "value"}', "json")
        assert res_ok["valid"] is True
        assert res_ok["score"] == 100

        res_bad = critic_evaluate_code('{bad_json: 123}', "json")
        assert res_bad["valid"] is False
        assert res_bad["score"] == 0

    def test_critic_review_plan(self) -> None:
        # Solid plan with verification
        good_steps = [
            "Scaffold plugin directory",
            "Write main logic in main.py",
            "Run unit tests to verify correctness",
        ]
        res_good = critic_review_plan("Build plugin", good_steps)
        assert res_good["feasible"] is True
        assert res_good["has_verification_step"] is True
        assert res_good["score"] == 100

        # Plan missing verification and containing destructive actions
        risky_steps = [
            "Drop old database table",
            "Recreate schema directly",
        ]
        res_risky = critic_review_plan("Migrate schema", risky_steps)
        assert res_risky["has_verification_step"] is False
        assert res_risky["score"] < 70
        assert len(res_risky["risks"]) >= 2
