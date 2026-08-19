"""Tests for MCPClientPlugin."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from harness.kernel.context import ServiceContext
from harness.mcp.client_plugin import MCPClientPlugin
from harness.services.tools import TOOL_REGISTRY_KEY, ToolRegistry


@pytest.mark.unit
class TestMCPClientPlugin:
    """Unit tests for MCPClientPlugin."""

    def test_metadata(self) -> None:
        plugin = MCPClientPlugin("filesystem", "npx", ["-y", "@modelcontextprotocol/server-filesystem"])
        assert plugin.name == "mcp.filesystem"
        assert plugin.version == "0.1.0"
        assert "External MCP Server client" in plugin.description
        assert plugin.trusted is True
        assert len(plugin.provides) == 1
        assert plugin.requires == [TOOL_REGISTRY_KEY]

    @pytest.mark.asyncio
    async def test_lifecycle_and_tool_registration(self) -> None:
        ctx = ServiceContext()
        registry = ToolRegistry()
        ctx.provide(TOOL_REGISTRY_KEY, registry)

        plugin = MCPClientPlugin("mock_server", "echo")
        await plugin.on_load(ctx)

        # Mock the underlying subprocess and RPC methods
        mock_tools_resp = {
            "jsonrpc": "2.0",
            "id": 2,
            "result": {
                "tools": [
                    {
                        "name": "read_file",
                        "description": "Read file contents",
                        "inputSchema": {
                            "type": "object",
                            "properties": {"path": {"type": "string"}},
                            "required": ["path"],
                        },
                    }
                ]
            },
        }

        with (
            patch.object(plugin, "_start_mcp_process", new_callable=AsyncMock) as mock_start,
            patch.object(plugin, "_send_rpc", new_callable=AsyncMock) as mock_rpc,
            patch.object(plugin, "_stop_mcp_process", new_callable=AsyncMock) as mock_stop,
        ):
            mock_rpc.side_effect = [
                {"jsonrpc": "2.0", "id": 1, "result": {}},  # initialize
                mock_tools_resp,  # tools/list
                {"jsonrpc": "2.0", "id": 3, "result": {"content": [{"type": "text", "text": "hello"}]}},  # tools/call
            ]

            await plugin.on_enable()
            mock_start.assert_awaited_once()

            # Verify tool registered
            assert "mcp.mock_server.read_file" in registry
            spec = registry.get("mcp.mock_server.read_file")
            assert spec is not None
            assert spec.description == "Read file contents"

            # Execute tool through registry
            res = await registry.invoke("mcp.mock_server.read_file", {"path": "test.txt"})
            assert res == {"status": "ok", "result": {"content": [{"type": "text", "text": "hello"}]}}

            # Disable plugin and verify tool unregistration
            await plugin.on_disable()
            assert "mcp.mock_server.read_file" not in registry
            mock_stop.assert_awaited_once()

            # Unload plugin
            await plugin.on_unload()

    @pytest.mark.asyncio
    async def test_rpc_not_running_raises(self) -> None:
        plugin = MCPClientPlugin("dummy", "dummy")
        with pytest.raises(RuntimeError, match="not running"):
            await plugin._send_rpc("test")
