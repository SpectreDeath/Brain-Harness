"""Plugin activation operations: discovery, dependency check, load, validate, and enable."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog

from harness.kernel.lifecycle.models import (
    DependencyError,
    PluginEntry,
    PluginState,
)

if TYPE_CHECKING:
    from harness.kernel.lifecycle.manager.graph_cache import LifecycleGraphCache
    from harness.plugins.base import HarnessPlugin

logger = structlog.get_logger()


def register_discovery(
    entries: dict[str, PluginEntry],
    graph_cache: LifecycleGraphCache,
    emit_event_fn: Any,
    plugin: HarnessPlugin,
) -> None:
    """Register a newly discovered plugin."""
    if plugin.name in entries:
        existing = entries[plugin.name]
        if existing.state not in (PluginState.UNLOADED, PluginState.ERROR):
            logger.warning(
                "Plugin already tracked, skipping",
                plugin=plugin.name,
                state=existing.state.value,
            )
            return

    entries[plugin.name] = PluginEntry(plugin=plugin)
    graph_cache.invalidate()
    logger.info("Plugin discovered", plugin=plugin.name, version=plugin.version)
    from harness.events.types import EventType

    emit_event_fn(
        EventType.PLUGIN_DISCOVERED,
        plugin.name,
        version=getattr(plugin, "version", "0.1.0"),
        description=getattr(plugin, "description", ""),
    )


def get_dependents(entries: dict[str, PluginEntry], name: str) -> list[str]:
    """Find all tracked plugins that require services provided by *name* (Definition 50)."""
    entry = entries.get(name)
    if entry is None:
        return []

    provided_key_names = {
        k.name if hasattr(k, "name") else str(k) for k in entry.plugin.provides
    }
    if not provided_key_names:
        return []

    dependents: list[str] = []
    for other_name, other_entry in entries.items():
        if other_name == name:
            continue
        req_names = {
            k.name if hasattr(k, "name") else str(k)
            for k in other_entry.plugin.requires
        }
        if req_names & provided_key_names:
            dependents.append(other_name)
    return dependents


def check_satisfaction(
    context: Any, entries: dict[str, PluginEntry], name: str
) -> tuple[bool, list[str]]:
    """Check coeffect satisfaction predicate (sigma |= d) for a plugin (Definition 24)."""
    entry = entries.get(name)
    if entry is None:
        return False, []

    missing: list[str] = []
    for key in entry.plugin.requires:
        if not context.has(key):
            missing.append(key.name if hasattr(key, "name") else str(key))
    return len(missing) == 0, missing


async def execute_load(
    context: Any, entry: PluginEntry, emit_event_fn: Any, name: str
) -> None:
    """Execute plugin on_load hook with scoped context."""
    from harness.events.types import EventType

    try:
        scoped_ctx = context.for_plugin(name)
        await entry.plugin.on_load(scoped_ctx)
        emit_event_fn(
            EventType.PLUGIN_LOADED,
            name,
            provides=[
                k.name if hasattr(k, "name") else str(k)
                for k in getattr(entry.plugin, "provides", [])
            ],
            requires=[
                k.name if hasattr(k, "name") else str(k)
                for k in getattr(entry.plugin, "requires", [])
            ],
        )
    except Exception as e:
        entry.state = PluginState.ERROR
        entry.error = str(e)
        logger.error("Plugin load failed", plugin=name, error=str(e))
        emit_event_fn(EventType.PLUGIN_ERROR, name, error=str(e), stage="load")
        raise


async def execute_validate(
    context: Any,
    entries: dict[str, PluginEntry],
    entry: PluginEntry,
    emit_event_fn: Any,
    name: str,
) -> None:
    """Validate a loaded plugin's dependencies and configuration."""
    from harness.events.types import EventType

    missing = []
    for key in entry.plugin.requires:
        if not context.has(key):
            provided_by_others = any(
                key in other.plugin.provides
                for other_name, other in entries.items()
                if other_name != name
                and other.state
                in (PluginState.LOADED, PluginState.VALIDATED, PluginState.ENABLED)
            )
            if not provided_by_others:
                missing.append(key.name if hasattr(key, "name") else str(key))

    if missing:
        entry.state = PluginState.ERROR
        entry.error = f"Missing dependencies: {missing}"
        emit_event_fn(
            EventType.PLUGIN_ERROR,
            name,
            error=entry.error,
            missing_dependencies=missing,
            stage="validate",
        )
        raise DependencyError(name, missing)

    emit_event_fn(EventType.PLUGIN_VALIDATED, name)


async def execute_enable(
    context: Any, entry: PluginEntry, emit_event_fn: Any, name: str
) -> None:
    """Execute plugin on_enable hook and activate services in context."""
    from harness.events.types import EventType

    try:
        context.set_plugin_services_active(name, True)
        await entry.plugin.on_enable()
        emit_event_fn(EventType.PLUGIN_ENABLED, name)
    except Exception as e:
        context.set_plugin_services_active(name, False)
        entry.state = PluginState.ERROR
        entry.error = str(e)
        logger.error("Plugin enable failed", plugin=name, error=str(e))
        emit_event_fn(EventType.PLUGIN_ERROR, name, error=str(e), stage="enable")
        raise
