"""OpenHands Bridge plugin providing action-observation streaming and sandboxed proactor execution."""

from __future__ import annotations

from typing import Any

import structlog

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.openhands_bridge import (
    OPENHANDS_BRIDGE_KEY,
    OpenHandsAction,
    OpenHandsBridgeService,
    OpenHandsEventStream,
    OpenHandsObservation,
)

logger = structlog.get_logger(__name__)


class OpenHandsBridgePlugin(HarnessPlugin, OpenHandsBridgeService):
    """Harness Plugin providing OpenHands action-observation stream management."""

    name = "plugin.openhands_bridge"
    version = "1.0.0"
    description = "OpenHands Bridge plugin for action-observation streaming and proactor execution"
    trusted = True

    def __init__(self) -> None:
        super().__init__()
        self._streams: dict[str, OpenHandsEventStream] = {}

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [OPENHANDS_BRIDGE_KEY]

    def on_load(self, context: ServiceContext) -> None:
        context.provide(OPENHANDS_BRIDGE_KEY, self, provider=self.name)
        logger.info("OpenHandsBridgePlugin registered into IoC container")

    def on_unload(self, context: ServiceContext) -> None:
        self._streams.clear()
        logger.info("OpenHandsBridgePlugin unloaded")

    def create_event_stream(self, stream_id: str) -> OpenHandsEventStream:
        """Create a new action-observation event stream."""
        if stream_id not in self._streams:
            self._streams[stream_id] = OpenHandsEventStream(stream_id=stream_id)
        return self._streams[stream_id]

    def record_action(self, stream_id: str, action: OpenHandsAction) -> None:
        """Record an agent action in the specified stream."""
        stream = self.create_event_stream(stream_id)
        stream.append_action(action)
        logger.debug("Recorded OpenHands action", stream_id=stream_id, action_type=action.action_type)

    def record_observation(self, stream_id: str, observation: OpenHandsObservation) -> None:
        """Record an environment observation in the specified stream."""
        stream = self.create_event_stream(stream_id)
        stream.append_observation(observation)
        logger.debug(
            "Recorded OpenHands observation",
            stream_id=stream_id,
            action_type=observation.action_type,
            observation_type=observation.observation_type,
        )

    def get_stream_events(self, stream_id: str) -> list[dict[str, Any]]:
        """Retrieve all recorded events for a stream."""
        if stream_id not in self._streams:
            return []
        return list(self._streams[stream_id].events)


# Export authoritative module-level singleton (Rule 45)
plugin = OpenHandsBridgePlugin()
