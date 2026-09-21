"""Comprehensive tests for deepened deterministic validation loop architecture.

Covers domain engine, slotted frozen dataclasses, 3-tier validation hierarchy,
bounded budget triage, IoC service key resolution, plugin validation, and Click CLI seams.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest
from click.testing import CliRunner

_ws_root = Path(__file__).resolve().parent.parent
_skill_scripts = (
    _ws_root / ".agents" / "skills" / "deterministic-validation-loop" / "scripts"
)
for _p in [_ws_root / "src", _skill_scripts, _ws_root]:
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from validation_loop_engine import (
    DEPLOYMENT_CONFIG_SPEC,
    PLUGIN_MANIFEST_SPEC,
    DeterministicValidationEngine,
    LoopExecutionResult,
    TriageRecord,
    ValidationReport,
    ValidationRule,
    ValidationSpec,
    ValidationTier,
)

from harness.commands.validation_loop import validation_loop_group
from harness.creator.validator import PluginValidator
from harness.kernel.context import ServiceContext
from harness.services.deterministic_validation import (
    DETERMINISTIC_VALIDATION_SERVICE_KEY,
    DeterministicValidationService,
    LoopExecutionResultData,
    ValidationResultData,
)
from plugins.agent_orchestration.deterministic_validation_loop.main import (
    DeterministicValidationPlugin,
)
from plugins.agent_orchestration.deterministic_validation_loop.main import (
    plugin as validation_plugin,
)


@pytest.fixture
def engine() -> DeterministicValidationEngine:
    return DeterministicValidationEngine()


@pytest.fixture
def service_context() -> ServiceContext:
    ctx = ServiceContext()
    ctx.provide(DETERMINISTIC_VALIDATION_SERVICE_KEY, validation_plugin)
    return ctx


# --- 1. Slotted & Frozen Dataclass Immutability (Rule 12 & Rule 43) ---


def test_frozen_dataclass_immutability():
    """Verify slotted & frozen dataclasses prevent attribute mutation (Rule 12 & Rule 43)."""
    rule = ValidationRule(
        name="test_rule",
        tier=ValidationTier.TIER_2_BOUNDS,
        description="Test rule description",
        predicate=lambda p: (True, None),
    )
    with pytest.raises((AttributeError, TypeError)):
        rule.name = "mutated_name"  # type: ignore

    spec = ValidationSpec(
        name="test_spec",
        schema={"type": "object"},
        rules=(rule,),
        bail_early_on_tier_1=True,
    )
    with pytest.raises((AttributeError, TypeError)):
        spec.name = "mutated_spec"  # type: ignore

    report = ValidationReport(is_valid=True, duration_ms=1.23)
    with pytest.raises((AttributeError, TypeError)):
        report.is_valid = False  # type: ignore

    triage = TriageRecord(
        request="test request",
        final_errors=("error1",),
        attempts=3,
        error_code=422,
    )
    with pytest.raises((AttributeError, TypeError)):
        triage.attempts = 4  # type: ignore

    loop_res = LoopExecutionResult(
        status="rejected",
        payload=None,
        attempts=3,
        errors=("error1",),
        triage_record=triage,
    )
    with pytest.raises((AttributeError, TypeError)):
        loop_res.status = "success"  # type: ignore


# --- 2. 3-Tier Validation Hierarchy & Early Bail ---


def test_tier_1_schema_pass_and_fail(engine: DeterministicValidationEngine):
    """Verify Tier 1 passes compliant payloads and bails early on structural failures."""
    valid_payload = {
        "service_name": "worker-pool",
        "replicas": 3,
        "resources": {"cpu_limit": 0.5, "memory_limit_mb": 512},
        "health_check": {
            "path": "/healthz",
            "timeout_seconds": 2,
            "interval_seconds": 10,
        },
    }
    report = engine.validate(DEPLOYMENT_CONFIG_SPEC, valid_payload)
    assert report.is_valid is True
    assert len(report.errors) == 0
    assert report.duration_ms >= 0.0

    # Missing required field bails early
    broken_structure = {"service_name": "worker-pool"}
    report_broken = engine.validate(DEPLOYMENT_CONFIG_SPEC, broken_structure)
    assert report_broken.is_valid is False
    assert len(report_broken.errors) == 1
    assert "Schema:" in report_broken.errors[0]
    assert ValidationTier.TIER_1_SCHEMA in report_broken.tier_failures


def test_tier_2_and_3_rules(engine: DeterministicValidationEngine):
    """Verify Tier 2 bounds and Tier 3 cross-field logical invariants."""
    # Boundary violation (Tier 2 in JSON Schema pattern / bounds)
    invalid_bounds = {
        "service_name": "INVALID_NAME!",
        "replicas": 50,
        "resources": {"cpu_limit": 0.5, "memory_limit_mb": 64},
        "health_check": {
            "path": "no-leading-slash",
            "timeout_seconds": 2,
            "interval_seconds": 10,
        },
    }
    rep_bounds = engine.validate(DEPLOYMENT_CONFIG_SPEC, invalid_bounds)
    assert rep_bounds.is_valid is False
    assert any("Schema:" in err for err in rep_bounds.errors)

    # Cross-field violation (Tier 3)
    cross_field_broken = {
        "service_name": "billing-api",
        "replicas": 8,
        "resources": {"cpu_limit": 0.5, "memory_limit_mb": 1024},
        "health_check": {
            "path": "/health",
            "timeout_seconds": 15,
            "interval_seconds": 10,
        },
    }
    rep_cross = engine.validate(DEPLOYMENT_CONFIG_SPEC, cross_field_broken)
    assert rep_cross.is_valid is False
    assert len(rep_cross.errors) == 2
    assert any("requires cpu_limit >= 1.0" in err for err in rep_cross.errors)
    assert any(
        "timeout_seconds must be < interval_seconds" in err for err in rep_cross.errors
    )
    assert ValidationTier.TIER_3_INVARIANTS in rep_cross.tier_failures


def test_plugin_manifest_spec_preset(engine: DeterministicValidationEngine):
    """Verify built-in plugin manifest preset."""
    valid_manifest = {
        "name": "my_plugin",
        "version": "1.0.0",
        "category": "agent_orchestration",
        "description": "A high-performance agent orchestration plugin",
        "provides": ["service.my_service"],
    }
    rep = engine.validate(PLUGIN_MANIFEST_SPEC, valid_manifest)
    assert rep.is_valid is True

    invalid_version = {
        "name": "my_plugin",
        "version": "1.0-beta",
        "category": "agent_orchestration",
        "description": "Short",
        "provides": [],
    }
    rep_inv = engine.validate(PLUGIN_MANIFEST_SPEC, invalid_version)
    assert rep_inv.is_valid is False


# --- 3. State Machine Loop Execution, Delta Injection & Triage ---


def test_run_loop_recovery_on_retry(engine: DeterministicValidationEngine):
    """Verify error delta feedback allows recovery on attempt 2."""

    def recovering_gen(req: str, errors: list[str], attempt: int) -> dict[str, Any]:
        if attempt == 1:
            return {
                "service_name": "worker-api",
                "replicas": 7,
                "resources": {"cpu_limit": 0.5, "memory_limit_mb": 512},
                "health_check": {
                    "path": "/healthz",
                    "timeout_seconds": 2,
                    "interval_seconds": 10,
                },
            }
        # Injected delta feedback received
        assert len(errors) == 1
        assert "requires cpu_limit >= 1.0" in errors[0]
        return {
            "service_name": "worker-api",
            "replicas": 7,
            "resources": {"cpu_limit": 1.5, "memory_limit_mb": 512},
            "health_check": {
                "path": "/healthz",
                "timeout_seconds": 2,
                "interval_seconds": 10,
            },
        }

    res = engine.run_loop(
        "Deploy worker API", recovering_gen, DEPLOYMENT_CONFIG_SPEC, max_attempts=3
    )
    assert res.status == "success"
    assert res.attempts == 2
    assert res.payload is not None
    assert res.payload["resources"]["cpu_limit"] == 1.5
    assert len(res.trace) == 2


def test_run_loop_exhausted_retries_fail_closed(engine: DeterministicValidationEngine):
    """Verify exhausted attempts halt at 3 with HTTP 422 triage record."""

    def broken_gen(req: str, errors: list[str], attempt: int) -> dict[str, Any]:
        return {
            "service_name": "broken-service",
            "replicas": 12,
            "resources": {"cpu_limit": 0.2, "memory_limit_mb": 256},
            "health_check": {
                "path": "/healthz",
                "timeout_seconds": 20,
                "interval_seconds": 5,
            },
        }

    res = engine.run_loop(
        "Deploy broken service", broken_gen, DEPLOYMENT_CONFIG_SPEC, max_attempts=3
    )
    assert res.status == "rejected"
    assert res.attempts == 3
    assert len(res.errors) >= 1
    assert res.triage_record is not None
    assert res.triage_record.error_code == 422
    assert res.triage_record.request == "Deploy broken service"


def test_format_error_feedback(engine: DeterministicValidationEngine):
    """Verify Ramavat structured delta error formatting."""
    feedback = engine.format_error_feedback(
        request="Deploy database",
        errors=["cpu_limit must be >= 1.0", "path must start with /"],
    )
    assert "Generate configuration for: Deploy database" in feedback
    assert "Your previous attempt had these errors:" in feedback
    assert "- cpu_limit must be >= 1.0" in feedback
    assert "- path must start with /" in feedback
    assert "Fix ALL of them." in feedback


def test_generate_visual_brief(engine: DeterministicValidationEngine, tmp_path: Path):
    """Verify interactive HTML brief generation."""
    triage = TriageRecord(
        request="Deploy cluster",
        final_errors=("Error A", "Error B"),
        attempts=3,
        error_code=422,
    )
    loop_res = LoopExecutionResult(
        status="rejected",
        payload=None,
        attempts=3,
        errors=("Error A", "Error B"),
        triage_record=triage,
        trace=(
            {"attempt": 1, "status": "failed", "errors": ["Error A"]},
            {"attempt": 2, "status": "failed", "errors": ["Error A", "Error B"]},
            {"attempt": 3, "status": "failed", "errors": ["Error A", "Error B"]},
        ),
    )
    out_file = tmp_path / "test-brief.html"
    res_path = engine.generate_visual_brief(loop_res, output_path=out_file)
    assert res_path.exists()
    content = res_path.read_text(encoding="utf-8")
    assert "Deterministic Validation Brief" in content
    assert "REJECTED" in content
    assert "HTTP 422 Logged" in content


# --- 4. Micro-Kernel IoC Service Key Resolution (Rules 1, 2, 49) ---


def test_ioc_service_resolution(service_context: ServiceContext):
    """Verify DeterministicValidationService resolves cleanly via ServiceKey."""
    svc = service_context.require(DETERMINISTIC_VALIDATION_SERVICE_KEY)
    assert isinstance(svc, DeterministicValidationService)

    # Validate via IoC service
    res = svc.validate(
        {
            "service_name": "payment-api",
            "replicas": 2,
            "resources": {"cpu_limit": 0.5, "memory_limit_mb": 512},
            "health_check": {
                "path": "/healthz",
                "timeout_seconds": 2,
                "interval_seconds": 10,
            },
        },
        spec="deployment_config",
    )
    assert isinstance(res, ValidationResultData)
    assert res.is_valid is True

    # List presets
    presets = svc.list_presets()
    assert "deployment_config" in presets
    assert "plugin_manifest" in presets

    # Execute loop via IoC service
    def gen(req: str, errs: list[str], att: int) -> dict[str, Any]:
        return {
            "service_name": "worker",
            "replicas": 3,
            "resources": {"cpu_limit": 1.0, "memory_limit_mb": 512},
            "health_check": {
                "path": "/h",
                "timeout_seconds": 2,
                "interval_seconds": 10,
            },
        }

    loop_res = svc.execute_loop(
        "Deploy worker", gen, spec="deployment_config", max_attempts=3
    )
    assert isinstance(loop_res, LoopExecutionResultData)
    assert loop_res.status == "success"
    assert loop_res.attempts == 1


# --- 5. Plugin Compliance (Rule 38, Rule 44, Rule 45) ---


def test_plugin_validation_sync():
    """Verify plugin complies with Harness PluginValidator with zero errors and warnings."""
    plugin_dir = Path("plugins/agent_orchestration/deterministic_validation_loop")
    report = PluginValidator.validate_sync(plugin_dir)
    assert report.valid is True
    assert len(report.errors) == 0
    assert len(report.warnings) == 0


@pytest.mark.asyncio
async def test_plugin_lifecycle_and_tools():
    """Verify plugin loads into container and handles tool executions."""
    ctx = ServiceContext()
    p = DeterministicValidationPlugin()
    await p.on_load(ctx)

    # Check key provided
    assert ctx.optional(DETERMINISTIC_VALIDATION_SERVICE_KEY) is p

    # Tool invocation: validate_payload
    tool_res = await p.validate_payload(
        payload={
            "service_name": "auth-svc",
            "replicas": 3,
            "resources": {"cpu_limit": 0.5, "memory_limit_mb": 512},
            "health_check": {
                "path": "/health",
                "timeout_seconds": 2,
                "interval_seconds": 10,
            },
        },
        spec="deployment_config",
    )
    assert tool_res["is_valid"] is True

    # Tool invocation: get_preset_spec
    spec_tool = await p.get_preset_spec_tool(name="deployment_config")
    assert spec_tool["name"] == "deployment_config"
    assert "schema" in spec_tool


# --- 6. Headless Click CLI Seams (Rule 6 & Rule 10) ---


def test_click_cli_specs():
    """Verify 'harness validation-loop specs' command."""
    runner = CliRunner()
    res = runner.invoke(validation_loop_group, ["specs"])
    assert res.exit_code == 0
    assert "deployment_config" in res.output
    assert "plugin_manifest" in res.output

    # Specific spec
    res_spec = runner.invoke(
        validation_loop_group, ["specs", "--name", "deployment_config"]
    )
    assert res_spec.exit_code == 0
    parsed = json.loads(res_spec.output)
    assert parsed["name"] == "deployment_config"


def test_click_cli_validate_success(tmp_path: Path):
    """Verify 'harness validation-loop validate' command."""
    cfg_file = tmp_path / "valid_cfg.json"
    cfg_file.write_text(
        json.dumps(
            {
                "service_name": "cli-test-service",
                "replicas": 2,
                "resources": {"cpu_limit": 0.5, "memory_limit_mb": 512},
                "health_check": {
                    "path": "/health",
                    "timeout_seconds": 2,
                    "interval_seconds": 10,
                },
            }
        ),
        encoding="utf-8",
    )
    runner = CliRunner()
    res = runner.invoke(
        validation_loop_group,
        ["validate", "--spec", "deployment_config", "--file", str(cfg_file)],
    )
    assert res.exit_code == 0
    assert "Status: PASSED" in res.output


def test_click_cli_validate_failure(tmp_path: Path):
    """Verify 'harness validation-loop validate' failure output."""
    cfg_file = tmp_path / "broken_cfg.json"
    cfg_file.write_text(
        json.dumps({"service_name": "broken"}),
        encoding="utf-8",
    )
    runner = CliRunner()
    res = runner.invoke(
        validation_loop_group,
        ["validate", "--spec", "deployment_config", "--file", str(cfg_file)],
    )
    assert res.exit_code == 1
    assert "Status: FAILED" in res.output
    assert "Schema:" in res.output


def test_click_cli_run_simulation():
    """Verify 'harness validation-loop run' command with retry recovery and failure simulations."""
    runner = CliRunner()
    res_rec = runner.invoke(
        validation_loop_group,
        [
            "run",
            "--request",
            "Deploy payment api",
            "--spec",
            "deployment_config",
            "--simulate",
            "retry_recovery",
        ],
    )
    assert res_rec.exit_code == 0
    assert "Attempts: 2/3" in res_rec.output
    assert "Result: SUCCESS" in res_rec.output

    res_fail = runner.invoke(
        validation_loop_group,
        [
            "run",
            "--request",
            "Deploy broken",
            "--spec",
            "deployment_config",
            "--simulate",
            "fail_exhausted",
        ],
    )
    assert res_fail.exit_code == 0
    assert "Attempts: 3/3" in res_fail.output
    assert "Result: REJECTED (HTTP 422 Fail-Closed)" in res_fail.output


def test_click_cli_brief(tmp_path: Path):
    """Verify 'harness validation-loop brief' generates HTML."""
    out_file = tmp_path / "cli-brief.html"
    runner = CliRunner()
    res = runner.invoke(
        validation_loop_group,
        ["brief", "--output", str(out_file)],
    )
    assert res.exit_code == 0
    assert out_file.exists()
    assert "Interactive Visual Brief generated" in res.output
