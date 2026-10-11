"""STDIO-based Model Context Protocol server orchestrator."""

from __future__ import annotations

import sys
from typing import Any

from harness.mcp.protocol import MCPProtocolCodec
from harness.mcp.server.context import MCPRequestContext
from harness.mcp.server.interceptors import (
    MCPInterceptorPipeline,
    MCPTelemetryInterceptor,
)
from harness.mcp.server.registry import MCPRegistry
from harness.mcp.server.router import MCPMethodRouter
from harness.mcp.server.transport import AsyncStdioServerTransport
from harness.services.tools import ToolRegistry

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


class HarnessMCPServer:
    """STDIO-based Model Context Protocol server."""

    def __init__(
        self,
        tool_registry: ToolRegistry,
        *,
        context: Any | None = None,
        loader: Any | None = None,
        registry: MCPRegistry | None = None,
        pipeline: MCPInterceptorPipeline | None = None,
        router: MCPMethodRouter | None = None,
    ) -> None:
        self.tool_registry = tool_registry
        self.context = context
        self.loader = loader
        self.registry = registry or MCPRegistry(
            tool_registry, context=context, loader=loader
        )
        self.pipeline = pipeline or MCPInterceptorPipeline([MCPTelemetryInterceptor()])
        self.codec = MCPProtocolCodec
        self.router = router or MCPMethodRouter(
            self.registry, pipeline=self.pipeline, codec=self.codec
        )
        self.transport = AsyncStdioServerTransport(
            self.router,
            codec=self.codec,
            event_bus=getattr(context, "event_bus", None) if context else None,
        )

    async def handle_request(self, request: dict[str, Any]) -> dict[str, Any]:
        """Process an incoming JSON-RPC MCP request dictionary."""
        req_id = request.get("id")
        method = request.get("method", "")
        params = request.get("params", {})
        if not isinstance(params, dict):
            params = {}

        ctx = MCPRequestContext(
            request_id=req_id,
            method=method,
            params=params,
            event_bus=getattr(self.context, "event_bus", None) if self.context else None,
            codec=self.codec,
        )
        return await self.router.dispatch(ctx)

    async def handle_batch(self, requests: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Process a batch of incoming JSON-RPC MCP requests."""
        return await self.router.dispatch_batch(
            requests,
            event_bus=getattr(self.context, "event_bus", None) if self.context else None,
        )

    async def dispatch_raw(self, raw_text: str | bytes) -> str | None:
        """Parse raw string or bytes and dispatch through transport."""
        text = raw_text.decode("utf-8") if isinstance(raw_text, bytes) else str(raw_text)
        return await self.transport.process_line(text)

    async def run_stdio(self) -> None:
        """Run the JSON-RPC loop over standard input/output."""
        loop = sys.stdin
        for line in loop:
            line_str = line.strip()
            if not line_str:
                continue

            resp_str = await self.dispatch_raw(line_str)
            if resp_str is not None:
                sys.stdout.write(resp_str + "\n")
                sys.stdout.flush()


__all__ = [
    "HarnessMCPServer",
]
