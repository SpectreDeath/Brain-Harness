"""Tests for deepened architecture of agent-skills-architect."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import pytest


def _load_script_module(name: str, rel_path: str) -> Any:
    path = Path(rel_path).resolve()
    assert path.is_file(), f"Script not found: {path}"
    spec = importlib.util.spec_from_file_location(name, str(path))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.mark.unit
def test_skill_ci_linter_self_and_defects(tmp_path: Path) -> None:
    """Verify SkillCiLinter passes 100% on self and catches intentional defects."""
    linter_mod = _load_script_module(
        "skill_ci_linter",
        ".agents/skills/agent-skills-architect/scripts/skill_ci_linter.py"
    )
    SkillCiLinter = linter_mod.SkillCiLinter

    # 1. Self-lint test
    self_path = Path(".agents/skills/agent-skills-architect").resolve()
    report = SkillCiLinter.lint(self_path)
    assert report.valid is True, f"Linter failed on self: {report.errors}"
    assert len(report.errors) == 0
    assert len(report.warnings) == 0
    assert any(c.name == "Line Count Budget" and c.passed for c in report.checks)
    assert any(c.name == "Link Verification" and c.passed for c in report.checks)

    # 2. Defect test: missing SKILL.md
    bad_dir = tmp_path / "bad-skill"
    bad_dir.mkdir()
    bad_report = SkillCiLinter.lint(bad_dir)
    assert bad_report.valid is False
    assert any("Missing mandatory SKILL.md" in err for err in bad_report.errors)

    # 3. Defect test: bad directory name (not kebab-case)
    camel_dir = tmp_path / "camelCaseSkill"
    camel_dir.mkdir()
    (camel_dir / "SKILL.md").write_text("---\nname: camel\ndescription: test\n---\n", encoding="utf-8")
    camel_report = SkillCiLinter.lint(camel_dir)
    assert camel_report.valid is False
    assert any("Directory Naming" in c.name and not c.passed for c in camel_report.checks)


@pytest.mark.unit
def test_eval_suite_runner_and_runs_ingestion(tmp_path: Path) -> None:
    """Verify evaluate_suite_file loads templates and handles custom run metrics."""
    calc_mod = _load_script_module(
        "eval_uplift_calculator_deepened",
        ".agents/skills/agent-skills-architect/scripts/eval_uplift_calculator.py"
    )
    evaluate_suite_file = calc_mod.evaluate_suite_file
    EvalQuadrant = calc_mod.EvalQuadrant

    # 1. Ingest template definition directly
    template_path = Path(".agents/skills/agent-skills-architect/resources/eval_matrix_template.json").resolve()
    report = evaluate_suite_file(template_path)
    assert report.passed_gate is True
    assert report.overall_quadrant == EvalQuadrant.DOMINANT_UPLIFT
    assert len(report.case_results) == 2
    assert report.avg_accuracy_uplift > 0.10
    assert report.avg_token_savings_pct > 30.0

    # 2. Ingest custom execution run telemetry
    runs_file = tmp_path / "test_runs.json"
    runs_payload = {
        "runs": [
            {
                "id": "eval_001_progressive_disclosure",
                "baseline": {"accuracy": 0.50, "tokens": 10000, "latency": 12.0},
                "with_skill": {"accuracy": 0.85, "tokens": 3000, "latency": 4.0}
            },
            {
                "id": "eval_002_runtime_security_middleware",
                "baseline": {"accuracy": 0.70, "tokens": 8000, "latency": 9.0},
                "with_skill": {"accuracy": 0.95, "tokens": 4000, "latency": 5.0}
            }
        ]
    }
    runs_file.write_text(json.dumps(runs_payload), encoding="utf-8")

    custom_report = evaluate_suite_file(template_path, runs_file)
    assert custom_report.passed_gate is True
    assert custom_report.overall_quadrant == EvalQuadrant.DOMINANT_UPLIFT
    case_map = dict(custom_report.case_results)
    assert "eval_001_progressive_disclosure" in case_map
    res_001 = case_map["eval_001_progressive_disclosure"]
    assert pytest.approx(res_001.accuracy_uplift, 0.01) == 0.35
    assert pytest.approx(res_001.token_efficiency_uplift_pct, 0.1) == 70.0


@pytest.mark.unit
def test_runtime_middleware_guard_policies() -> None:
    """Verify ToolApprovalMiddleware enforces read-only auto-approval and script gating."""
    guard_mod = _load_script_module(
        "runtime_middleware_guard",
        ".agents/skills/agent-skills-architect/scripts/runtime_middleware_guard.py"
    )
    ToolApprovalMiddleware = guard_mod.ToolApprovalMiddleware
    ToolCall = guard_mod.ToolCall
    ToolRiskLevel = guard_mod.ToolRiskLevel
    RuntimeSecurityContext = guard_mod.RuntimeSecurityContext

    middleware = ToolApprovalMiddleware(sandbox_enabled=True)
    ctx = RuntimeSecurityContext(
        services={"db_conn": "mock_postgres_pool"},
        function_invocation_kwargs={"tenant_id": "cust_123"},
        auto_approve_read_only=True,
        trusted_skills=("agent-skills-architect", "trusted-skill"),
    )

    # 1. Read-only tool should be auto-approved
    call_read = ToolCall("load_skill", {"skill_name": "any-skill"}, ToolRiskLevel.READ_ONLY)
    dec_read = middleware.intercept(call_read, ctx)
    assert dec_read.approved is True
    assert dec_read.requires_user_prompt is False

    # 2. Mutating tool for untrusted skill should be gated (requires prompt)
    call_mutate = ToolCall("run_skill_script", {"skill_name": "untrusted-skill"}, ToolRiskLevel.MUTATING)
    dec_mutate = middleware.intercept(call_mutate, ctx)
    assert dec_mutate.approved is False
    assert dec_mutate.requires_user_prompt is True

    # 3. Mutating tool for trusted skill with sandbox should be approved in sandbox
    call_trusted = ToolCall("run_skill_script", {"skill_name": "trusted-skill"}, ToolRiskLevel.MUTATING)
    dec_trusted = middleware.intercept(call_trusted, ctx)
    assert dec_trusted.approved is True
    assert dec_trusted.sandboxed is True
    assert dec_trusted.requires_user_prompt is False

    # 4. Context injection forwards services and kwargs
    base_args = {"action": "fetch"}
    augmented = middleware.inject_runtime_context("load_skill", base_args, ctx)
    assert augmented["tenant_id"] == "cust_123"
    assert augmented["__services__"]["db_conn"] == "mock_postgres_pool"
