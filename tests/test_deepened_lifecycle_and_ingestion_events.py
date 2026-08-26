"""Tests for deepened lifecycle events, ingestion telemetry, AgentSessionPlugin, and MCP resources."""

import asyncio
import json
from pathlib import Path
import pytest
from httpx import ASGITransport, AsyncClient

from harness.agent.base import AgentStep
from harness.agent.session import (
    AGENT_SESSION_MANAGER_KEY,
    AgentSessionManager,
    AgentSessionPlugin,
    StorageBackedSessionStore,
)
from harness.events.bus import EventBus
from harness.events.types import EventType, HarnessEvent
from harness.ingestion.pipeline import PluginIngestionPipeline
from harness.kernel.context import ServiceContext, ServiceKey
from harness.kernel.lifecycle import PluginLifecycle
from harness.kernel.runtime import HarnessRuntime
from harness.mcp.server import HarnessMCPServer
from harness.plugins.base import HarnessPlugin
from harness.services.storage import StoragePlugin
from harness.services.tools import ToolRegistry, ToolSpec
from harness.ui.server import create_app


class MockDummyPlugin(HarnessPlugin):
    def __init__(self, name: str = "mock.plugin", version: str = "1.2.3") -> None:
        self._name = name
        self._version = version
        self._loaded = False
        self._enabled = False

    @property
    def name(self) -> str:
        return self._name

    @property
    def version(self) -> str:
        return self._version

    @property
    def description(self) -> str:
        return "Mock plugin for testing lifecycle events"

    @property
    def provides(self) -> list[ServiceKey[any]]:
        return [ServiceKey(f"svc.{self.name}")]

    @property
    def requires(self) -> list[ServiceKey[any]]:
        return []

    async def on_load(self, ctx: ServiceContext) -> None:
        self._loaded = True

    async def on_enable(self) -> None:
        self._enabled = True

    async def on_disable(self) -> None:
        self._enabled = False

    async def on_unload(self) -> None:
        self._loaded = False


class FailingPlugin(HarnessPlugin):
    @property
    def name(self) -> str:
        return "failing.plugin"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def description(self) -> str:
        return "Fails on enable"

    @property
    def provides(self) -> list[ServiceKey[any]]:
        return []

    @property
    def requires(self) -> list[ServiceKey[any]]:
        return []

    async def on_load(self, ctx: ServiceContext) -> None:
        pass

    async def on_enable(self) -> None:
        raise RuntimeError("Planned enable failure")


@pytest.mark.asyncio
async def test_lifecycle_event_emission_full_cycle():
    """Verify that PluginLifecycle emits typed events across the full lifecycle."""
    ctx = ServiceContext()
    bus = EventBus()
    ctx.attach_event_bus(bus)
    lifecycle = PluginLifecycle(ctx, event_bus=bus)

    emitted_types = []

    async def tracker(event: HarnessEvent) -> None:
        emitted_types.append(event.event_type.value)

    bus.on_all(tracker)

    plugin = MockDummyPlugin("test.lifecycle.plugin")

    # 1. Discover
    lifecycle.discover(plugin)
    await asyncio.sleep(0.01)
    assert EventType.PLUGIN_DISCOVERED.value in emitted_types

    # 2. Load
    await lifecycle.load(plugin.name)
    await asyncio.sleep(0.01)
    assert EventType.PLUGIN_LOADED.value in emitted_types

    # 3. Validate
    await lifecycle.validate(plugin.name)
    await asyncio.sleep(0.01)
    assert EventType.PLUGIN_VALIDATED.value in emitted_types

    # 4. Enable
    await lifecycle.enable(plugin.name)
    await asyncio.sleep(0.01)
    assert EventType.PLUGIN_ENABLED.value in emitted_types

    # 5. Disable
    await lifecycle.disable(plugin.name)
    await asyncio.sleep(0.01)
    assert EventType.PLUGIN_DISABLED.value in emitted_types

    # 6. Unload
    await lifecycle.unload(plugin.name)
    await asyncio.sleep(0.01)
    assert EventType.PLUGIN_UNLOADED.value in emitted_types


@pytest.mark.asyncio
async def test_lifecycle_event_emission_on_failure():
    """Verify that PluginLifecycle emits PLUGIN_ERROR event on load/enable failure."""
    ctx = ServiceContext()
    bus = EventBus()
    lifecycle = PluginLifecycle(ctx, event_bus=bus)

    emitted_events = []

    async def tracker(event: HarnessEvent) -> None:
        emitted_events.append(event)

    bus.on_all(tracker)

    fail_plugin = FailingPlugin()
    lifecycle.discover(fail_plugin)
    await lifecycle.load(fail_plugin.name)
    await lifecycle.validate(fail_plugin.name)

    with pytest.raises(RuntimeError, match="Planned enable failure"):
        await lifecycle.enable(fail_plugin.name)

    await asyncio.sleep(0.01)
    error_events = [e for e in bus.log if e.event_type == EventType.PLUGIN_ERROR]
    assert len(error_events) >= 1
    assert error_events[0].source == "failing.plugin"
    assert "Planned enable failure" in error_events[0].payload.get("error", "")


@pytest.mark.asyncio
async def test_ingestion_pipeline_telemetry(tmp_path: Path):
    """Verify that PluginIngestionPipeline and RepoFetcher emit typed ingestion events."""
    bus = EventBus()
    emitted = []

    async def tracker(event: HarnessEvent) -> None:
        emitted.append(event)

    bus.on_all(tracker)

    # Create dummy local plugin directory
    local_plugin = tmp_path / "sample_plugin"
    local_plugin.mkdir()
    (local_plugin / "plugin.json").write_text(
        json.dumps({
            "name": "sample_plugin",
            "version": "1.0.0",
            "description": "Test plugin",
            "language": "python",
            "entrypoint": "main.py",
        })
    )
    (local_plugin / "main.py").write_text(
        "def execute(task=''):\n    return {'status': 'ok'}\n"
    )

    pipeline = PluginIngestionPipeline(event_bus=bus, plugin_dir=tmp_path)
    plugin = await pipeline.ingest(local_plugin)

    await asyncio.sleep(0.01)
    event_types = [e.event_type for e in bus.log]
    assert EventType.REPO_FETCH_STARTED in event_types
    assert EventType.REPO_FETCH_COMPLETED in event_types
    assert EventType.REPO_INSPECTED in event_types
    assert EventType.REPO_CONVERTED in event_types
    assert plugin.name == "sample_plugin"


@pytest.mark.asyncio
async def test_agent_session_plugin_auto_wiring():
    """Verify AgentSessionPlugin automatically wires StorageBackedSessionStore when StorageService exists."""
    ctx = ServiceContext()
    bus = EventBus()
    ctx.attach_event_bus(bus)

    storage_plugin = StoragePlugin(db_path=":memory:")
    session_plugin = AgentSessionPlugin()

    lifecycle = PluginLifecycle(ctx, event_bus=bus)
    lifecycle.discover(storage_plugin)
    lifecycle.discover(session_plugin)

    await lifecycle.enable_all()

    session_mgr = ctx.optional(AGENT_SESSION_MANAGER_KEY)
    assert session_mgr is not None
    assert isinstance(session_mgr, AgentSessionManager)
    assert isinstance(session_mgr.store, StorageBackedSessionStore)

    # Create and verify persistent session
    sess = await session_mgr.create_session("Automated test task")
    assert sess.task == "Automated test task"

    fetched = await session_mgr.get_session(sess.session_id)
    assert fetched is not None
    assert fetched.session_id == sess.session_id


@pytest.mark.asyncio
async def test_runtime_sessions_and_export():
    """Verify HarnessRuntime automatically provisions sessions property and export helper."""
    async with HarnessRuntime.create(db_path=":memory:", auto_load_user_plugins=False) as rt:
        assert rt.sessions is not None
        assert isinstance(rt.sessions, AgentSessionManager)

        sess = await rt.sessions.create_session("Runtime task", metadata={"run": 1})
        await rt.sessions.record_step(sess.session_id, AgentStep(step_number=1, thought="Thinking"))
        await rt.sessions.complete_session(sess.session_id, "Completed successfully")

        md_export = await rt.export_session(sess.session_id, format="markdown")
        assert f"Agent Execution Session: `{sess.session_id}`" in md_export
        assert "Completed successfully" in md_export

        json_export = await rt.export_session(sess.session_id, format="json")
        data = json.loads(json_export)
        assert data["session_id"] == sess.session_id
        assert data["status"] == "completed"


@pytest.mark.asyncio
async def test_mcp_server_resources_and_prompts():
    """Verify HarnessMCPServer handles resources/list, resources/read, prompts/list, prompts/get."""
    registry = ToolRegistry()
    registry.register(ToolSpec(name="test_tool", description="Test", executor=lambda: {"res": 1}))

    server = HarnessMCPServer(tool_registry=registry)

    # 1. Initialize
    init_resp = await server.handle_request({"id": 1, "method": "initialize"})
    assert "capabilities" in init_resp["result"]
    assert "resources" in init_resp["result"]["capabilities"]
    assert "prompts" in init_resp["result"]["capabilities"]

    # 2. Resources List
    res_list = await server.handle_request({"id": 2, "method": "resources/list"})
    uris = [r["uri"] for r in res_list["result"]["resources"]]
    assert "harness://plugins/catalog" in uris
    assert "harness://system/status" in uris

    # 3. Resources Read
    res_read = await server.handle_request({
        "id": 3,
        "method": "resources/read",
        "params": {"uri": "harness://system/status"},
    })
    assert len(res_read["result"]["contents"]) == 1
    assert "test_tool" in res_read["result"]["contents"][0]["text"]

    # 4. Prompts List
    p_list = await server.handle_request({"id": 4, "method": "prompts/list"})
    prompt_names = [p["name"] for p in p_list["result"]["prompts"]]
    assert "agent_task" in prompt_names
    assert "plugin_review" in prompt_names

    # 5. Prompts Get
    p_get = await server.handle_request({
        "id": 5,
        "method": "prompts/get",
        "params": {"name": "agent_task", "arguments": {"task": "Write tests"}},
    })
    assert len(p_get["result"]["messages"]) == 1
    assert "Write tests" in p_get["result"]["messages"][0]["content"]["text"]


@pytest.mark.asyncio
async def test_ui_session_endpoints():
    """Verify FastAPI UI server session endpoints."""
    async with HarnessRuntime.create(db_path=":memory:", auto_load_user_plugins=False) as rt:
        app = create_app(rt)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Create session in runtime
            sess = await rt.sessions.create_session("UI test task")
            await rt.sessions.complete_session(sess.session_id, "UI Answer")

            # 1. GET /api/sessions
            r1 = await client.get("/api/sessions")
            assert r1.status_code == 200
            data1 = r1.json()
            assert data1["total"] >= 1
            s_ids = [s["session_id"] for s in data1["sessions"]]
            assert sess.session_id in s_ids

            # 2. GET /api/sessions/{id}
            r2 = await client.get(f"/api/sessions/{sess.session_id}")
            assert r2.status_code == 200
            data2 = r2.json()
            assert data2["status"] == "ok"
            assert data2["session"]["final_answer"] == "UI Answer"

            # 3. GET /api/sessions/{id}/export
            r3 = await client.get(f"/api/sessions/{sess.session_id}/export?format=markdown")
            assert r3.status_code == 200
            data3 = r3.json()
            assert data3["status"] == "ok"
            assert f"Agent Execution Session: `{sess.session_id}`" in data3["content"]
