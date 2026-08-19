# Solution: Subscribe to and Publish Audit Events

## Explanation

The solution registers an async callback via `bus.subscribe(listener, event_type=EventType.PLUGIN_ENABLED)`, then publishes an event with `await bus.publish(...)`. The bus asynchronously dispatches the event to all matching subscribers.
