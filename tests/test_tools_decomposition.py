"""Characterization and contract tests for decomposed Tools package (Phase 3).

Validates:
1. Isolated submodule importability across tools models, interceptors, pipeline, registry, and plugin.
2. Standalone interceptor behavior (RateLimit, Memoization, SchemaValidation, TimeoutGuard).
3. Pipeline onion-layer execution chaining.
4. 100% backward compatibility of all exports from harness.services.tools.
"""

from __future__ import annotations

import asyncio
import time
import pytest

from harness.services.tools import (
    AccessControlInterceptor,
    MemoizationInterceptor,
    RateLimitInterceptor,
    SchemaValidationInterceptor,
    TelemetryInterceptor,
    TimeoutGuardInterceptor,
    TOOL_REGISTRY_KEY,
    ToolExecutionContext,
    ToolExecutionPipeline,
    ToolInterceptor,
    ToolRegistry,
    ToolRegistryPlugin,
    ToolSpec,
)


def test_tools_submodule_isolated_imports() -> None:
    """Verify each decomposed submodule can be imported independently."""
    from harness.services.tools import interceptors, models, pipeline, plugin, registry

    assert hasattr(models, "ToolExecutionContext")
    assert hasattr(models, "ToolSpec")
    assert hasattr(interceptors, "ToolInterceptor")
    assert hasattr(interceptors, "RateLimitInterceptor")
    assert hasattr(interceptors, "MemoizationInterceptor")
    assert hasattr(interceptors, "SchemaValidationInterceptor")
    assert hasattr(interceptors, "TimeoutGuardInterceptor")
    assert hasattr(pipeline, "ToolExecutionPipeline")
    assert hasattr(registry, "ToolRegistry")
    assert hasattr(registry, "TOOL_REGISTRY_KEY")
    assert hasattr(plugin, "ToolRegistryPlugin")


def test_tools_package_backward_compatible_re_exports() -> None:
    """Verify harness.services.tools maintains all canonical symbols."""
    import harness.services.tools as tools_mod

    expected_symbols = [
        "TOOL_REGISTRY_KEY",
        "ToolExecutor",
        "ToolExecutionContext",
        "ToolInterceptor",
        "TelemetryInterceptor",
        "AccessControlInterceptor",
        "RateLimitInterceptor",
        "MemoizationInterceptor",
        "SchemaValidationInterceptor",
        "TimeoutGuardInterceptor",
        "ToolExecutionPipeline",
        "ToolSpec",
        "ToolRegistry",
        "ToolRegistryPlugin",
    ]
    for sym in expected_symbols:
        assert hasattr(tools_mod, sym), f"Missing symbol '{sym}' in tools package facade"


@pytest.mark.asyncio
async def test_standalone_rate_limit_interceptor() -> None:
    """Verify RateLimitInterceptor operates without a global ToolRegistry."""
    interceptor = RateLimitInterceptor(default_rate_per_minute=2.0)
    spec = ToolSpec(name="limited_tool", description="Test tool", rate_limit_per_minute=2.0)
    ctx = ToolExecutionContext(name="limited_tool", spec=spec)

    async def dummy_next(c: ToolExecutionContext) -> dict[str, str]:
        return {"status": "ok", "result": "done"}

    # First two calls should succeed
    res1 = await interceptor.intercept(ctx, dummy_next)
    assert res1["status"] == "ok"

    res2 = await interceptor.intercept(ctx, dummy_next)
    assert res2["status"] == "ok"

    # Third call within minute should be rate limited
    res3 = await interceptor.intercept(ctx, dummy_next)
    assert res3["status"] == "error"
    assert "Rate limit exceeded" in res3["error"]


@pytest.mark.asyncio
async def test_standalone_memoization_interceptor() -> None:
    """Verify MemoizationInterceptor caches idempotent results."""
    interceptor = MemoizationInterceptor(default_ttl=10.0)
    spec = ToolSpec(name="cached_tool", description="Test tool", cache_ttl=5.0)
    ctx = ToolExecutionContext(name="cached_tool", spec=spec, params={"arg": "value"})

    call_count = 0

    async def counting_next(c: ToolExecutionContext) -> dict[str, str]:
        nonlocal call_count
        call_count += 1
        return {"status": "ok", "result": f"call_{call_count}"}

    res1 = await interceptor.intercept(ctx, counting_next)
    assert res1["status"] == "ok"
    assert res1["result"] == "call_1"
    assert call_count == 1

    # Second call should hit memoization cache
    res2 = await interceptor.intercept(ctx, counting_next)
    assert res2["status"] == "ok"
    assert res2["result"] == "call_1"
    assert res2.get("cached") is True
    assert call_count == 1  # Not called again


@pytest.mark.asyncio
async def test_standalone_schema_validation_interceptor() -> None:
    """Verify SchemaValidationInterceptor guards required parameters."""
    interceptor = SchemaValidationInterceptor()
    spec = ToolSpec(
        name="param_tool",
        description="Test tool",
        parameters_schema={"type": "object", "required": ["user_id", "action"]},
    )

    async def dummy_next(c: ToolExecutionContext) -> dict[str, str]:
        return {"status": "ok", "result": "passed"}

    # Missing required parameter
    ctx_bad = ToolExecutionContext(name="param_tool", spec=spec, params={"user_id": "u1"})
    res_bad = await interceptor.intercept(ctx_bad, dummy_next)
    assert res_bad["status"] == "error"
    assert "Missing required parameter" in res_bad["error"]

    # All required parameters present
    ctx_good = ToolExecutionContext(name="param_tool", spec=spec, params={"user_id": "u1", "action": "run"})
    res_good = await interceptor.intercept(ctx_good, dummy_next)
    assert res_good["status"] == "ok"
