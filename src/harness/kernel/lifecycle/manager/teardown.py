"""Plugin teardown operations: disable and unload with guarded withdrawal (Theorem 63)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog

from harness.kernel.lifecycle.manager.activation import get_dependents
from harness.kernel.lifecycle.models import (
    PluginEntry,
    PluginState,
)

if TYPE_CHECKING:
    from harness.kernel.lifecycle.manager.core import PluginLifecycle

logger = structlog.get_logger()


async def execute_disable(
    manager: PluginLifecycle,
    context: Any,
    entries: dict[str, PluginEntry],
    entry: PluginEntry,
    emit_event_fn: Any,
    name: str,
    cascade: bool = True,
) -> None:
    """Disable an enabled plugin with guarded withdrawal (Theorem 63)."""
    from harness.events.types import EventType

    if cascade:
        dependents = get_dependents(entries, name)
        active_dependents = [
            dep
            for dep in dependents
            if entries.get(dep) and entries[dep].state == PluginState.ENABLED
        ]
        if active_dependents:
            try:
                all_active = [
                    n for n, e in entries.items() if e.state == PluginState.ENABLED
                ]
                graph = manager.build_dependency_graph(all_active)
                trans_deps = graph.transitive_dependents(name)
                active_trans_deps = [
                    dep
                    for dep in trans_deps
                    if entries.get(dep) and entries[dep].state == PluginState.ENABLED
                ]
                target_deps = active_trans_deps or active_dependents
                order = manager.resolve_enable_order(target_deps)
                for dep in reversed(order):
                    await manager.disable(dep, cascade=False)
            except Exception as e:
                logger.warning(
                    "Error draining dependents during disable",
                    plugin=name,
                    error=str(e),
                )

    context.set_plugin_services_active(name, False)
    try:
        await entry.plugin.on_disable()
        emit_event_fn(EventType.PLUGIN_DISABLED, name)
    except Exception as e:
        logger.warning("Plugin disable had errors", plugin=name, error=str(e))
        emit_event_fn(EventType.PLUGIN_ERROR, name, error=str(e), stage="disable")


async def execute_unload(
    manager: PluginLifecycle,
    context: Any,
    entries: dict[str, PluginEntry],
    entry: PluginEntry,
    emit_event_fn: Any,
    name: str,
) -> None:
    """Unload a plugin and revoke its services with guarded deactivation (Theorem 63)."""
    from harness.events.types import EventType

    if entry.state == PluginState.ENABLED:
        await manager.disable(name, cascade=True)
    else:
        dependents = get_dependents(entries, name)
        active_dependents = [
            dep
            for dep in dependents
            if entries.get(dep) and entries[dep].state == PluginState.ENABLED
        ]
        if active_dependents:
            try:
                all_active = [
                    n for n, e in entries.items() if e.state == PluginState.ENABLED
                ]
                graph = manager.build_dependency_graph(all_active)
                trans_deps = graph.transitive_dependents(name)
                active_trans_deps = [
                    dep
                    for dep in trans_deps
                    if entries.get(dep) and entries[dep].state == PluginState.ENABLED
                ]
                target_deps = active_trans_deps or active_dependents
                order = manager.resolve_enable_order(target_deps)
                for dep in reversed(order):
                    await manager.disable(dep, cascade=False)
            except Exception as e:
                logger.warning(
                    "Error draining dependents during unload",
                    plugin=name,
                    error=str(e),
                )

    try:
        await entry.plugin.on_unload()
    except Exception as e:
        logger.warning("Plugin unload had errors", plugin=name, error=str(e))

    revoked = context.revoke_all_from(name)
    if revoked:
        logger.info(
            "Plugin services revoked on unload",
            plugin=name,
            services=revoked,
        )

    emit_event_fn(EventType.PLUGIN_UNLOADED, name, revoked_services=revoked or [])
