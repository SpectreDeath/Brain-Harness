"""Tests for deepened seams in EventBus, PluginLifecycle, and ToolRegistry."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import pytest

from harness.events.bus import EventBus
from harness.events.types import EventType, HarnessEvent, plugin_event
from harness.kernel.context import ServiceContext, ServiceKey
from harness.kernel.lifecycle import PluginLifecycle, PluginState
from harness.plugins.base import HarnessPlugin
from harness.services.tools import ToolRegistry, ToolSpec


class MockPlugin(HarnessPlugin):
    def __init__(self, name: str, version: str = "1.0.0", fail_on_enable: bool = False) -> None:
        self._name = name
        self._version = version
        self._fail_on_enable = fail_on_enable
        self.key = ServiceKey[str](f"svc.{name}")

    @property
    def name(self) -> str:
        return self._name

    @property
    def version(self) -> str:
        return self._version

    @property
    def description(self) -> str:
        return f"Mock plugin {self._name}"

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [self.key]

    async def on_load(self, ctx: ServiceContext) -> None:
        ctx.provide(self.key, f"value-{self._name}", provider=self.name)

    async def on_enable(self) -> None:
        if self._fail_on_enable:
            raise RuntimeError(f"Simulated failure enabling {self._name}")

    async def on_disable(self) -> None:
        pass

    async def on_unload(self) -> None:
        pass


@pytest.mark.unit
class TestEventBusDeepenedSeams:
    @pytest.mark.asyncio
    async def test_event_bus_live_streaming(self) -> None:
        bus = EventBus()
        received: list[HarnessEvent] = []

        async def _consumer() -> None:
            async for evt in bus.stream(replay_history=False):
                received.append(evt)
                if len(received) >= 2:
                    break

        task = asyncio.create_task(_consumer())
        await asyncio.sleep(0.01)

        # Emit events
        e1 = plugin_event(EventType.PLUGIN_ENABLED, "plug-1")
        e2 = plugin_event(EventType.PLUGIN_DISABLED, "plug-1")
        await bus.emit(e1)
        await bus.emit(e2)

        await asyncio.wait_for(task, timeout=2.0)
        assert len(received) == 2
        assert received[0].event_type == EventType.PLUGIN_ENABLED
        assert received[1].event_type == EventType.PLUGIN_DISABLED

    @pytest.mark.asyncio
    async def test_event_bus_stream_filtering_and_replay(self) -> None:
        bus = EventBus()
        # Historical events
        h1 = plugin_event(EventType.PLUGIN_DISCOVERED, "plug-a")
        h2 = plugin_event(EventType.PLUGIN_ENABLED, "plug-b")
        await bus.emit(h1)
        await bus.emit(h2)

        received: list[HarnessEvent] = []

        async def _consumer() -> None:
            async for evt in bus.stream(event_type=EventType.PLUGIN_ENABLED, replay_history=True):
                received.append(evt)
                if len(received) >= 2:
                    break

        task = asyncio.create_task(_consumer())
        await asyncio.sleep(0.01)

        # Emit matching and non-matching live events
        await bus.emit(plugin_event(EventType.PLUGIN_DISCOVERED, "plug-c"))
        await bus.emit(plugin_event(EventType.PLUGIN_ENABLED, "plug-c"))

        await asyncio.wait_for(task, timeout=2.0)
        assert len(received) == 2
        assert received[0].source == "plug-b"
        assert received[1].source == "plug-c"

    def test_event_bus_lazy_iter_log_file(self, tmp_path: Path) -> None:
        log_file = tmp_path / "events.jsonl"
        bus = EventBus(log_file=log_file)

        # Write events synchronously / emit
        e1 = plugin_event(EventType.PLUGIN_DISCOVERED, "p1")
        e2 = plugin_event(EventType.PLUGIN_LOADED, "p1")
        e3 = plugin_event(EventType.PLUGIN_ENABLED, "p1")
        bus.emit_sync(e1)
        bus.emit_sync(e2)
        bus.emit_sync(e3)

        # Test lazy generator
        events = list(EventBus.iter_log_file(log_file))
        assert len(events) == 3
        assert events[0].id == e1.id

        # Test filtered lazy reading
        filtered = list(EventBus.iter_log_file(log_file, event_type=EventType.PLUGIN_ENABLED))
        assert len(filtered) == 1
        assert filtered[0].id == e3.id

        # Test tail limit
        limited = list(EventBus.iter_log_file(log_file, limit=2))
        assert len(limited) == 2
        assert limited[0].id == e2.id
        assert limited[1].id == e3.id

    def test_harness_event_to_dict(self) -> None:
        evt = plugin_event(EventType.PLUGIN_ENABLED, "my-plugin")
        d = evt.to_dict()
        assert d["id"] == evt.id
        assert d["event_type"] == "plugin.enabled"
        assert d["source"] == "my-plugin"
        assert "timestamp" in d


@pytest.mark.unit
@pytest.mark.asyncio
class TestPluginLifecycleDeepenedSeams:
    async def test_register_and_enable_happy_path(self) -> None:
        ctx = ServiceContext()
        lifecycle = PluginLifecycle(ctx)
        plugin = MockPlugin("test-plugin")

        success = await lifecycle.register_and_enable(plugin)
        assert success is True
        assert lifecycle.get_state("test-plugin") == PluginState.ENABLED
        assert ctx.has(plugin.key)
        assert ctx.require(plugin.key) == "value-test-plugin"

    async def test_ensure_enabled_from_various_states(self) -> None:
        ctx = ServiceContext()
        lifecycle = PluginLifecycle(ctx)
        plugin = MockPlugin("stateful-plugin")

        # Start by discovering
        lifecycle.discover(plugin)
        assert lifecycle.get_state("stateful-plugin") == PluginState.DISCOVERED

        # Advance directly to enabled
        success = await lifecycle.ensure_enabled("stateful-plugin")
        assert success is True
        assert lifecycle.get_state("stateful-plugin") == PluginState.ENABLED

        # Idempotent call when already enabled
        assert await lifecycle.ensure_enabled("stateful-plugin") is True

        # Disable, then ensure_enabled
        await lifecycle.disable("stateful-plugin")
        assert lifecycle.get_state("stateful-plugin") == PluginState.DISABLED
        assert await lifecycle.ensure_enabled("stateful-plugin") is True
        assert lifecycle.get_state("stateful-plugin") == PluginState.ENABLED

    async def test_register_and_enable_failure_handling(self) -> None:
        ctx = ServiceContext()
        lifecycle = PluginLifecycle(ctx)
        plugin = MockPlugin("failing-plugin", fail_on_enable=True)

        success = await lifecycle.register_and_enable(plugin)
        assert success is False
        assert lifecycle.get_state("failing-plugin") == PluginState.ERROR
        assert lifecycle.get_error("failing-plugin") is not None


@pytest.mark.unit
class TestToolRegistryDeepenedSeams:
    def test_to_catalog_and_to_openai_tools(self) -> None:
        registry = ToolRegistry()

        def sample_add(a: int, b: int) -> int:
            """Add two numbers together."""
            return a + b

        spec = ToolSpec.from_callable(sample_add, name="math.add", provider="math.plugin")
        registry.register(spec)

        # Test ToolSpec to_dict
        spec_dict = spec.to_dict()
        assert spec_dict["name"] == "math.add"
        assert spec_dict["provider"] == "math.plugin"
        assert "a" in spec_dict["parameters"]
        assert "b" in spec_dict["parameters"]

        # Test ToolRegistry to_catalog
        catalog = registry.to_catalog()
        assert len(catalog) == 1
        assert catalog[0]["name"] == "math.add"

        # Test ToolRegistry to_openai_tools
        openai_tools = registry.to_openai_tools()
        assert len(openai_tools) == 1
        assert openai_tools[0]["type"] == "function"
        assert openai_tools[0]["function"]["name"] == "math.add"
        assert "description" in openai_tools[0]["function"]

        # Test ToolSpec to_mcp_tool & ToolRegistry to_mcp_tools
        mcp_tool = spec.to_mcp_tool()
        assert mcp_tool["name"] == "math.add"
        assert mcp_tool["description"] == "Add two numbers together."
        assert "inputSchema" in mcp_tool

        mcp_tools = registry.to_mcp_tools()
        assert len(mcp_tools) == 1
        assert mcp_tools[0]["name"] == "math.add"


@pytest.mark.unit
class TestAgentTelemetryAndTrajectorySeams:
    def test_agent_and_llm_event_factories(self) -> None:
        from harness.events.types import EventType, agent_event, llm_event

        evt1 = agent_event(
            EventType.AGENT_TASK_STARTED,
            agent_name="agent.react",
            task="Analyze repo",
            max_steps=5,
        )
        assert evt1.event_type == EventType.AGENT_TASK_STARTED
        assert evt1.source == "agent.react"
        assert evt1.payload["task"] == "Analyze repo"
        assert evt1.payload["max_steps"] == 5

        evt2 = llm_event(
            EventType.LLM_REQUEST,
            source="agent.react",
            step=1,
            message_count=3,
        )
        assert evt2.event_type == EventType.LLM_REQUEST
        assert evt2.source == "agent.react"
        assert evt2.payload["step"] == 1

    def test_agent_trajectory_and_result_to_dict(self) -> None:
        from harness.agent.base import AgentStep, AgentTrajectory

        traj = AgentTrajectory(task="Sample task", metadata={"env": "test"})
        step = AgentStep(
            step_number=1,
            thought="Thinking...",
            action="math.add",
            action_input={"a": 1, "b": 2},
            observation=3,
        )
        traj.add_step(step)
        traj.mark_completed("Answer is 3")

        # Test AgentStep to_dict
        step_d = step.to_dict()
        assert step_d["step_number"] == 1
        assert step_d["action"] == "math.add"
        assert step_d["observation"] == 3

        # Test AgentTrajectory to_dict
        traj_d = traj.to_dict()
        assert traj_d["task"] == "Sample task"
        assert traj_d["status"] == "completed"
        assert traj_d["final_answer"] == "Answer is 3"
        assert len(traj_d["steps"]) == 1

        # Test AgentTrajectory to_summary
        sum_d = traj.to_summary()
        assert sum_d["task"] == "Sample task"
        assert sum_d["status"] == "completed"
        assert sum_d["steps_count"] == 1

        # Test AgentTaskResult to_dict
        result = traj.to_result()
        res_d = result.to_dict()
        assert res_d["task"] == "Sample task"
        assert res_d["final_answer"] == "Answer is 3"
        assert len(res_d["steps"]) == 1


@pytest.mark.unit
@pytest.mark.asyncio
class TestMCPServerAndUIServerDeepenedSeams:
    async def test_mcp_server_tools_list_uses_registry_mcp_seam(self) -> None:
        from harness.mcp.server import HarnessMCPServer

        registry = ToolRegistry()
        def demo_fn(x: str) -> str:
            """Echo text."""
            return x

        registry.register(ToolSpec.from_callable(demo_fn, name="demo.echo"))
        mcp_server = HarnessMCPServer(registry)

        resp = await mcp_server.handle_request({"id": 1, "method": "tools/list"})
        assert resp["id"] == 1
        assert "result" in resp
        tools = resp["result"]["tools"]
        assert len(tools) == 1
        assert tools[0]["name"] == "demo.echo"
        assert "inputSchema" in tools[0]

    async def test_ui_server_events_endpoint_with_runtime(self) -> None:
        from httpx import ASGITransport, AsyncClient
        from harness.events.types import EventType, HarnessEvent
        from harness.kernel.runtime import HarnessRuntime
        from harness.ui.server import create_app

        async with HarnessRuntime.create(db_path=":memory:") as rt:
            await rt.event_bus.emit(HarnessEvent(event_type=EventType.HARNESS_STARTED))
            app = create_app(rt)
            transport = ASGITransport(app=app)

            async with AsyncClient(transport=transport, base_url="http://test") as client:
                res = await client.get("/api/events")
                assert res.status_code == 200
                events = res.json()
                assert len(events) >= 1
                assert any(e["event_type"] == EventType.HARNESS_STARTED.value for e in events)

