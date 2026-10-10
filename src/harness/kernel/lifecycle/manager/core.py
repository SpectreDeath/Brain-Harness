"""PluginLifecycle coordinator class orchestrating state transitions and dependency resolution."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog

from harness.kernel.graph import DependencyGraph
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
from harness.kernel.lifecycle.manager.teardown import (
    execute_disable,
    execute_unload,
)
from harness.kernel.lifecycle.manager.workflows import (
    ensure_enabled,
    register_and_enable,
    reload_plugin,
)
from harness.kernel.lifecycle.models import (
    PluginEntry,
    PluginState,
)
from harness.kernel.lifecycle.transitions import (
    emit_lifecycle_event,
    validate_transition,
)

if TYPE_CHECKING:
    from harness.kernel.context import ServiceContext
    from harness.plugins.base import HarnessPlugin

logger = structlog.get_logger()


class PluginLifecycle:
    """Manages plugin state transitions with dependency resolution."""

    def __init__(self, context: ServiceContext, event_bus: Any | None = None) -> None:
        self._context = context
        self._event_bus = event_bus or getattr(context, "event_bus", None)
        self._entries: dict[str, PluginEntry] = {}
        self._graph_cache = LifecycleGraphCache()

    @property
    def event_bus(self) -> Any | None:
        return self._event_bus or getattr(self._context, "event_bus", None)

    def attach_event_bus(self, event_bus: Any) -> None:
        self._event_bus = event_bus

    def _emit_event(self, event_type: Any, plugin_name: str, **extra: Any) -> None:
        emit_lifecycle_event(self.event_bus, event_type, plugin_name, **extra)

    @property
    def plugins(self) -> dict[str, PluginEntry]:
        return dict(self._entries)

    def _transition(self, name: str, target: PluginState) -> None:
        entry = self._entries.get(name)
        if entry is None:
            raise KeyError(f"Plugin not found: {name!r}")
        validate_transition(name, entry.state, target)
        old_state, entry.state = entry.state, target
        if target != PluginState.ERROR:
            entry.error = None
        if target in (PluginState.ENABLED, PluginState.DISABLED, PluginState.UNLOADED, PluginState.ERROR):
            self._graph_cache.invalidate()
        logger.info("Plugin state transition", plugin=name, from_state=old_state.value, to_state=target.value)

    def discover(self, plugin: HarnessPlugin) -> None:
        """Register a newly discovered plugin."""
        register_discovery(self._entries, self._graph_cache, self._emit_event, plugin)

    async def load(self, name: str) -> None:
        """Load a discovered plugin."""
        entry = self._entries.get(name)
        if entry is None:
            raise KeyError(f"Plugin not found: {name!r}")
        self._transition(name, PluginState.LOADED)
        await execute_load(self._context, entry, self._emit_event, name)

    async def validate(self, name: str) -> None:
        """Validate a loaded plugin's dependencies and configuration."""
        entry = self._entries.get(name)
        if entry is None:
            raise KeyError(f"Plugin not found: {name!r}")
        await execute_validate(self._context, self._entries, entry, self._emit_event, name)
        self._transition(name, PluginState.VALIDATED)

    async def enable(self, name: str) -> None:
        """Enable a validated plugin."""
        entry = self._entries.get(name)
        if entry is None:
            raise KeyError(f"Plugin not found: {name!r}")
        self._transition(name, PluginState.ENABLED)
        await execute_enable(self._context, entry, self._emit_event, name)

    def get_dependents(self, name: str) -> list[str]:
        return get_dependents(self._entries, name)

    def check_satisfaction(self, name: str) -> tuple[bool, list[str]]:
        return check_satisfaction(self._context, self._entries, name)

    async def disable(self, name: str, *, cascade: bool = True) -> None:
        entry = self._entries.get(name)
        if entry is None:
            raise KeyError(f"Plugin not found: {name!r}")
        await execute_disable(self, self._context, self._entries, entry, self._emit_event, name, cascade=cascade)
        self._transition(name, PluginState.DISABLED)

    async def unload(self, name: str) -> None:
        entry = self._entries.get(name)
        if entry is None:
            raise KeyError(f"Plugin not found: {name!r}")
        await execute_unload(self, self._context, self._entries, entry, self._emit_event, name)
        self._transition(name, PluginState.UNLOADED)

    async def ensure_enabled(self, name: str) -> bool:
        return await ensure_enabled(self, self._entries, name)

    async def register_and_enable(self, plugin: HarnessPlugin) -> bool:
        return await register_and_enable(self, plugin)

    async def reload(self, plugin: HarnessPlugin) -> bool:
        return await reload_plugin(self, self._entries, plugin)

    def build_dependency_graph(self, names: list[str] | None = None) -> DependencyGraph[str]:
        return self._graph_cache.get_or_build(self._entries, names)

    def resolve_enable_waves(self, names: list[str] | None = None) -> list[list[str]]:
        return self._graph_cache.resolve_waves(self._entries, names)

    def resolve_enable_order(self, names: list[str] | None = None) -> list[str]:
        return self._graph_cache.resolve_order(self._entries, names)

    async def enable_all(
        self,
        *,
        trusted_only: bool = False,
        skip_user_plugins: bool = False,
        enable_timeout: float = 30.0,
    ) -> dict[str, bool]:
        return await enable_all_plugins(
            self, self._context, self._entries,
            trusted_only=trusted_only, skip_user_plugins=skip_user_plugins, enable_timeout=enable_timeout
        )

    async def disable_all(self) -> dict[str, bool]:
        return await disable_all_plugins(self, self._entries)

    async def unload_all(self) -> dict[str, bool]:
        return await unload_all_plugins(self, self._entries)

    def get_state(self, name: str) -> PluginState:
        entry = self._entries.get(name)
        if entry is None:
            raise KeyError(f"Plugin not found: {name!r}")
        return entry.state

    def get_error(self, name: str) -> str | None:
        entry = self._entries.get(name)
        if entry is None:
            raise KeyError(f"Plugin not found: {name!r}")
        return entry.error

    def summary(self) -> dict[str, str]:
        return {name: entry.state.value for name, entry in self._entries.items()}
