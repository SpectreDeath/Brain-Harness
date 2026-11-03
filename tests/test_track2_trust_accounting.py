"""Tests for Track 2: Trust accounting, ToolRegistry aliases, MCP list/call alignment, and persistence."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
import pytest

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.plugins.manifest import PluginManifest
from harness.plugins.sandboxed import SandboxedPlugin
from harness.services.tools.models import ToolSpec
from harness.services.tools.registry import ToolRegistry
from harness.mcp.server.router import MCPMethodRouter
from harness.mcp.server.context import MCPRequestContext
from harness.commands.tools import (
    toggle_tool_by_name,
    _update_persistent_tool_state,
)


class DummyPlugin(HarnessPlugin):
    @property
    def name(self) -> str:
        return "dummy.plugin"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def trusted(self) -> bool:
        return True

    @property
    def trust_justification(self) -> str:
        return "Pure computation for test verification"


def test_trust_justification_fields():
    # 1. Base plugin
    plugin = DummyPlugin()
    assert plugin.trusted is True
    assert plugin.trust_justification == "Pure computation for test verification"

    # 2. Manifest
    manifest = PluginManifest(
        name="test.manifest",
        version="1.0.0",
        trusted=True,
        trust_justification="Advisory only, verified safe",
    )
    assert manifest.trusted is True
    assert manifest.trust_justification == "Advisory only, verified safe"

    # 3. SandboxedPlugin proxy
    sandboxed = SandboxedPlugin(manifest, Path("."))
    assert sandboxed.trusted is True
    assert sandboxed.trust_justification == "Advisory only, verified safe"


@pytest.mark.asyncio
async def test_tool_registry_alias_lifecycle():
    registry = ToolRegistry()
    mock_executor = AsyncMock(return_value={"status": "ok", "result": 42})

    # Register canonical tool
    registry.register(
        name="canonical.tool",
        description="A canonical tool",
        executor=mock_executor,
        provider="dummy.provider",
    )
    # Register alias
    registry.register_alias("tool_alias", "canonical.tool")

    assert registry.has_tool("tool_alias")
    assert registry.has_tool("canonical.tool")
    assert registry.resolve_tool_name("tool_alias") == "canonical.tool"

    # Verify listing with aliases
    tools_no_aliases = registry.list_tools(include_aliases=False)
    assert len(tools_no_aliases) == 1
    assert tools_no_aliases[0].name == "canonical.tool"

    tools_with_aliases = registry.list_tools(include_aliases=True)
    assert len(tools_with_aliases) == 2
    names = {t.name for t in tools_with_aliases}
    assert "canonical.tool" in names
    assert "tool_alias" in names

    # Registering under an alias name resolves to canonical rather than creating shadow entry
    registry.register(
        name="tool_alias",
        description="Overwriting via alias",
        executor=mock_executor,
        provider="dummy.provider",
    )
    assert len(registry.list_tools(include_aliases=False)) == 1
    assert registry._tools["canonical.tool"].description == "Overwriting via alias"

    # Unregister by alias resolves and prunes alias
    assert registry.unregister("tool_alias") is True
    assert not registry.has_tool("canonical.tool")
    assert not registry.has_tool("tool_alias")
    assert "tool_alias" not in registry._aliases


@pytest.mark.asyncio
async def test_tool_registry_unregister_all_prunes_aliases():
    registry = ToolRegistry()
    mock_executor = AsyncMock(return_value={"status": "ok"})

    registry.register("tool_a", "Tool A", mock_executor, provider="plugin_x")
    registry.register("tool_b", "Tool B", mock_executor, provider="plugin_y")
    registry.register_alias("alias_a", "tool_a")
    registry.register_alias("alias_b", "tool_b")

    removed = registry.unregister_all_from("plugin_x")
    assert removed == ["tool_a"]
    assert "alias_a" not in registry._aliases
    assert "alias_b" in registry._aliases
    assert registry.has_tool("alias_b")


@pytest.mark.asyncio
async def test_mcp_router_list_matches_call_and_includes_aliases():
    registry = ToolRegistry()
    mock_exec_1 = AsyncMock(return_value={"status": "ok", "result": "res1"})
    mock_exec_2 = AsyncMock(return_value={"status": "ok", "result": "res2"})

    registry.register("tool_enabled", "Enabled tool", mock_exec_1, enabled=True)
    registry.register("tool_disabled", "Disabled tool", mock_exec_2, enabled=False)
    registry.register_alias("alias_enabled", "tool_enabled")
    registry.register_alias("alias_disabled", "tool_disabled")

    mock_mcp_reg = MagicMock()
    mock_mcp_reg.tool_registry = registry

    router = MCPMethodRouter(registry=mock_mcp_reg)
    # 1. tools/list should only return ENABLED tools and aliases of enabled tools
    ctx_list = MCPRequestContext(request_id=1, method="tools/list", params={})
    list_res = await router.dispatch(ctx_list)
    tools = list_res["result"]["tools"]
    tool_names = {t["name"] for t in tools}
    assert "tool_enabled" in tool_names
    assert "alias_enabled" in tool_names
    assert "tool_disabled" not in tool_names
    assert "alias_disabled" not in tool_names

    # 2. tools/call should succeed on enabled tool and alias
    ctx_call1 = MCPRequestContext(
        request_id=2, method="tools/call", params={"name": "alias_enabled", "arguments": {}}
    )
    call_res1 = await router.dispatch(ctx_call1)
    assert not call_res1.get("isError")
    assert "res1" in call_res1["result"]["content"][0]["text"]

    # 3. tools/call should fail on disabled tool
    ctx_call2 = MCPRequestContext(
        request_id=3, method="tools/call", params={"name": "tool_disabled", "arguments": {}}
    )
    call_res2 = await router.dispatch(ctx_call2)
    assert call_res2.get("isError") or "disabled" in str(call_res2)


def test_cli_exact_tool_matching(tmp_path: Path):
    # Verify _update_persistent_tool_state
    _update_persistent_tool_state(
        enabled=["tool_a"],
        disabled=["tool_b"],
        config_dir=tmp_path,
    )
    state_file = tmp_path / "tool_state.json"
    assert state_file.exists()
    data = json.loads(state_file.read_text(encoding="utf-8"))
    assert data["enabled_tools"] == ["tool_a"]
    assert data["disabled_tools"] == ["tool_b"]
