"""Contract test suite for Agent Desktop Plugin (plugin.agent_desktop)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Ensure plugin directory and src are on sys.path
_PLUGIN_DIR = (
    Path(__file__).resolve().parents[1]
    / "plugins"
    / "integration_and_io"
    / "agent_desktop"
)
if str(_PLUGIN_DIR) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_DIR))

_SRC = Path(__file__).resolve().parents[1] / "src"
if _SRC.exists() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from harness.creator.validator import PluginValidator
from harness.kernel.context import ServiceContext
from harness.services.agent_desktop import (
    AGENT_DESKTOP_KEY,
    AgentDesktopService,
)
from plugins.integration_and_io.agent_desktop.main import (
    AgentDesktopPlugin,
    desktop_act,
    desktop_find,
    desktop_manage_window,
    desktop_snapshot,
    desktop_status,
    desktop_wait,
    plugin,
)


@pytest.mark.unit
class TestAgentDesktopPlugin:
    """Validate Agent Desktop Plugin lifecycle, IoC registration, and tool entrypoints."""

    def test_plugin_validator_compliance(self) -> None:
        """Verify plugin passes PluginValidator checks adhering to Rule 34 and Rule 38."""
        report = PluginValidator.validate_sync(_PLUGIN_DIR)
        assert report.valid is True, f"Plugin validation failed: {report.errors}"

    def test_plugin_metadata_and_singleton(self) -> None:
        """Verify plugin metadata, provides key, and singleton export per Rule 45."""
        assert plugin.name == "plugin.agent_desktop"
        assert plugin.version == "1.1.0"
        assert AGENT_DESKTOP_KEY in plugin.provides
        assert isinstance(plugin, AgentDesktopPlugin)
        assert isinstance(plugin, AgentDesktopService)

    @pytest.mark.asyncio
    async def test_ioc_context_provision_and_resolution(self) -> None:
        """Verify plugin registers into ServiceContext and resolves via AGENT_DESKTOP_KEY."""
        ctx = ServiceContext()
        await plugin.on_load(ctx)

        resolved = ctx.require(AGENT_DESKTOP_KEY)
        assert resolved is plugin

    @pytest.mark.asyncio
    async def test_plugin_protocol_methods(self) -> None:
        """Verify AgentDesktopService protocol implementation on plugin instance."""
        snap = await plugin.snapshot(app="TestApp", interactive_only=True)
        assert snap.status == "ok"
        assert snap.snapshot_id != ""

        act_res = await plugin.act(action="click", ref_id="@snap_test:e1")
        assert act_res.status == "ok"
        assert act_res.ok is True

        find_res = await plugin.find(app="TestApp", role="button")
        assert find_res.status == "ok"

        win_res = await plugin.manage_window(operation="list-windows")
        assert win_res.status == "ok"

        status_res = await plugin.get_status()
        assert status_res.status == "ok"

    def test_top_level_tool_handlers(self) -> None:
        """Verify top-level function wrappers declared in plugin.json."""
        snap = desktop_snapshot(app="TestApp", interactive_only=True)
        assert snap["status"] == "ok"
        assert "snapshot_id" in snap

        act_res = desktop_act(action="click", ref_id="@snap_test:e1")
        assert act_res["status"] == "ok"
        assert act_res["ok"] is True

        find_res = desktop_find(app="TestApp", role="button")
        assert find_res["status"] == "ok"

        win_res = desktop_manage_window(operation="list-windows")
        assert win_res["status"] == "ok"

        wait_res = desktop_wait(app="TestApp", timeout_ms=100)
        assert wait_res["status"] == "ok"

        status_res = desktop_status()
        assert status_res["status"] == "ok"
