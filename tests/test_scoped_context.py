"""Tests for ScopedServiceContext and lifecycle state management."""

from __future__ import annotations

import pytest

from harness.kernel.context import (
    ScopedServiceContext,
    ServiceContext,
    ServiceKey,
    ServiceNotFoundError,
)
from harness.kernel.lifecycle import PluginLifecycle, PluginState
from harness.plugins.base import HarnessPlugin


class MockPlugin(HarnessPlugin):
    def __init__(self, name: str, provides_key: ServiceKey[str], value: str) -> None:
        self._name = name
        self._key = provides_key
        self._value = value

    @property
    def name(self) -> str:
        return self._name

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def provides(self) -> list[ServiceKey[str]]:
        return [self._key]

    async def on_load(self, ctx: ServiceContext) -> None:
        ctx.provide(self._key, self._value)


@pytest.mark.unit
@pytest.mark.asyncio
class TestScopedServiceContext:
    async def test_scoped_context_provides_and_tracking(self) -> None:
        root_ctx = ServiceContext()
        scoped_ctx = root_ctx.for_plugin("my_plugin")

        assert isinstance(scoped_ctx, ScopedServiceContext)
        assert scoped_ctx.plugin_name == "my_plugin"

        key = ServiceKey[str]("test.service")
        scoped_ctx.provide(key, "my_val")

        assert "test.service" in scoped_ctx.provided_keys
        assert root_ctx.has(key)
        assert root_ctx.require(key) == "my_val"
        assert root_ctx.list_services()["test.service"] == "my_plugin"

    async def test_lifecycle_automatic_scoping_and_revocation(self) -> None:
        root_ctx = ServiceContext()
        lifecycle = PluginLifecycle(root_ctx)

        key = ServiceKey[str]("service.val")
        plugin = MockPlugin("plugin_a", key, "hello_a")
        lifecycle.discover(plugin)

        # Discovered -> Loaded
        await lifecycle.load("plugin_a")
        assert root_ctx.has(key)
        assert root_ctx.list_services()["service.val"] == "plugin_a"

        # Validate -> Enable
        await lifecycle.validate("plugin_a")
        await lifecycle.enable("plugin_a")
        assert lifecycle.get_state("plugin_a") == PluginState.ENABLED

        # Disable
        await lifecycle.disable("plugin_a")
        assert lifecycle.get_state("plugin_a") == PluginState.DISABLED

        # Unload -> verify automatic revocation
        await lifecycle.unload("plugin_a")
        assert not root_ctx.has(key)
        with pytest.raises(ServiceNotFoundError):
            root_ctx.require(key)
