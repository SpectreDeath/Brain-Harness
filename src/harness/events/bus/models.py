"""Models and service keys for the asynchronous event bus."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from harness.kernel.context import ServiceKey
from ..types import HarnessEvent

if TYPE_CHECKING:
    from .core import EventBus

# Canonical service key for event bus
EVENT_BUS_KEY: ServiceKey[EventBus] = ServiceKey("events.bus")

# Type alias for event handlers
EventHandler = Callable[[HarnessEvent], Awaitable[None]]


@runtime_checkable
class EventBusService(Protocol):
    """Protocol defining the core service contract of the event bus."""

    async def emit(self, event: HarnessEvent) -> None:
        """Emit an event asynchronously."""
        ...

    def emit_sync(self, event: HarnessEvent) -> None:
        """Emit an event synchronously."""
        ...

    def fire(self, event: HarnessEvent) -> None:
        """Emit an event synchronously (canonical context-aware emission seam)."""
        ...

    def on(self, event_type: Any, handler: EventHandler) -> None:
        """Subscribe a handler to an event type."""
        ...

    def off(self, handler: EventHandler) -> None:
        """Unsubscribe a handler from all event types."""
        ...

    @property
    def log(self) -> list[HarnessEvent]:
        """Return the current list of logged events."""
        ...
