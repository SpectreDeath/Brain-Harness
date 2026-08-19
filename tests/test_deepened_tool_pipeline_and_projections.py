"""Unit and integration tests for deepened Tool Execution Pipeline and Event Stream Projection Engine."""

from __future__ import annotations

import asyncio
import time
from typing import Any

import pytest

from harness.events.bus import (
    AuditProjection,
    EventBus,
    EventProjectionEngine,
    MetricsProjection,
)
from harness.events.types import EventType, llm_event, plugin_event, tool_event
from harness.services.tools import (
    AccessControlInterceptor,
    MemoizationInterceptor,
    RateLimitInterceptor,
    SchemaValidationInterceptor,
    TelemetryInterceptor,
    TimeoutGuardInterceptor,
    ToolExecutionContext,
    ToolExecutionPipeline,
    ToolRegistry,
    ToolSpec,
)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_access_control_interceptor_policies() -> None:
    bus = EventBus()
    acl = AccessControlInterceptor()

    # Tool with restricted realms
    spec = ToolSpec(
        name="admin.reset",
        description="Admin tool",
        allowed_realms=["admin_realm", "root_realm"],
        executor=lambda: {"status": "ok", "result": "reset_done"},
    )

    async def mock_handler(ctx: ToolExecutionContext) -> dict[str, Any]:
        return {"status": "ok", "result": "executed"}

    # 1. Denied realm
    denied_ctx = ToolExecutionContext(
        name="admin.reset",
        spec=spec,
        params={},
        metadata={"realm": "guest_realm"},
        event_bus=bus,
    )
    res_denied = await acl.intercept(denied_ctx, mock_handler)
    assert res_denied["status"] == "error"
    assert "Access denied" in res_denied["error"]
    assert "guest_realm" in res_denied["error"]

    # 2. Allowed realm
    allowed_ctx = ToolExecutionContext(
        name="admin.reset",
        spec=spec,
        params={},
        metadata={"realm": "admin_realm"},
        event_bus=bus,
    )
    res_allowed = await acl.intercept(allowed_ctx, mock_handler)
    assert res_allowed["status"] == "ok"
    assert res_allowed["result"] == "executed"

    # 3. Unrestricted tool
    unrestricted_spec = ToolSpec(
        name="public.search",
        description="Public tool",
        allowed_realms=None,
        executor=lambda: {"status": "ok"},
    )
    unrestricted_ctx = ToolExecutionContext(
        name="public.search",
        spec=unrestricted_spec,
        params={},
        metadata={"realm": "anonymous"},
        event_bus=bus,
    )
    res_unrestricted = await acl.intercept(unrestricted_ctx, mock_handler)
    assert res_unrestricted["status"] == "ok"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_rate_limit_interceptor() -> None:
    bus = EventBus()
    rate_limiter = RateLimitInterceptor(default_rate_per_minute=2.0)

    spec = ToolSpec(
        name="api.query",
        description="Rate limited query",
        rate_limit_per_minute=2.0,  # 2 requests max initial burst
    )

    call_count = 0

    async def mock_handler(ctx: ToolExecutionContext) -> dict[str, Any]:
        nonlocal call_count
        call_count += 1
        return {"status": "ok", "result": call_count}

    ctx = ToolExecutionContext(
        name="api.query",
        spec=spec,
        params={},
        event_bus=bus,
    )

    # First two calls should succeed
    res1 = await rate_limiter.intercept(ctx, mock_handler)
    assert res1["status"] == "ok"
    assert res1["result"] == 1

    res2 = await rate_limiter.intercept(ctx, mock_handler)
    assert res2["status"] == "ok"
    assert res2["result"] == 2

    # Third immediate call should fail due to rate limit
    res3 = await rate_limiter.intercept(ctx, mock_handler)
    assert res3["status"] == "error"
    assert "Rate limit exceeded" in res3["error"]

    # Reset allows invocation again
    rate_limiter.reset()
    res4 = await rate_limiter.intercept(ctx, mock_handler)
    assert res4["status"] == "ok"
    assert res4["result"] == 3


@pytest.mark.unit
@pytest.mark.asyncio
async def test_memoization_interceptor() -> None:
    memoizer = MemoizationInterceptor()
    spec = ToolSpec(
        name="calc.factorial",
        description="Pure math calculation",
        cache_ttl=60.0,  # 60s cache
    )

    execution_count = 0

    async def mock_handler(ctx: ToolExecutionContext) -> dict[str, Any]:
        nonlocal execution_count
        execution_count += 1
        return {"status": "ok", "result": ctx.params.get("n", 0) * 2}

    ctx1 = ToolExecutionContext(
        name="calc.factorial",
        spec=spec,
        params={"n": 5},
    )

    # 1. Initial call
    res1 = await memoizer.intercept(ctx1, mock_handler)
    assert res1["status"] == "ok"
    assert res1["result"] == 10
    assert execution_count == 1
    assert not res1.get("cached", False)

    # 2. Second identical call (cache hit)
    res2 = await memoizer.intercept(ctx1, mock_handler)
    assert res2["status"] == "ok"
    assert res2["result"] == 10
    assert execution_count == 1  # Handler was NOT invoked
    assert res2.get("cached") is True

    # 3. Different parameters (cache miss)
    ctx2 = ToolExecutionContext(
        name="calc.factorial",
        spec=spec,
        params={"n": 10},
    )
    res3 = await memoizer.intercept(ctx2, mock_handler)
    assert res3["status"] == "ok"
    assert res3["result"] == 20
    assert execution_count == 2

    # 4. Clear cache
    memoizer.clear()
    res4 = await memoizer.intercept(ctx1, mock_handler)
    assert res4["status"] == "ok"
    assert execution_count == 3


@pytest.mark.unit
@pytest.mark.asyncio
async def test_tool_spec_from_callable_policy_fields() -> None:
    def sample_func(query: str, count: int = 10) -> str:
        """Search query."""
        return f"Results for {query} ({count})"

    spec = ToolSpec.from_callable(
        sample_func,
        name="search.engine",
        allowed_realms=["core", "search_realm"],
        rate_limit_per_minute=60.0,
        cache_ttl=30.0,
    )

    assert spec.name == "search.engine"
    assert spec.allowed_realms == ["core", "search_realm"]
    assert spec.rate_limit_per_minute == 60.0
    assert spec.cache_ttl == 30.0

    d = spec.to_dict()
    assert d["allowed_realms"] == ["core", "search_realm"]
    assert d["rate_limit_per_minute"] == 60.0
    assert d["cache_ttl"] == 30.0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_tool_registry_full_onion_pipeline_integration() -> None:
    bus = EventBus()
    registry = ToolRegistry(event_bus=bus)

    async def compute(x: int) -> int:
        return x ** 2

    spec = ToolSpec.from_callable(
        compute,
        name="math.square",
        allowed_realms=["allowed_user"],
        cache_ttl=10.0,
    )
    registry.register(spec)

    # Invoke with unauthorized realm
    err_res = await registry.invoke("math.square", {"x": 4}, metadata={"realm": "unauthorized"})
    assert err_res["status"] == "error"
    assert "Access denied" in err_res["error"]

    # Invoke with authorized realm
    ok_res = await registry.invoke("math.square", {"x": 4}, metadata={"realm": "allowed_user"})
    assert ok_res["status"] == "ok"
    assert ok_res["result"] == 16

    # Cached hit
    cached_res = await registry.invoke("math.square", {"x": 4}, metadata={"realm": "allowed_user"})
    assert cached_res["status"] == "ok"
    assert cached_res["result"] == 16
    assert cached_res.get("cached") is True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_event_projections_and_engine() -> None:
    bus = EventBus()
    engine = EventProjectionEngine(bus)

    metrics_proj = MetricsProjection()
    audit_proj = AuditProjection()

    engine.register("metrics", metrics_proj)
    engine.register("audit", audit_proj)

    # Emit various events
    await bus.emit(plugin_event(EventType.PLUGIN_ENABLED, "plugin-a"))
    await bus.emit(tool_event(EventType.TOOL_INVOKED, "tool-1", params={"q": "test"}))
    await bus.emit(tool_event(EventType.TOOL_RESULT, "tool-1", result="done"))
    await bus.emit(tool_event(EventType.TOOL_ERROR, "tool-1", error="invalid query"))
    await bus.emit(
        llm_event(
            EventType.LLM_RESPONSE,
            provider="mock",
            model="mock-v1",
            content="answer",
            usage={"total_tokens": 150},
        )
    )

    metrics = engine.get_state("metrics")
    assert metrics["total_events"] == 5
    assert metrics["tool_invocations"]["tool-1"] == 1
    assert metrics["tool_results"]["tool-1"] == 1
    assert metrics["tool_errors"]["tool-1"] == 1
    assert metrics["total_tokens"] == 150
    assert metrics["llm_calls"] == 1

    audit = engine.get_state("audit")
    assert len(audit) >= 2  # PLUGIN_ENABLED, TOOL_ERROR, etc.
    event_types = [r["event_type"] for r in audit]
    assert EventType.PLUGIN_ENABLED.value in event_types
    assert EventType.TOOL_ERROR.value in event_types


@pytest.mark.unit
@pytest.mark.asyncio
async def test_event_bus_replay_stream() -> None:
    bus = EventBus()

    # Pre-populate events
    t0 = time.time()
    await bus.emit(plugin_event(EventType.PLUGIN_DISCOVERED, "p1"))
    await asyncio.sleep(0.01)
    t1 = time.time()
    await bus.emit(plugin_event(EventType.PLUGIN_LOADED, "p1"))
    await bus.emit(tool_event(EventType.TOOL_INVOKED, "t1"))
    t2 = time.time()
    await bus.emit(plugin_event(EventType.PLUGIN_ENABLED, "p1"))

    # Replay all
    all_replayed = [e async for e in bus.replay_stream()]
    assert len(all_replayed) == 4

    # Replay with time window
    window_replayed = [
        e async for e in bus.replay_stream(from_timestamp=t1, to_timestamp=t2)
    ]
    assert len(window_replayed) >= 2

    # Replay with event_types filter
    tool_events_only = [
        e async for e in bus.replay_stream(event_types=[EventType.TOOL_INVOKED])
    ]
    assert len(tool_events_only) == 1
    assert tool_events_only[0].event_type == EventType.TOOL_INVOKED
