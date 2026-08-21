"""Plugin lifecycle manager — state machine and dependency resolution.

Manages plugin transitions through the lifecycle:

    DISCOVERED → LOADED → VALIDATED → ENABLED ⇄ DISABLED → UNLOADED

When a plugin is unloaded, all services it provided are automatically
revoked from the ServiceContext.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from harness.kernel.context import ServiceContext
    from harness.plugins.base import HarnessPlugin

logger = structlog.get_logger()


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
    PluginState.LOADED: frozenset({PluginState.VALIDATED, PluginState.UNLOADED, PluginState.ERROR}),
    PluginState.VALIDATED: frozenset({PluginState.ENABLED, PluginState.UNLOADED, PluginState.ERROR}),
    PluginState.ENABLED: frozenset({PluginState.DISABLED, PluginState.ERROR}),
    PluginState.DISABLED: frozenset({PluginState.ENABLED, PluginState.UNLOADED, PluginState.ERROR}),
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
        super().__init__(
            f"Plugin {plugin!r} has unsatisfied dependencies: {missing}"
        )


class CyclicDependencyError(Exception):
    """Raised when a dependency cycle is detected."""

    def __init__(self, cycle: list[str]) -> None:
        self.cycle = cycle
        super().__init__(f"Cyclic dependency detected: {' → '.join(cycle)}")


@dataclass
class PluginEntry:
    """Tracks a plugin's state and metadata within the lifecycle manager."""

    plugin: HarnessPlugin
    state: PluginState = PluginState.DISCOVERED
    error: str | None = None

    @property
    def name(self) -> str:
        return self.plugin.name


class PluginLifecycle:
    """Manages plugin state transitions with dependency resolution.

    Ensures plugins are enabled in dependency order (topological sort)
    and disabled/unloaded in reverse order. When a plugin is unloaded,
    its services are automatically revoked from the context.
    """

    def __init__(
        self,
        context: ServiceContext,
        event_bus: Any | None = None,
    ) -> None:
        self._context = context
        self._event_bus = event_bus or getattr(context, "event_bus", None)
        self._entries: dict[str, PluginEntry] = {}

    @property
    def event_bus(self) -> Any | None:
        """Attached event bus, if any."""
        return self._event_bus or getattr(self._context, "event_bus", None)

    def attach_event_bus(self, event_bus: Any) -> None:
        """Attach an event bus for lifecycle telemetry."""
        self._event_bus = event_bus

    def _emit_event(self, event_type: Any, plugin_name: str, **extra: Any) -> None:
        """Emit a lifecycle event onto the attached event bus."""
        bus = self.event_bus
        if bus is not None:
            from harness.events.types import plugin_event

            evt = plugin_event(event_type, plugin_name, **extra)
            bus.fire(evt)

    @property
    def plugins(self) -> dict[str, PluginEntry]:
        """All tracked plugins and their entries."""
        return dict(self._entries)

    def _transition(self, name: str, target: PluginState) -> None:
        """Validate and perform a state transition."""
        entry = self._entries.get(name)
        if entry is None:
            raise KeyError(f"Plugin not found: {name!r}")

        valid_targets = _TRANSITIONS.get(entry.state, frozenset())
        if target not in valid_targets:
            raise InvalidTransitionError(name, entry.state, target)

        old_state = entry.state
        entry.state = target
        if target != PluginState.ERROR:
            entry.error = None

        logger.info(
            "Plugin state transition",
            plugin=name,
            from_state=old_state.value,
            to_state=target.value,
        )

    # --- Lifecycle operations ---

    def discover(self, plugin: HarnessPlugin) -> None:
        """Register a newly discovered plugin."""
        if plugin.name in self._entries:
            existing = self._entries[plugin.name]
            if existing.state not in (PluginState.UNLOADED, PluginState.ERROR):
                logger.warning(
                    "Plugin already tracked, skipping",
                    plugin=plugin.name,
                    state=existing.state.value,
                )
                return

        self._entries[plugin.name] = PluginEntry(plugin=plugin)
        logger.info("Plugin discovered", plugin=plugin.name, version=plugin.version)
        from harness.events.types import EventType

        self._emit_event(
            EventType.PLUGIN_DISCOVERED,
            plugin.name,
            version=getattr(plugin, "version", "0.1.0"),
            description=getattr(plugin, "description", ""),
        )

    async def load(self, name: str) -> None:
        """Load a discovered plugin."""
        entry = self._entries.get(name)
        if entry is None:
            raise KeyError(f"Plugin not found: {name!r}")

        self._transition(name, PluginState.LOADED)
        from harness.events.types import EventType

        try:
            scoped_ctx = self._context.for_plugin(name)
            await entry.plugin.on_load(scoped_ctx)
            self._emit_event(
                EventType.PLUGIN_LOADED,
                name,
                provides=[k.name if hasattr(k, "name") else str(k) for k in getattr(entry.plugin, "provides", [])],
                requires=[k.name if hasattr(k, "name") else str(k) for k in getattr(entry.plugin, "requires", [])],
            )
        except Exception as e:
            entry.state = PluginState.ERROR
            entry.error = str(e)
            logger.error("Plugin load failed", plugin=name, error=str(e))
            self._emit_event(EventType.PLUGIN_ERROR, name, error=str(e), stage="load")
            raise

    async def validate(self, name: str) -> None:
        """Validate a loaded plugin's dependencies and configuration."""
        entry = self._entries.get(name)
        if entry is None:
            raise KeyError(f"Plugin not found: {name!r}")

        from harness.events.types import EventType

        # Check that all required services exist (or will be provided by
        # another plugin in the current batch)
        missing = []
        for key in entry.plugin.requires:
            if not self._context.has(key):
                # Check if any other loaded plugin provides it
                provided_by_others = any(
                    key in other.plugin.provides
                    for other_name, other in self._entries.items()
                    if other_name != name
                    and other.state
                    in (PluginState.LOADED, PluginState.VALIDATED, PluginState.ENABLED)
                )
                if not provided_by_others:
                    missing.append(key.name)

        if missing:
            entry.state = PluginState.ERROR
            entry.error = f"Missing dependencies: {missing}"
            self._emit_event(
                EventType.PLUGIN_ERROR,
                name,
                error=entry.error,
                missing_dependencies=missing,
                stage="validate",
            )
            raise DependencyError(name, missing)

        self._transition(name, PluginState.VALIDATED)
        self._emit_event(EventType.PLUGIN_VALIDATED, name)

    async def enable(self, name: str) -> None:
        """Enable a validated plugin."""
        entry = self._entries.get(name)
        if entry is None:
            raise KeyError(f"Plugin not found: {name!r}")

        self._transition(name, PluginState.ENABLED)
        from harness.events.types import EventType

        try:
            self._context.set_plugin_services_active(name, True)
            await entry.plugin.on_enable()
            self._emit_event(EventType.PLUGIN_ENABLED, name)
        except Exception as e:
            self._context.set_plugin_services_active(name, False)
            entry.state = PluginState.ERROR
            entry.error = str(e)
            logger.error("Plugin enable failed", plugin=name, error=str(e))
            self._emit_event(EventType.PLUGIN_ERROR, name, error=str(e), stage="enable")
            raise

    def get_dependents(self, name: str) -> list[str]:
        """Find all tracked plugins that require services provided by *name* (Definition 50)."""
        entry = self._entries.get(name)
        if entry is None:
            return []

        provided_key_names = {
            k.name if hasattr(k, "name") else str(k) for k in entry.plugin.provides
        }
        if not provided_key_names:
            return []

        dependents: list[str] = []
        for other_name, other_entry in self._entries.items():
            if other_name == name:
                continue
            req_names = {
                k.name if hasattr(k, "name") else str(k) for k in other_entry.plugin.requires
            }
            if req_names & provided_key_names:
                dependents.append(other_name)
        return dependents

    def check_satisfaction(self, name: str) -> tuple[bool, list[str]]:
        """Check coeffect satisfaction predicate (σ ⊧ d) for a plugin (Definition 24).

        Returns:
            Tuple of (is_satisfied, list_of_missing_keys).
        """
        entry = self._entries.get(name)
        if entry is None:
            return False, []

        missing: list[str] = []
        for key in entry.plugin.requires:
            if not self._context.has(key):
                missing.append(key.name if hasattr(key, "name") else str(key))
        return len(missing) == 0, missing

    async def disable(self, name: str, *, cascade: bool = True) -> None:
        """Disable an enabled plugin.

        When *cascade* is True, active dependents are disabled first (Guarded Withdrawal, Theorem 63)
        to prevent dangling dependencies during teardown.
        """
        entry = self._entries.get(name)
        if entry is None:
            raise KeyError(f"Plugin not found: {name!r}")

        # Guarded withdrawal: disable active dependents before disabling this provider
        if cascade:
            dependents = self.get_dependents(name)
            active_dependents = [
                dep
                for dep in dependents
                if self._entries.get(dep) and self._entries[dep].state == PluginState.ENABLED
            ]
            if active_dependents:
                try:
                    order = self.resolve_enable_order(active_dependents)
                    for dep in reversed(order):
                        await self.disable(dep, cascade=True)
                except Exception as e:
                    logger.warning("Error draining dependents during disable", plugin=name, error=str(e))

        self._transition(name, PluginState.DISABLED)
        self._context.set_plugin_services_active(name, False)
        from harness.events.types import EventType

        try:
            await entry.plugin.on_disable()
            self._emit_event(EventType.PLUGIN_DISABLED, name)
        except Exception as e:
            logger.warning("Plugin disable had errors", plugin=name, error=str(e))
            self._emit_event(EventType.PLUGIN_ERROR, name, error=str(e), stage="disable")

    async def unload(self, name: str) -> None:
        """Unload a plugin and revoke all its services with guarded deactivation (Theorem 63).

        Ensures that any dependent plugins are disabled and torn down first while
        this plugin's services are still accessible, before final revocation.
        """
        entry = self._entries.get(name)
        if entry is None:
            raise KeyError(f"Plugin not found: {name!r}")

        # If enabled, disable first (which cascades to dependents)
        if entry.state == PluginState.ENABLED:
            await self.disable(name, cascade=True)
        else:
            # If disabled or loaded, ensure any remaining active dependents are drained
            dependents = self.get_dependents(name)
            active_dependents = [
                dep
                for dep in dependents
                if self._entries.get(dep) and self._entries[dep].state == PluginState.ENABLED
            ]
            if active_dependents:
                try:
                    order = self.resolve_enable_order(active_dependents)
                    for dep in reversed(order):
                        await self.disable(dep, cascade=True)
                except Exception as e:
                    logger.warning("Error draining dependents during unload", plugin=name, error=str(e))

        self._transition(name, PluginState.UNLOADED)
        from harness.events.types import EventType

        try:
            await entry.plugin.on_unload()
        except Exception as e:
            logger.warning("Plugin unload had errors", plugin=name, error=str(e))

        # Revoke all services this plugin provided
        revoked = self._context.revoke_all_from(name)
        if revoked:
            logger.info(
                "Plugin services revoked on unload",
                plugin=name,
                services=revoked,
            )

        self._emit_event(EventType.PLUGIN_UNLOADED, name, revoked_services=revoked or [])


    async def ensure_enabled(self, name: str) -> bool:
        """Advance a plugin from its current state directly to ENABLED.

        Automatically executes any missing prerequisite transitions:
        DISCOVERED → LOADED → VALIDATED → ENABLED (or DISABLED → ENABLED).
        If any step fails, records the error and returns False.

        Args:
            name: Plugin name to enable.

        Returns:
            True if plugin reached ENABLED state, False otherwise.
        """
        entry = self._entries.get(name)
        if entry is None:
            raise KeyError(f"Plugin not found: {name!r}")

        if entry.state == PluginState.ENABLED:
            return True

        try:
            if entry.state in (PluginState.DISCOVERED, PluginState.UNLOADED):
                if entry.state == PluginState.UNLOADED:
                    self.discover(entry.plugin)
                await self.load(name)

            if entry.state == PluginState.LOADED:
                await self.validate(name)

            if entry.state in (PluginState.VALIDATED, PluginState.DISABLED):
                await self.enable(name)

            return entry.state == PluginState.ENABLED
        except Exception as e:
            logger.error("ensure_enabled failed", plugin=name, error=str(e))
            return False

    async def register_and_enable(self, plugin: HarnessPlugin) -> bool:
        """Atomically register, load, validate, and enable a plugin in one call.

        Provides a deep, single-call seam for callers adding dynamic or ingested plugins.

        Args:
            plugin: The plugin instance to register and activate.

        Returns:
            True if plugin was successfully registered and enabled, False otherwise.
        """
        self.discover(plugin)
        return await self.ensure_enabled(plugin.name)

    async def reload(self, plugin: HarnessPlugin) -> bool:
        """Atomically reload or hot-swap an active or modified plugin instance.

        If the plugin is currently tracked and in LOADED, VALIDATED, ENABLED,
        or DISABLED state, gracefully unloads it (revoking old service registrations),
        re-registers the updated instance, and advances it back to ENABLED.

        Args:
            plugin: The new or updated HarnessPlugin instance.

        Returns:
            True if plugin was successfully reloaded and enabled, False otherwise.
        """
        name = plugin.name
        if name in self._entries:
            entry = self._entries[name]
            if entry.state in (
                PluginState.LOADED,
                PluginState.VALIDATED,
                PluginState.ENABLED,
                PluginState.DISABLED,
            ):
                try:
                    await self.unload(name)
                except Exception as e:
                    logger.warning(
                        "Unload during plugin reload encountered warning",
                        plugin=name,
                        error=str(e),
                    )

        self.discover(plugin)
        return await self.ensure_enabled(name)

    # --- Batch operations ---

    def resolve_enable_order(self, names: list[str] | None = None) -> list[str]:
        """Topological sort of plugins by their dependency graph.

        Delegates to the pure ``topological_sort()`` function in
        ``harness.kernel.graph`` so the algorithm is independently testable.

        Args:
            names: Specific plugins to sort. Defaults to all validated plugins.

        Returns:
            Plugin names in dependency-safe enable order.

        Raises:
            CyclicDependencyError: If a dependency cycle is detected.
        """
        from harness.kernel.graph import topological_sort

        if names is None:
            names = [
                n
                for n, e in self._entries.items()
                if e.state in (PluginState.VALIDATED, PluginState.LOADED, PluginState.DISABLED)
            ]

        # Build a provides → plugin_name lookup
        provider_map: dict[str, str] = {}
        for name in names:
            entry = self._entries.get(name)
            if entry:
                for key in entry.plugin.provides:
                    provider_map[key.name] = name

        # Build adjacency: plugin → set of plugins it depends on
        edges: dict[str, set[str]] = {n: set() for n in names}
        for name in names:
            entry = self._entries.get(name)
            if entry:
                for key in entry.plugin.requires:
                    dep_plugin = provider_map.get(key.name)
                    if dep_plugin and dep_plugin != name:
                        edges[name].add(dep_plugin)

        return topological_sort(names, edges)

    async def enable_all(self) -> dict[str, bool]:
        """Enable all validated or disabled plugins in dependency order.

        Automatically advances any DISCOVERED or LOADED plugins through
        load and validate stages before resolving dependency order.

        Returns:
            Dict mapping plugin names to success status.
        """
        for name, entry in list(self._entries.items()):
            if entry.state == PluginState.DISCOVERED:
                try:
                    await self.load(name)
                    await self.validate(name)
                except Exception as e:
                    logger.warning("Failed loading plugin before enable_all", plugin=name, error=str(e))
            elif entry.state == PluginState.LOADED:
                try:
                    await self.validate(name)
                except Exception as e:
                    logger.warning("Failed validating plugin before enable_all", plugin=name, error=str(e))

        to_enable = [
            n
            for n, e in self._entries.items()
            if e.state in (PluginState.VALIDATED, PluginState.DISABLED)
        ]

        try:
            order = self.resolve_enable_order(to_enable)
        except CyclicDependencyError:
            logger.error("Cannot enable plugins: cyclic dependencies detected")
            raise

        results: dict[str, bool] = {
            n: True for n, e in self._entries.items() if e.state == PluginState.ENABLED
        }
        for name in order:
            try:
                await self.enable(name)
                results[name] = True
            except Exception as e:
                results[name] = False
                logger.error("Failed to enable plugin", plugin=name, error=str(e))

        return results

    async def disable_all(self) -> dict[str, bool]:
        """Disable all enabled plugins in reverse dependency order."""
        enabled = [
            n
            for n, e in self._entries.items()
            if e.state == PluginState.ENABLED
        ]

        try:
            order = self.resolve_enable_order(enabled)
        except CyclicDependencyError:
            order = enabled

        results: dict[str, bool] = {}
        for name in reversed(order):
            try:
                await self.disable(name)
                results[name] = True
            except Exception as e:
                results[name] = False
                logger.error("Failed to disable plugin", plugin=name, error=str(e))

        return results

    async def unload_all(self) -> dict[str, bool]:
        """Unload all plugins, disabling them first if needed."""
        await self.disable_all()

        results: dict[str, bool] = {}
        for name, entry in list(self._entries.items()):
            if entry.state in (PluginState.DISABLED, PluginState.LOADED, PluginState.VALIDATED):
                try:
                    await self.unload(name)
                    results[name] = True
                except Exception as e:
                    results[name] = False
                    logger.error("Failed to unload plugin", plugin=name, error=str(e))

        return results

    def get_state(self, name: str) -> PluginState:
        """Get a plugin's current state."""
        entry = self._entries.get(name)
        if entry is None:
            raise KeyError(f"Plugin not found: {name!r}")
        return entry.state

    def get_error(self, name: str) -> str | None:
        """Get a plugin's error message, if any."""
        entry = self._entries.get(name)
        if entry is None:
            raise KeyError(f"Plugin not found: {name!r}")
        return entry.error

    def summary(self) -> dict[str, str]:
        """Get a summary of all plugins and their states."""
        return {name: entry.state.value for name, entry in self._entries.items()}
