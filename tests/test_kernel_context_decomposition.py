"""Contract test suite for ServiceContext decomposition per AGENTS.md Rules 1, 2, 8, 11, 12, 54, 58."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from harness.kernel import (
    DuplicateServiceError,
    ScopedServiceContext,
    ServiceContext,
    ServiceEntry,
    ServiceKey,
    ServiceNotFoundError,
)
from harness.kernel.context import resolve_service_context
from harness.kernel.context.effects import register_effect
from harness.kernel.context.interceptors import collect_interceptors
from harness.kernel.context.lookup import require_service
from harness.kernel.context.mutations import provide_service
from harness.kernel.context.realms import resolve_realm


@pytest.mark.unit
class TestKernelContextDecompositionContracts:
    def test_submodule_line_count_invariants(self) -> None:
        """Rule 11: All decomposed submodules in harness/kernel/context must be <= 200 lines."""
        pkg_dir = Path("src/harness/kernel/context")
        assert pkg_dir.exists() and pkg_dir.is_dir()

        submodules = list(pkg_dir.glob("*.py"))
        assert len(submodules) >= 9, f"Expected at least 9 submodules, found {len(submodules)}"

        for mod in submodules:
            lines = len(mod.read_text(encoding="utf-8").splitlines())
            assert (
                lines <= 200
            ), f"Module {mod.name} exceeds 200 lines ({lines} lines). Violates Rule 11."

    def test_facade_and_kernel_reexports(self) -> None:
        """Verify 100% backward compatibility of re-exported symbols from harness.kernel and context."""
        import harness.kernel as k
        import harness.kernel.context as kc

        for symbol in [
            "ServiceContext",
            "ServiceKey",
            "ServiceEntry",
            "ServiceNotFoundError",
            "DuplicateServiceError",
            "ScopedServiceContext",
        ]:
            assert hasattr(k, symbol)
            assert hasattr(kc, symbol)
            assert getattr(k, symbol) is getattr(kc, symbol)

    def test_single_seam_resolver(self) -> None:
        """Rule 58: resolve_service_context must resolve existing context or construct a new root."""
        ctx = ServiceContext()
        resolved = resolve_service_context(ctx)
        assert resolved is ctx

        new_resolved = resolve_service_context(None)
        assert isinstance(new_resolved, ServiceContext)
        assert new_resolved.parent is None

    def test_service_key_contracts(self) -> None:
        """Verify ServiceKey typed hashing, equality, and representation."""
        k1 = ServiceKey[str]("test.service")
        k2 = ServiceKey[str]("test.service")
        k3 = ServiceKey[int]("other.service")

        assert k1 == k2
        assert k1 != k3
        assert hash(k1) == hash(k2)
        assert repr(k1) == "ServiceKey('test.service')"

    def test_realms_isolation(self) -> None:
        """Verify coeffect realm isolation helper functions and method."""
        root = ServiceContext()
        key = ServiceKey[str]("scoped.res")
        root.provide(key, "root_val")

        isolated = root.isolate(key, realm="custom_realm")
        assert resolve_realm(isolated, key.name) == "custom_realm"
        isolated.provide(key, "isolated_val")

        assert root.require(key) == "root_val"
        assert isolated.require(key) == "isolated_val"

    def test_interceptors_chaining_and_epoch(self) -> None:
        """Verify coeffect interceptors chaining and epoch invalidation."""
        root = ServiceContext()
        key = ServiceKey[int]("counter")
        root.provide(key, 10)

        child1 = root.intercept(key, lambda n: n + 5)
        child2 = child1.intercept(key, lambda n: n * 2)

        assert root.require(key) == 10
        assert child1.require(key) == 15
        assert child2.require(key) == 30

        chain = collect_interceptors(child2, key.name)
        assert len(chain) == 2

    @pytest.mark.asyncio
    async def test_transactional_rollback_and_compaction(self) -> None:
        """Verify transaction rollback on error and inverse compaction on success."""
        root = ServiceContext()
        key_a = ServiceKey[str]("tx.a")
        key_b = ServiceKey[str]("tx.b")
        root.provide(key_a, "initial_a")

        # 1. Rollback on exception
        with pytest.raises(RuntimeError):
            async with root.transaction() as tx:
                tx.provide(key_a, "overwritten_a", allow_override=True)
                tx.provide(key_b, "tx_b")
                raise RuntimeError("forced failure")

        assert root.require(key_a) == "initial_a"
        assert not root.has(key_b)

        # 2. Compaction on commit
        init_len = len(root._dispose_stack)
        async with root.transaction() as tx:
            for i in range(25):
                tx.provide(key_a, f"val_{i}", allow_override=True)

        added = len(root._dispose_stack) - init_len
        assert added <= 2, f"Expected <= 2 compacted inverses, got {added}"
        assert root.require(key_a) == "val_24"

    def test_rule_54_dispose_stack_purging(self) -> None:
        """Rule 54: revoke(), hot_swap(), and revoke_all_from() must purge stale inverses from _dispose_stack."""
        ctx = ServiceContext()
        key_a = ServiceKey[str]("purge.a")
        key_b = ServiceKey[str]("purge.b")

        ctx.provide(key_a, "a1", provider="plugin-p")
        ctx.provide(key_b, "b1", provider="plugin-p")
        assert len(ctx._dispose_stack) == 2

        # hot_swap should not accumulate extra inverse closures
        ctx.hot_swap(key_a, "a2", provider="plugin-p")
        assert len(ctx._dispose_stack) == 2

        # revoke key_a should purge its inverse closure
        ctx.revoke(key_a)
        assert len(ctx._dispose_stack) == 1
        assert getattr(ctx._dispose_stack[0], "_realm_key", None) == key_b.name

        # revoke_all_from should purge all plugin-p closures
        ctx.revoke_all_from("plugin-p")
        assert len(ctx._dispose_stack) == 0

    @pytest.mark.asyncio
    async def test_scoped_context_lifecycle(self) -> None:
        """Verify ScopedServiceContext provider binding, tracking, and teardown."""
        root = ServiceContext()
        scoped = root.for_plugin("my_plugin")
        key = ServiceKey[str]("scoped.service")

        scoped.provide(key, "scoped_value")
        assert "scoped.service" in scoped.provided_keys
        assert root.require(key) == "scoped_value"

        # Disposing scoped context should revoke services from parent
        await scoped.dispose()
        assert not root.has(key)

    def test_direct_submodule_function_seams(self) -> None:
        """Verify direct invocations of partitioned submodule functions."""
        ctx = ServiceContext()
        key = ServiceKey[str]("direct.seam")
        provide_service(ctx, key, "hello_direct")

        val = require_service(ctx, key)
        assert val == "hello_direct"

        effect_reverted = False

        def _my_effect() -> Any:
            nonlocal effect_reverted

            def _inv() -> None:
                nonlocal effect_reverted
                effect_reverted = True

            return _inv

        disposer = register_effect(ctx, _my_effect)
        assert not effect_reverted
        disposer()
        assert effect_reverted
