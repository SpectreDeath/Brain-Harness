"""Tests for the PluginLifecycle manager."""

import pytest

from harness.kernel.context import ServiceContext, ServiceKey
from harness.kernel.graph import topological_sort
from harness.kernel.lifecycle import (
    CyclicDependencyError,
    DependencyError,
    InvalidTransitionError,
    PluginLifecycle,
    PluginState,
)
from harness.plugins.base import HarnessPlugin


class StubPlugin(HarnessPlugin):
    """Minimal plugin for testing."""

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
        self.loaded = False


@pytest.mark.unit
@pytest.mark.asyncio
class TestPluginLifecycle:
    async def test_discover(self) -> None:
        ctx = ServiceContext()
        lc = PluginLifecycle(ctx)
        plugin = StubPlugin("test")
        lc.discover(plugin)
        assert lc.get_state("test") == PluginState.DISCOVERED

    async def test_full_lifecycle(self) -> None:
        ctx = ServiceContext()
        lc = PluginLifecycle(ctx)
        plugin = StubPlugin("test")

        lc.discover(plugin)
        assert lc.get_state("test") == PluginState.DISCOVERED

        await lc.load("test")
        assert lc.get_state("test") == PluginState.LOADED
        assert plugin.loaded

        await lc.validate("test")
        assert lc.get_state("test") == PluginState.VALIDATED

        await lc.enable("test")
        assert lc.get_state("test") == PluginState.ENABLED
        assert plugin.enabled

        await lc.disable("test")
        assert lc.get_state("test") == PluginState.DISABLED
        assert not plugin.enabled

        await lc.unload("test")
        assert lc.get_state("test") == PluginState.UNLOADED

    async def test_invalid_transition(self) -> None:
        ctx = ServiceContext()
        lc = PluginLifecycle(ctx)
        plugin = StubPlugin("test")
        lc.discover(plugin)

        with pytest.raises(InvalidTransitionError):
            await lc.enable("test")  # Can't enable from DISCOVERED

    async def test_missing_dependency(self) -> None:
        ctx = ServiceContext()
        lc = PluginLifecycle(ctx)
        dep_key = ServiceKey[str]("missing.service")
        plugin = StubPlugin("needy", requires=[dep_key])

        lc.discover(plugin)
        await lc.load("needy")

        with pytest.raises(DependencyError):
            await lc.validate("needy")

    async def test_dependency_satisfied_by_other_plugin(self) -> None:
        ctx = ServiceContext()
        lc = PluginLifecycle(ctx)

        svc_key = ServiceKey[str]("shared.service")
        provider = StubPlugin("provider", provides=[svc_key])
        consumer = StubPlugin("consumer", requires=[svc_key])

        lc.discover(provider)
        lc.discover(consumer)

        await lc.load("provider")
        await lc.load("consumer")

        # Provider validates first and provides the service
        await lc.validate("provider")
        # Consumer should validate because provider is loaded
        await lc.validate("consumer")

    async def test_unload_revokes_services(self) -> None:
        ctx = ServiceContext()
        lc = PluginLifecycle(ctx)
        key = ServiceKey[str]("my.service")
        plugin = StubPlugin("provider", provides=[key])

        lc.discover(plugin)
        await lc.load("provider")
        assert ctx.has(key)

        await lc.validate("provider")
        await lc.enable("provider")
        await lc.unload("provider")
        assert not ctx.has(key)

    async def test_enable_all_order(self) -> None:
        ctx = ServiceContext()
        lc = PluginLifecycle(ctx)

        svc_key = ServiceKey[str]("base.service")
        base = StubPlugin("base", provides=[svc_key])
        dependent = StubPlugin("dependent", requires=[svc_key])

        lc.discover(base)
        lc.discover(dependent)
        await lc.load("base")
        await lc.load("dependent")
        await lc.validate("base")
        await lc.validate("dependent")

        results = await lc.enable_all()
        assert results["base"] is True
        assert results["dependent"] is True

    async def test_summary(self) -> None:
        ctx = ServiceContext()
        lc = PluginLifecycle(ctx)
        lc.discover(StubPlugin("a"))
        lc.discover(StubPlugin("b"))

        summary = lc.summary()
        assert summary == {"a": "discovered", "b": "discovered"}

    async def test_resolve_enable_order(self) -> None:
        ctx = ServiceContext()
        lc = PluginLifecycle(ctx)

        k1 = ServiceKey[str]("svc.a")
        k2 = ServiceKey[str]("svc.b")

        a = StubPlugin("a", provides=[k1])
        b = StubPlugin("b", provides=[k2], requires=[k1])

        lc.discover(a)
        lc.discover(b)
        await lc.load("a")
        await lc.load("b")

        order = lc.resolve_enable_order(["a", "b"])
        assert order.index("a") < order.index("b")

    async def test_diamond_dependency_order(self) -> None:
        """A→B, A→C, B→D, C→D (diamond). D must come first, A last."""
        ctx = ServiceContext()
        lc = PluginLifecycle(ctx)

        k_d = ServiceKey[str]("svc.d")
        k_b = ServiceKey[str]("svc.b")
        k_c = ServiceKey[str]("svc.c")

        d = StubPlugin("d", provides=[k_d])
        b = StubPlugin("b", provides=[k_b], requires=[k_d])
        c = StubPlugin("c", provides=[k_c], requires=[k_d])
        a = StubPlugin("a", requires=[k_b, k_c])

        for p in [d, b, c, a]:
            lc.discover(p)
            await lc.load(p.name)
            await lc.validate(p.name)

        order = lc.resolve_enable_order(["a", "b", "c", "d"])
        assert order.index("d") < order.index("b")
        assert order.index("d") < order.index("c")
        assert order.index("b") < order.index("a")
        assert order.index("c") < order.index("a")


@pytest.mark.unit
class TestTopologicalSort:
    """Unit tests for the pure topological_sort function."""

    def test_linear_chain(self) -> None:
        # a → b → c  (a depends on b, b depends on c)
        order = topological_sort(
            nodes=["a", "b", "c"],
            edges={"a": {"b"}, "b": {"c"}},
        )
        assert order.index("c") < order.index("b") < order.index("a")

    def test_independent_nodes(self) -> None:
        order = topological_sort(nodes=["x", "y", "z"], edges={})
        assert set(order) == {"x", "y", "z"}

    def test_diamond(self) -> None:
        # d is depended on by b and c; a depends on both b and c
        order = topological_sort(
            nodes=["a", "b", "c", "d"],
            edges={"a": {"b", "c"}, "b": {"d"}, "c": {"d"}},
        )
        assert order.index("d") < order.index("b")
        assert order.index("d") < order.index("c")
        assert order.index("b") < order.index("a")
        assert order.index("c") < order.index("a")

    def test_single_node(self) -> None:
        assert topological_sort(nodes=["solo"], edges={}) == ["solo"]

    def test_cycle_raises(self) -> None:
        with pytest.raises(CyclicDependencyError):
            topological_sort(
                nodes=["a", "b"],
                edges={"a": {"b"}, "b": {"a"}},
            )

    def test_self_loop_raises(self) -> None:
        with pytest.raises(CyclicDependencyError):
            topological_sort(nodes=["a"], edges={"a": {"a"}})
