"""OpenHands Bridge Service protocol, slotted/frozen data models, and ServiceKey."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from harness.kernel.context import ServiceKey


@dataclass(slots=True, frozen=True)
class OpenHandsAction:
    """An action dispatched by an autonomous agent (Rule 12)."""

    action_type: str
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def __post_init__(self) -> None:
        assert self.action_type.strip(), "action_type cannot be empty"


@dataclass(slots=True, frozen=True)
class OpenHandsObservation:
    """An observation received from environment execution (Rule 12)."""

    action_type: str
    observation_type: str
    content: str = ""
    success: bool = True
    timestamp: float = field(default_factory=time.time)

    def __post_init__(self) -> None:
        assert self.observation_type.strip(), "observation_type cannot be empty"


@dataclass(slots=True)
class OpenHandsEventStream:
    """Transactional action-observation event stream."""

    stream_id: str
    events: list[dict[str, Any]] = field(default_factory=list)

    def append_action(self, action: OpenHandsAction) -> None:
        self.events.append({
            "kind": "action",
            "type": action.action_type,
            "payload": action.payload,
            "timestamp": action.timestamp,
        })

    def append_observation(self, obs: OpenHandsObservation) -> None:
        self.events.append({
            "kind": "observation",
            "action_type": obs.action_type,
            "observation_type": obs.observation_type,
            "content": obs.content,
            "success": obs.success,
            "timestamp": obs.timestamp,
        })


@runtime_checkable
class OpenHandsBridgeService(Protocol):
    """Protocol for OpenHands action-observation streaming and sandboxed proactor execution."""

    def create_event_stream(self, stream_id: str) -> OpenHandsEventStream:
        """Create a new action-observation event stream."""
        ...

    def record_action(self, stream_id: str, action: OpenHandsAction) -> None:
        """Record an agent action in the specified stream."""
        ...

    def record_observation(self, stream_id: str, observation: OpenHandsObservation) -> None:
        """Record an environment observation in the specified stream."""
        ...

    def get_stream_events(self, stream_id: str) -> list[dict[str, Any]]:
        """Retrieve all recorded events for a stream."""
        ...


OPENHANDS_BRIDGE_KEY: ServiceKey[OpenHandsBridgeService] = ServiceKey("service.openhands_bridge")
