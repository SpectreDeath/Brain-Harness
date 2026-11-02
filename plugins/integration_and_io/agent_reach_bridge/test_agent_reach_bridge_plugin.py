"""Contract test suite for Agent Reach Bridge Plugin."""

from __future__ import annotations

import sys
from pathlib import Path
import pytest

# Ensure plugin directory is on sys.path
_PLUGIN_DIR = Path(__file__).parent
if str(_PLUGIN_DIR) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_DIR))

from harness.creator.validator import PluginValidator
from harness.kernel.context import ServiceContext
from harness.services.agent_reach import (
    AGENT_REACH_SERVICE_KEY,
    AgentReachProtocol,
)
from plugins.integration_and_io.agent_reach_bridge.main import (
    AgentReachBridgePlugin,
    plugin,
    reach_action,
    reach_inspect_channels,
    reach_read,
    reach_scrub_url,
)


@pytest.mark.unit
class TestAgentReachBridgePlugin:
    """Validate Agent Reach Bridge Plugin lifecycle, IoC registration, and tool entrypoints."""

    def test_plugin_validator_compliance(self) -> None:
        """Verify plugin passes PluginValidator checks adhering to Rule 34 and Rule 38."""
        report = PluginValidator.validate_sync(_PLUGIN_DIR)
        assert report.valid is True, f"Plugin validation failed: {report.errors}"

    def test_plugin_metadata_and_singleton(self) -> None:
        """Verify plugin metadata, provides key, and singleton export per Rule 45."""
        assert plugin.name == "plugin.agent_reach_bridge"
        assert plugin.version == "1.0.0"
        assert AGENT_REACH_SERVICE_KEY in plugin.provides
        assert isinstance(plugin, AgentReachBridgePlugin)
        assert isinstance(plugin, AgentReachProtocol)

    @pytest.mark.asyncio
    async def test_ioc_context_provision_and_resolution(self) -> None:
        """Verify plugin registers into ServiceContext and resolves via AGENT_REACH_SERVICE_KEY."""
        ctx = ServiceContext()
        await plugin.on_load(ctx)

        resolved = ctx.require(AGENT_REACH_SERVICE_KEY)
        assert resolved is plugin

    def test_reach_read_tool(self) -> None:
        """Verify reading a URL returns a valid Schema v1 envelope."""
        res = reach_read(url="https://github.com/Panniantong/Agent-Reach")
        assert res["schema_version"] == 1
        assert res["ok"] is True
        assert res["channel"] == "github"
        assert res["action"] == "read"
        assert len(res["items"]) >= 1

    def test_reach_action_tool(self) -> None:
        """Verify executing an action generates an envelope with sanitized params."""
        res = reach_action(
            channel="youtube",
            action="transcript",
            params={"video_id": "dQw4w9WgXcQ", "token": "https://alice:secret@example.com"},
        )
        assert res["schema_version"] == 1
        assert res["ok"] is True
        assert res["channel"] == "youtube"
        assert res["action"] == "transcript"
        assert "secret" not in str(res["items"])
        assert "***:***" in str(res["items"])

    def test_reach_inspect_channels_tool(self) -> None:
        """Verify inspection surfaces registered platforms."""
        channels = reach_inspect_channels()
        channel_names = [c["name"] for c in channels]
        assert "web" in channel_names
        assert "youtube" in channel_names
        assert "github" in channel_names
        assert "bilibili" in channel_names
        assert "xiaohongshu" in channel_names

    def test_reach_scrub_url_tool(self) -> None:
        """Verify credential scrubber redacts inline basic auth."""
        dirty = "https://user:password123@api.github.com/repos/test"
        clean = reach_scrub_url(dirty)
        assert clean == "https://***:***@api.github.com/repos/test"

