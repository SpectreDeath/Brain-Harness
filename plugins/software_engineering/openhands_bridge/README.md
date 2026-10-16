# OpenHands Bridge Plugin

A sandboxed Harness plugin providing action-observation event stream modeling and execution records derived from the OpenHands autonomous platform.

## Capabilities
- **Action-Observation Streaming**: Structured event logs recording dispatched agent actions and environment observations.
- **Proactor Isolation**: Headless serialization for async subprocess sandboxes.

## Service Key
- `service.openhands_bridge` (`OPENHANDS_BRIDGE_KEY`)


---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `create_event_stream` | `(stream_id)` | Create a new action-observation event stream. |
| `record_action` | `(stream_id, action)` | Record an agent action in the specified stream. |
| `record_observation` | `(stream_id, observation)` | Record an environment observation in the specified stream. |
| `get_stream_events` | `(stream_id)` | Retrieve all recorded events for a stream. |
