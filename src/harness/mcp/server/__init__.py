"""MCP (Model Context Protocol) STDIO server and method router for Harness.

Exposes all registered Harness tools, resources, and execution surfaces to any MCP client
(such as Claude Desktop, VS Code, Cursor, or external orchestrators) via STDIO or JSON-RPC.
"""

from __future__ import annotations

import sys

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

from harness.mcp.server.context import (
    MCP_REGISTRY_KEY,
    MCPHandler,
    MCPRequestContext,
)
from harness.mcp.server.interceptors import (
    MCPAccessControlInterceptor,
    MCPInterceptor,
    MCPInterceptorPipeline,
    MCPTelemetryInterceptor,
)
from harness.mcp.server.http_transport import StreamableHttpServerTransport
from harness.mcp.server.registry import MCPRegistry
from harness.mcp.server.router import MCPMethodRouter
from harness.mcp.server.server import HarnessMCPServer
from harness.mcp.server.transport import AsyncStdioServerTransport

__all__ = [
    "AsyncStdioServerTransport",
    "HarnessMCPServer",
    "MCPAccessControlInterceptor",
    "MCPHandler",
    "MCPInterceptor",
    "MCPInterceptorPipeline",
    "MCPMethodRouter",
    "MCPRegistry",
    "MCPRequestContext",
    "MCPTelemetryInterceptor",
    "MCP_REGISTRY_KEY",
    "StreamableHttpServerTransport",
]
