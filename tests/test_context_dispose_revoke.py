"""Contract test suite for IoC ServiceContext disposal, revocation, and Rule 54 invariants."""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from harness.kernel.context import ServiceContext, ServiceKey
from harness.kernel.context.effects import register_effect
from harness.kernel.context.models import ServiceNotFoundError


class DummyService:
    def __init__(self, val: str) -> None:
        self.val = val


KEY_A = ServiceKey[DummyService]("dummy.service.a")
KEY_B = ServiceKey[DummyService]("dummy.service.b")
KEY_C = ServiceKey[DummyService]("dummy.service.c")


@pytest.mark.unit
class TestContextDisposeRevokeContracts:
    """Test suite validating Rule 54 inverse-accumulator synchronization and lifecycle invariants."""

    @pytest.mark.asyncio
    async def test_revoke_service_purges_inverse_and_prevents_execution_on_dispose(self) -> None:
        """Rule 54: revoke() purges matching inverse closures from _dispose_stack."""
        root = ServiceContext()
        root.provide(KEY_A, DummyService("a"), provider="plugin-1")

        assert len(root._dispose_stack) == 1
        inv = root._dispose_stack[0]
        assert getattr(inv, "_realm_key", None) == KEY_A.name
        assert getattr(inv, "_provider", None) == "plugin-1"

        revoked = root.revoke(KEY_A)
        assert revoked is True
        assert len(root._dispose_stack) == 0
        assert not root.has(KEY_A)

        # Disposing the container must succeed without executing orphaned closures
        await root.dispose()
        assert len(root._dispose_stack) == 0

    @pytest.mark.asyncio
    async def test_revoke_all_from_provider_purges_only_matching_inverses(self) -> None:
        """Rule 54: revoke_all_from() purges all inverse closures provided by a specific plugin."""
        root = ServiceContext()
        root.provide(KEY_A, DummyService("a"), provider="plugin-alpha")
        root.provide(KEY_B, DummyService("b"), provider="plugin-alpha")
        root.provide(KEY_C, DummyService("c"), provider="plugin-beta")

        assert len(root._dispose_stack) == 3

        revoked = root.revoke_all_from("plugin-alpha")
        assert set(revoked) == {KEY_A.name, KEY_B.name}
        assert not root.has(KEY_A)
        assert not root.has(KEY_B)
        assert root.has(KEY_C)

        # Only plugin-beta's inverse closure should remain
        assert len(root._dispose_stack) == 1
        assert getattr(root._dispose_stack[0], "_provider", None) == "plugin-beta"
        assert getattr(root._dispose_stack[0], "_realm_key", None) == KEY_C.name

        # Container disposal clears remaining closures cleanly
        await root.dispose()
        assert len(root._dispose_stack) == 0
        assert not root.has(KEY_C)

    @pytest.mark.asyncio
    async def test_hot_swap_service_purges_old_inverses_without_accumulation(self) -> None:
        """Rule 54: hot_swap() replaces the inverse closure without duplicate accumulation."""
        root = ServiceContext()
        root.provide(KEY_A, DummyService("v1"), provider="plugin-1")
        assert len(root._dispose_stack) == 1

        for i in range(2, 6):
            root.hot_swap(KEY_A, DummyService(f"v{i}"), provider="plugin-1")
            assert len(root._dispose_stack) == 1, f"Accumulation detected at iteration {i}"

        assert root.require(KEY_A).val == "v5"

        # Disposal runs the single active inverse closure
        await root.dispose()
        assert len(root._dispose_stack) == 0
        assert not root.has(KEY_A)

    @pytest.mark.asyncio
    async def test_scoped_context_mid_session_unload_no_double_dispose(self) -> None:
        """Unloading a plugin mid-session through ScopedServiceContext does not double-dispose in root."""
        root = ServiceContext()
        scoped = root.for_plugin("plugin-worker")

        scoped.provide(KEY_A, DummyService("worker-a"))
        scoped.provide(KEY_B, DummyService("worker-b"))

        assert root.has(KEY_A)
        assert root.has(KEY_B)
        assert len(root._dispose_stack) == 2

        # Unload the scoped context mid-session
        await scoped.dispose()

        assert not root.has(KEY_A)
        assert not root.has(KEY_B)
        assert len(root._dispose_stack) == 0

        # Root disposal afterward should not encounter any orphaned closures
        await root.dispose()
        assert len(root._dispose_stack) == 0

    @pytest.mark.asyncio
    async def test_child_context_isolation_does_not_corrupt_parent(self) -> None:
        """Child context disposal executes only child inverses, preserving parent state intact."""
        parent = ServiceContext()
        parent.provide(KEY_A, DummyService("parent_val"), provider="parent_plugin")

        child = parent.child()
        child.provide(KEY_B, DummyService("child_val"), provider="child_plugin")

        assert len(parent._dispose_stack) == 1
        assert len(child._dispose_stack) == 1

        # Disposing the child clears only child._dispose_stack
        await child.dispose()
        assert len(child._dispose_stack) == 0
        assert not child.has(KEY_B)

        # Parent remains completely intact
        assert len(parent._dispose_stack) == 1
        assert parent.has(KEY_A)
        assert parent.require(KEY_A).val == "parent_val"

        # Disposing parent cleans up parent
        await parent.dispose()
        assert len(parent._dispose_stack) == 0
        assert not parent.has(KEY_A)

    @pytest.mark.asyncio
    async def test_register_effect_lifo_order_and_early_disposal(self) -> None:
        """Revertible effects registered via register_effect run in LIFO order and support early self-disposal."""
        root = ServiceContext()
        execution_order: list[str] = []

        def _effect_1() -> Any:
            def _inv_1() -> None:
                execution_order.append("inv_1")
            return _inv_1

        def _effect_2() -> Any:
            async def _inv_2() -> None:
                await asyncio.sleep(0.001)
                execution_order.append("inv_2")
            return _inv_2

        def _effect_3() -> Any:
            def _inv_3() -> None:
                execution_order.append("inv_3")
            return _inv_3

        disposer_1 = register_effect(root, _effect_1)
        disposer_2 = register_effect(root, _effect_2)
        disposer_3 = register_effect(root, _effect_3)

        assert len(root._dispose_stack) == 3

        # Early self-disposal of effect 2
        res = disposer_2()
        if asyncio.iscoroutine(res):
            await res
        assert execution_order == ["inv_2"]
        assert len(root._dispose_stack) == 2

        # Calling self-disposer again should be idempotent
        res_repeat = disposer_2()
        if asyncio.iscoroutine(res_repeat):
            await res_repeat
        assert execution_order == ["inv_2"]

        # Disposing context should execute effect 3 then effect 1 (LIFO)
        await root.dispose()
        assert execution_order == ["inv_2", "inv_3", "inv_1"]
        assert len(root._dispose_stack) == 0
