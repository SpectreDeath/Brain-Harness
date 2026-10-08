"""Lifecycle models, states, and error types."""

from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from harness.kernel.context import ServiceKey
from harness.kernel.graph import (
    CyclicDependencyError,
    DependencyGraph,
    GraphCycleError,
)

if TYPE_CHECKING:
    from harness.kernel.lifecycle.manager import PluginLifecycle
    from harness.plugins.base import HarnessPlugin


class PluginState(enum.Enum):
    """States a plugin can be in during its lifecycle."""

    DISCOVERED = "discovered"
    LOADED = "loaded"
    VALIDATED = "validated"
    ENABLED = "enabled"
    DISABLED = "disabled"
    UNLOADED = "unloaded"
    ERROR = "error"


# Valid state transitions
_TRANSITIONS: dict[PluginState, frozenset[PluginState]] = {
    PluginState.DISCOVERED: frozenset({PluginState.LOADED, PluginState.ERROR}),
    PluginState.LOADED: frozenset(
        {PluginState.VALIDATED, PluginState.UNLOADED, PluginState.ERROR}
    ),
    PluginState.VALIDATED: frozenset(
        {PluginState.ENABLED, PluginState.UNLOADED, PluginState.ERROR}
    ),
    PluginState.ENABLED: frozenset({PluginState.DISABLED, PluginState.ERROR}),
    PluginState.DISABLED: frozenset(
        {PluginState.ENABLED, PluginState.UNLOADED, PluginState.ERROR}
    ),
    PluginState.UNLOADED: frozenset({PluginState.DISCOVERED}),
    PluginState.ERROR: frozenset({PluginState.UNLOADED, PluginState.DISCOVERED}),
}


class InvalidTransitionError(Exception):
    """Raised when attempting an invalid state transition."""

    def __init__(self, plugin: str, current: PluginState, target: PluginState) -> None:
        self.plugin = plugin
        self.current = current
        self.target = target
        super().__init__(
            f"Invalid transition for {plugin!r}: {current.value} → {target.value}"
        )


class DependencyError(Exception):
    """Raised when plugin dependencies cannot be satisfied."""

    def __init__(self, plugin: str, missing: list[str]) -> None:
        self.plugin = plugin
        self.missing = missing
        super().__init__(f"Plugin {plugin!r} has unsatisfied dependencies: {missing}")


@dataclass(slots=True)
class PluginEntry:
    """Tracks a plugin's state and metadata within the lifecycle manager."""

    plugin: HarnessPlugin
    state: PluginState = PluginState.DISCOVERED
    error: str | None = None

    @property
    def name(self) -> str:
        return self.plugin.name


PLUGIN_LIFECYCLE_KEY: ServiceKey[Any] = ServiceKey("kernel.plugin_lifecycle")

__all__ = [
    "CyclicDependencyError",
    "DependencyError",
    "DependencyGraph",
    "GraphCycleError",
    "InvalidTransitionError",
    "PLUGIN_LIFECYCLE_KEY",
    "PluginEntry",
    "PluginState",
    "_TRANSITIONS",
]
