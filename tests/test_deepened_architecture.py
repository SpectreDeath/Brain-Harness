"""Tests for deepened architecture seams: lifecycle reload, batch storage, tool mount, and introspection."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import pytest

from harness.creator.dynamic import DynamicPluginBuilder, RuntimeIntrospector
from harness.kernel.context import ServiceContext, ServiceKey
from harness.kernel.lifecycle import PluginLifecycle, PluginState
from harness.plugins.base import HarnessPlugin
from harness.plugins.loader import PluginLoader
from harness.plugins.tool_mount import ToolMountMixin
from harness.plugins.watcher import PluginFileEventHandler
from harness.services.storage import SQLiteStorageService, StorageService
from harness.services.tools import ToolRegistry, ToolSpec


class SimpleTestPlugin(HarnessPlugin):
    def __init__(self, name: str = "test.simple", version: str = "0.1.0") -> None:
        self._name = name
        self._version = version
        self._load_count = 0
        self._enable_count = 0
        self._unload_count = 0

    @property
    def name(self) -> str:
        return self._name

    @property
    def version(self) -> str:
        return self._version

    @property
    def description(self) -> str:
        return f"Simple test plugin {self.name}"

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [ServiceKey(f"service.{self.name}")]

    @property
    def trusted(self) -> bool:
        return True

    async def on_load(self, ctx: ServiceContext) -> None:
        self._load_count += 1
        ctx.provide(ServiceKey(f"service.{self.name}"), f"instance_{self.version}", provider=self.name)

    async def on_enable(self) -> None:
        self._enable_count += 1

    async def on_disable(self) -> None:
        pass

    async def on_unload(self) -> None:
        self._unload_count += 1


class ToolMountedPlugin(ToolMountMixin, HarnessPlugin):
    def __init__(self, name: str = "test.tool_mounted") -> None:
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def description(self) -> str:
        return "Test plugin with ToolMountMixin"

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return self.tool_mount_requires()

    @property
    def trusted(self) -> bool:
        return True

    async def on_load(self, ctx: ServiceContext) -> None:
        self.setup_tool_mount(ctx, self.name)

    async def on_enable(self) -> None:
        spec = ToolSpec(
            name=f"{self.name}.echo",
            description="Echoes input",
            executor=lambda msg: f"echo: {msg}",
            provider=self.name,
        )
        await self.mount_tools([spec])

    async def on_disable(self) -> None:
        await self.unmount_tools()

    async def on_unload(self) -> None:
        self.teardown_tool_mount()


@pytest.mark.unit
class TestLifecycleReload:
    """Test PluginLifecycle.reload() atomic reload and state transitions."""

    @pytest.mark.asyncio
    async def test_reload_new_plugin(self) -> None:
        ctx = ServiceContext()
        lc = PluginLifecycle(ctx)
        p = SimpleTestPlugin(name="test.reload1", version="1.0.0")

        # Reloading an untracked plugin discovers and enables it
        success = await lc.reload(p)
        assert success is True
        assert lc.get_state("test.reload1") == PluginState.ENABLED
        assert ctx.require(ServiceKey("service.test.reload1")) == "instance_1.0.0"

    @pytest.mark.asyncio
    async def test_reload_already_enabled_plugin(self) -> None:
        ctx = ServiceContext()
        lc = PluginLifecycle(ctx)
        p1 = SimpleTestPlugin(name="test.reload2", version="1.0.0")

        # Initial register and enable
        await lc.register_and_enable(p1)
        assert lc.get_state("test.reload2") == PluginState.ENABLED
        assert ctx.require(ServiceKey("service.test.reload2")) == "instance_1.0.0"

        # Hot-reload with updated plugin instance
        p2 = SimpleTestPlugin(name="test.reload2", version="2.0.0")
        success = await lc.reload(p2)
        assert success is True
        assert lc.get_state("test.reload2") == PluginState.ENABLED
        # Context should reflect the reloaded instance
        assert ctx.require(ServiceKey("service.test.reload2")) == "instance_2.0.0"
        assert p1._unload_count == 1
        assert p2._load_count == 1


@pytest.mark.unit
class TestStorageBatchOperations:
    """Test high-throughput batch operations on StorageService."""

    @pytest.mark.asyncio
    async def test_sqlite_batch_crud(self) -> None:
        storage = SQLiteStorageService(":memory:")

        # 1. set_many
        data = {
            "config:theme": "dark",
            "config:lang": "python",
            "user:101": {"name": "Alice", "role": "admin"},
            "user:102": {"name": "Bob", "role": "editor"},
            "temp:cache": 42,
        }
        await storage.set_many(data)

        # 2. get_many
        retrieved = await storage.get_many(["config:theme", "user:101", "nonexistent"])
        assert retrieved["config:theme"] == "dark"
        assert retrieved["user:101"] == {"name": "Alice", "role": "admin"}
        assert "nonexistent" not in retrieved

        # 3. get_all with prefix
        configs = await storage.get_all(prefix="config:")
        assert len(configs) == 2
        assert configs["config:theme"] == "dark"
        assert configs["config:lang"] == "python"

        users = await storage.get_all(prefix="user:")
        assert len(users) == 2
        assert users["user:101"]["name"] == "Alice"
        assert users["user:102"]["name"] == "Bob"

        # 4. delete_many
        deleted_count = await storage.delete_many(["temp:cache", "config:theme", "nonexistent"])
        assert deleted_count == 2
        assert await storage.exists("temp:cache") is False
        assert await storage.exists("config:theme") is False
        assert await storage.exists("config:lang") is True

        storage.close()

    @pytest.mark.asyncio
    async def test_empty_batch_operations(self) -> None:
        storage = SQLiteStorageService(":memory:")
        await storage.set_many({})
        assert await storage.get_many([]) == {}
        assert await storage.delete_many([]) == 0
        storage.close()


@pytest.mark.unit
class TestToolMountProtocol:
    """Test ToolMountMixin setup and unmount protocol."""

    @pytest.mark.asyncio
    async def test_tool_mount_and_unmount(self) -> None:
        ctx = ServiceContext()
        tool_reg = ToolRegistry()
        ctx.provide(ServiceKey("tools.registry"), tool_reg, provider="core")

        lc = PluginLifecycle(ctx)
        plugin = ToolMountedPlugin("plugin.greeter")

        await lc.register_and_enable(plugin)
        assert tool_reg.count == 1
        assert "plugin.greeter.echo" in tool_reg

        # Invoke mounted tool
        res = await tool_reg.invoke("plugin.greeter.echo", {"msg": "hello"})
        assert res["status"] == "ok"
        assert res["result"] == "echo: hello"

        # Disable unmounts tools
        await lc.disable("plugin.greeter")
        assert tool_reg.count == 0

        # Unload tears down
        await lc.unload("plugin.greeter")


@pytest.mark.unit
class TestIntrospectionObservability:
    """Test RuntimeIntrospector tool topology and status reports."""

    @pytest.mark.asyncio
    async def test_introspector_status_and_mermaid_graph(self) -> None:
        ctx = ServiceContext()
        tool_reg = ToolRegistry()
        ctx.provide(ServiceKey("tools.registry"), tool_reg, provider="core")

        lc = PluginLifecycle(ctx)
        plugin = ToolMountedPlugin("plugin.observed")
        await lc.register_and_enable(plugin)

        introspector = RuntimeIntrospector(ctx, lc, tool_reg)
        report = introspector.get_status_report()

        assert "tools_by_provider" in report
        assert "plugin.observed" in report["tools_by_provider"]
        assert "plugin.observed.echo" in report["tools_by_provider"]["plugin.observed"]

        # Mermaid without tools
        graph_no_tools = introspector.generate_mermaid_graph(include_tools=False)
        assert "T_plugin_observed_echo" not in graph_no_tools

        # Mermaid with tools
        graph_with_tools = introspector.generate_mermaid_graph(include_tools=True)
        assert "T_plugin_observed_echo" in graph_with_tools
        assert "P_plugin_observed -.->|exposes| T_plugin_observed_echo" in graph_with_tools
