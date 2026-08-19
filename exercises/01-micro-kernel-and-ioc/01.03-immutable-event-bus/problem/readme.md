# Problem: Subscribe to and Publish Audit Events

## Objective

Set up an `EventBus`, subscribe to `PLUGIN_ENABLED` events, publish a custom event, and verify that your callback captures the event in memory.

## Tasks

1. Initialize `EventBus`.
2. Register an async subscriber filtering for `EventType.PLUGIN_ENABLED`.
3. Publish a `PLUGIN_ENABLED` event and capture it in an accumulator list.
