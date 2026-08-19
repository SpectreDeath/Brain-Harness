"""Exercise 04.03: Model Context Protocol (MCP) Integration (Problem)."""

from __future__ import annotations

from typing import Any

from harness.services.tools import ToolRegistry


async def handle_mcp_discovery() -> dict[str, Any]:
    registry = ToolRegistry()  # noqa: F841
    # TODO: Register tool "system.ping"
    # TODO: Create HarnessMCPServer with registry
    # TODO: Handle request {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
    # TODO: Return response dictionary
    raise NotImplementedError
