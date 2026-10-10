"""Single-seam resolver for EventBus per AGENTS.md Rule 58."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .models import EVENT_BUS_KEY

if TYPE_CHECKING:
    from harness.kernel.context import ServiceContext
    from .core import EventBus


def resolve_event_bus(target: Any = None, **kwargs: Any) -> EventBus:
    """Resolve or instantiate an authoritative EventBus instance (Rule 58).

    Args:
        target: Optional ServiceContext, existing EventBus, or None.
        **kwargs: Optional constructor arguments passed to EventBus if instantiated.

    Returns:
        An authoritative EventBus instance.
    """
    from .core import EventBus

    if target is None:
        return EventBus(**kwargs)

    if isinstance(target, EventBus):
        return target

    # Handle ServiceContext resolution
    if hasattr(target, "optional") and hasattr(target, "provide"):
        existing = target.optional(EVENT_BUS_KEY)
        if existing is not None and isinstance(existing, EventBus):
            return existing
        bus = EventBus(**kwargs)
        target.provide(EVENT_BUS_KEY, bus)
        return bus

    return EventBus(**kwargs)
