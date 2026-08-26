"""Tests for built-in services: Storage, ToolRegistry, and LLM."""

from pathlib import Path

import pytest

from harness.kernel.context import ServiceContext
from harness.services.llm import (
    LLM_SERVICE_KEY,
    LLMPlugin,
)
from harness.services.storage import (
    STORAGE_SERVICE_KEY,
    SQLiteStorageService,
    StoragePlugin,
)
from harness.services.tools import (
    TOOL_REGISTRY_KEY,
    ToolRegistry,
    ToolRegistryPlugin,
)


@pytest.mark.unit
@pytest.mark.asyncio
class TestStorageService:
    async def test_key_value_crud(self) -> None:
        storage = SQLiteStorageService(":memory:")
        assert await storage.get("nonexistent") is None
        assert not await storage.exists("foo")

        await storage.set("foo", {"bar": 123, "active": True})
        assert await storage.exists("foo")
        assert await storage.get("foo") == {"bar": 123, "active": True}

        # Update
        await storage.set("foo", "updated_string")
        assert await storage.get("foo") == "updated_string"

        # List keys
        await storage.set("foo_2", 456)
        await storage.set("baz", 789)
        keys = await storage.list_keys(prefix="foo")
        assert set(keys) == {"foo", "foo_2"}

        # Delete
        assert await storage.delete("baz") is True
        assert await storage.delete("nonexistent") is False
        assert not await storage.exists("baz")

        # Clear
        count = await storage.clear()
        assert count == 2
        assert len(await storage.list_keys()) == 0
        storage.close()

    async def test_storage_plugin_lifecycle(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test_store.db"
        plugin = StoragePlugin(db_path=db_path)
        ctx = ServiceContext()

        assert STORAGE_SERVICE_KEY in plugin.provides
        assert plugin.trusted is True


        await plugin.on_load(ctx)
        assert ctx.has(STORAGE_SERVICE_KEY)
        storage = ctx.require(STORAGE_SERVICE_KEY)

        await storage.set("plugin_test", "works")
        assert await storage.get("plugin_test") == "works"

        await plugin.on_unload()


@pytest.mark.unit
@pytest.mark.asyncio
class TestToolRegistry:
    async def test_tool_registration_and_invoke(self) -> None:
        registry = ToolRegistry()

        async def sample_tool(x: int, y: int = 1) -> int:
            return x + y

        registry.register(
            name="math.add",
            description="Add two numbers",
            executor=sample_tool,
            parameters_schema={
                "type": "object",
                "properties": {
                    "x": {"type": "integer"},
                    "y": {"type": "integer", "default": 1},
                },
                "required": ["x"],
            },
            provider="math-plugin",
        )

        assert "math.add" in registry
        assert registry.count == 1

        # Invoke
        result = await registry.invoke("math.add", {"x": 5, "y": 10})
        assert result == {"status": "ok", "result": 15}

        # Default argument
        result_default = await registry.invoke("math.add", {"x": 5})
        assert result_default == {"status": "ok", "result": 6}

        # Nonexistent tool
        missing = await registry.invoke("nonexistent")
        assert missing["status"] == "error"

        # Export schemas
        schemas = registry.get_schemas()
        assert len(schemas) == 1
        assert schemas[0]["function"]["name"] == "math.add"

        # Unregister by provider
        removed = registry.unregister_all_from("math-plugin")
        assert removed == ["math.add"]
        assert registry.count == 0

    async def test_tool_enable_disable_lifecycle(self) -> None:
        registry = ToolRegistry()

        async def dummy_tool() -> str:
            return "executed"

        registry.register(name="test.tool1", description="Tool 1", executor=dummy_tool, provider="p1")
        registry.register(name="test.tool2", description="Tool 2", executor=dummy_tool, provider="p2")

        assert registry.is_tool_enabled("test.tool1") is True
        assert registry.is_tool_enabled("test.tool2") is True
        assert len(registry.list_tools(enabled_only=True)) == 2

        # Disable tool1
        assert registry.disable_tool("test.tool1") is True
        assert registry.is_tool_enabled("test.tool1") is False
        assert len(registry.list_tools(enabled_only=True)) == 1
        assert len(registry.list_tools(enabled_only=False)) == 2

        # Schemas should filter out disabled tools
        schemas = registry.get_schemas(enabled_only=True)
        assert len(schemas) == 1
        assert schemas[0]["function"]["name"] == "test.tool2"

        # Invoke disabled tool returns error
        inv = await registry.invoke("test.tool1")
        assert inv["status"] == "error"
        assert "disabled" in inv["error"]

        # Toggle tool1 back on
        assert registry.toggle_tool("test.tool1") is True
        assert registry.is_tool_enabled("test.tool1") is True

        inv_ok = await registry.invoke("test.tool1")
        assert inv_ok == {"status": "ok", "result": "executed"}

    async def test_tool_telemetry_and_schema_validation(self) -> None:
        import asyncio

        from harness.events.bus import EventBus
        from harness.events.types import EventType, HarnessEvent

        bus = EventBus()
        events: list[HarnessEvent] = []

        async def capture_event(e: HarnessEvent) -> None:
            events.append(e)

        bus.on_all(capture_event)
        registry = ToolRegistry(event_bus=bus)

        async def slow_or_fast_tool(delay: float = 0.0) -> str:
            if delay > 0:
                await asyncio.sleep(delay)
            return "done"

        registry.register(
            name="test.tool",
            description="Test tool",
            executor=slow_or_fast_tool,
            parameters_schema={
                "type": "object",
                "properties": {"delay": {"type": "number"}},
                "required": ["delay"],
            },
            provider="test-provider",
        )

        # 1. Missing required field -> schema error event
        res_missing = await registry.invoke("test.tool", {})
        assert res_missing["status"] == "error"
        assert "Missing required parameter" in res_missing["error"]
        assert any(e.event_type == EventType.TOOL_ERROR for e in events)

        events.clear()

        # 2. Successful call -> TOOL_INVOKED & TOOL_RESULT
        res_ok = await registry.invoke("test.tool", {"delay": 0.0})
        assert res_ok == {"status": "ok", "result": "done"}
        assert len(events) == 2
        assert events[0].event_type == EventType.TOOL_INVOKED
        assert events[1].event_type == EventType.TOOL_RESULT

        events.clear()

        # 3. Timeout -> TOOL_ERROR with timeout message
        res_timeout = await registry.invoke("test.tool", {"delay": 0.5}, timeout=0.05)
        assert res_timeout["status"] == "error"
        assert "timed out" in res_timeout["error"]
        assert any(e.event_type == EventType.TOOL_ERROR for e in events)

    async def test_tool_plugin_lifecycle(self) -> None:
        plugin = ToolRegistryPlugin()
        ctx = ServiceContext()

        assert plugin.provides == [TOOL_REGISTRY_KEY]
        await plugin.on_load(ctx)
        assert ctx.has(TOOL_REGISTRY_KEY)
        await plugin.on_unload()

    async def test_custom_interceptor_pipeline(self) -> None:
        from collections.abc import Awaitable, Callable
        from typing import Any
        from harness.services.tools import ToolExecutionContext, ToolInterceptor

        audit_log: list[str] = []

        class AuditInterceptor(ToolInterceptor):
            async def intercept(
                self,
                ctx: ToolExecutionContext,
                next_handler: Callable[[ToolExecutionContext], Awaitable[dict[str, Any]]],
            ) -> dict[str, Any]:
                audit_log.append(f"before:{ctx.name}")
                res = await next_handler(ctx)
                audit_log.append(f"after:{ctx.name}:{res.get('status')}")
                return res

        registry = ToolRegistry()
        registry.add_interceptor(AuditInterceptor())

        async def greet(name: str) -> str:
            return f"Hello, {name}!"

        registry.register(
            name="greet",
            description="Greet someone",
            executor=greet,
            parameters_schema={
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"],
            },
        )

        res = await registry.invoke("greet", {"name": "Alice"})
        assert res == {"status": "ok", "result": "Hello, Alice!"}
        assert audit_log == ["before:greet", "after:greet:ok"]


@pytest.mark.unit
@pytest.mark.asyncio
class TestLLMPlugin:
    async def test_llm_plugin_lifecycle(self) -> None:
        plugin = LLMPlugin(default_model="gpt-4o-mini")
        ctx = ServiceContext()

        assert plugin.provides == [LLM_SERVICE_KEY]
        assert plugin.trusted is True

        await plugin.on_load(ctx)
        assert ctx.has(LLM_SERVICE_KEY)
        await plugin.on_unload()
