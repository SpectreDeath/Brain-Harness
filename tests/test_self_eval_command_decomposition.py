"""Contract verification tests for Cycle 52: Self-Evaluation Command Decomposition.

Verifies:
- Direct imports from decomposed submodules and subpackage facade re-exports
- Group consolidation: eval_group has exactly 7 registered subcommands (Rule 6)
- Engine adapter conforms to SelfEvaluatingPipelineService protocol
- Service resolver fallback and IoC resolution
- Headless Click execution via CliRunner (Rule 10)
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from harness.commands.self_eval import (
    SelfEvaluatingPipelineEngineAdapter,
    brief_cmd,
    drift_cmd,
    eval_group,
    gate_cmd,
    get_self_eval_service,
    judge_cmd,
    kappa_cmd,
    layer1_cmd,
    regression_cmd,
)
from harness.commands.self_eval.agreement import (
    drift_cmd as direct_drift,
    kappa_cmd as direct_kappa,
)
from harness.commands.self_eval.brief import brief_cmd as direct_brief
from harness.commands.self_eval.brief_adapter import generate_visual_brief_via_engine
from harness.commands.self_eval.engine_adapter import (
    SelfEvaluatingPipelineEngineAdapter as DirectAdapter,
)
from harness.commands.self_eval.group import eval_group as direct_group
from harness.commands.self_eval.judge import judge_cmd as direct_judge
from harness.commands.self_eval.layer1 import layer1_cmd as direct_layer1
from harness.commands.self_eval.regression import (
    gate_cmd as direct_gate,
    regression_cmd as direct_regression,
)
from harness.commands.self_eval.resolver import (
    get_self_eval_service as direct_resolver,
)
from harness.kernel.context import ServiceContext
from harness.services.self_evaluating_pipeline import (
    SELF_EVALUATING_PIPELINE_SERVICE_KEY,
    Layer1ReportData,
    SelfEvaluatingPipelineService,
)


@pytest.mark.unit
def test_self_eval_command_exports_and_imports() -> None:
    """Verify package facade re-exports match decomposed module definitions."""
    assert direct_group is eval_group
    assert direct_resolver is get_self_eval_service
    assert DirectAdapter is SelfEvaluatingPipelineEngineAdapter
    assert direct_layer1 is layer1_cmd
    assert direct_judge is judge_cmd
    assert direct_kappa is kappa_cmd
    assert direct_drift is drift_cmd
    assert direct_regression is regression_cmd
    assert direct_gate is gate_cmd
    assert direct_brief is brief_cmd
    assert callable(generate_visual_brief_via_engine)


@pytest.mark.unit
def test_self_eval_group_consolidation() -> None:
    """Verify eval_group consolidation per Rule 6 has all 7 subcommands."""
    subcommand_names = set(eval_group.commands.keys())
    expected_names = {"layer1", "judge", "kappa", "drift", "regression", "gate", "brief"}
    assert subcommand_names == expected_names, f"Missing or unexpected subcommands: {subcommand_names}"


@pytest.mark.unit
def test_self_eval_engine_adapter_conformance() -> None:
    """Verify SelfEvaluatingPipelineEngineAdapter implements SelfEvaluatingPipelineService protocol."""
    adapter = SelfEvaluatingPipelineEngineAdapter()
    assert isinstance(adapter, SelfEvaluatingPipelineService)

    # Verify layer 1 evaluation execution
    res = adapter.evaluate_layer1("Short test string with proper length")
    assert isinstance(res, Layer1ReportData)
    assert res.passed is True


@pytest.mark.unit
def test_self_eval_service_resolver() -> None:
    """Verify get_self_eval_service returns valid service from IoC and fallback."""
    # 1. Fallback resolution without context
    svc = get_self_eval_service(None)
    assert isinstance(svc, SelfEvaluatingPipelineService)

    # 2. Context with registered service
    ctx = ServiceContext()
    custom_adapter = SelfEvaluatingPipelineEngineAdapter()
    ctx.provide(SELF_EVALUATING_PIPELINE_SERVICE_KEY, custom_adapter)
    resolved = get_self_eval_service(ctx)
    assert resolved is custom_adapter


@pytest.mark.unit
def test_self_eval_cli_runner_subcommands() -> None:
    """Verify headless execution of CLI commands via CliRunner."""
    runner = CliRunner()

    # 1. Layer 1 command
    r1 = runner.invoke(eval_group, ["layer1", '{"status": "ok"}', "--schema", "json"])
    assert r1.exit_code == 0
    assert "Layer 1 Status: PASS" in r1.output

    # 2. Judge command
    response_text = "2 plus 2 equals 4. In standard integer arithmetic, adding two units to two units yields four."
    r2 = runner.invoke(eval_group, ["judge", "What is 2+2?", response_text])
    assert r2.exit_code == 0
    assert "Layer 2 Judge Status: PASS" in r2.output

    # 3. Gate command with inline JSON
    before = json.dumps([3.0, 3.1, 3.2, 3.0, 3.1, 3.2, 3.1, 3.0, 3.2, 3.1])
    after = json.dumps([4.5, 4.6, 4.5, 4.7, 4.6, 4.5, 4.6, 4.7, 4.5, 4.6])
    r3 = runner.invoke(eval_group, ["gate", "--before", before, "--after", after])
    assert r3.exit_code == 0
    assert "Deployment Gate Verdict:" in r3.output
