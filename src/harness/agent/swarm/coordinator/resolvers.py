"""Single-seam resolver factory for SwarmCoordinator services (Rule 58)."""

from __future__ import annotations

from harness.kernel.context import ServiceContext

from .core import SWARM_COORDINATOR_KEY, SwarmCoordinator


def resolve_swarm_coordinator(context: ServiceContext) -> SwarmCoordinator:
    """Resolve or construct the SwarmCoordinator service from the service context."""
    existing = context.optional(SWARM_COORDINATOR_KEY)
    if existing is not None and isinstance(existing, SwarmCoordinator):
        return existing

    from harness.events.bus import EVENT_BUS_KEY, EventBus

    bus: EventBus | None = context.optional(EVENT_BUS_KEY)
    return SwarmCoordinator(context=context, event_bus=bus)
