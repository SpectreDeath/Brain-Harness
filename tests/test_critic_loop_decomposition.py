"""Contract verification test suite for Critic Loop Decomposition (Cycle 47).

Verifies:
1. Subpackage structure and strict line count bounds (Rule 11: all submodules <= 200 lines).
2. Slotted & frozen dataclass contracts on domain models (Rule 12 & Rule 43).
3. Typed service key CRITIC_EVALUATION_SERVICE_KEY (Rule 2).
4. Module singleton plugin export (Rule 45).
5. 100% backward-compatible facade re-exports across critic_loop.
6. Rubric scoring, command safety screening, and AST static analysis.
7. Dialectical multi-agent debate and arbiter verdict synthesis.
"""

from __future__ import annotations

import sys
from pathlib import Path
import pytest

from harness.kernel.context import ServiceContext, ServiceKey
from plugins.agent_orchestration.critic_loop.main import (
    CRITIC_EVALUATION_SERVICE_KEY,
    CRITIC_LOOP_KEY,
    CommandSafetyReport,
    CriticEvaluationService,
    CriticEvaluationServiceImpl,
    CriticLoopPlugin,
    CriticLoopService,
    DebateRound,
    RubricCriterionScore,
    RubricScoreReport,
    _DANGEROUS_PATTERNS,
    check_command_safety,
    conduct_dialectical_debate,
    critic_check_safety,
    critic_evaluate_code,
    critic_review_plan,
    evaluate,
    evaluate_code_ast,
    evaluate_rubric,
    plugin,
    review_plan_feasibility,
    run_critic_loop,
    synthesize_debate_verdict,
)

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


class TestCriticLoopDecompositionArchitecture:
    """Architectural and structural invariants for critic_loop subpackage."""

    def test_submodule_structure_and_line_limits(self) -> None:
        """Rule 11: All decomposed submodules must strictly remain <= 200 lines."""
        pkg_dir = (
            Path(__file__).parent.parent
            / "plugins"
            / "agent_orchestration"
            / "critic_loop"
        )
        assert pkg_dir.is_dir(), f"Expected directory at {pkg_dir}"

        # Check main.py
        main_py = pkg_dir / "main.py"
        assert main_py.is_file()
        main_lines = len(main_py.read_text(encoding="utf-8").splitlines())
        assert main_lines <= 200, f"main.py has {main_lines} lines (> 200)"

        engine_dir = pkg_dir / "engine"
        assert engine_dir.is_dir()

        expected_engine_modules = {
            "__init__.py",
            "models.py",
            "rubric.py",
            "safety.py",
            "code_ast.py",
            "plan.py",
            "debate.py",
            "refinement.py",
            "service.py",
        }

        found_modules = {p.name for p in engine_dir.glob("*.py")}
        assert expected_engine_modules.issubset(found_modules)

        for mod_name in expected_engine_modules:
            mod_path = engine_dir / mod_name
            lines = len(mod_path.read_text(encoding="utf-8").splitlines())
            assert lines <= 200, f"Module {mod_name} has {lines} lines, exceeding Rule 11 limit (200)"

    def test_slotted_frozen_dataclass_models(self) -> None:
        """Rule 12 & Rule 43: All domain models must be slotted and frozen."""
        crit = RubricCriterionScore("typing", 1.0, "Type annotations verified")
        assert hasattr(crit, "__slots__")
        assert not hasattr(crit, "__dict__")

        with pytest.raises((AttributeError, TypeError)):
            crit.score = 0.5

        rep = CommandSafetyReport("rm -rf /", False, "critical", 1, ["root deletion"])
        assert hasattr(rep, "__slots__")
        assert not hasattr(rep, "__dict__")

        rnd = DebateRound(1, "Pro claim", "Con claim")
        assert hasattr(rnd, "__slots__")
        assert not hasattr(rnd, "__dict__")

    def test_typed_service_key_and_plugin_singleton(self) -> None:
        """Rule 2 & Rule 45: Typed service key and plugin singleton."""
        assert isinstance(CRITIC_EVALUATION_SERVICE_KEY, ServiceKey)
        assert CRITIC_EVALUATION_SERVICE_KEY.name == "service.critic_evaluation"
        assert CRITIC_LOOP_KEY is CRITIC_EVALUATION_SERVICE_KEY

        assert isinstance(plugin, CriticLoopPlugin)
        assert CRITIC_EVALUATION_SERVICE_KEY in plugin.provides

    @pytest.mark.asyncio
    async def test_ioc_lifecycle_and_service_resolution(self) -> None:
        """Verify plugin registration and resolution via IoC container."""
        ctx = ServiceContext()
        p = CriticLoopPlugin()
        await p.on_load(ctx)

        assert ctx.has(CRITIC_EVALUATION_SERVICE_KEY)
        svc = ctx.require(CRITIC_EVALUATION_SERVICE_KEY)
        assert isinstance(svc, CriticEvaluationService)

        # Verify rubric evaluation via resolved service
        res = svc.evaluate_rubric("def foo() -> int:\n    return 42", ["typing", "clean style"])
        assert res["score"] > 0.7
        assert res["passed"]

    def test_safety_check_and_ast_evaluation(self) -> None:
        """Verify command safety and AST code evaluation."""
        safe_res = critic_check_safety("git status")
        assert safe_res["is_safe"] is True

        unsafe_res = critic_check_safety("rm -rf /")
        assert unsafe_res["is_safe"] is False
        assert unsafe_res["risk_level"] == "critical"

        ast_res = critic_evaluate_code("def add(a: int, b: int) -> int:\n    return a + b\n")
        assert ast_res["valid"] is True
        assert ast_res["metrics"]["functions_count"] == 1

    def test_dialectical_debate_and_arbiter_synthesis(self) -> None:
        """Verify dialectical debate rounds and arbiter recommendation synthesis."""
        debate = conduct_dialectical_debate(
            "Use Slotted Dataclasses",
            ["Reduces memory footprint", "Prevents arbitrary attribute assignment"],
            ["Requires explicit __slots__ declaration"],
        )
        assert debate["total_rounds"] == 2

        verdict = synthesize_debate_verdict(debate)
        assert verdict["recommendation"] == "PROCEED_WITH_MITIGATIONS"
        assert "Arbiter Verdict" in verdict["verdict_markdown"]
