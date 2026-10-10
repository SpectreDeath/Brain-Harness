"""Dependency graph caching and topological order resolution."""

from __future__ import annotations

from typing import TYPE_CHECKING

from harness.kernel.graph import DependencyGraph
from harness.kernel.lifecycle.models import PluginEntry, PluginState
from harness.kernel.lifecycle.sorter import (
    build_dependency_graph as _build_graph,
    resolve_enable_order as _resolve_order,
    resolve_enable_waves as _resolve_waves,
)


class LifecycleGraphCache:
    """Manages epoch-invalidated dependency graphs and topological waves."""

    def __init__(self) -> None:
        self.epoch: int = 0
        self._cached: tuple[int, tuple[str, ...], DependencyGraph[str]] | None = None

    def invalidate(self) -> None:
        """Bump epoch to invalidate cached graphs."""
        self.epoch += 1

    def get_or_build(
        self, entries: dict[str, PluginEntry], names: list[str] | None = None
    ) -> DependencyGraph[str]:
        """Construct or return cached DependencyGraph."""
        if names is None:
            names = [
                n
                for n, e in entries.items()
                if e.state
                in (PluginState.VALIDATED, PluginState.LOADED, PluginState.DISABLED)
            ]

        names_key = tuple(sorted(names))
        if self._cached is not None:
            cached_epoch, cached_names, cached_g = self._cached
            if cached_epoch == self.epoch and cached_names == names_key:
                return cached_g

        graph = _build_graph(entries, names)
        self._cached = (self.epoch, names_key, graph)
        return graph

    def resolve_waves(
        self, entries: dict[str, PluginEntry], names: list[str] | None = None
    ) -> list[list[str]]:
        """Compute parallel execution waves."""
        graph = self.get_or_build(entries, names)
        return _resolve_waves(graph)

    def resolve_order(
        self, entries: dict[str, PluginEntry], names: list[str] | None = None
    ) -> list[str]:
        """Compute topological dependency-safe enable order."""
        graph = self.get_or_build(entries, names)
        return _resolve_order(graph)
