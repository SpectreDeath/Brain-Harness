"""EventBus subpackage facade with 100% backward compatibility."""

from .core import EventBus
from .ledger import EventLedger
from .models import EVENT_BUS_KEY, EventBusService, EventHandler
from .persistence import iter_log_file, persist_event, persist_event_sync, read_log_file
from .projections import (
    AuditProjection,
    EventProjection,
    EventProjectionEngine,
    MetricsProjection,
)
from .resolvers import resolve_event_bus
from .streaming import replay_stream_events, stream_events
from .subscriptions import SubscriptionRegistry

__all__ = [
    "EVENT_BUS_KEY",
    "AuditProjection",
    "EventBus",
    "EventBusService",
    "EventHandler",
    "EventLedger",
    "EventProjection",
    "EventProjectionEngine",
    "MetricsProjection",
    "SubscriptionRegistry",
    "iter_log_file",
    "persist_event",
    "persist_event_sync",
    "read_log_file",
    "replay_stream_events",
    "resolve_event_bus",
    "stream_events",
]
