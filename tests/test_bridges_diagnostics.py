"""Tests for Ecosystem Bridge Diagnostics, Locator inspection, commands, and CLI."""

from __future__ import annotations

from pathlib import Path
import pytest
from click.testing import CliRunner

from harness.bridges.locator import BridgeDiagnosticReport, EcosystemLocator
from harness.commands.bridges import check_bridge_status_cmd, list_bridges_cmd
from harness.cli import main as cli_main


@pytest.mark.unit
class TestBridgeDiagnostics:
    """Test EcosystemLocator diagnostic inspection and structured report model."""

    def test_bridge_diagnostic_report_model(self) -> None:
        report = BridgeDiagnosticReport(
            project_name="em-cubed",
            available=True,
            path="/mock/path/em-cubed",
            env_var="EM_CUBED_PATH",
            capabilities=["code_execution", "tool_hosting"],
            status="connected",
        )
        assert report.project_name == "em-cubed"
        assert report.available is True
        assert report.status == "connected"
        assert len(report.capabilities) == 2

    def test_locator_inspect_all(self) -> None:
        reports = EcosystemLocator.inspect_all()
        assert len(reports) >= 3
        names = [r.project_name for r in reports]
        assert "em-cubed" in names
        assert "Memtext" in names
        assert "Skill Flywheel" in names

    def test_locator_inspect_single_bridge(self) -> None:
        rep = EcosystemLocator.inspect_bridge("Memtext")
        assert rep.project_name == "Memtext"
        assert rep.env_var == "MEMTEXT_PATH"
        assert "memory_graph" in rep.capabilities

    def test_commands_list_and_status(self) -> None:
        bridges = list_bridges_cmd()
        assert isinstance(bridges, list)
        assert len(bridges) >= 3

        status_all = check_bridge_status_cmd()
        assert status_all["status"] == "ok"
        assert status_all["total_bridges"] >= 3

        status_single = check_bridge_status_cmd("em-cubed")
        assert status_single["status"] == "ok"
        assert status_single["bridge"]["project_name"] == "em-cubed"

    def test_cli_bridge_commands(self) -> None:
        runner = CliRunner()

        # Test harness bridge list
        res_list = runner.invoke(cli_main, ["bridge", "list"])
        assert res_list.exit_code == 0
        assert "Ecosystem Bridges" in res_list.output
        assert "em-cubed" in res_list.output

        # Test harness bridge status overview
        res_status = runner.invoke(cli_main, ["bridge", "status"])
        assert res_status.exit_code == 0
        assert "Ecosystem Bridges Overview" in res_status.output

        # Test harness bridge status <name>
        res_single = runner.invoke(cli_main, ["bridge", "status", "Memtext"])
        assert res_single.exit_code == 0
        assert "Bridge Diagnostic Report: Memtext" in res_single.output
