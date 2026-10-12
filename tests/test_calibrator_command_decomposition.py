"""Contract verification tests for Cycle 53: Coding Harness Calibrator Command Decomposition.

Verifies:
- Direct imports from decomposed submodules and package facade re-exports
- Group consolidation: calibrator_group has exactly 4 registered subcommands (Rule 6)
- Engine adapter conforms to CodingHarnessCalibratorService protocol (Rule 49)
- Service resolver fallback and IoC resolution (Rule 58)
- Headless Click execution via CliRunner (Rule 10)
"""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from harness.commands.calibrator import (
    CodingHarnessCalibratorEngineAdapter,
    calibrator_brief_cli,
    calibrator_group,
    calibrator_recommend_cli,
    calibrator_repatch_cli,
    calibrator_staging_cli,
    get_calibrator_service,
)
from harness.commands.calibrator.brief import (
    calibrator_brief_cli as direct_brief,
)
from harness.commands.calibrator.engine_adapter import (
    CodingHarnessCalibratorEngineAdapter as DirectAdapter,
)
from harness.commands.calibrator.group import (
    calibrator_group as direct_group,
)
from harness.commands.calibrator.recommend import (
    calibrator_recommend_cli as direct_recommend,
)
from harness.commands.calibrator.repatch import (
    calibrator_repatch_cli as direct_repatch,
)
from harness.commands.calibrator.resolver import (
    get_calibrator_service as direct_resolver,
)
from harness.commands.calibrator.staging import (
    calibrator_staging_cli as direct_staging,
)
from harness.kernel.context import ServiceContext
from harness.services.coding_harness_calibrator import (
    CODING_HARNESS_CALIBRATOR_SERVICE_KEY,
    CalibrationRecommendationData,
    CodingHarnessCalibratorService,
)


@pytest.mark.unit
def test_calibrator_command_exports_and_imports() -> None:
    """Verify package facade re-exports match decomposed module definitions."""
    assert direct_group is calibrator_group
    assert direct_resolver is get_calibrator_service
    assert DirectAdapter is CodingHarnessCalibratorEngineAdapter
    assert direct_recommend is calibrator_recommend_cli
    assert direct_staging is calibrator_staging_cli
    assert direct_repatch is calibrator_repatch_cli
    assert direct_brief is calibrator_brief_cli


@pytest.mark.unit
def test_calibrator_group_consolidation() -> None:
    """Verify calibrator_group consolidation per Rule 6 has all 4 subcommands."""
    subcommand_names = set(calibrator_group.commands.keys())
    expected_names = {"recommend", "staging", "repatch", "brief"}
    assert subcommand_names == expected_names, f"Missing or unexpected subcommands: {subcommand_names}"


@pytest.mark.unit
def test_calibrator_engine_adapter_conformance() -> None:
    """Verify CodingHarnessCalibratorEngineAdapter implements CodingHarnessCalibratorService protocol."""
    adapter = CodingHarnessCalibratorEngineAdapter()
    assert isinstance(adapter, CodingHarnessCalibratorService)

    rec = adapter.calibrate(
        model_name="Claude-3.7-Sonnet",
        parameter_billions=550.0,
        workload="codebase_repo",
    )
    assert isinstance(rec, CalibrationRecommendationData)
    assert rec.model_name == "Claude-3.7-Sonnet"


@pytest.mark.unit
def test_calibrator_service_resolver() -> None:
    """Verify get_calibrator_service returns valid service from IoC and fallback."""
    # 1. Fallback resolution without context
    svc = get_calibrator_service(None)
    assert isinstance(svc, CodingHarnessCalibratorService)

    # 2. Context with registered service
    ctx = ServiceContext()
    custom_adapter = CodingHarnessCalibratorEngineAdapter()
    ctx.provide(CODING_HARNESS_CALIBRATOR_SERVICE_KEY, custom_adapter)
    resolved = get_calibrator_service(ctx)
    assert resolved is custom_adapter


@pytest.mark.unit
def test_calibrator_cli_runner_subcommands() -> None:
    """Verify headless execution of CLI commands via CliRunner."""
    runner = CliRunner()

    # 1. recommend
    r1 = runner.invoke(calibrator_group, ["recommend", "-m", "Claude-3.7-Sonnet", "-p", "550", "-w", "codebase_repo"])
    assert r1.exit_code == 0
    assert "Coding Harness Calibration Recommendation" in r1.output

    # 2. staging
    r2 = runner.invoke(calibrator_group, ["staging", "--budget", "100000", "--turns", "5"])
    assert r2.exit_code == 0
    assert "Two-Tier Context Staging" in r2.output

    # 3. repatch
    r3 = runner.invoke(calibrator_group, ["repatch", "-m", "strong_550b", "-a", "bash_only", "-w", "terminal_cli"])
    assert r3.exit_code == 0
    assert "Empirical Re-Patch & Cost Prediction" in r3.output
