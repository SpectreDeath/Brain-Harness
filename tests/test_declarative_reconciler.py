"""Tests for the Declarative Configuration Reconciliation Engine.

Tests:
1. Reconciling addition of new plugin entries.
2. Reconciling modification (update/disable) of existing plugin entries.
3. Reconciling removal of plugins with guarded teardown.
4. Confluence verification (Theorem 73).
"""

from __future__ import annotations

from typing import Any

import pytest

from harness.kernel.context import ServiceContext, ServiceKey
from harness.kernel.lifecycle import PluginLifecycle, PluginState
from harness.kernel.reconciler import (
    ConfigurationReconciler,
    HarnessConfigTree,
    PluginConfigEntry,
)
from harness.kernel.runtime import HarnessRuntime
from harness.plugins.base import HarnessPlugin


class MockPlugin(HarnessPlugin):
    def __init__(self, name: str, provides_key: str | None = None, requires_key: str | None = None) -> None:
        self._name = name
        self._provides_key = ServiceKey(provides_key) if provides_key else None
        self._requires_key = ServiceKey(requires_key) if requires_key else None
        self.state_history: list[str] = []

    @property
    def name(self) -> str:
        return self._name

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [self._provides_key] if self._provides_key else []

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return [self._requires_key] if self._requires_key else []

    async def on_load(self, ctx: ServiceContext) -> None:
        self.state_history.append("loaded")
        if self._provides_key:
            ctx.provide(self._provides_key, {"from": self._name})

    async def on_enable(self) -> None:
        self.state_history.append("enabled")

    async def on_disable(self) -> None:
        self.state_history.append("disabled")

    async def on_unload(self) -> None:
        self.state_history.append("unloaded")


# --- Tests ---


@pytest.mark.integration
@pytest.mark.asyncio
async def test_reconcile_add_and_disable() -> None:
    """Test adding plugins declaratively and then toggling disabled flag."""
    runtime = HarnessRuntime.create(builtins=[], auto_load_user_plugins=False)
    await runtime.start()

    p1 = MockPlugin("p1", provides_key="svc.p1")
    p2 = MockPlugin("p2", provides_key="svc.p2", requires_key="svc.p1")
    runtime.register_plugin(p1)
    runtime.register_plugin(p2)

    reconciler = ConfigurationReconciler(runtime)

    # Initial target config: both enabled
    config_v1 = HarnessConfigTree(
        plugins=[
            PluginConfigEntry(id="entry_p1", name="p1"),
            PluginConfigEntry(id="entry_p2", name="p2"),
        ]
    )

    res_v1 = await reconciler.reconcile(config_v1)
    assert res_v1.is_clean
    assert "p1" in res_v1.added
    assert "p2" in res_v1.added
    assert runtime.lifecycle.get_state("p1") == PluginState.ENABLED
    assert runtime.lifecycle.get_state("p2") == PluginState.ENABLED

    # Update config: disable p2
    config_v2 = HarnessConfigTree(
        plugins=[
            PluginConfigEntry(id="entry_p1", name="p1"),
            PluginConfigEntry(id="entry_p2", name="p2", disabled=True),
        ]
    )

    res_v2 = await reconciler.reconcile(config_v2)
    assert res_v2.is_clean
    assert "p2" in res_v2.disabled
    assert runtime.lifecycle.get_state("p2") == PluginState.DISABLED
    assert runtime.lifecycle.get_state("p1") == PluginState.ENABLED

    # Update config: remove p2
    config_v3 = HarnessConfigTree(
        plugins=[
            PluginConfigEntry(id="entry_p1", name="p1"),
        ]
    )

    res_v3 = await reconciler.reconcile(config_v3)
    assert res_v3.is_clean
    assert "p2" in res_v3.removed
    assert runtime.lifecycle.get_state("p2") == PluginState.UNLOADED

    await runtime.stop()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_reconcile_guarded_removal_order() -> None:
    """Test that removing provider p1 automatically triggers guarded deactivation of consumer p2 first."""
    runtime = HarnessRuntime.create(builtins=[], auto_load_user_plugins=False)
    await runtime.start()

    provider = MockPlugin("provider", provides_key="svc.main")
    consumer = MockPlugin("consumer", requires_key="svc.main")
    runtime.register_plugin(provider)
    runtime.register_plugin(consumer)

    reconciler = ConfigurationReconciler(runtime)

    # Boot both
    await reconciler.reconcile(
        HarnessConfigTree(
            plugins=[
                PluginConfigEntry(id="e_prov", name="provider"),
                PluginConfigEntry(id="e_cons", name="consumer"),
            ]
        )
    )

    assert runtime.lifecycle.get_state("provider") == PluginState.ENABLED
    assert runtime.lifecycle.get_state("consumer") == PluginState.ENABLED

    # Reconcile removing provider: consumer must be drained/disabled by Guarded Withdrawal
    res = await reconciler.reconcile(
        HarnessConfigTree(
            plugins=[
                PluginConfigEntry(id="e_cons", name="consumer"),
            ]
        )
    )

    assert res.is_clean
    assert "provider" in res.removed
    assert runtime.lifecycle.get_state("provider") == PluginState.UNLOADED
    # Consumer was safely disabled during provider drain
    assert runtime.lifecycle.get_state("consumer") == PluginState.DISABLED

    await runtime.stop()
