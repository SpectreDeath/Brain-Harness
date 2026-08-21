"""Declarative Configuration Reconciliation Engine.

Realizes Section 5.2 of the Spatiotemporal Composability framework:
- Orchestrators declare the desired topology of the system as a persistent configuration tree.
- The reconciler computes minimal operational diffs against the running system and applies
  them incrementally without tearing down untouched plugins.
- By Theorem 73 (Confluence), the quiescent state reached by incremental reconciliation
  is identical to that of a from-scratch static assembly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

import structlog
from pydantic import BaseModel, Field

from harness.kernel.lifecycle import PluginState

if TYPE_CHECKING:
    from harness.kernel.runtime import HarnessRuntime
    from harness.plugins.base import HarnessPlugin

logger = structlog.get_logger()


class PluginConfigEntry(BaseModel):
    """Declarative specification for an individual plugin instance (Definition 74)."""

    id: str = Field(..., description="Stable unique identifier for reconciliation")
    name: str = Field(..., description="Plugin module name or registered identifier")
    source: str | None = Field(None, description="Optional GitHub URL, local path, or package name")
    config: dict[str, Any] = Field(default_factory=dict, description="Configuration parameters passed to plugin")
    isolate: dict[str, str] = Field(default_factory=dict, description="Coeffect isolation realm mappings (key -> realm)")
    disabled: bool = Field(False, description="Whether the plugin is administratively disabled")


class HarnessConfigTree(BaseModel):
    """Authoritative declarative configuration for a Harness system."""

    version: str = "1.0.0"
    plugins: list[PluginConfigEntry] = Field(default_factory=list)


@dataclass
class ReconciliationResult:
    """Summary metrics of a reconciliation pass."""

    added: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)
    updated: list[str] = field(default_factory=list)
    disabled: list[str] = field(default_factory=list)
    errors: dict[str, str] = field(default_factory=dict)

    @property
    def is_clean(self) -> bool:
        return len(self.errors) == 0


@dataclass
class ConfigurationDriftReport:
    """Pre-flight drift analysis comparing target declarative configuration with live runtime state."""

    to_add: list[str] = field(default_factory=list)
    to_remove: list[str] = field(default_factory=list)
    to_update: list[str] = field(default_factory=list)
    to_disable: list[str] = field(default_factory=list)
    to_enable: list[str] = field(default_factory=list)
    unchanged: list[str] = field(default_factory=list)

    @property
    def has_drift(self) -> bool:
        return bool(
            self.to_add
            or self.to_remove
            or self.to_update
            or self.to_disable
            or self.to_enable
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "has_drift": self.has_drift,
            "to_add": list(self.to_add),
            "to_remove": list(self.to_remove),
            "to_update": list(self.to_update),
            "to_disable": list(self.to_disable),
            "to_enable": list(self.to_enable),
            "unchanged": list(self.unchanged),
        }


class ConfigurationReconciler:
    """Reconciles declarative configuration trees against the live HarnessRuntime.

    Translates declarative configuration diffs into minimal imperative fiber lifecycle
    transitions (Theorem 73 Confluence).
    """

    def __init__(self, runtime: HarnessRuntime) -> None:
        self._runtime = runtime
        self._last_config: dict[str, PluginConfigEntry] = {}

    @property
    def runtime(self) -> HarnessRuntime:
        return self._runtime

    def detect_drift(
        self, config: HarnessConfigTree | dict[str, Any] | list[dict[str, Any]]
    ) -> ConfigurationDriftReport:
        """Compute pre-flight declarative drift without applying any lifecycle mutations."""
        if isinstance(config, list):
            target_tree = HarnessConfigTree(
                plugins=[PluginConfigEntry.model_validate(item) for item in config]
            )
        elif isinstance(config, dict):
            target_tree = HarnessConfigTree.model_validate(config)
        else:
            target_tree = config

        target_map = {entry.id: entry for entry in target_tree.plugins}
        current_map = self._last_config
        lifecycle = self._runtime.lifecycle

        report = ConfigurationDriftReport()

        # Check removed
        for entry_id, old_entry in current_map.items():
            if entry_id not in target_map:
                report.to_remove.append(old_entry.name)

        # Check existing vs target
        for entry_id, target_entry in target_map.items():
            plugin_name = target_entry.name
            if entry_id in current_map:
                old_entry = current_map[entry_id]
                if target_entry.disabled and not old_entry.disabled:
                    report.to_disable.append(plugin_name)
                elif not target_entry.disabled and old_entry.disabled:
                    report.to_enable.append(plugin_name)
                elif (
                    target_entry.config != old_entry.config
                    or target_entry.isolate != old_entry.isolate
                ):
                    report.to_update.append(plugin_name)
                else:
                    report.unchanged.append(plugin_name)
            else:
                # New entry
                if target_entry.source or plugin_name not in lifecycle.plugins:
                    report.to_add.append(plugin_name)
                else:
                    state = lifecycle.get_state(plugin_name)
                    if target_entry.disabled and state == PluginState.ENABLED:
                        report.to_disable.append(plugin_name)
                    elif not target_entry.disabled and state != PluginState.ENABLED:
                        report.to_enable.append(plugin_name)
                    else:
                        report.unchanged.append(plugin_name)

        return report

    async def reconcile(
        self, config: HarnessConfigTree | dict[str, Any] | list[dict[str, Any]]
    ) -> ReconciliationResult:
        """Incrementally reconcile runtime state against target configuration.

        Args:
            config: Target declarative configuration.

        Returns:
            ReconciliationResult with detailed change metrics.
        """
        if isinstance(config, list):
            target_tree = HarnessConfigTree(
                plugins=[PluginConfigEntry.model_validate(item) for item in config]
            )
        elif isinstance(config, dict):
            target_tree = HarnessConfigTree.model_validate(config)
        else:
            target_tree = config

        target_map = {entry.id: entry for entry in target_tree.plugins}
        current_map = self._last_config

        result = ReconciliationResult()
        lifecycle = self._runtime.lifecycle

        # Step 1: Detect removed entries & unload via Guarded Withdrawal (Theorem 63)
        for entry_id, old_entry in list(current_map.items()):
            if entry_id not in target_map:
                try:
                    plugin_name = old_entry.name
                    if plugin_name in lifecycle.plugins:
                        await lifecycle.unload(plugin_name)
                        result.removed.append(plugin_name)
                        logger.info("Reconciler unloaded removed plugin", id=entry_id, plugin=plugin_name)
                except Exception as e:
                    result.errors[entry_id] = str(e)
                    logger.error("Reconciliation unload failed", id=entry_id, error=str(e))

        # Step 2: Handle updated / disabled entries
        for entry_id, target_entry in target_map.items():
            if entry_id in current_map:
                old_entry = current_map[entry_id]
                plugin_name = target_entry.name

                # Check if disabled status changed
                if target_entry.disabled and not old_entry.disabled:
                    try:
                        if plugin_name in lifecycle.plugins and lifecycle.get_state(plugin_name) == PluginState.ENABLED:
                            await lifecycle.disable(plugin_name)
                            result.disabled.append(plugin_name)
                    except Exception as e:
                        result.errors[entry_id] = str(e)

                elif not target_entry.disabled and old_entry.disabled:
                    try:
                        if plugin_name in lifecycle.plugins:
                            await lifecycle.ensure_enabled(plugin_name)
                            result.updated.append(plugin_name)
                    except Exception as e:
                        result.errors[entry_id] = str(e)

                # Check if config or isolation realms changed
                elif target_entry.config != old_entry.config or target_entry.isolate != old_entry.isolate:
                    try:
                        # Apply isolation realms to context if configured
                        for key_name, realm in target_entry.isolate.items():
                            from harness.kernel.context import ServiceKey
                            self._runtime.context.isolate(ServiceKey(key_name), realm)

                        result.updated.append(plugin_name)
                    except Exception as e:
                        result.errors[entry_id] = str(e)

        # Step 3: Handle newly added entries
        for entry_id, target_entry in target_map.items():
            if entry_id not in current_map:
                plugin_name = target_entry.name
                try:
                    # Apply isolation realms if defined
                    for key_name, realm in target_entry.isolate.items():
                        from harness.kernel.context import ServiceKey
                        self._runtime.context.isolate(ServiceKey(key_name), realm)

                    # Ingest if external source is provided
                    if target_entry.source:
                        await self._runtime.add_plugin_from_source(
                            target_entry.source,
                            auto_enable=not target_entry.disabled,
                        )
                        result.added.append(plugin_name)
                    elif plugin_name in lifecycle.plugins:
                        if not target_entry.disabled:
                            await lifecycle.ensure_enabled(plugin_name)
                        result.added.append(plugin_name)
                    else:
                        logger.warning("Plugin not yet discovered or registered in runtime", plugin=plugin_name)

                except Exception as e:
                    result.errors[entry_id] = str(e)
                    logger.error("Reconciliation add failed", id=entry_id, error=str(e))

        # Commit reconciled state
        self._last_config = target_map
        return result
