"""Plugin lifecycle manager — state machine and dependency resolution facade.

Decomposed into:
- models: PluginState, PluginEntry, transitions map, error types, and service key.
- transitions: Transition validation and event emission helpers.
- sorter: DependencyGraph builder, topological sorting, and execution waves.
- manager: PluginLifecycle orchestrator and resolve_plugin_lifecycle IoC factory.
"""

from __future__ import annotations

from harness.kernel.graph import (
    CyclicDependencyError,
    DependencyGraph,
    GraphCycleError,
)
from harness.kernel.lifecycle.manager import (
    PluginLifecycle,
    resolve_plugin_lifecycle,
)
from harness.kernel.lifecycle.models import (
    PLUGIN_LIFECYCLE_KEY,
    DependencyError,
    InvalidTransitionError,
    PluginEntry,
    PluginState,
    _TRANSITIONS,
)
from harness.kernel.lifecycle.sorter import (
    build_dependency_graph,
    resolve_enable_order,
    resolve_enable_waves,
)
from harness.kernel.lifecycle.transitions import (
    emit_lifecycle_event,
    validate_transition,
)

__all__ = [
    "CyclicDependencyError",
    "DependencyError",
    "DependencyGraph",
    "GraphCycleError",
    "InvalidTransitionError",
    "PLUGIN_LIFECYCLE_KEY",
    "PluginEntry",
    "PluginLifecycle",
    "PluginState",
    "_TRANSITIONS",
    "build_dependency_graph",
    "emit_lifecycle_event",
    "resolve_enable_order",
    "resolve_enable_waves",
    "resolve_plugin_lifecycle",
    "validate_transition",
]
