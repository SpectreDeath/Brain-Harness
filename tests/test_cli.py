"""Comprehensive tests for the CLI."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from click.testing import CliRunner

from harness.agent.base import AgentTaskResult
from harness.cli import main


@pytest.mark.unit
class TestCLI:
    def test_version(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output

    def test_init(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["init", str(tmp_path)])
        assert result.exit_code == 0
        assert "initialized" in result.output.lower() or "✓" in result.output
        assert (tmp_path / "plugins").exists()
        assert (tmp_path / ".harness" / "config.json").exists()

    def test_plugin_list_empty(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["plugin", "list"])
        assert result.exit_code == 0

    def test_plugin_inspect_nonexistent(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["plugin", "inspect", "/nonexistent/path"])
        assert result.exit_code == 0
        assert "not found" in result.output.lower() or "✗" in result.output

    def test_plugin_inspect_valid(self, tmp_path: Path) -> None:
        runner = CliRunner()
        plugin_dir = tmp_path / "test_plugin"
        plugin_dir.mkdir()
        (plugin_dir / "plugin.json").write_text(
            json.dumps({"name": "test_plug", "version": "1.0.0", "description": "Test plug"})
        )
        result = runner.invoke(main, ["plugin", "inspect", str(plugin_dir)])
        assert result.exit_code == 0
        assert "test_plug" in result.output

    def test_bridge_status(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["bridge", "status"])
        assert result.exit_code == 0
        assert "Ecosystem Component" in result.output

    def test_services(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["services"])
        assert result.exit_code == 0
        assert "Service Key" in result.output

    def test_events_no_log(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()
        result = runner.invoke(main, ["events"])
        assert result.exit_code == 0
        assert "No event log found" in result.output

    def test_events_with_log(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        log_dir = tmp_path / ".harness"
        log_dir.mkdir(parents=True)
        log_file = log_dir / "events.jsonl"
        log_file.write_text(
            json.dumps({"id": "1", "event_type": "plugin.loaded", "source": "core", "timestamp": "2026-08-14T12:00:00"}) + "\n"
        )
        runner = CliRunner()
        result = runner.invoke(main, ["events"])
        assert result.exit_code == 0
        assert "plugin.loaded" in result.output

    def test_creator_build(self, tmp_path: Path) -> None:
        runner = CliRunner()
        target = tmp_path / "quick_tool"
        result = runner.invoke(main, ["creator", "build", "quick_tool", "--description", "test", "--target-dir", str(target)])
        assert result.exit_code == 0
        assert (target / "plugin.json").exists()
        assert (target / "main.py").exists()

    def test_creator_build_with_options(self, tmp_path: Path) -> None:
        runner = CliRunner()
        target = tmp_path / "ts_service"
        result = runner.invoke(main, [
            "creator", "build", "ts_service",
            "--description", "TypeScript API",
            "--target-dir", str(target),
            "--language", "typescript",
            "--tools", "fetch_data,process_data",
            "--deps", "axios,lodash",
            "--isolation", "subprocess",
            "--preset", "api_wrapper",
        ])
        assert result.exit_code == 0
        assert (target / "plugin.json").exists()
        assert (target / "index.ts").exists()
        assert (target / "tsconfig.json").exists()

        manifest_data = json.loads((target / "plugin.json").read_text(encoding="utf-8"))
        assert manifest_data["language"] == "typescript"
        assert len(manifest_data["entrypoints"]) == 2

    def test_creator_init(self, tmp_path: Path) -> None:
        runner = CliRunner()
        target = tmp_path / "interactive_plugin"
        prompts = [
            "interactive_plugin",  # Name
            "Interactive test plugin",  # Description
            "python",  # Language
            "general",  # Preset
            "run_job",  # Tools
            "httpx",  # Dependencies
            "subprocess",  # Isolation
            "tools",  # Category
            str(target),  # Target Directory
        ]
        result = runner.invoke(main, ["creator", "init"], input="\n".join(prompts) + "\n")
        assert result.exit_code == 0
        assert "Successfully initialized plugin" in result.output
        assert (target / "plugin.json").exists()
        assert (target / "main.py").exists()

    def test_introspect_command(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["introspect"])
        assert result.exit_code == 0
        assert "System Introspection Report" in result.output

    def test_agent_run_mock(self) -> None:
        runner = CliRunner()
        with patch("harness.kernel.runtime.HarnessRuntime.run_task", new_callable=AsyncMock) as mock_task:
            mock_task.return_value = AgentTaskResult(
                task="test task",
                status="success",
                final_answer="Task done.",
                steps=[],
            )
            result = runner.invoke(main, ["agent", "run", "do something"])
            assert result.exit_code == 0
            assert "Starting agent task" in result.output
            assert "Task done" in result.output
