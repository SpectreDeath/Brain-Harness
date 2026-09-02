"""MCP commands — pure async functions for Model Context Protocol server."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    from harness.kernel.runtime import HarnessRuntime
    from harness.mcp.server import HarnessMCPServer

logger = structlog.get_logger()


@dataclass
class McpServeResult:
    """Outcome of initializing or running the MCP server."""

    server: HarnessMCPServer
    tools_count: int = 0
    status: str = "running"

    def to_dict(self) -> dict[str, Any]:
        return {
            "tools_count": self.tools_count,
            "status": self.status,
        }


async def serve_mcp_cmd(
    stdio: bool = True,
    db_path: str = ":memory:",
    runtime: HarnessRuntime | None = None,
    shutdown_event: asyncio.Event | None = None,
) -> McpServeResult:
    """Run the MCP server exposing Harness tools to external agents.

    Args:
        stdio: If True, connects stdio transport for agent communication.
        db_path: SQLite database path.
        runtime: Existing active HarnessRuntime instance (optional).
        shutdown_event: Optional event to trigger server shutdown.

    Returns:
        McpServeResult with active server instance.
    """
    from harness.kernel.runtime import HarnessRuntime
    from harness.mcp.server import HarnessMCPServer

    rt = runtime or HarnessRuntime.create(db_path=db_path)
    if not runtime:
        await rt.start()

    tool_reg = rt.tools
    if not tool_reg:
        raise RuntimeError("Tool registry service not available")

    server = HarnessMCPServer(tool_reg)
    tools_count = len(tool_reg.list_tools())
    logger.info("Initialized Harness MCP server", tools_count=tools_count)

    result = McpServeResult(server=server, tools_count=tools_count, status="running")

    if stdio:
        if shutdown_event:
            server_task = asyncio.create_task(server.run_stdio())
            await shutdown_event.wait()
            server_task.cancel()
            try:
                await server_task
            except asyncio.CancelledError:
                pass
        else:
            await server.run_stdio()

        if not runtime:
            await rt.stop()
        result.status = "stopped"

    return result


# --- Click CLI adapters ---
import click
from harness.commands._utils import _run_async


@click.group("mcp")
def mcp_group() -> None:
    """Model Context Protocol (MCP) server commands."""


@mcp_group.command("serve")
def mcp_serve() -> None:
    """Start the MCP STDIO server exposing Harness tools to external agents."""
    _run_async(serve_mcp_cmd(stdio=True))


__all__ = [
    "McpServeResult",
    "mcp_group",
    "serve_mcp_cmd",
]
