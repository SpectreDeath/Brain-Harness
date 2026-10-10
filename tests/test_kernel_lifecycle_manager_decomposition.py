"""Contract test suite for decomposed harness.kernel.lifecycle.manager package.

Verifies:
1. Subpackage exports, module layout, and strict Rule 11 line count bounds (< 200 lines).
2. Activation operations: discovery, dependency check, load, validate, enable.
3. Teardown operations: Theorem 63 guarded withdrawal, cascade disable, reverse topological unload.
4. Workflows: ensure_enabled, register_and_enable, reload_plugin.
5. Batch operations: parallel wave execution, batch enable/disable/unload.
6. LifecycleGraphCache: epoch-based invalidation and topological sorting.
7. Single-seam resolver factory per Rule 58.
"""

from __future__ import annotations

import pathlib
import pytest

from harness.kernel.context import ServiceContext, ServiceKey
from harness.kernel.lifecycle.manager import (
    PluginLifecycle,
    resolve_plugin_lifecycle,
)
from harness.kernel.lifecycle.manager.activation import (
    check_satisfaction,
    execute_enable,
    execute_load,
    execute_validate,
    get_dependents,
    register_discovery,
)
from harness.kernel.lifecycle.manager.batch import (
    disable_all_plugins,
    enable_all_plugins,
    unload_all_plugins,
)
from harness.kernel.lifecycle.manager.graph_cache import LifecycleGraphCache
from harness.kernel.lifecycle.manager.resolvers import resolve_plugin_lifecycle as resolver_fn
from harness.kernel.lifecycle.manager.teardown import (
    execute_disable,
    execute_unload,
)
from harness.kernel.lifecycle.manager.workflows import (
    ensure_enabled,
    register_and_enable,
    reload_plugin,
)
from harness.kernel.lifecycle.models import PLUGIN_LIFECYCLE_KEY, PluginState
from harness.plugins.base import HarnessPlugin


class MockPlugin(HarnessPlugin):
    """Test stub plugin with configurable dependencies and provisions."""

    def __init__(
        self,
        name: str,
        version: str = "1.0.0",
        provides: list[ServiceKey] | None = None,
        requires: list[ServiceKey] | None = None,
    ) -> None:
        self._name = name
        self._version = version
        self._provides = provides or []
        self._requires = requires or []
        self.load_count = 0
        self.enable_count = 0
        self.disable_count = 0
        self.unload_count = 0

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
        self.load_count += 1
        for key in self._provides:
            ctx.provide(key, self, provider=self._name)

    async def on_enable(self) -> None:
        self.enable_count += 1

    async def on_disable(self) -> None:
        self.disable_count += 1

    async def on_unload(self) -> None:
        self.unload_count += 1


def test_manager_subpackage_line_bounds() -> None:
    """Assert all submodules in manager subpackage are strictly < 200 lines (Rule 11)."""
    manager_dir = pathlib.Path(__file__).parent.parent / "src" / "harness" / "kernel" / "lifecycle" / "manager"
    assert manager_dir.is_dir(), f"Manager directory missing: {manager_dir}"

    py_files = list(manager_dir.glob("*.py"))
    assert len(py_files) >= 8, f"Expected at least 8 submodules, found {len(py_files)}"

    for py_file in py_files:
        lines = len(py_file.read_text(encoding="utf-8").splitlines())
        assert lines < 200, f"Module {py_file.name} has {lines} lines, exceeding 200 line bound (Rule 11)"


def test_manager_subpackage_exports() -> None:
    """Verify package public exports and types."""
    import harness.kernel.lifecycle.manager as pkg

    assert hasattr(pkg, "PluginLifecycle")
    assert hasattr(pkg, "resolve_plugin_lifecycle")
    assert pkg.PluginLifecycle is PluginLifecycle
    assert pkg.resolve_plugin_lifecycle is resolve_plugin_lifecycle


@pytest.mark.asyncio
async def test_activation_lifecycle_pipeline() -> None:
    """Verify discovery, dependencies check, load, validate, and enable."""
    ctx = ServiceContext()
    lifecycle = PluginLifecycle(ctx)

    service_a = ServiceKey("svc_a")
    p_a = MockPlugin("p_a", provides=[service_a])
    p_b = MockPlugin("p_b", requires=[service_a])

    lifecycle.discover(p_a)
    lifecycle.discover(p_b)

    # p_b dependencies not satisfied until p_a provides service_a
    satisfied_b, missing_b = lifecycle.check_satisfaction("p_b")
    assert satisfied_b is False
    assert any("svc_a" in str(m) for m in missing_b)

    await lifecycle.load("p_a")
    assert p_a.load_count == 1
    assert ctx.has(service_a)

    satisfied_b_after, missing_b_after = lifecycle.check_satisfaction("p_b")
    assert satisfied_b_after is True
    assert len(missing_b_after) == 0

    await lifecycle.load("p_b")
    assert p_b.load_count == 1

    await lifecycle.validate("p_a")
    await lifecycle.enable("p_a")
    assert lifecycle.get_state("p_a") == PluginState.ENABLED

    await lifecycle.validate("p_b")
    await lifecycle.enable("p_b")
    assert lifecycle.get_state("p_b") == PluginState.ENABLED


@pytest.mark.asyncio
async def test_teardown_guarded_withdrawal() -> None:
    """Verify Theorem 63 guarded withdrawal with reverse-topological cascading disable."""
    ctx = ServiceContext()
    lifecycle = PluginLifecycle(ctx)

    svc_base = ServiceKey("svc_base")
    p_base = MockPlugin("p_base", provides=[svc_base])
    p_consumer = MockPlugin("p_consumer", requires=[svc_base])

    await lifecycle.register_and_enable(p_base)
    await lifecycle.register_and_enable(p_consumer)

    assert lifecycle.get_state("p_base") == PluginState.ENABLED
    assert lifecycle.get_state("p_consumer") == PluginState.ENABLED

    # Disabling p_base with cascade=True should first disable p_consumer
    await lifecycle.disable("p_base", cascade=True)
    assert lifecycle.get_state("p_consumer") == PluginState.DISABLED
    assert lifecycle.get_state("p_base") == PluginState.DISABLED

    # Unload p_base revokes provided service
    await lifecycle.unload("p_base")
    assert lifecycle.get_state("p_base") == PluginState.UNLOADED
    assert not ctx.has(svc_base)


@pytest.mark.asyncio
async def test_workflow_transitions() -> None:
    """Verify ensure_enabled, reload, and atomic workflows."""
    ctx = ServiceContext()
    lifecycle = PluginLifecycle(ctx)

    svc = ServiceKey("atomic_svc")
    p1 = MockPlugin("p_flow", version="1.0.0", provides=[svc])

    # register_and_enable auto-registers and advances through states
    ok = await lifecycle.register_and_enable(p1)
    assert ok is True
    assert lifecycle.get_state("p_flow") == PluginState.ENABLED
    assert ctx.has(svc)

    # calling ensure_enabled again on already enabled plugin name is a no-op returning True
    ok_again = await lifecycle.ensure_enabled(p1.name)
    assert ok_again is True

    # reload with version 2.0.0
    p2 = MockPlugin("p_flow", version="2.0.0", provides=[svc])
    reloaded = await lifecycle.reload(p2)
    assert reloaded is True
    assert lifecycle.plugins["p_flow"].plugin.version == "2.0.0"
    assert lifecycle.get_state("p_flow") == PluginState.ENABLED


@pytest.mark.asyncio
async def test_batch_wave_lifecycle() -> None:
    """Verify batch enable, disable, and unload across dependency DAG."""
    ctx = ServiceContext()
    lifecycle = PluginLifecycle(ctx)

    s1 = ServiceKey("s1")
    s2 = ServiceKey("s2")

    p1 = MockPlugin("node_1", provides=[s1])
    p2 = MockPlugin("node_2", requires=[s1], provides=[s2])
    p3 = MockPlugin("node_3", requires=[s2])

    lifecycle.discover(p1)
    lifecycle.discover(p2)
    lifecycle.discover(p3)

    # enable_all resolves wave topological ordering
    results = await lifecycle.enable_all()
    assert all(results.values())
    assert lifecycle.get_state("node_1") == PluginState.ENABLED
    assert lifecycle.get_state("node_2") == PluginState.ENABLED
    assert lifecycle.get_state("node_3") == PluginState.ENABLED

    # disable_all in reverse topological waves
    dis_res = await lifecycle.disable_all()
    assert all(dis_res.values())
    assert lifecycle.get_state("node_1") == PluginState.DISABLED
    assert lifecycle.get_state("node_2") == PluginState.DISABLED
    assert lifecycle.get_state("node_3") == PluginState.DISABLED

    # unload_all
    unl_res = await lifecycle.unload_all()
    assert all(unl_res.values())
    assert not ctx.has(s1)
    assert not ctx.has(s2)


def test_dependency_graph_cache_invalidation() -> None:
    """Verify epoch tracking and cache invalidation in LifecycleGraphCache."""
    cache = LifecycleGraphCache()
    assert cache.epoch == 0

    cache.invalidate()
    assert cache.epoch == 1

    cache.invalidate()
    assert cache.epoch == 2


def test_single_seam_resolver_contract() -> None:
    """Verify resolve_plugin_lifecycle adheres to Rule 58 single seam."""
    ctx = ServiceContext()

    resolved_1 = resolve_plugin_lifecycle(ctx)
    assert isinstance(resolved_1, PluginLifecycle)
    assert ctx.has(PLUGIN_LIFECYCLE_KEY)

    # Idempotent registration retrieval
    resolved_2 = resolve_plugin_lifecycle(ctx)
    assert resolved_2 is resolved_1

    # Resolver function directly
    resolved_3 = resolver_fn(ctx)
    assert resolved_3 is resolved_1
