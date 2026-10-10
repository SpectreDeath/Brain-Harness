"""Subscription registry and safe handler invocation for event bus."""

from __future__ import annotations

import asyncio
import inspect
from collections import defaultdict
from typing import TYPE_CHECKING

import structlog

from .models import EventHandler

if TYPE_CHECKING:
    from ..types import EventType, HarnessEvent

logger = structlog.get_logger()


class SubscriptionRegistry:
    """Manages event subscriptions and handles concurrent dispatch with error isolation."""

    __slots__ = ("_handlers",)

    def __init__(self) -> None:
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)

    def on(
        self,
        event_type: EventType | str,
        handler: EventHandler,
    ) -> None:
        """Subscribe a handler to an event type.

        Args:
            event_type: The event type to subscribe to, or ``"*"`` for all events.
            handler: Async callable that receives the event.
        """
        from ..types import EventType as _EventType

        key = event_type.value if isinstance(event_type, _EventType) else str(event_type)
        self._handlers[key].append(handler)
        logger.debug(
            "Event handler registered",
            event_type=key,
            handler=getattr(handler, "__name__", repr(handler)),
        )

    subscribe = on

    def off(self, handler: EventHandler) -> None:
        """Unsubscribe a handler from all event types.

        Args:
            handler: The handler to remove.
        """
        for key, handler_list in self._handlers.items():
            self._handlers[key] = [h for h in handler_list if h is not handler]

    def on_all(self, handler: EventHandler) -> None:
        """Subscribe a handler to ALL event types."""
        self.on("*", handler)

    def get_handlers(self, event_type_val: str) -> list[EventHandler]:
        """Return all matching handlers for a specific event type string plus wildcard."""
        handlers: list[EventHandler] = []
        handlers.extend(self._handlers.get(event_type_val, []))
        handlers.extend(self._handlers.get("*", []))
        return handlers

    @property
    def handler_count(self) -> int:
        """Total number of registered handlers across all event types."""
        return sum(len(handlers) for handlers in self._handlers.values())

    @property
    def handlers(self) -> dict[str, list[EventHandler]]:
        """Access internal handler mapping."""
        return self._handlers

    @staticmethod
    async def safe_call(handler: EventHandler, event: HarnessEvent) -> None:
        """Call an individual handler with async error isolation."""
        res = handler(event)
        if inspect.isawaitable(res):
            await res

    async def dispatch(self, event: HarnessEvent) -> None:
        """Dispatch event concurrently to all matching handlers with error isolation."""
        handlers = self.get_handlers(event.event_type.value)
        if not handlers:
            return

        results = await asyncio.gather(
            *(self.safe_call(h, event) for h in handlers),
            return_exceptions=True,
        )
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning(
                    "Event handler error",
                    event_type=event.event_type.value,
                    handler=getattr(handlers[i], "__name__", repr(handlers[i])),
                    error=str(result),
                )
