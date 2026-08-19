"""Tests for ServiceContext — the canonical service registration surface.

Previously covered ServiceRegistry which was a thin, unused wrapper.
Those behaviours now live directly in ServiceContext.
"""

import pytest

from harness.kernel.context import ServiceContext, ServiceKey


@pytest.mark.unit
@pytest.mark.asyncio
class TestServiceContextContract:
    async def test_provide_and_require(self) -> None:
        ctx = ServiceContext()
        key = ServiceKey[str]("test")
        ctx.provide(key, "value")
        assert ctx.require(key) == "value"

    async def test_optional(self) -> None:
        ctx = ServiceContext()
        key = ServiceKey[str]("missing")
        assert ctx.optional(key) is None

    async def test_has(self) -> None:
        ctx = ServiceContext()
        key = ServiceKey[str]("test")
        assert not ctx.has(key)
        ctx.provide(key, "value")
        assert ctx.has(key)

    async def test_revoke(self) -> None:
        ctx = ServiceContext()
        key = ServiceKey[str]("test")
        ctx.provide(key, "value")
        assert ctx.revoke(key) is True
        assert not ctx.has(key)

    async def test_revoke_all_from(self) -> None:
        ctx = ServiceContext()
        k1 = ServiceKey[str]("a")
        k2 = ServiceKey[str]("b")
        ctx.provide(k1, "1", provider="p")
        ctx.provide(k2, "2", provider="p")
        revoked = ctx.revoke_all_from("p")
        assert set(revoked) == {"a", "b"}

    async def test_hot_swap(self) -> None:
        ctx = ServiceContext()
        key = ServiceKey[str]("test")
        ctx.provide(key, "old")
        assert ctx.require(key) == "old"
        ctx.hot_swap(key, "new", provider="swapper")
        assert ctx.require(key) == "new"

    async def test_list_services(self) -> None:
        ctx = ServiceContext()
        ctx.provide(ServiceKey[str]("a"), "1", provider="p1")
        services = ctx.list_services()
        assert "a" in services

    async def test_child_scope(self) -> None:
        ctx = ServiceContext()
        key = ServiceKey[str]("root")
        ctx.provide(key, "value")
        child = ctx.child()
        assert child.require(key) == "value"

    async def test_event_bus_telemetry(self) -> None:
        from harness.events.bus import EventBus
        from harness.events.types import EventType

        bus = EventBus()
        ctx = ServiceContext(event_bus=bus)

        k1 = ServiceKey[str]("svc.demo")
        ctx.provide(k1, "v1", provider="demo_plugin")

        # Check SERVICE_PROVIDED event emitted
        events = bus.filter_log(event_type=EventType.SERVICE_PROVIDED)
        assert len(events) >= 1
        assert events[0].source == "demo_plugin"
        assert events[0].payload == {"service": "svc.demo", "provider": "demo_plugin"}

        # Hot-swap
        ctx.hot_swap(k1, "v2", provider="hot_plugin")
        hot_events = bus.filter_log(event_type=EventType.SERVICE_HOT_SWAPPED)
        assert len(hot_events) == 1
        assert hot_events[0].payload["service"] == "svc.demo"

        # Revoke
        ctx.revoke(k1)
        revoked_events = bus.filter_log(event_type=EventType.SERVICE_REVOKED)
        assert len(revoked_events) == 1
        assert revoked_events[0].payload["service"] == "svc.demo"
