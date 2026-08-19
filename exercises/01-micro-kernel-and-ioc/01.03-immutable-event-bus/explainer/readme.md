# Immutable Event Bus

## Overview

The `EventBus` provides an append-only, asynchronous event streaming hub. All major kernel actions (service registrations, tool invocations, plugin lifecycle changes, agent thoughts) emit immutable `HarnessEvent` records.

```python
from harness.events.bus import EventBus
from harness.events.types import HarnessEvent, EventType

bus = EventBus(log_file=Path(".harness/events.jsonl"))

# Subscribe to tool events
async def on_tool_call(event: HarnessEvent) -> None:
    print(f"Tool invoked: {event.payload}")

bus.subscribe(on_tool_call, event_type=EventType.TOOL_INVOKED)

# Publish an event
await bus.publish(HarnessEvent(
    type=EventType.TOOL_INVOKED,
    source="agent.react",
    payload={"tool": "fs_read_file", "path": "main.py"},
))
```

## Key Invariants

1. **Append-Only**: Events are strictly appended to the log file in JSONL format; events are never mutated or deleted.
2. **Async Dispatch**: Subscribers receive events asynchronously without blocking the publishing thread.
