"""Live UI Stream Projection Engine — Authoritative dashboard telemetry and WebSocket channel broadcasting.

Decouples FastAPI HTTP / WebSocket transport mechanics from kernel lifecycle,
agent session trees, swarm executions, and system event streams.
"""

from __future__ import annotations

import json
from collections import defaultdict, deque
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

import structlog
from fastapi import WebSocket

from harness.events.bus import EventBus
from harness.events.types import EventType, HarnessEvent

if TYPE_CHECKING:
    from harness.ui.server import RuntimeAdapter

logger = structlog.get_logger()


class ChannelSubscription:
    """Manages an active WebSocket client connection with granular channel subscriptions."""

    def __init__(self, websocket: WebSocket, initial_channels: set[str] | None = None) -> None:
        self.websocket = websocket
        self.channels: set[str] = initial_channels or {"events", "agent", "swarm", "metrics", "system"}

    def is_subscribed(self, channel: str) -> bool:
        """Check if client is subscribed to a specific telemetry channel."""
        return "*" in self.channels or channel in self.channels

    def update_channels(self, channels: list[str] | set[str]) -> None:
        """Update subscribed channels."""
        self.channels = set(channels)


class UIProjectionEngine:
    """Authoritative projection engine maintaining live UI state and broadcasting filtered telemetry streams."""

    VALID_CHANNELS = {"events", "agent", "swarm", "metrics", "system", "*"}

    def __init__(
        self,
        adapter: RuntimeAdapter | None = None,
        event_bus: EventBus | None = None,
        max_feed_size: int = 100,
    ) -> None:
        self.adapter = adapter
        self.event_bus = event_bus
        self._subscriptions: list[ChannelSubscription] = []
        self._activity_feed: deque[dict[str, Any]] = deque(maxlen=max_feed_size)
        self._channel_event_counts: dict[str, int] = defaultdict(int)

        if event_bus is not None:
            self._attach_event_bus(event_bus)

    def _attach_event_bus(self, bus: EventBus) -> None:
        """Hook into EventBus to update live projections and broadcast across subscribed channels."""
        async def _event_dispatcher(event: HarnessEvent) -> None:
            await self.handle_event(event)

        bus.on("*", _event_dispatcher)

    async def handle_event(self, event: HarnessEvent) -> None:
        """Process an incoming event, update projection feeds, and broadcast to subscribed clients."""
        etype = event.event_type.value if isinstance(event.event_type, EventType) else str(event.event_type)
        channel = self._classify_event_channel(etype)
        self._channel_event_counts[channel] += 1

        feed_entry = {
            "id": event.id,
            "timestamp": event.timestamp.isoformat() if isinstance(event.timestamp, datetime) else str(event.timestamp),
            "channel": channel,
            "event_type": etype,
            "source": event.source,
            "payload": event.payload,
        }
        self._activity_feed.append(feed_entry)

        # Broadcast to subscribed WebSocket clients
        await self.broadcast(
            channel=channel,
            message={
                "type": "event",
                "channel": channel,
                "data": event.to_dict(),
            },
        )

    def _classify_event_channel(self, event_type_str: str) -> str:
        """Map event types to high-level UI telemetry channels."""
        et = event_type_str.lower()
        if "agent" in et or "step" in et or "session" in et:
            return "agent"
        if "swarm" in et:
            return "swarm"
        if "metric" in et or "usage" in et or "token" in et:
            return "metrics"
        if "plugin" in et or "system" in et or "lifecycle" in et or "harness" in et:
            return "system"
        return "events"

    async def connect_client(
        self, websocket: WebSocket, initial_channels: set[str] | None = None
    ) -> ChannelSubscription:
        """Register a new WebSocket connection."""
        await websocket.accept()
        sub = ChannelSubscription(websocket, initial_channels=initial_channels)
        self._subscriptions.append(sub)
        logger.debug("WebSocket client connected to UIProjectionEngine", channels=list(sub.channels))
        return sub

    def disconnect_client(self, websocket: WebSocket) -> None:
        """Remove a disconnected WebSocket client."""
        self._subscriptions = [s for s in self._subscriptions if s.websocket != websocket]

    async def handle_client_message(self, websocket: WebSocket, raw_text: str) -> None:
        """Handle incoming command messages from WebSocket clients (e.g. channel subscription updates)."""
        try:
            msg = json.loads(raw_text)
            msg_type = msg.get("type", "")

            if msg_type == "subscribe":
                channels = set(msg.get("channels", []))
                for sub in self._subscriptions:
                    if sub.websocket == websocket:
                        sub.update_channels(channels)
                        await websocket.send_text(
                            json.dumps({
                                "type": "subscription_ack",
                                "channels": list(sub.channels),
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                            })
                        )
                        break

            elif msg_type == "ping":
                await websocket.send_text(json.dumps({"type": "pong", "timestamp": datetime.now(timezone.utc).isoformat()}))

        except Exception as e:
            logger.warning("Error processing UI client message", error=str(e))

    async def broadcast(self, channel: str, message: dict[str, Any]) -> None:
        """Broadcast payload to all clients subscribed to the target channel."""
        text = json.dumps(message)
        dead_connections: list[WebSocket] = []

        for sub in list(self._subscriptions):
            if sub.is_subscribed(channel):
                try:
                    await sub.websocket.send_text(text)
                except Exception:
                    dead_connections.append(sub.websocket)

        for dead in dead_connections:
            self.disconnect_client(dead)

    def get_activity_feed(self, limit: int = 50, channel: str | None = None) -> list[dict[str, Any]]:
        """Retrieve recent chronological activity feed entries."""
        feed = list(self._activity_feed)
        if channel:
            feed = [entry for entry in feed if entry["channel"] == channel]
        return feed[-limit:] if limit > 0 else feed

    def get_projection_status(self) -> dict[str, Any]:
        """Return projection engine telemetry metrics."""
        return {
            "active_clients": len(self._subscriptions),
            "feed_size": len(self._activity_feed),
            "channel_counts": dict(self._channel_event_counts),
            "channels_available": list(self.VALID_CHANNELS),
        }
