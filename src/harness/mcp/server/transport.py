"""Non-blocking asynchronous STDIO transport for MCP server (Rule 14 & Rule 23)."""

from __future__ import annotations

import json
import sys
from typing import Any

from harness.mcp.protocol import (
    JSONRPC_PARSE_ERROR,
    MCPNotification,
    MCPProtocolCodec,
)
from harness.mcp.server.context import MCPRequestContext
from harness.mcp.server.router import MCPMethodRouter

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


class AsyncStdioServerTransport:
    """Non-blocking async STDIO transport for MCP server."""

    def __init__(
        self,
        router: MCPMethodRouter,
        *,
        codec: type[MCPProtocolCodec] = MCPProtocolCodec,
        event_bus: Any | None = None,
    ) -> None:
        self.router = router
        self.codec = codec
        self.event_bus = event_bus

    async def process_line(self, line: str) -> str | None:
        """Process a single raw JSON-RPC string line and return serialized response text or None for notification."""
        line_str = line.strip()
        if not line_str:
            return None

        try:
            parsed = self.codec.parse_payload(line_str)
        except Exception as e:
            err_resp = self.codec.encode_error(None, code=JSONRPC_PARSE_ERROR, message=str(e))
            return json.dumps(err_resp)

        if isinstance(parsed, list):
            # Batch request
            batch_reqs = [{"id": r.id, "method": r.method, "params": r.params} for r in parsed]
            batch_resps = await self.router.dispatch_batch(batch_reqs, event_bus=self.event_bus)
            return json.dumps(batch_resps)

        if isinstance(parsed, MCPNotification):
            ctx = MCPRequestContext(
                request_id=None,
                method=parsed.method,
                params=parsed.params,
                event_bus=self.event_bus,
                codec=self.codec,
            )
            await self.router.dispatch(ctx)
            return None

        # Standard MCPRequest
        ctx = MCPRequestContext(
            request_id=parsed.id,
            method=parsed.method,
            params=parsed.params,
            event_bus=self.event_bus,
            codec=self.codec,
        )
        resp = await self.router.dispatch(ctx)
        return json.dumps(resp)


__all__ = [
    "AsyncStdioServerTransport",
]
