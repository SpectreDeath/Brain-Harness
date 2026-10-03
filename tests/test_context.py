"""Tests for the ServiceContext IoC container."""

import pytest

from harness.kernel.context import (
    DuplicateServiceError,
    ServiceContext,
    ServiceKey,
    ServiceNotFoundError,
)


@pytest.mark.unit
class TestServiceKey:
    def test_equality(self) -> None:
        k1 = ServiceKey[str]("llm.provider")
        k2 = ServiceKey[str]("llm.provider")
        assert k1 == k2

    def test_inequality(self) -> None:
        k1 = ServiceKey[str]("llm.provider")
        k2 = ServiceKey[str]("storage.default")
        assert k1 != k2

    def test_hash(self) -> None:
        k1 = ServiceKey[str]("llm.provider")
        k2 = ServiceKey[str]("llm.provider")
        assert hash(k1) == hash(k2)
        assert {k1, k2} == {k1}

    def test_repr(self) -> None:
        k = ServiceKey[str]("llm.provider")
        assert "llm.provider" in repr(k)


@pytest.mark.unit
class TestServiceContext:
    def test_provide_and_require(self) -> None:
        ctx = ServiceContext()
        key = ServiceKey[str]("test.service")
        ctx.provide(key, "hello")
        assert ctx.require(key) == "hello"

    def test_require_missing_raises(self) -> None:
        ctx = ServiceContext()
        key = ServiceKey[str]("missing")
        with pytest.raises(ServiceNotFoundError):
            ctx.require(key)

    def test_optional_returns_none(self) -> None:
        ctx = ServiceContext()
        key = ServiceKey[str]("missing")
        assert ctx.optional(key) is None

    def test_optional_returns_value(self) -> None:
        ctx = ServiceContext()
        key = ServiceKey[str]("test")
        ctx.provide(key, 42)
        assert ctx.optional(key) == 42

    def test_duplicate_raises(self) -> None:
        ctx = ServiceContext()
        key = ServiceKey[str]("test")
        ctx.provide(key, "first")
        with pytest.raises(DuplicateServiceError):
            ctx.provide(key, "second")

    def test_allow_override(self) -> None:
        ctx = ServiceContext()
        key = ServiceKey[str]("test")
        ctx.provide(key, "first")
        ctx.provide(key, "second", allow_override=True)
        assert ctx.require(key) == "second"

    def test_has(self) -> None:
        ctx = ServiceContext()
        key = ServiceKey[str]("test")
        assert not ctx.has(key)
        ctx.provide(key, "value")
        assert ctx.has(key)

    def test_contains(self) -> None:
        ctx = ServiceContext()
        key = ServiceKey[str]("test")
        assert key not in ctx
        ctx.provide(key, "value")
        assert key in ctx

    def test_revoke(self) -> None:
        ctx = ServiceContext()
        key = ServiceKey[str]("test")
        ctx.provide(key, "value")
        assert ctx.revoke(key) is True
        assert not ctx.has(key)

    def test_revoke_missing(self) -> None:
        ctx = ServiceContext()
        key = ServiceKey[str]("missing")
        assert ctx.revoke(key) is False

    def test_revoke_all_from(self) -> None:
        ctx = ServiceContext()
        k1 = ServiceKey[str]("svc.a")
        k2 = ServiceKey[str]("svc.b")
        k3 = ServiceKey[str]("svc.c")
        ctx.provide(k1, "a", provider="plugin-x")
        ctx.provide(k2, "b", provider="plugin-x")
        ctx.provide(k3, "c", provider="plugin-y")

        revoked = ctx.revoke_all_from("plugin-x")
        assert set(revoked) == {"svc.a", "svc.b"}
        assert not ctx.has(k1)
        assert not ctx.has(k2)
        assert ctx.has(k3)

    def test_list_services(self) -> None:
        ctx = ServiceContext()
        k1 = ServiceKey[str]("svc.a")
        k2 = ServiceKey[str]("svc.b")
        ctx.provide(k1, "a", provider="p1")
        ctx.provide(k2, "b")

        services = ctx.list_services()
        assert services == {"svc.a": "p1", "svc.b": None}


class TestServiceContextParentChild:
    def test_child_inherits_parent(self) -> None:
        parent = ServiceContext()
        key = ServiceKey[str]("parent.service")
        parent.provide(key, "inherited")

        child = parent.child()
        assert child.require(key) == "inherited"

    def test_child_overrides_parent(self) -> None:
        parent = ServiceContext()
        key = ServiceKey[str]("shared")
        parent.provide(key, "parent_value")

        child = parent.child()
        child.provide(key, "child_value")
        assert child.require(key) == "child_value"
        assert parent.require(key) == "parent_value"

    def test_child_does_not_leak_to_parent(self) -> None:
        parent = ServiceContext()
        child = parent.child()
        key = ServiceKey[str]("child.only")
        child.provide(key, "local")

        assert child.has(key)
        assert not parent.has(key)

    def test_has_walks_parent(self) -> None:
        parent = ServiceContext()
        key = ServiceKey[str]("test")
        parent.provide(key, "val")

        child = parent.child()
        assert child.has(key)


@pytest.mark.unit
class TestServiceContextInterception:
    def test_interceptor_wrapping(self) -> None:
        ctx = ServiceContext()
        key = ServiceKey[str]("greeting")
        ctx.provide(key, "hello")

        child = ctx.intercept(key, lambda s: f"{s} world")
        assert child.require(key) == "hello world"
        assert ctx.require(key) == "hello"

    def test_interceptor_hierarchy_ordering(self) -> None:
        ctx = ServiceContext()
        key = ServiceKey[int]("number")
        ctx.provide(key, 5)

        # Parent adds 10, child multiplies by 2: (5 + 10) * 2 = 30
        parent_child = ctx.intercept(key, lambda n: n + 10)
        grandchild = parent_child.intercept(key, lambda n: n * 2)

        assert grandchild.require(key) == 30

    def test_interceptor_concurrent_safety(self) -> None:
        import concurrent.futures

        ctx = ServiceContext()
        key = ServiceKey[int]("counter")
        ctx.provide(key, 1)

        errors: list[Exception] = []

        def worker(i: int) -> None:
            try:
                for _ in range(50):
                    # Intercept and create derived context
                    c = ctx.intercept(key, lambda n: n + 1)
                    val = c.require(key)
                    assert val >= 2
            except Exception as e:
                errors.append(e)

        with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool:
            futures = [pool.submit(worker, i) for i in range(16)]
            concurrent.futures.wait(futures)

        assert not errors, f"Concurrent intercept errors: {errors}"


@pytest.mark.asyncio
async def test_context_lock_free_read_latency() -> None:
    """Validate that high-frequency writes do not cause lock contention or read failure."""
    import asyncio
    import time

    ctx = ServiceContext()
    keys = [ServiceKey[int](f"service_{i}") for i in range(50)]
    for i, key in enumerate(keys):
        ctx.provide(key, i)

    # 1. Baseline: concurrent tasks performing reads without writer pressure
    async def reader_task(iterations: int = 500) -> float:
        t0 = time.perf_counter()
        for _ in range(iterations):
            for k in keys:
                assert ctx.require(k) is not None
        return time.perf_counter() - t0

    baseline_times = await asyncio.gather(*(reader_task() for _ in range(20)))
    avg_baseline = sum(baseline_times) / len(baseline_times)

    # 2. Under writer pressure: background writer mutating at high frequency
    writer_running = True
    writer_key = ServiceKey[str]("writer.key")
    ctx.provide(writer_key, "initial")

    async def writer_task() -> None:
        counter = 0
        while writer_running:
            counter += 1
            ctx.provide(writer_key, f"v_{counter}", allow_override=True)
            await asyncio.sleep(0.001)

    w_task = asyncio.create_task(writer_task())
    try:
        contended_times = await asyncio.gather(*(reader_task() for _ in range(20)))
    finally:
        writer_running = False
        await w_task

    avg_contended = sum(contended_times) / len(contended_times)
    # Read latency under write pressure should remain bounded
    assert avg_contended < avg_baseline * 3.5, (
        f"Contended latency ({avg_contended:.4f}s) exceeded bound vs baseline ({avg_baseline:.4f}s)"
    )


@pytest.mark.asyncio
async def test_transaction_inverse_compaction() -> None:
    """Verify that multi-step transactions compact redundant inverses down to O(K) keys."""
    ctx = ServiceContext()
    key_a = ServiceKey[str]("key.a")
    key_b = ServiceKey[str]("key.b")

    initial_stack_len = len(ctx._dispose_stack)

    async with ctx.transaction() as tx:
        for i in range(50):
            tx.provide(key_a, f"val_a_{i}", allow_override=True)
            tx.provide(key_b, f"val_b_{i}", allow_override=True)

    # Inverses should be compacted: at most 2 inverses (one per unique key mutated), NOT 100
    added_inverses = len(ctx._dispose_stack) - initial_stack_len
    assert added_inverses <= 2, f"Expected <= 2 compacted inverses, got {added_inverses}"

    # Disposing root context should still cleanly dispose both keys
    await ctx.dispose()
    assert not ctx.has(key_a)
    assert not ctx.has(key_b)


def test_interceptor_epoch_increments_on_write() -> None:
    """Verify that _interceptor_epoch bumps on provide, revoke, and hot-swap for cache busting."""
    ctx = ServiceContext()
    key = ServiceKey[str]("epoch.test")

    e0 = getattr(ctx, "_interceptor_epoch", 0)
    ctx.provide(key, "v1")
    e1 = getattr(ctx, "_interceptor_epoch", 0)
    assert e1 == e0 + 1, f"Epoch should increment on provide: {e1} != {e0 + 1}"

    ctx.provide(key, "v2", allow_override=True)
    e2 = getattr(ctx, "_interceptor_epoch", 0)
    assert e2 == e1 + 1, f"Epoch should increment on override provide: {e2} != {e1 + 1}"

    ctx.hot_swap(key, "v3")
    e3 = getattr(ctx, "_interceptor_epoch", 0)
    assert e3 == e2 + 1, f"Epoch should increment on hot_swap: {e3} != {e2 + 1}"

    ctx.revoke(key)
    e4 = getattr(ctx, "_interceptor_epoch", 0)
    assert e4 == e3 + 1, f"Epoch should increment on revoke: {e4} != {e3 + 1}"
