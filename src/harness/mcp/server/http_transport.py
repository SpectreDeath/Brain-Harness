"""Streamable HTTP and SSE Server Transport for Model Context Protocol (MCP).

Supports JSON-RPC 2.0 POST message dispatch, Server-Sent Events (SSE) streaming,
and ASGI application interface for hosting the Harness MCP server remotely.
"""

from __future__ import annotations

import asyncio
import json
import uuid
from collections.abc import AsyncIterator
from typing import Any

import structlog

from harness.mcp.protocol import (
    JSONRPC_PARSE_ERROR,
    MCPNotification,
    MCPProtocolCodec,
)
from harness.mcp.server.context import MCPRequestContext
from harness.mcp.server.router import MCPMethodRouter

logger = structlog.get_logger()


class StreamableHttpServerTransport:
    """Streamable HTTP and SSE Server Transport for remote MCP clients."""

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
        self._active_sessions: dict[str, asyncio.Queue[str]] = {}

    def create_session(self) -> str:
        """Create a new SSE session and return its unique session ID."""
        session_id = str(uuid.uuid4())
        self._active_sessions[session_id] = asyncio.Queue(maxsize=100)
        return session_id

    def close_session(self, session_id: str) -> None:
        """Close an active SSE session."""
        self._active_sessions.pop(session_id, None)

    async def handle_post(
        self,
        body: str | bytes,
        headers: dict[str, str] | None = None,
    ) -> tuple[int, dict[str, str], str]:
        """Handle incoming JSON-RPC HTTP POST request."""
        raw_text = body.decode("utf-8") if isinstance(body, bytes) else str(body)
        raw_clean = raw_text.strip()
        json_headers = {"Content-Type": "application/json"}

        if not raw_clean:
            err = self.codec.encode_error(None, code=JSONRPC_PARSE_ERROR, message="Empty request body")
            return 400, json_headers, json.dumps(err)

        try:
            parsed = self.codec.parse_payload(raw_clean)
        except Exception as e:
            err = self.codec.encode_error(None, code=JSONRPC_PARSE_ERROR, message=str(e))
            return 400, json_headers, json.dumps(err)

        if isinstance(parsed, list):
            # Batch request
            batch_reqs = [{"id": r.id, "method": r.method, "params": r.params} for r in parsed]
            batch_resps = await self.router.dispatch_batch(batch_reqs, event_bus=self.event_bus)
            return 200, json_headers, json.dumps(batch_resps)

        if isinstance(parsed, MCPNotification):
            ctx = MCPRequestContext(
                request_id=None,
                method=parsed.method,
                params=parsed.params,
                event_bus=self.event_bus,
                codec=self.codec,
            )
            await self.router.dispatch(ctx)
            return 204, {}, ""

        ctx = MCPRequestContext(
            request_id=parsed.id,
            method=parsed.method,
            params=parsed.params,
            event_bus=self.event_bus,
            codec=self.codec,
        )
        resp = await self.router.dispatch(ctx)
        return 200, json_headers, json.dumps(resp)

    async def sse_event_stream(
        self,
        session_id: str,
        *,
        message_endpoint: str = "/message",
    ) -> AsyncIterator[str]:
        """Generate Server-Sent Events stream for an active session."""
        queue = self._active_sessions.get(session_id)
        if queue is None:
            queue = asyncio.Queue(maxsize=100)
            self._active_sessions[session_id] = queue

        # Initial endpoint event per standard MCP SSE specification
        endpoint_url = f"{message_endpoint}?sessionId={session_id}"
        yield f"event: endpoint\ndata: {endpoint_url}\n\n"

        while True:
            try:
                msg = await asyncio.wait_for(queue.get(), timeout=15.0)
                yield f"event: message\ndata: {msg}\n\n"
            except asyncio.TimeoutError:
                # Keepalive comment
                yield ": keepalive\n\n"
            except asyncio.CancelledError:
                break

    async def asgi_app(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        """Minimal standard ASGI 3.0 handler for mounting in ASGI servers."""
        if scope["type"] != "http":
            return

        method = scope.get("method", "GET").upper()
        path = scope.get("path", "/")

        if method == "POST":
            body_chunks: list[bytes] = []
            more_body = True
            while more_body:
                message = await receive()
                body_chunks.append(message.get("body", b""))
                more_body = message.get("more_body", False)

            status, resp_headers, resp_body = await self.handle_post(b"".join(body_chunks))
            header_tuples = [(k.encode("utf-8"), v.encode("utf-8")) for k, v in resp_headers.items()]

            await send({"type": "http.response.start", "status": status, "headers": header_tuples})
            await send({"type": "http.response.body", "body": resp_body.encode("utf-8")})
            return

        if method == "GET" and "/sse" in path:
            session_id = self.create_session()
            headers = [
                (b"content-type", b"text/event-stream"),
                (b"cache-control", b"no-cache"),
                (b"connection", b"keep-alive"),
            ]
            await send({"type": "http.response.start", "status": 200, "headers": headers})
            try:
                async for chunk in self.sse_event_stream(session_id):
                    await send({"type": "http.response.body", "body": chunk.encode("utf-8"), "more_body": True})
            finally:
                self.close_session(session_id)
            return

        # 404 fallback
        await send({"type": "http.response.start", "status": 404, "headers": [(b"content-type", b"text/plain")]})
        await send({"type": "http.response.body", "body": b"Not Found"})
