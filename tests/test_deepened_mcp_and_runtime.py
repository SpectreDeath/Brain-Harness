"""Unit and integration tests for deepened MCPProtocolCodec and RuntimeAdapter seams."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

from harness.events.bus import EventBus
from harness.events.types import EventType, HarnessEvent
from harness.kernel.context import ServiceContext, ServiceKey
from harness.kernel.lifecycle import PluginLifecycle, PluginState
from harness.kernel.runtime import HarnessRuntime
from harness.mcp.protocol import (
    JSONRPC_METHOD_NOT_FOUND,
    JSONRPC_PARSE_ERROR,
    MCPProtocolCodec,
    MCPRequest,
)
from harness.mcp.server import HarnessMCPServer
from harness.plugins.base import HarnessPlugin
from harness.services.tools import ToolRegistry, ToolSpec
from harness.ui.server import RuntimeAdapter, create_app


class SimpleTestPlugin(HarnessPlugin):
    def __init__(self, name: str) -> None:
        self._name = name
        self.key = ServiceKey[str](f"svc.{name}")

    @property
    def name(self) -> str:
        return self._name

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return f"Plugin {self._name}"

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [self.key]

    async def on_load(self, ctx: ServiceContext) -> None:
        ctx.provide(self.key, f"val_{self._name}", provider=self.name)


@pytest.mark.unit
class TestMCPProtocolCodecSeam:
    """Test MCPProtocolCodec serialization, deserialization, and schema translation."""

    def test_parse_valid_request(self) -> None:
        raw = json.dumps({"jsonrpc": "2.0", "id": 42, "method": "tools/list", "params": {}})
        req = MCPProtocolCodec.parse_request(raw)
        assert isinstance(req, MCPRequest)
        assert req.id == 42
        assert req.method == "tools/list"
        assert req.params == {}

    def test_parse_bytes_and_non_dict_params(self) -> None:
        raw = b'{"jsonrpc": "2.0", "id": "req-1", "method": "test", "params": "simple"}'
        req = MCPProtocolCodec.parse_request(raw)
        assert req.id == "req-1"
        assert req.method == "test"
        assert req.params == {"value": "simple"}

    def test_parse_invalid_json(self) -> None:
        with pytest.raises(ValueError, match="JSON parse error"):
            MCPProtocolCodec.parse_request("{invalid_json")

    def test_parse_non_object(self) -> None:
        with pytest.raises(ValueError, match="payload must be a JSON object"):
            MCPProtocolCodec.parse_request("123")

    def test_encode_response_and_error(self) -> None:
        resp = MCPProtocolCodec.encode_response(101, {"status": "ok"})
        assert resp["jsonrpc"] == "2.0"
        assert resp["id"] == 101
        assert resp["result"] == {"status": "ok"}

        err_resp = MCPProtocolCodec.encode_error(102, code=-32600, message="Invalid Request", data={"details": "bad"})
        assert err_resp["jsonrpc"] == "2.0"
        assert err_resp["id"] == 102
        assert err_resp["error"]["code"] == -32600
        assert err_resp["error"]["message"] == "Invalid Request"
        assert err_resp["error"]["data"] == {"details": "bad"}

    def test_encode_request(self) -> None:
        req = MCPProtocolCodec.encode_request("tools/call", {"name": "calc.add"}, req_id=99)
        assert req["jsonrpc"] == "2.0"
        assert req["id"] == 99
        assert req["method"] == "tools/call"
        assert req["params"]["name"] == "calc.add"

    def test_build_initialize_response(self) -> None:
        init_resp = MCPProtocolCodec.build_initialize_response(1, server_name="test-server", version="2.0.0")
        assert init_resp["id"] == 1
        assert init_resp["result"]["serverInfo"]["name"] == "test-server"
        assert init_resp["result"]["serverInfo"]["version"] == "2.0.0"
        assert "capabilities" in init_resp["result"]

    def test_build_tools_list_response(self) -> None:
        tools = [{"name": "test.tool", "description": "Test"}]
        resp = MCPProtocolCodec.build_tools_list_response(2, tools)
        assert resp["id"] == 2
        assert resp["result"]["tools"] == tools

    def test_build_tool_call_response(self) -> None:
        # Structured result
        resp1 = MCPProtocolCodec.build_tool_call_response(3, {"output": 42}, is_error=False)
        assert resp1["id"] == 3
        assert resp1["result"]["isError"] is False
        assert json.loads(resp1["result"]["content"][0]["text"]) == {"output": 42}

        # Plain text / error result
        resp2 = MCPProtocolCodec.build_tool_call_response(4, "Tool failed", is_error=True)
        assert resp2["id"] == 4
        assert resp2["result"]["isError"] is True
        assert resp2["result"]["content"][0]["text"] == "Tool failed"

    def test_tool_spec_and_mcp_translation(self) -> None:
        def sample_add(a: int, b: int) -> int:
            """Add two numbers."""
            return a + b

        native_spec = ToolSpec.from_callable(sample_add, name="math.add", provider="math")
        mcp_dict = MCPProtocolCodec.tool_spec_to_mcp(native_spec)

        assert mcp_dict["name"] == "math.add"
        assert mcp_dict["description"] == "Add two numbers."
        assert "inputSchema" in mcp_dict

        # Translate back to ToolSpec
        imported_spec = MCPProtocolCodec.mcp_tool_to_spec(
            mcp_dict,
            provider="ext",
            executor=lambda **kw: 10,
        )
        assert imported_spec.name == "ext.math.add"
        assert imported_spec.description == "Add two numbers."
        assert imported_spec.provider == "ext"
        assert imported_spec.executor is not None


@pytest.mark.unit
@pytest.mark.asyncio
class TestHarnessMCPServerDeepenedSeam:
    """Test HarnessMCPServer integration with MCPProtocolCodec."""

    async def test_server_initialize_and_tools_list(self) -> None:
        registry = ToolRegistry()
        def greet(name: str) -> str:
            """Greet someone."""
            return f"Hello, {name}"

        registry.register(ToolSpec.from_callable(greet, name="demo.greet"))
        server = HarnessMCPServer(registry)

        init_resp = await server.handle_request({"id": 1, "method": "initialize"})
        assert init_resp["id"] == 1
        assert init_resp["result"]["serverInfo"]["name"] == "harness-mcp"

        list_resp = await server.handle_request({"id": 2, "method": "tools/list"})
        assert list_resp["id"] == 2
        tools = list_resp["result"]["tools"]
        assert len(tools) == 1
        assert tools[0]["name"] == "demo.greet"

    async def test_server_tool_call_success_and_error(self) -> None:
        registry = ToolRegistry()
        def multiply(x: int, y: int) -> int:
            return x * y

        registry.register(ToolSpec.from_callable(multiply, name="calc.multiply"))
        server = HarnessMCPServer(registry)

        call_resp = await server.handle_request({
            "id": 10,
            "method": "tools/call",
            "params": {"name": "calc.multiply", "arguments": {"x": 6, "y": 7}},
        })
        assert call_resp["id"] == 10
        assert call_resp["result"]["isError"] is False
        assert json.loads(call_resp["result"]["content"][0]["text"]) == 42

        # Non-existent tool call
        missing_resp = await server.handle_request({
            "id": 11,
            "method": "tools/call",
            "params": {"name": "non_existent"},
        })
        assert missing_resp["id"] == 11
        assert missing_resp["result"]["isError"] is True

    async def test_server_unknown_method(self) -> None:
        registry = ToolRegistry()
        server = HarnessMCPServer(registry)

        err_resp = await server.handle_request({"id": 99, "method": "unknown/op"})
        assert err_resp["id"] == 99
        assert err_resp["error"]["code"] == JSONRPC_METHOD_NOT_FOUND


@pytest.mark.unit
@pytest.mark.asyncio
class TestRuntimeAdapterAndUIServerDeepenedSeam:
    """Test RuntimeAdapter and FastAPI UI Server endpoints."""

    async def test_runtime_adapter_with_standalone_lifecycle(self) -> None:
        ctx = ServiceContext()
        lifecycle = PluginLifecycle(ctx)
        bus = EventBus()

        adapter = RuntimeAdapter(ctx, lifecycle=lifecycle, event_bus=bus)
        assert adapter.is_unified_runtime is False
        assert adapter.context is ctx
        assert adapter.lifecycle is lifecycle

        p1 = SimpleTestPlugin("plug1")
        p2 = SimpleTestPlugin("plug2")
        lifecycle.discover(p1)
        lifecycle.discover(p2)

        # Enable all
        results = await adapter.enable_all()
        assert results.get("plug1") is True
        assert results.get("plug2") is True

        # Disable all
        disabled = await adapter.disable_all(keep_core=True)
        assert "plug1" in disabled
        assert "plug2" in disabled

    async def test_runtime_adapter_with_unified_runtime(self) -> None:
        async with HarnessRuntime.create(db_path=":memory:") as rt:
            adapter = RuntimeAdapter(rt)
            assert adapter.is_unified_runtime is True
            assert adapter.context is rt.context
            assert adapter.lifecycle is rt.lifecycle
            assert adapter.event_bus is rt.event_bus

            # Disable and re-enable non-core
            disabled = await adapter.disable_all(keep_core=True)
            assert isinstance(disabled, list)

            results = await adapter.enable_all()
            assert isinstance(results, dict)

    async def test_ui_server_plugin_enable_disable_endpoints(self) -> None:
        async with HarnessRuntime.create(db_path=":memory:") as rt:
            app = create_app(rt)
            transport = ASGITransport(app=app)

            async with AsyncClient(transport=transport, base_url="http://test") as client:
                # Get status
                st_res = await client.get("/api/status")
                assert st_res.status_code == 200
                st_data = st_res.json()
                assert "plugins" in st_data
                assert "services" in st_data

                # Enable all
                enable_res = await client.post("/api/plugins/enable-all")
                assert enable_res.status_code == 200
                assert enable_res.json()["status"] == "ok"

                # Disable all (keep core)
                disable_res = await client.post("/api/plugins/disable-all")
                assert disable_res.status_code == 200
                assert disable_res.json()["status"] == "ok"
