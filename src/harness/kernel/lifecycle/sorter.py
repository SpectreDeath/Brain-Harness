"""Dependency graph construction, topological sorting, and parallel execution waves."""

from __future__ import annotations

from typing import TYPE_CHECKING

from harness.kernel.graph import (
    CyclicDependencyError,
    DependencyGraph,
    GraphCycleError,
)
from harness.kernel.lifecycle.models import PluginEntry, PluginState

if TYPE_CHECKING:
    pass


def build_dependency_graph(
    entries: dict[str, PluginEntry],
    names: list[str] | None = None,
) -> DependencyGraph[str]:
    """Construct a DependencyGraph for tracked or specified plugins."""
    if names is None:
        names = [
            n
            for n, e in entries.items()
            if e.state
            in (PluginState.VALIDATED, PluginState.LOADED, PluginState.DISABLED)
        ]

    graph = DependencyGraph[str]()
    for n in names:
        graph.add_node(n)

    # Build a provides -> plugin_name lookup
    provider_map: dict[str, str] = {}
    for name in names:
        entry = entries.get(name)
        if entry:
            for key in entry.plugin.provides:
                provider_map[key.name] = name

    # Add directed dependency edges (dep_plugin must load before name)
    for name in names:
        entry = entries.get(name)
        if entry:
            for key in entry.plugin.requires:
                dep_plugin = provider_map.get(key.name)
                if dep_plugin and dep_plugin != name and graph.has_node(dep_plugin):
                    graph.add_edge(from_node=dep_plugin, to_node=name)

    return graph


def resolve_enable_waves(graph: DependencyGraph[str]) -> list[list[str]]:
    """Compute parallel execution waves for enabling plugins."""
    try:
        return graph.execution_waves()
    except GraphCycleError as e:
        raise CyclicDependencyError(e.cycle) from e


def resolve_enable_order(graph: DependencyGraph[str]) -> list[str]:
    """Topological sort of plugins by their dependency graph."""
    try:
        return graph.topological_sort()
    except GraphCycleError as e:
        raise CyclicDependencyError(e.cycle) from e


__all__ = [
    "build_dependency_graph",
    "resolve_enable_order",
    "resolve_enable_waves",
]
