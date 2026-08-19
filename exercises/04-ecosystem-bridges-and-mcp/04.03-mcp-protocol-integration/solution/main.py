"""Exercise 04.03: Model Context Protocol (MCP) Integration (Solution)."""

from __future__ import annotations

from typing import Any

from harness.mcp.server import HarnessMCPServer
from harness.services.tools import ToolRegistry


async def handle_mcp_discovery() -> dict[str, Any]:
    registry = ToolRegistry()
    registry.register(
        name="system.ping",
        description="Return pong health status",
        executor=lambda: {"status": "pong"},
    )

    server = HarnessMCPServer(tool_registry=registry)
    return await server.handle_request({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
        "params": {},
    })
