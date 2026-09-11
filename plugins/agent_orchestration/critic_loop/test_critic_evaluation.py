"""Comprehensive tests for Critic & Safety Evaluation Gate Plugin."""

from pathlib import Path
import pytest
import sys

# Ensure Harness core is on path
_HARNESS_SRC = Path(__file__).resolve().parents[3] / "src"
if _HARNESS_SRC.exists() and str(_HARNESS_SRC) not in sys.path:
    sys.path.insert(0, str(_HARNESS_SRC))

from harness.kernel.context import ServiceContext
from plugins.agent_orchestration.critic_loop.main import (
    CriticEvaluationService,
    CriticEvaluationServiceImpl,
    CriticLoopPlugin,
    CRITIC_EVALUATION_SERVICE_KEY,
    CRITIC_LOOP_KEY,
    evaluate_rubric,
    run_critic_loop,
    critic_check_safety,
    critic_evaluate_code,
    critic_review_plan,
    conduct_dialectical_debate,
    synthesize_debate_verdict,
    plugin,
)


def test_rubric_evaluation() -> None:
    service = CriticEvaluationServiceImpl()

    code = (
        'def add(a: int, b: int) -> int:\n'
        '    """Add two integers."""\n'
        '    try:\n'
        '        return a + b\n'
        '    except Exception:\n'
        '        return 0\n'
    )
    rubric = [
        "Include strict type annotations",
        "Provide clear docstrings",
        "Implement robust error handling",
    ]

    res = service.evaluate_rubric(code, rubric)
    assert res["overall_score"] >= 0.90
    assert res["passed"] is True
    assert len(res["breakdown"]) == 3


def test_command_safety_check() -> None:
    service = CriticEvaluationServiceImpl()

    # Dangerous commands
    res_danger1 = service.check_command_safety("rm -rf /")
    assert res_danger1["is_safe"] is False
    assert res_danger1["risk_level"] == "critical"
    assert len(res_danger1["violations"]) > 0

    res_danger2 = service.check_command_safety("git reset --hard HEAD~1")
    assert res_danger2["is_safe"] is False
    assert res_danger2["risk_level"] in ("critical", "high")

    # Safe command
    res_safe = service.check_command_safety("git status")
    assert res_safe["is_safe"] is True
    assert res_safe["risk_level"] == "low"
    assert len(res_safe["violations"]) == 0


def test_code_ast_evaluation() -> None:
    service = CriticEvaluationServiceImpl()

    # Good Python code
    good_code = (
        "def compute(x: int) -> int:\n"
        "    '''Compute square.'''\n"
        "    return x * x\n"
    )
    res_good = service.evaluate_code_ast(good_code, "python")
    assert res_good["valid"] is True
    assert res_good["metrics"]["functions_count"] == 1
    assert len(res_good["issues"]) == 0

    # Bad Python code with anti-patterns
    bad_code = (
        "def dangerous(x):\n"
        "    try:\n"
        "        return eval(x)\n"
        "    except:\n"
        "        pass\n"
    )
    res_bad = service.evaluate_code_ast(bad_code, "python")
    assert res_bad["valid"] is True
    assert any("eval()" in issue for issue in res_bad["issues"])
    assert any("Bare 'except:'" in issue for issue in res_bad["issues"])
    assert any("lacks a docstring" in issue for issue in res_bad["issues"])

    # JSON evaluation
    res_json_good = service.evaluate_code_ast('{"name": "test", "version": 1}', "json")
    assert res_json_good["valid"] is True

    res_json_bad = service.evaluate_code_ast('{name: invalid_json}', "json")
    assert res_json_bad["valid"] is False
    assert len(res_json_bad["issues"]) > 0


def test_plan_feasibility_review() -> None:
    service = CriticEvaluationServiceImpl()

    # Plan missing verification
    plan_unverified = ["Edit config file", "Restart daemon"]
    res1 = service.review_plan_feasibility("Update config", plan_unverified)
    assert res1["has_verification_step"] is False
    assert res1["score"] < 100
    assert any("verification" in r.lower() for r in res1["risks"])

    # Solid plan with verification
    plan_verified = [
        "Create backup snapshot",
        "Modify configuration setting",
        "Verify service status and health check",
    ]
    res2 = service.review_plan_feasibility("Safe update", plan_verified)
    assert res2["has_verification_step"] is True
    assert res2["feasible"] is True
    assert res2["score"] >= 80


def test_dialectical_debate_and_verdict() -> None:
    service = CriticEvaluationServiceImpl()

    topic = "Migrate monolith to microservices"
    pros = [
        "Allows independent team deployments",
        "Isolates failure domains",
    ]
    cons = [
        "Greatly increases distributed tracing and operational complexity",
        "High networking latency and transaction overhead",
        "Multiplies deployment infrastructure costs",
    ]

    debate = service.conduct_dialectical_debate(topic, pros, cons)
    assert debate["total_rounds"] == 3
    assert debate["pro_points_count"] == 2
    assert debate["con_points_count"] == 3

    verdict = service.synthesize_debate_verdict(debate)
    assert verdict["status"] == "ok"
    assert "Arbiter Verdict" in verdict["verdict_markdown"]
    assert verdict["recommendation"] in ("PROCEED_WITH_MITIGATIONS", "REJECT_OR_RETHINK")


@pytest.mark.asyncio
async def test_refinement_loop_convergence() -> None:
    service = CriticEvaluationServiceImpl()

    draft = "def greet(name: str) -> str:\n    '''Greet someone.'''\n    try:\n        return f'Hello {name}'\n    except Exception:\n        return ''\n"
    res = await service.refine(
        task="Write a greetings function",
        draft=draft,
        threshold=0.80,
    )
    assert res["converged"] is True
    assert res["final_score"] >= 0.80


@pytest.mark.asyncio
async def test_critic_plugin_lifecycle_and_service_resolution() -> None:
    context = ServiceContext()
    p = CriticLoopPlugin()

    await p.enable(context)

    # Resolution via primary key
    resolved = context.require(CRITIC_EVALUATION_SERVICE_KEY)
    assert resolved is not None
    assert isinstance(resolved, CriticEvaluationService)

    # Resolution via alias key
    alias_resolved = context.require(CRITIC_LOOP_KEY)
    assert alias_resolved is resolved

    # Verify all protocol methods exist
    assert hasattr(resolved, "evaluate_rubric")
    assert hasattr(resolved, "check_command_safety")
    assert hasattr(resolved, "evaluate_code_ast")
    assert hasattr(resolved, "review_plan_feasibility")
    assert hasattr(resolved, "conduct_dialectical_debate")
    assert hasattr(resolved, "synthesize_debate_verdict")
    assert hasattr(resolved, "refine")

    await p.disable(context)
