"""Comprehensive test suite for OpenCode Bridge service and plugin.

Adheres to:
- Rule 2: Typed service keys (OPENCODE_BRIDGE_KEY).
- Rule 12: Slotted and frozen dataclass immutability.
- Rule 38: PluginValidator synchronous validation.
- Rule 43: Frozen dataclass mutation assertion via pytest.raises.
- Rule 45: Plugin module singleton export.
- Rule 58: Single-seam resolver factory (resolve_opencode_bridge).
"""

from __future__ import annotations

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from harness.creator.validator import PluginValidator
from harness.kernel.context import ServiceContext
from harness.services.opencode_bridge import (
    BUILTIN_OPENCODE_TOOLS,
    OPENCODE_BRIDGE_KEY,
    DefaultOpenCodeBridgeService,
    OpenCodeBridgeService,
    OpenCodeCatalogResult,
    OpenCodeRunResult,
    OpenCodeSessionResult,
    OpenCodeStatusResult,
    resolve_opencode_bridge,
)
from plugins.agent_orchestration.opencode_bridge.main import (
    OpenCodeBridgePlugin,
    opencode_run_prompt,
    opencode_session_info,
    opencode_status,
    opencode_tool_catalog,
    plugin,
)



class TestOpenCodeBridgeDataModels:
    """Verifies slotted, frozen dataclass immutability and post-init assertions (Rule 12 & 43)."""

    def test_status_result_frozen_and_valid(self) -> None:
        result = OpenCodeStatusResult(
            is_installed=True,
            version="2.1.4",
            server_status="running",
            active_port=4096,
            executable_path="/usr/local/bin/opencode",
            status="ok",
        )
        assert result.is_installed is True
        assert result.version == "2.1.4"
        assert result.active_port == 4096
        assert result.status == "ok"

        # Verify immutability (Rule 43: direct attribute assignment inside pytest.raises)
        with pytest.raises((AttributeError, TypeError)):
            result.is_installed = False  # type: ignore[misc]

    def test_status_result_invalid_status_assertion(self) -> None:
        with pytest.raises(AssertionError, match="Invalid status"):
            OpenCodeStatusResult(is_installed=False, status="unknown_status")

    def test_run_result_frozen_and_valid(self) -> None:
        result = OpenCodeRunResult(
            exit_code=0,
            output='{"status": "ok"}',
            status="ok",
            duration_ms=42.5,
            parsed_json={"status": "ok"},
        )
        assert result.exit_code == 0
        assert result.duration_ms == 42.5
        assert result.parsed_json == {"status": "ok"}

        with pytest.raises((AttributeError, TypeError)):
            result.exit_code = 1  # type: ignore[misc]

    def test_run_result_negative_duration_assertion(self) -> None:
        with pytest.raises(AssertionError, match="Negative duration"):
            OpenCodeRunResult(exit_code=0, output="", duration_ms=-10.0)

    def test_catalog_result_frozen(self) -> None:
        result = OpenCodeCatalogResult(
            tools_count=len(BUILTIN_OPENCODE_TOOLS),
            tools=tuple(BUILTIN_OPENCODE_TOOLS),
            mcp_servers=("filesystem", "git"),
            status="ok",
        )
        assert result.tools_count == len(BUILTIN_OPENCODE_TOOLS)
        assert len(result.tools) > 0
        assert "filesystem" in result.mcp_servers

        with pytest.raises((AttributeError, TypeError)):
            result.tools_count = 0  # type: ignore[misc]


class TestOpenCodeBridgeResolver:
    """Verifies single-seam resolver factory behavior (Rule 58)."""

    def test_resolve_without_context(self) -> None:
        svc = resolve_opencode_bridge(None)
        assert isinstance(svc, DefaultOpenCodeBridgeService)
        assert isinstance(svc, OpenCodeBridgeService)

    def test_resolve_from_ioc_context(self) -> None:
        ctx = ServiceContext()
        custom_svc = MagicMock(spec=OpenCodeBridgeService)
        ctx.provide(OPENCODE_BRIDGE_KEY, custom_svc, provider="unit_test")

        resolved = resolve_opencode_bridge(ctx)
        assert resolved is custom_svc

    def test_resolve_fallback_when_unregistered(self) -> None:
        ctx = ServiceContext()
        resolved = resolve_opencode_bridge(ctx)
        assert isinstance(resolved, DefaultOpenCodeBridgeService)


class TestOpenCodeBridgeEngine:
    """Verifies DefaultOpenCodeBridgeService execution with mock and real CLI behaviors."""

    def test_catalog_inspection(self) -> None:
        engine = DefaultOpenCodeBridgeService(cli_path=None)
        catalog = engine.get_tool_catalog()
        assert catalog.status == "ok"
        assert catalog.tools_count >= 15
        tool_names = [t["name"] for t in catalog.tools]
        assert "read" in tool_names
        assert "write" in tool_names
        assert "persistent_pty" in tool_names
        assert "codemode" in tool_names

    def test_get_status_cli_not_found(self) -> None:
        engine = DefaultOpenCodeBridgeService(cli_path="/nonexistent/bin/opencode")
        status = engine.get_status()
        assert status.status == "cli_not_found"
        assert status.is_installed is False
        assert status.server_status == "not_installed"

    def test_get_status_mocked_cli(self) -> None:
        engine = DefaultOpenCodeBridgeService(cli_path="/mock/opencode")
        with patch("pathlib.Path.exists", return_value=True), \
             patch("subprocess.run") as mock_run:
            # First call: --version
            mock_run.side_effect = [
                MagicMock(returncode=0, stdout="2.1.4\n", stderr=""),
                MagicMock(returncode=0, stdout="Running on http://localhost:4096\n", stderr=""),
            ]
            status = engine.get_status()
            assert status.status == "ok"
            assert status.is_installed is True
            assert status.version == "2.1.4"
            assert status.server_status == "running"
            assert status.active_port == 4096

    def test_run_prompt_mocked_success(self) -> None:
        engine = DefaultOpenCodeBridgeService(cli_path="/mock/opencode")
        with patch("pathlib.Path.exists", return_value=True), \
             patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout='{"result": "Task completed successfully"}',
                stderr="",
            )
            res = engine.run_prompt(
                message="Build and test",
                model="anthropic/claude-3-7-sonnet",
                format="json",
                auto_approve=True,
            )
            assert res.status == "ok"
            assert res.exit_code == 0
            assert res.parsed_json == {"result": "Task completed successfully"}
            assert res.duration_ms >= 0.0

            # Verify command arguments passed to subprocess.run
            call_args = mock_run.call_args[0][0]
            assert "/mock/opencode" in call_args
            assert "run" in call_args
            assert "Build and test" in call_args
            assert "--format" in call_args
            assert "json" in call_args
            assert "--model" in call_args
            assert "anthropic/claude-3-7-sonnet" in call_args
            assert "--auto" in call_args

    def test_run_prompt_timeout_handling(self) -> None:
        engine = DefaultOpenCodeBridgeService(cli_path="/mock/opencode")
        with patch("pathlib.Path.exists", return_value=True), \
             patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd=["opencode"], timeout=5)):
            res = engine.run_prompt(message="Sleep task", timeout_seconds=5)
            assert res.status == "error"
            assert res.exit_code == -1
            assert "timed out after 5 seconds" in (res.error or "")

    def test_session_info_mocked(self) -> None:
        engine = DefaultOpenCodeBridgeService(cli_path="/mock/opencode")
        with patch("pathlib.Path.exists", return_value=True), \
             patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout='[{"id": "sess_123", "title": "Refactor API"}]',
                stderr="",
            )
            res = engine.get_session_info(action="list")
            assert res.status == "ok"
            assert len(res.sessions) == 1
            assert res.sessions[0]["id"] == "sess_123"


class TestOpenCodeBridgePluginLifecycle:
    """Verifies IoC lifecycle, singleton export, and tool entrypoints (Rule 45)."""

    def test_plugin_module_singleton_exists(self) -> None:
        assert isinstance(plugin, OpenCodeBridgePlugin)
        assert plugin.name == "plugin.opencode_bridge"
        assert plugin.version == "1.0.0"
        assert OPENCODE_BRIDGE_KEY in plugin.provides

    def test_plugin_ioc_registration(self) -> None:
        ctx = ServiceContext()
        plugin.on_load(ctx)

        resolved = ctx.require(OPENCODE_BRIDGE_KEY)
        assert resolved is plugin

        plugin.on_unload(ctx)

    def test_standalone_entrypoint_functions(self) -> None:
        catalog = opencode_tool_catalog()
        assert isinstance(catalog, dict)
        assert catalog["status"] == "ok"
        assert catalog["tools_count"] >= 15
        assert "persistent_pty" in [t["name"] for t in catalog["tools"]]

        status = opencode_status()
        assert isinstance(status, dict)
        assert "is_installed" in status

        sessions = opencode_session_info(action="list")
        assert isinstance(sessions, dict)
        assert "sessions" in sessions

    def test_plugin_validator_sync_pass_rate(self) -> None:
        from pathlib import Path
        plugin_path = Path("plugins/agent_orchestration/opencode_bridge").resolve()
        report = PluginValidator.validate_sync(plugin_path)
        assert report.valid is True
        assert len(report.errors) == 0
        for check in report.checks:
            assert check.passed is True
