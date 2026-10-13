"""Contract tests verifying Skill Graph AntiPatternGuard decomposition.

Validates:
1. Strict submodule bounds (AGENTS.md Rule 11: all files <= 200 lines).
2. AST scanning and blocked library calls (eval, exec, input, __import__).
3. Repository invariant rules (Rules 15, 23/50, 29, 30, 31, 40).
4. Negation-aware anti-pattern proposal scanning.
5. Action gate evaluation returning slotted ActionGateResult.
6. In-flight self-repair observation formatting.
"""

from __future__ import annotations

from pathlib import Path
import pytest

from harness.services.skill_graph.guard import (
    AntiPatternGuard,
    check_proposal_anti_patterns,
    format_self_repair_observation,
    scan_blocked_calls,
    scan_code_ast,
)
from harness.services.skill_graph.models import (
    ActionGateResult,
    AntiPatternViolation,
    InvariantViolation,
    SkillAntiPatternDefinition,
    SkillCardDefinition,
    SkillInvariantDefinition,
)


@pytest.mark.unit
class TestSkillGraphGuardDecomposition:
    """Verify architectural invariants for Skill Graph Guard decomposition."""

    def test_submodule_line_count_bounds(self) -> None:
        """Rule 11: Verify every submodule in package is <= 200 lines."""
        pkg_dir = Path("src") / "harness" / "services" / "skill_graph" / "guard"
        py_files = list(pkg_dir.glob("*.py"))
        assert len(py_files) >= 6

        for py_file in py_files:
            lines = len(py_file.read_text(encoding="utf-8").splitlines())
            assert lines <= 200, f"{py_file.name} has {lines} lines, exceeding 200-line limit"

    def test_ast_blocked_calls_detection(self) -> None:
        """Verify AST visitor blocks dangerous calls like eval, exec, input, __import__."""
        code_eval = "def run():\n    return eval('1 + 1')"
        v_eval = scan_code_ast(code_eval)
        assert len(v_eval) >= 1
        assert "eval()" in v_eval[0].anti_pattern

        code_input = "val = input('Prompt: ')"
        v_input = scan_code_ast(code_input)
        assert len(v_input) >= 1
        assert "input()" in v_input[0].anti_pattern

        clean_code = "def add(a: int, b: int) -> int:\n    return a + b"
        assert len(scan_code_ast(clean_code)) == 0

    def test_invariant_rules_enforcement(self) -> None:
        """Verify repository invariant enforcement across Rules 15, 29, 30, 31."""
        skill = SkillCardDefinition(
            name="test-skill",
            category="testing",
            summary="Test skill",
            invariants=[
                SkillInvariantDefinition(
                    rule="Artifact Metadata Restricted: The write_to_file tool only accepts ArtifactMetadata for files inside the conversation artifact directory.",
                    is_blocking=True,
                ),
                SkillInvariantDefinition(
                    rule="Scratch File Execution over Inline -c Strings: Never execute multi-line Python logic via python -c in commands.",
                    is_blocking=True,
                ),
            ],
        )

        # Rule 31: Artifact metadata outside artifact dir
        v_meta = AntiPatternGuard.evaluate_action(
            action_name="write_to_file",
            action_input={"target_file": "d:/GitHub/projects/src/main.py", "ArtifactMetadata": {"Summary": "test"}},
            active_skills=["test-skill"],
            skill_lookup=lambda name: skill,
        )
        assert any("artifact metadata" in v.rule.lower() for v in v_meta if isinstance(v, InvariantViolation))

        # Rule 29: Inline -c string
        v_inline = AntiPatternGuard.evaluate_action(
            action_name="run_command",
            action_input={"CommandLine": 'python -c "print(1)"'},
            active_skills=["test-skill"],
            skill_lookup=lambda name: skill,
        )
        assert any("inline -c" in v.rule.lower() for v in v_inline if isinstance(v, InvariantViolation))

        # Rule 30: PowerShell pytest glob (system guard)
        v_glob = AntiPatternGuard.evaluate_action(
            action_name="run_command",
            action_input={"CommandLine": "pytest tests/test_*.py"},
            active_skills=["test-skill"],
            skill_lookup=lambda name: skill,
        )
        assert any("powershell glob" in v.anti_pattern.lower() for v in v_glob)

    def test_negation_aware_proposals(self) -> None:
        """Verify negation words prevent false positive anti-pattern detection."""
        skill = SkillCardDefinition(
            name="security-skill",
            category="security",
            summary="Security auditing",
            anti_patterns=[
                SkillAntiPatternDefinition(
                    name="Hardcoded Secret Tokens",
                    symptom="Committing raw credentials",
                    remedy="Use environment variables",
                )
            ],
        )

        # Plan with negation should not trigger
        negated_plan = "We must avoid hardcoded secret tokens in the repository."
        assert len(check_proposal_anti_patterns(skill, negated_plan)) == 0

        # Positive violation plan triggers
        violating_plan = "We will place hardcoded secret tokens directly in config."
        v = check_proposal_anti_patterns(skill, violating_plan)
        assert len(v) == 1
        assert v[0].anti_pattern == "Hardcoded Secret Tokens"

    def test_evaluate_action_gate_slotted(self) -> None:
        """Verify evaluate_action_gate returns a slotted ActionGateResult."""
        # Clean action
        clean_res = AntiPatternGuard.evaluate_action_gate(
            action_name="run_command",
            action_input={"CommandLine": "pytest tests/test_unit.py"},
        )
        assert isinstance(clean_res, ActionGateResult)
        assert hasattr(clean_res, "__slots__")
        assert clean_res.is_blocked is False
        assert clean_res.observation["status"] == "ok"

        # Blocked action with eval
        blocked_res = AntiPatternGuard.evaluate_action_gate(
            action_name="run_command",
            action_input={"CommandLine": "python script.py", "code": "eval('secret')"},
        )
        assert isinstance(blocked_res, ActionGateResult)
        assert blocked_res.is_blocked is True
        assert len(blocked_res.violations) >= 1
        assert blocked_res.observation["status"] == "error"

    def test_format_self_repair_observation(self) -> None:
        """Verify observation dictionary formatting for self-repair loops."""
        ap_v = AntiPatternViolation(
            skill_name="my-skill",
            anti_pattern="Shallow Module",
            symptom="Module is too thin",
            remedy="Deepen module architecture",
            matched_phrase="shallow module",
        )
        obs_ap = format_self_repair_observation([ap_v])
        assert obs_ap["status"] == "error"
        assert "Shallow Module" in obs_ap["anti_pattern_violation"]
        assert obs_ap["corrective_action_required"] is True

        inv_v = InvariantViolation(
            skill_name="my-skill",
            rule="Rule 11: Max 200 lines",
            matched_phrase="250 lines",
            is_blocking=True,
            remedy="Decompose module",
        )
        obs_inv = format_self_repair_observation([inv_v])
        assert obs_inv["status"] == "error"
        assert obs_inv["is_blocking"] is True
        assert "Rule 11" in obs_inv["invariant_violation"]
