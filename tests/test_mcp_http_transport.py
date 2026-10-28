"""Tests for StreamableHttpServerTransport and remote MCP hosting."""

from __future__ import annotations

import json
import pytest

from harness.mcp.server.http_transport import StreamableHttpServerTransport
from harness.mcp.server.server import HarnessMCPServer
from harness.services.tools import ToolRegistry


@pytest.mark.unit
@pytest.mark.asyncio
class TestStreamableHttpServerTransport:
    async def test_handle_post_initialize_and_tool_call(self) -> None:
        registry = ToolRegistry()

        async def greet(name: str) -> str:
            return f"Hello, {name}!"

        registry.register(
            name="demo.greet",
            description="Greet someone",
            executor=greet,
            parameters_schema={
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"],
            },
        )

        server = HarnessMCPServer(registry)

        # 1. Initialize POST
        init_payload = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
        status, headers, body = await server.handle_http_post(init_payload)

        assert status == 200
        assert headers["Content-Type"] == "application/json"
        data = json.loads(body)
        assert data["result"]["serverInfo"]["name"] == "harness-mcp"
        assert data["result"]["protocolVersion"] == "2024-11-05"

        # 2. Tool Call POST
        call_payload = json.dumps({
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": "demo.greet", "arguments": {"name": "Alice"}},
        })
        status, headers, body = await server.handle_http_post(call_payload)
        assert status == 200
        data = json.loads(body)
        assert "Hello, Alice!" in data["result"]["content"][0]["text"]

    async def test_handle_post_invalid_json(self) -> None:
        registry = ToolRegistry()
        server = HarnessMCPServer(registry)

        status, headers, body = await server.handle_http_post("{malformed json")
        assert status == 400
        data = json.loads(body)
        assert "error" in data

    async def test_handle_post_batch(self) -> None:
        registry = ToolRegistry()
        server = HarnessMCPServer(registry)

        batch_payload = json.dumps([
            {"jsonrpc": "2.0", "id": 10, "method": "tools/list", "params": {}},
            {"jsonrpc": "2.0", "id": 11, "method": "initialize", "params": {}},
        ])
        status, headers, body = await server.handle_http_post(batch_payload)
        assert status == 200
        data = json.loads(body)
        assert len(data) == 2

    async def test_sse_event_stream_initial_endpoint(self) -> None:
        registry = ToolRegistry()
        server = HarnessMCPServer(registry)
        transport: StreamableHttpServerTransport = server.http_transport

        session_id = transport.create_session()
        assert session_id in transport._active_sessions

        gen = transport.sse_event_stream(session_id)
        first_event = await anext(gen)
        assert "event: endpoint\n" in first_event
        assert f"sessionId={session_id}" in first_event

        # Push a message into the session queue
        queue = transport._active_sessions[session_id]
        await queue.put(json.dumps({"jsonrpc": "2.0", "method": "notifications/test"}))

        second_event = await anext(gen)
        assert "event: message\n" in second_event
        assert "notifications/test" in second_event

        transport.close_session(session_id)
        assert session_id not in transport._active_sessions

    async def test_asgi_app_dispatch(self) -> None:
        registry = ToolRegistry()
        server = HarnessMCPServer(registry)
        transport: StreamableHttpServerTransport = server.http_transport

        scope = {"type": "http", "method": "POST", "path": "/message"}
        messages_sent: list[dict] = []

        async def receive() -> dict:
            return {
                "body": json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}).encode("utf-8"),
                "more_body": False,
            }

        async def send(msg: dict) -> None:
            messages_sent.append(msg)

        await transport.asgi_app(scope, receive, send)

        assert len(messages_sent) == 2
        assert messages_sent[0]["type"] == "http.response.start"
        assert messages_sent[0]["status"] == 200
        assert messages_sent[1]["type"] == "http.response.body"
