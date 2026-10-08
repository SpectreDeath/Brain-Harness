"""Lifecycle state transition validator and event emission helpers."""

from __future__ import annotations

from typing import Any

import structlog

from harness.kernel.lifecycle.models import (
    InvalidTransitionError,
    PluginState,
    _TRANSITIONS,
)

logger = structlog.get_logger()


def validate_transition(plugin_name: str, current: PluginState, target: PluginState) -> None:
    """Validate that transition from current to target state is permissible."""
    valid_targets = _TRANSITIONS.get(current, frozenset())
    if target not in valid_targets:
        raise InvalidTransitionError(plugin_name, current, target)


def emit_lifecycle_event(
    event_bus: Any | None,
    event_type: Any,
    plugin_name: str,
    **extra: Any,
) -> None:
    """Emit a lifecycle event onto the attached event bus if available."""
    if event_bus is not None:
        from harness.events.types import plugin_event

        evt = plugin_event(event_type, plugin_name, **extra)
        event_bus.fire(evt)


__all__ = [
    "emit_lifecycle_event",
    "validate_transition",
]
