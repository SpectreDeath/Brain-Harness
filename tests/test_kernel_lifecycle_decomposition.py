"""Characterization test contract for decomposed harness.kernel.lifecycle package."""

from __future__ import annotations

import asyncio
from typing import Any
import pytest

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin


class StubLifecyclePlugin(HarnessPlugin):
    """Stub plugin for lifecycle tests."""

    def __init__(
        self,
        name: str = "stub",
        version: str = "1.0.0",
        provides: list[ServiceKey] | None = None,
        requires: list[ServiceKey] | None = None,
    ) -> None:
        self._name = name
        self._version = version
        self._provides = provides or []
        self._requires = requires or []
        self.loaded = False
        self.enabled = False
        self.unloaded = False

    @property
    def name(self) -> str:
        return self._name

    @property
    def version(self) -> str:
        return self._version

    @property
    def provides(self) -> list[ServiceKey]:
        return self._provides

    @property
    def requires(self) -> list[ServiceKey]:
        return self._requires

    async def on_load(self, ctx: ServiceContext) -> None:
        self.loaded = True
        for key in self._provides:
            ctx.provide(key, self, provider=self._name)

    async def on_enable(self) -> None:
        self.enabled = True

    async def on_disable(self) -> None:
        self.enabled = False

    async def on_unload(self) -> None:
        self.unloaded = True


def test_submodule_independent_imports() -> None:
    """Verify all decomposed submodules can be imported independently."""
    from harness.kernel.lifecycle.models import (
        PluginState,
        PluginEntry,
        _TRANSITIONS,
        InvalidTransitionError,
        DependencyError,
        PLUGIN_LIFECYCLE_KEY,
    )
    from harness.kernel.lifecycle.transitions import (
        validate_transition,
        emit_lifecycle_event,
    )
    from harness.kernel.lifecycle.sorter import (
        build_dependency_graph,
        resolve_enable_waves,
        resolve_enable_order,
    )
    from harness.kernel.lifecycle.manager import (
        PluginLifecycle,
        resolve_plugin_lifecycle,
    )
    from harness.kernel.lifecycle import (
        PluginState as RootPluginState,
        PluginLifecycle as RootPluginLifecycle,
        PluginEntry as RootPluginEntry,
        CyclicDependencyError,
        DependencyGraph,
        GraphCycleError,
        InvalidTransitionError as RootInvalidTransitionError,
        DependencyError as RootDependencyError,
        PLUGIN_LIFECYCLE_KEY as ROOT_KEY,
        resolve_plugin_lifecycle as root_resolve_plugin_lifecycle,
    )

    assert RootPluginState is PluginState
    assert RootPluginLifecycle is PluginLifecycle
    assert RootPluginEntry is PluginEntry
    assert RootInvalidTransitionError is InvalidTransitionError
    assert RootDependencyError is DependencyError
    assert ROOT_KEY is PLUGIN_LIFECYCLE_KEY
    assert root_resolve_plugin_lifecycle is resolve_plugin_lifecycle


def test_plugin_entry_slotted_immutability_and_slots() -> None:
    """Verify PluginEntry uses slots=True (Rule 12)."""
    from harness.kernel.lifecycle.models import PluginEntry, PluginState

    p = StubLifecyclePlugin("test-plugin")
    entry = PluginEntry(plugin=p, state=PluginState.DISCOVERED)

    assert entry.name == "test-plugin"
    assert entry.state == PluginState.DISCOVERED
    assert hasattr(entry, "__slots__")

    # In slotted dataclasses without __dict__, assigning unknown attributes raises AttributeError
    with pytest.raises(AttributeError):
        entry.unslotted_dynamic_field = "invalid"  # type: ignore[attr-defined]


def test_transitions_table_and_validation() -> None:
    """Verify transition validation and state table rules."""
    from harness.kernel.lifecycle.models import PluginState, InvalidTransitionError
    from harness.kernel.lifecycle.transitions import validate_transition

    # Valid transition: DISCOVERED -> LOADED
    validate_transition("test", PluginState.DISCOVERED, PluginState.LOADED)

    # Invalid transition: DISCOVERED -> ENABLED
    with pytest.raises(InvalidTransitionError) as exc_info:
        validate_transition("test", PluginState.DISCOVERED, PluginState.ENABLED)
    assert exc_info.value.plugin == "test"
    assert exc_info.value.current == PluginState.DISCOVERED
    assert exc_info.value.target == PluginState.ENABLED


@pytest.mark.asyncio
async def test_sorter_dependency_graph_and_waves() -> None:
    """Verify graph builder, topological sort, and execution waves."""
    from harness.kernel.lifecycle.models import PluginEntry, PluginState
    from harness.kernel.lifecycle.sorter import (
        build_dependency_graph,
        resolve_enable_waves,
        resolve_enable_order,
    )
    from harness.kernel.graph import CyclicDependencyError

    key_a = ServiceKey("service.a")
    key_b = ServiceKey("service.b")

    p_a = StubLifecyclePlugin("plugin_a", provides=[key_a])
    p_b = StubLifecyclePlugin("plugin_b", requires=[key_a], provides=[key_b])
    p_c = StubLifecyclePlugin("plugin_c", requires=[key_b])

    entries = {
        "plugin_a": PluginEntry(plugin=p_a, state=PluginState.LOADED),
        "plugin_b": PluginEntry(plugin=p_b, state=PluginState.LOADED),
        "plugin_c": PluginEntry(plugin=p_c, state=PluginState.LOADED),
    }

    graph = build_dependency_graph(entries, ["plugin_a", "plugin_b", "plugin_c"])
    order = resolve_enable_order(graph)
    assert order == ["plugin_a", "plugin_b", "plugin_c"]

    waves = resolve_enable_waves(graph)
    assert waves == [["plugin_a"], ["plugin_b"], ["plugin_c"]]

    # Cycle detection
    p_cyclic_1 = StubLifecyclePlugin("c1", requires=[key_b], provides=[key_a])
    p_cyclic_2 = StubLifecyclePlugin("c2", requires=[key_a], provides=[key_b])
    cyclic_entries = {
        "c1": PluginEntry(plugin=p_cyclic_1, state=PluginState.LOADED),
        "c2": PluginEntry(plugin=p_cyclic_2, state=PluginState.LOADED),
    }
    c_graph = build_dependency_graph(cyclic_entries, ["c1", "c2"])
    with pytest.raises(CyclicDependencyError):
        resolve_enable_order(c_graph)


@pytest.mark.asyncio
async def test_plugin_lifecycle_full_lifecycle_and_guarded_withdrawal() -> None:
    """Verify full plugin lifecycle, guarded withdrawal, and service revocation."""
    from harness.kernel.lifecycle.manager import PluginLifecycle
    from harness.kernel.lifecycle.models import PluginState

    ctx = ServiceContext()
    lifecycle = PluginLifecycle(ctx)

    key_dep = ServiceKey("dep_service")
    p1 = StubLifecyclePlugin("provider", provides=[key_dep])
    p2 = StubLifecyclePlugin("consumer", requires=[key_dep])

    lifecycle.discover(p1)
    lifecycle.discover(p2)

    assert lifecycle.get_state("provider") == PluginState.DISCOVERED
    assert lifecycle.get_state("consumer") == PluginState.DISCOVERED

    # Advance provider
    await lifecycle.load("provider")
    await lifecycle.validate("provider")
    await lifecycle.enable("provider")
    assert lifecycle.get_state("provider") == PluginState.ENABLED
    assert ctx.has(key_dep)

    # Advance consumer
    await lifecycle.load("consumer")
    await lifecycle.validate("consumer")
    await lifecycle.enable("consumer")
    assert lifecycle.get_state("consumer") == PluginState.ENABLED

    # Check dependents
    deps = lifecycle.get_dependents("provider")
    assert "consumer" in deps

    # Guarded withdrawal: Disabling provider should first disable consumer (Theorem 63)
    await lifecycle.disable("provider", cascade=True)
    assert lifecycle.get_state("consumer") == PluginState.DISABLED
    assert lifecycle.get_state("provider") == PluginState.DISABLED

    # Unload provider: consumer was already disabled, services should be revoked
    await lifecycle.unload("provider")
    assert lifecycle.get_state("provider") == PluginState.UNLOADED
    assert not ctx.has(key_dep)


@pytest.mark.asyncio
async def test_plugin_lifecycle_atomic_operations() -> None:
    """Verify ensure_enabled, register_and_enable, and reload deep seams."""
    from harness.kernel.lifecycle.manager import PluginLifecycle
    from harness.kernel.lifecycle.models import PluginState

    ctx = ServiceContext()
    lifecycle = PluginLifecycle(ctx)

    key = ServiceKey("atomic_service")
    p = StubLifecyclePlugin("atomic_plugin", provides=[key])

    # register_and_enable
    success = await lifecycle.register_and_enable(p)
    assert success is True
    assert lifecycle.get_state("atomic_plugin") == PluginState.ENABLED
    assert ctx.has(key)

    # reload
    p_v2 = StubLifecyclePlugin("atomic_plugin", version="2.0.0", provides=[key])
    reload_success = await lifecycle.reload(p_v2)
    assert reload_success is True
    assert lifecycle.get_state("atomic_plugin") == PluginState.ENABLED
    assert lifecycle.plugins["atomic_plugin"].plugin.version == "2.0.0"

    # unload_all
    unload_res = await lifecycle.unload_all()
    assert unload_res.get("atomic_plugin") is True
    assert not ctx.has(key)


def test_resolve_plugin_lifecycle_single_seam() -> None:
    """Verify Rule 58 single-seam IoC resolution for PluginLifecycle."""
    from harness.kernel.lifecycle.manager import (
        PluginLifecycle,
        resolve_plugin_lifecycle,
    )
    from harness.kernel.lifecycle.models import PLUGIN_LIFECYCLE_KEY

    ctx = ServiceContext()

    # When not registered, resolve_plugin_lifecycle instantiates and registers it
    lifecycle1 = resolve_plugin_lifecycle(ctx)
    assert isinstance(lifecycle1, PluginLifecycle)
    assert ctx.has(PLUGIN_LIFECYCLE_KEY)

    # Subsequent resolution retrieves the cached instance
    lifecycle2 = resolve_plugin_lifecycle(ctx)
    assert lifecycle2 is lifecycle1

    # Works if object exposes lifecycle attribute
    class MockRuntime:
        def __init__(self, lc: PluginLifecycle) -> None:
            self.lifecycle = lc

    runtime = MockRuntime(lifecycle1)
    assert resolve_plugin_lifecycle(runtime) is lifecycle1
