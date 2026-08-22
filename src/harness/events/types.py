"""Event type definitions for the harness event bus.

Every significant action in the harness emits a typed event. Events are
immutable Pydantic models stored in an append-only log.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class EventType(str, Enum):
    """Categories of events emitted by the harness."""

    # Plugin lifecycle
    PLUGIN_DISCOVERED = "plugin.discovered"
    PLUGIN_LOADED = "plugin.loaded"
    PLUGIN_RELOADED = "plugin.reloaded"
    PLUGIN_VALIDATED = "plugin.validated"
    PLUGIN_ENABLED = "plugin.enabled"
    PLUGIN_DISABLED = "plugin.disabled"
    PLUGIN_UNLOADED = "plugin.unloaded"
    PLUGIN_ERROR = "plugin.error"

    # Service registry
    SERVICE_PROVIDED = "service.provided"
    SERVICE_REVOKED = "service.revoked"
    SERVICE_HOT_SWAPPED = "service.hot_swapped"

    # Tool invocation
    TOOL_REGISTERED = "tool.registered"
    TOOL_INVOKED = "tool.invoked"
    TOOL_RESULT = "tool.result"
    TOOL_ERROR = "tool.error"

    # LLM operations
    LLM_REQUEST = "llm.request"
    LLM_RESPONSE = "llm.response"
    LLM_ERROR = "llm.error"

    # Ingestion pipeline
    REPO_FETCH_STARTED = "ingestion.fetch_started"
    REPO_FETCH_COMPLETED = "ingestion.fetch_completed"
    REPO_INSPECTED = "ingestion.inspected"
    REPO_CONVERTED = "ingestion.converted"
    REPO_FETCH_ERROR = "ingestion.fetch_error"

    # Agent telemetry
    AGENT_TASK_STARTED = "agent.task_started"
    AGENT_STEP_STARTED = "agent.step_started"
    AGENT_STEP_COMPLETED = "agent.step_completed"
    AGENT_TASK_COMPLETED = "agent.task_completed"
    AGENT_TASK_FAILED = "agent.task_failed"

    # System
    HARNESS_STARTED = "harness.started"
    HARNESS_STOPPED = "harness.stopped"
    CUSTOM = "custom"


class HarnessEvent(BaseModel):
    """Base event model for the harness event bus.

    All events carry a unique ID, timestamp, source plugin, event type,
    and an arbitrary payload. Events are immutable once created.
    """

    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    event_type: EventType
    source: str = "harness"
    """Name of the plugin or system component that emitted the event."""
    trace_id: str | None = None
    """Optional trace ID for correlating related events."""
    payload: dict[str, Any] = Field(default_factory=dict)

    model_config = {"frozen": True}

    def to_dict(self) -> dict[str, Any]:
        """Serialize event to standard dictionary with ISO timestamp and string event type."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type.value,
            "source": self.source,
            "trace_id": self.trace_id,
            "payload": self.payload,
        }

    def __repr__(self) -> str:
        return (
            f"HarnessEvent(type={self.event_type.value}, "
            f"source={self.source!r}, id={self.id})"
        )


# --- Convenience factory functions ---


def plugin_event(
    event_type: EventType,
    plugin_name: str,
    **extra: Any,
) -> HarnessEvent:
    """Create a plugin lifecycle event."""
    return HarnessEvent(
        event_type=event_type,
        source=plugin_name,
        payload={"plugin": plugin_name, **extra},
    )


def service_event(
    event_type: EventType,
    service_name: str,
    provider: str | None = None,
    **extra: Any,
) -> HarnessEvent:
    """Create a service registry event."""
    return HarnessEvent(
        event_type=event_type,
        source=provider or "harness",
        payload={"service": service_name, "provider": provider, **extra},
    )


def tool_event(
    event_type: EventType,
    tool_name: str,
    source: str = "harness",
    **extra: Any,
) -> HarnessEvent:
    """Create a tool invocation event."""
    return HarnessEvent(
        event_type=event_type,
        source=source,
        payload={"tool": tool_name, **extra},
    )


def ingestion_event(
    event_type: EventType,
    url: str,
    **extra: Any,
) -> HarnessEvent:
    """Create an ingestion pipeline event."""
    return HarnessEvent(
        event_type=event_type,
        source="ingestion",
        payload={"url": url, **extra},
    )


def agent_event(
    event_type: EventType,
    agent_name: str,
    task: str,
    **extra: Any,
) -> HarnessEvent:
    """Create an agent telemetry event."""
    return HarnessEvent(
        event_type=event_type,
        source=agent_name,
        payload={"agent": agent_name, "task": task, **extra},
    )


def llm_event(
    event_type: EventType,
    source: str = "llm",
    **extra: Any,
) -> HarnessEvent:
    """Create an LLM operation event."""
    return HarnessEvent(
        event_type=event_type,
        source=source,
        payload=extra,
    )

