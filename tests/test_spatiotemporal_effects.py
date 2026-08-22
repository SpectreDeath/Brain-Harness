"""Unit and integration tests for Spatiotemporal Composability principles.

Tests:
1. Revertible effects and LIFO accumulator composition (Theorem 7, Theorem 16).
2. Early self-disposal of individual effects.
3. Scoped context effect tracking and disposal.
4. Event subscription effect tracking via ctx.subscribe().
5. Guarded dependency withdrawal (Theorem 63 & Definition 50).
6. Coeffect satisfaction predicate (Definition 24, σ ⊧ d).
7. ToolMountMixin automatic effect unmounting.
"""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from harness.events.bus import EventBus
from harness.events.types import EventType, HarnessEvent
from harness.kernel.context import ServiceContext, ServiceKey
from harness.kernel.lifecycle import PluginLifecycle, PluginState
from harness.plugins.base import HarnessPlugin
from harness.plugins.tool_mount import ToolMountMixin
from harness.services.tools import ToolRegistry, ToolSpec


# --- Test Helpers & Mock Plugins ---


class SimpleProviderPlugin(HarnessPlugin):
    def __init__(self, name: str = "provider.service") -> None:
        self._name = name
        self.service_key: ServiceKey[dict[str, Any]] = ServiceKey(f"svc.{name}")
        self.teardown_log: list[str] = []

    @property
    def name(self) -> str:
        return self._name

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [self.service_key]

    async def on_load(self, ctx: ServiceContext) -> None:
        ctx.provide(self.service_key, {"status": "ok", "provider": self._name})

    async def on_disable(self) -> None:
        self.teardown_log.append("provider.disabled")

    async def on_unload(self) -> None:
        self.teardown_log.append("provider.unloaded")


class DependentConsumerPlugin(HarnessPlugin):
    def __init__(
        self,
        name: str = "consumer.service",
        provider_key: ServiceKey[Any] | None = None,
    ) -> None:
        self._name = name
        self.provider_key = provider_key or ServiceKey("svc.provider.service")
        self.teardown_observed_service_state: list[Any] = []
        self._ctx: ServiceContext | None = None

    @property
    def name(self) -> str:
        return self._name

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return [self.provider_key]

    async def on_load(self, ctx: ServiceContext) -> None:
        self._ctx = ctx

    async def on_disable(self) -> None:
        # Crucial test for Theorem 63: during disable, provider's service MUST still be accessible
        if self._ctx is not None and self._ctx.has(self.provider_key):
            svc = self._ctx.require(self.provider_key)
            self.teardown_observed_service_state.append(svc)
        else:
            self.teardown_observed_service_state.append("MISSING_SERVICE")

    async def on_unload(self) -> None:
        if self._ctx is not None and self._ctx.has(self.provider_key):
            svc = self._ctx.require(self.provider_key)
            self.teardown_observed_service_state.append(svc)
        else:
            self.teardown_observed_service_state.append("MISSING_SERVICE")


# --- Tests ---


@pytest.mark.unit
def test_revertible_effect_lifo_accumulator() -> None:
    """Test that ctx.effect records inverses and dispose() runs them in LIFO order."""
    ctx = ServiceContext()
    order: list[int] = []

    def effect_1() -> Any:
        order.append(1)
        return lambda: order.append(-1)

    def effect_2() -> Any:
        order.append(2)
        return lambda: order.append(-2)

    def effect_3() -> Any:
        order.append(3)
        return lambda: order.append(-3)

    ctx.effect(effect_1)
    ctx.effect(effect_2)
    ctx.effect(effect_3)

    assert order == [1, 2, 3]

    # Dispose should execute inverses in reverse (LIFO: -3, -2, -1)
    asyncio.run(ctx.dispose())
    assert order == [1, 2, 3, -3, -2, -1]


@pytest.mark.unit
def test_revertible_effect_early_self_disposal() -> None:
    """Test that an individual effect can be reverted early via its disposer closure."""
    ctx = ServiceContext()
    log: list[str] = []

    def effect_a() -> Any:
        log.append("apply_a")
        return lambda: log.append("revert_a")

    def effect_b() -> Any:
        log.append("apply_b")
        return lambda: log.append("revert_b")

    disp_a = ctx.effect(effect_a)
    _ = ctx.effect(effect_b)
    assert log == ["apply_a", "apply_b"]

    # Revert A early
    disp_a()
    assert log == ["apply_a", "apply_b", "revert_a"]

    # Disposing context now should only run B's inverse
    asyncio.run(ctx.dispose())
    assert log == ["apply_a", "apply_b", "revert_a", "revert_b"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_event_subscription_effect_tracking() -> None:
    """Test that ctx.subscribe() automatically tracks handler unregistration on dispose."""
    bus = EventBus()
    ctx = ServiceContext(event_bus=bus)
    received: list[str] = []

    async def _handler(evt: HarnessEvent) -> None:
        received.append(evt.source)

    ctx.subscribe(EventType.PLUGIN_ENABLED, _handler)
    assert bus.handler_count == 1

    await bus.emit(HarnessEvent(event_type=EventType.PLUGIN_ENABLED, source="p1"))
    assert received == ["p1"]

    # Context disposal should automatically unsubscribe handler
    await ctx.dispose()
    assert bus.handler_count == 0

    await bus.emit(HarnessEvent(event_type=EventType.PLUGIN_ENABLED, source="p2"))
    assert received == ["p1"]  # No new event received


@pytest.mark.unit
@pytest.mark.asyncio
async def test_scoped_context_disposal() -> None:
    """Test that ScopedServiceContext.dispose() clears both local effects and parent registrations."""
    parent_ctx = ServiceContext()
    scoped_ctx = parent_ctx.for_plugin("test-plugin")
    key = ServiceKey[str]("test.service")

    scoped_ctx.provide(key, "my_val")
    assert parent_ctx.has(key)
    assert parent_ctx.require(key) == "my_val"

    await scoped_ctx.dispose()
    assert not parent_ctx.has(key)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_guarded_withdrawal_ordering_theorem_63() -> None:
    """Test Guarded Withdrawal: unloading provider A drains dependent consumer B first.

    Consumer B retains valid access to provider A's service during B's teardown,
    and A's service is revoked only after B is inactive (Theorem 63).
    """
    ctx = ServiceContext()
    lifecycle = PluginLifecycle(ctx)

    provider = SimpleProviderPlugin("db_provider")
    consumer = DependentConsumerPlugin("auth_consumer", provider.service_key)

    # Discover and enable both in topological order
    lifecycle.discover(provider)
    lifecycle.discover(consumer)

    assert await lifecycle.ensure_enabled(provider.name)
    assert await lifecycle.ensure_enabled(consumer.name)

    assert lifecycle.get_state(provider.name) == PluginState.ENABLED
    assert lifecycle.get_state(consumer.name) == PluginState.ENABLED

    # Unload provider: Guarded withdrawal should drain consumer first
    await lifecycle.unload(provider.name)

    assert lifecycle.get_state(consumer.name) == PluginState.DISABLED
    assert lifecycle.get_state(provider.name) == PluginState.UNLOADED

    # Assert consumer observed provider's service as valid and accessible during teardown
    assert len(consumer.teardown_observed_service_state) >= 1
    assert all(
        isinstance(state, dict) and state.get("status") == "ok"
        for state in consumer.teardown_observed_service_state
    )

    # Provider service is now revoked
    assert not ctx.has(provider.service_key)


@pytest.mark.unit
def test_coeffect_satisfaction_predicate() -> None:
    """Test check_satisfaction(plugin_name) predicate."""
    ctx = ServiceContext()
    lifecycle = PluginLifecycle(ctx)

    provider = SimpleProviderPlugin("kv_store")
    consumer = DependentConsumerPlugin("kv_client", provider.service_key)

    lifecycle.discover(provider)
    lifecycle.discover(consumer)

    is_sat, missing = lifecycle.check_satisfaction(consumer.name)
    assert not is_sat
    assert missing == [provider.service_key.name]

    # Provide the service
    ctx.provide(provider.service_key, {"status": "ready"})
    is_sat, missing = lifecycle.check_satisfaction(consumer.name)
    assert is_sat
    assert missing == []


@pytest.mark.unit
@pytest.mark.asyncio
async def test_tool_mount_revertible_effects() -> None:
    """Test that ToolMountMixin registers tools with automatic effect unmounting."""
    ctx = ServiceContext()
    tool_registry = ToolRegistry()
    ctx.provide(ServiceKey("tools.registry"), tool_registry)

    class MyToolPlugin(ToolMountMixin, HarnessPlugin):
        name = "test_tool_plugin"
        version = "1.0.0"

        async def on_load(self, context: ServiceContext) -> None:
            self.setup_tool_mount(context, self.name)

        async def on_enable(self) -> None:
            spec = ToolSpec(
                name="sample_tool",
                description="A sample tool",
                executor=lambda: "done",
            )
            await self.mount_tools([spec])

    plugin = MyToolPlugin()
    scoped_ctx = ctx.for_plugin(plugin.name)
    await plugin.on_load(scoped_ctx)
    await plugin.on_enable()

    assert tool_registry.get("sample_tool") is not None

    # Disposing scoped context should automatically unmount the tool
    await scoped_ctx.dispose()
    assert tool_registry.get("sample_tool") is None
