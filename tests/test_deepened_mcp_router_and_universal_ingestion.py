"""Unit and integration tests for deepened MCP Router and Universal Ingestion Source Registry."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from harness.events.bus import EventBus
from harness.events.types import EventType, HarnessEvent
from harness.ingestion.resolvers import (
    GitHubSourceResolver,
    LocalDirectorySourceResolver,
    OpenAPISourceResolver,
    PyPISourceResolver,
    ResolvedSource,
    SourceResolver,
    UniversalSourceRegistry,
)
from harness.ingestion.pipeline import PluginIngestionPipeline
from harness.mcp.protocol import (
    JSONRPC_METHOD_NOT_FOUND,
    MCPNotification,
    MCPProtocolCodec,
    MCPRequest,
)
from harness.mcp.server import (
    HarnessMCPServer,
    MCPAccessControlInterceptor,
    MCPInterceptorPipeline,
    MCPMethodRouter,
    MCPRegistry,
    MCPRequestContext,
    MCPTelemetryInterceptor,
)
from harness.services.tools import ToolRegistry, ToolSpec


def test_mcp_protocol_codec_batch_and_notifications() -> None:
    """Test MCPProtocolCodec with single, notification, and batch payloads."""
    # 1. Single request
    single_json = json.dumps({"jsonrpc": "2.0", "id": "req-1", "method": "tools/list", "params": {}})
    parsed_single = MCPProtocolCodec.parse_payload(single_json)
    assert isinstance(parsed_single, MCPRequest)
    assert parsed_single.id == "req-1"
    assert parsed_single.method == "tools/list"

    # 2. Notification (no id)
    notif_json = json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {"client": "test"}})
    parsed_notif = MCPProtocolCodec.parse_payload(notif_json)
    assert isinstance(parsed_notif, MCPNotification)
    assert parsed_notif.method == "notifications/initialized"
    assert parsed_notif.params == {"client": "test"}

    # 3. Batch payload
    batch_json = json.dumps([
        {"jsonrpc": "2.0", "id": 1, "method": "ping"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
    ])
    parsed_batch = MCPProtocolCodec.parse_payload(batch_json)
    assert isinstance(parsed_batch, list)
    assert len(parsed_batch) == 2
    assert parsed_batch[0].id == 1
    assert parsed_batch[0].method == "ping"
    assert parsed_batch[1].id == 2
    assert parsed_batch[1].method == "tools/list"

    # 4. Encoding notification
    notif_encoded = MCPProtocolCodec.encode_notification("custom/alert", {"level": "info"})
    assert notif_encoded == {"jsonrpc": "2.0", "method": "custom/alert", "params": {"level": "info"}}

    # 5. Empty batch error
    with pytest.raises(ValueError, match="batch payload cannot be empty"):
        MCPProtocolCodec.parse_payload("[]")


@pytest.mark.asyncio
async def test_mcp_method_router_and_custom_routes() -> None:
    """Test MCPMethodRouter registration, built-in routes, and custom extensions."""
    tools = ToolRegistry()
    registry = MCPRegistry(tools)
    router = MCPMethodRouter(registry)

    # Built-in ping
    ctx_ping = MCPRequestContext(request_id="ping-1", method="ping", params={})
    resp_ping = await router.dispatch(ctx_ping)
    assert resp_ping["id"] == "ping-1"
    assert resp_ping["result"] == {}

    # Register custom method
    async def _custom_echo(params: dict[str, Any], ctx: MCPRequestContext) -> dict[str, Any]:
        return router.codec.encode_response(ctx.request_id, {"echo": params.get("msg")})

    router.register("custom/echo", _custom_echo)
    assert router.has_route("custom/echo")

    ctx_echo = MCPRequestContext(request_id="echo-1", method="custom/echo", params={"msg": "hello harness"})
    resp_echo = await router.dispatch(ctx_echo)
    assert resp_echo["result"] == {"echo": "hello harness"}

    # Non-existent method
    ctx_unknown = MCPRequestContext(request_id="err-1", method="non_existent_method", params={})
    resp_unknown = await router.dispatch(ctx_unknown)
    assert "error" in resp_unknown
    assert resp_unknown["error"]["code"] == JSONRPC_METHOD_NOT_FOUND


@pytest.mark.asyncio
async def test_mcp_interceptor_pipeline_and_access_control() -> None:
    """Test MCP interceptor pipeline with telemetry and access control policies."""
    tools = ToolRegistry()
    registry = MCPRegistry(tools)

    bus = EventBus()
    emitted_events: list[HarnessEvent] = []
    bus.on_all(lambda e: emitted_events.append(e))

    # Access control allowing only 'initialize' and 'ping'
    acl = MCPAccessControlInterceptor(allowed_methods={"initialize", "ping"})
    telemetry = MCPTelemetryInterceptor()
    pipeline = MCPInterceptorPipeline([acl, telemetry])

    router = MCPMethodRouter(registry, pipeline=pipeline)

    # Allowed method
    ctx_ping = MCPRequestContext(request_id=10, method="ping", params={}, event_bus=bus)
    resp_ping = await router.dispatch(ctx_ping)
    assert "result" in resp_ping
    assert len(emitted_events) >= 1

    # Blocked method
    ctx_tools = MCPRequestContext(request_id=11, method="tools/list", params={}, event_bus=bus)
    resp_tools = await router.dispatch(ctx_tools)
    assert "error" in resp_tools
    assert resp_tools["error"]["code"] == -32001
    assert "Access denied" in resp_tools["error"]["message"]


@pytest.mark.asyncio
async def test_harness_mcp_server_batch_and_transport() -> None:
    """Test HarnessMCPServer handling batch requests and raw STDIO lines."""
    tools = ToolRegistry()
    tools.register(
        ToolSpec(
            name="math.add",
            description="Add two numbers",
            parameters_schema={"type": "object", "properties": {"a": {"type": "number"}, "b": {"type": "number"}}},
            executor=lambda a, b: a + b,
        )
    )

    server = HarnessMCPServer(tools)

    # 1. Batch dispatch via handle_batch
    batch_req = [
        {"id": "b1", "method": "initialize", "params": {}},
        {"id": "b2", "method": "tools/call", "params": {"name": "math.add", "arguments": {"a": 5, "b": 7}}},
    ]
    batch_resp = await server.handle_batch(batch_req)
    assert len(batch_resp) == 2
    assert batch_resp[0]["id"] == "b1"
    assert batch_resp[0]["result"]["serverInfo"]["name"] == "harness-mcp"
    assert batch_resp[1]["id"] == "b2"
    assert "12" in batch_resp[1]["result"]["content"][0]["text"]

    # 2. Raw line dispatch via dispatch_raw (single request)
    raw_single = json.dumps({"jsonrpc": "2.0", "id": 99, "method": "tools/list", "params": {}})
    resp_line = await server.dispatch_raw(raw_single)
    assert resp_line is not None
    data = json.loads(resp_line)
    assert data["id"] == 99
    assert len(data["result"]["tools"]) >= 1

    # 3. Raw line dispatch (notification)
    raw_notif = json.dumps({"jsonrpc": "2.0", "method": "notifications/progress", "params": {"value": 50}})
    resp_notif = await server.dispatch_raw(raw_notif)
    assert resp_notif is None  # Notifications produce no response per JSON-RPC 2.0


@pytest.mark.asyncio
async def test_universal_source_resolvers(tmp_path: Path) -> None:
    """Test UniversalSourceRegistry resolution and priority mechanism."""
    registry = UniversalSourceRegistry.create_default()

    # 1. Matches PyPI
    pypi_resolver = registry.get_resolver("pypi:requests")
    assert isinstance(pypi_resolver, PyPISourceResolver)

    # 2. Matches OpenAPI
    openapi_resolver = registry.get_resolver("openapi:https://example.com/spec.json")
    assert isinstance(openapi_resolver, OpenAPISourceResolver)

    # 3. Matches Local Directory
    local_dir = tmp_path / "my_plugin"
    local_dir.mkdir()
    local_resolver = registry.get_resolver(str(local_dir))
    assert isinstance(local_resolver, LocalDirectorySourceResolver)

    resolved_local = await registry.resolve(str(local_dir), target_base_dir=tmp_path)
    assert isinstance(resolved_local, ResolvedSource)
    assert resolved_local.scheme == "local"
    assert resolved_local.directory == local_dir.resolve()

    # 4. Matches GitHub (fallback)
    gh_resolver = registry.get_resolver("https://github.com/owner/repo")
    assert isinstance(gh_resolver, GitHubSourceResolver)

    # 5. Custom pluggable resolver with priority
    class CustomMemoryResolver(SourceResolver):
        @property
        def name(self) -> str:
            return "memory"

        def matches(self, source: str | Path) -> bool:
            return str(source).startswith("memory:")

        async def resolve(
            self,
            source: str | Path,
            *,
            target_base_dir: Path,
            ref: str = "main",
            force: bool = False,
            github_token: str | None = None,
            event_bus: Any | None = None,
        ) -> ResolvedSource:
            plug_dir = target_base_dir / "mem_plug"
            plug_dir.mkdir(parents=True, exist_ok=True)
            (plug_dir / "plugin.json").write_text(
                json.dumps({
                    "name": "memory-plug",
                    "version": "1.0.0",
                    "description": "In-memory test plugin",
                    "isolation": "in_process",
                    "entrypoints": [],
                }),
                encoding="utf-8",
            )
            return ResolvedSource(source_str=str(source), scheme="memory", directory=plug_dir)

    custom_reg = UniversalSourceRegistry()
    custom_reg.register(CustomMemoryResolver(), priority=5)
    custom_reg.register(LocalDirectorySourceResolver(), priority=50)

    matched = custom_reg.get_resolver("memory:test-plugin")
    assert matched.name == "memory"

    resolved_mem = await custom_reg.resolve("memory:test-plugin", target_base_dir=tmp_path)
    assert resolved_mem.scheme == "memory"
    assert (resolved_mem.directory / "plugin.json").exists()


@pytest.mark.asyncio
async def test_plugin_ingestion_pipeline_with_custom_resolver(tmp_path: Path) -> None:
    """Test PluginIngestionPipeline using pluggable source registry and telemetry."""
    bus = EventBus()
    emitted: list[HarnessEvent] = []
    bus.on_all(lambda e: emitted.append(e))

    class MockSourceResolver(SourceResolver):
        @property
        def name(self) -> str:
            return "mock"

        def matches(self, source: str | Path) -> bool:
            return str(source).startswith("mock://")

        async def resolve(
            self,
            source: str | Path,
            *,
            target_base_dir: Path,
            ref: str = "main",
            force: bool = False,
            github_token: str | None = None,
            event_bus: Any | None = None,
        ) -> ResolvedSource:
            d = target_base_dir / "mock_plugin"
            d.mkdir(parents=True, exist_ok=True)
            (d / "plugin.json").write_text(
                json.dumps({
                    "name": "mock-plugin",
                    "version": "0.5.0",
                    "description": "Mocked test plugin",
                    "isolation": "in_process",
                    "entrypoints": [{"name": "run", "file": "main.py", "function": "run"}],
                }),
                encoding="utf-8",
            )
            (d / "main.py").write_text("def run(): return 42\n", encoding="utf-8")
            return ResolvedSource(source_str=str(source), scheme="mock", directory=d)

    registry = UniversalSourceRegistry()
    registry.register(MockSourceResolver(), priority=1)

    pipeline = PluginIngestionPipeline(
        plugin_dir=tmp_path / "plugins",
        event_bus=bus,
        registry=registry,
    )

    plugin = await pipeline.ingest("mock://repo/test")
    assert plugin.name == "mock-plugin"
    assert plugin.manifest.version == "0.5.0"

    event_types = [e.event_type for e in emitted]
    assert EventType.REPO_INSPECTED in event_types
    assert EventType.REPO_CONVERTED in event_types
