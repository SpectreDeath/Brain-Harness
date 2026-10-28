"""Tests for MCP STDIO server protocol handling."""

import pytest

from harness.mcp.server import HarnessMCPServer
from harness.services.tools import ToolRegistry


@pytest.mark.unit
@pytest.mark.asyncio
class TestMCPServer:
    async def test_mcp_handshake_and_tool_dispatch(self) -> None:
        registry = ToolRegistry()

        async def multiply(a: int, b: int) -> int:
            return a * b

        registry.register(
            name="math.multiply",
            description="Multiply two integers",
            executor=multiply,
            parameters_schema={
                "type": "object",
                "properties": {
                    "a": {"type": "integer"},
                    "b": {"type": "integer"},
                },
                "required": ["a", "b"],
            },
        )

        server = HarnessMCPServer(registry)

        # 1. Initialize
        init_req = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
        init_resp = await server.handle_request(init_req)
        assert init_resp["result"]["serverInfo"]["name"] == "harness-mcp"
        assert init_resp["result"]["protocolVersion"] == "2024-11-05"

        # 2. Tools List
        list_req = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
        list_resp = await server.handle_request(list_req)
        tools = list_resp["result"]["tools"]
        assert len(tools) == 1
        assert tools[0]["name"] == "math.multiply"

        # 3. Tools Call
        call_req = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "math.multiply", "arguments": {"a": 6, "b": 7}},
        }
        call_resp = await server.handle_request(call_req)
        assert call_resp["result"]["isError"] is False
        assert "42" in call_resp["result"]["content"][0]["text"]

        # 4. Unknown method
        bad_req = {"jsonrpc": "2.0", "id": 4, "method": "unknown/method"}
        bad_resp = await server.handle_request(bad_req)
        assert "error" in bad_resp

    async def test_protocol_version_pinning_and_negotiation(self) -> None:
        from harness.mcp.protocol import (
            DEFAULT_PROTOCOL_VERSION,
            LATEST_PROTOCOL_VERSION,
            SUPPORTED_PROTOCOL_VERSIONS,
            negotiate_protocol_version,
            validate_protocol_version,
        )

        assert DEFAULT_PROTOCOL_VERSION == "2024-11-05"
        assert LATEST_PROTOCOL_VERSION == "2026-07-28"
        assert "2024-11-05" in SUPPORTED_PROTOCOL_VERSIONS
        assert "2026-07-28" in SUPPORTED_PROTOCOL_VERSIONS

        assert validate_protocol_version("2024-11-05") is True
        assert validate_protocol_version("2026-07-28") is True
        assert validate_protocol_version("1999-01-01") is False

        assert negotiate_protocol_version("2026-07-28") == "2026-07-28"
        assert negotiate_protocol_version("2024-11-05") == "2024-11-05"
        assert negotiate_protocol_version(None) == "2024-11-05"
        assert negotiate_protocol_version("unsupported") == "2024-11-05"

