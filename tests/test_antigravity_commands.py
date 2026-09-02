"""Tests for Antigravity Click CLI Commands."""

from __future__ import annotations

import json
import pytest
from click.testing import CliRunner

from harness.cli import main


@pytest.mark.unit
class TestAntigravityCliCommands:
    def test_antigravity_group_help(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["antigravity", "--help"])
        assert result.exit_code == 0
        assert "Google Antigravity SDK & CLI headless inspection seams." in result.output
        assert "status" in result.output
        assert "policy" in result.output
        assert "telemetry" in result.output

    def test_antigravity_status_text(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["antigravity", "status"])
        assert result.exit_code == 0
        assert "Google Antigravity Headless System Status" in result.output
        assert "Proactor Channel" in result.output
        assert "Active Triggers" in result.output

    def test_antigravity_status_json(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["antigravity", "status", "--json-output"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["proactor_channel"] == "127.0.0.1:4242"
        assert "registered_triggers" in data
        assert isinstance(data["trigger_details"], list)

    def test_antigravity_policy_permissive(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["antigravity", "policy", "--tool", "view_file", "--cmd", "cat foo"])
        assert result.exit_code == 0
        assert "[ALLOW]" in result.output

    def test_antigravity_policy_deny(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["antigravity", "policy", "--tool", "run_command", "--cmd", "rm -rf /"])
        assert result.exit_code == 0
        assert "[DENY]" in result.output
        assert "Catastrophic" in result.output

    def test_antigravity_policy_ask_user(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["antigravity", "policy", "--tool", "run_command", "--cmd", "git push --force"])
        assert result.exit_code == 0
        assert "[ASK_USER]" in result.output
        assert "Force push" in result.output

    def test_antigravity_policy_json(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["antigravity", "policy", "--tool", "run_command", "--cmd", "rm -rf /", "--json-output"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["decision"] == "DENY"
        assert data["tool"] == "run_command"

    def test_antigravity_telemetry_text(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["antigravity", "telemetry", "--mode", "tool"])
        assert result.exit_code == 0
        assert "Antigravity Dynamic Statusline IPC Summary" in result.output
        assert "Mode               : tool" in result.output
        assert "Total Tokens" in result.output

    def test_antigravity_telemetry_json(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["antigravity", "telemetry", "--mode", "review", "--json-output"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["mode"] == "review"
        assert data["tokens"]["total"] > 0
        assert "context_fill_ratio" in data["tokens"]
