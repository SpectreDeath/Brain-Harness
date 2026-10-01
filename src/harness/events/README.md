# Harness Event Bus & Audit Logging (`harness.events`)

The `harness.events` package provides the asynchronous event bus, immutable audit log, and typed domain event models that coordinate state changes across Brain Harness.

---

## Central Function & Capabilities

The event subsystem provides real-time pub/sub telemetry and an unalterable flight recorder:
1. **Asynchronous Pub/Sub**: Enables decoupled communication between plugins, agent execution engines, and UI projections without circular dependencies.
2. **Immutable Event Audit Log**: Records every significant system transition (plugin lifecycle, tool invocations, LLM requests, ingestion events) to an append-only sequence.
3. **Structured Event Taxonomy**: Strictly typed event schemas using Pydantic models with UTC ISO timestamps and unique UUIDs.
4. **Subscription Filtering**: Pattern-based and type-based event subscription handlers supporting both async coroutines and synchronous callbacks.

---

## Architectural Invariants

- **Events are Append-Only (Rule 4)**: The event bus log is strictly immutable. Events cannot be mutated, reordered, or deleted once published.
- **Typed IoC Registration (Rule 2)**: The event bus is registered and resolved via `EVENT_BUS_KEY` (`ServiceKey[EventBus]`).
- **Bounded Diagnostic Observability (Rule 53)**: Subprocess execution errors and tool failures emit structured event observations into the event stream with trailing diagnostic lines.

---

## Key Modules & Symbols

| Module | Core Classes / Symbols | Description |
|---|---|---|
| [`bus.py`](bus.py) | `EventBus`, `EventHandler`, `EVENT_BUS_KEY` | Async event dispatcher managing in-memory event queues and subscriber registries. |
| [`types.py`](types.py) | `HarnessEvent`, `EventType`, `plugin_event`, `tool_event` | Immutable event schemas, event type enumeration, and helper constructor factories. |

---

## Event Categories (`EventType`)

| Category | Examples | Description |
|---|---|---|
| `plugin.*` | `plugin.discovered`, `plugin.loaded`, `plugin.enabled` | State transitions across the plugin lifecycle manager. |
| `service.*` | `service.provided`, `service.revoked`, `service.hot_swapped` | Dynamic IoC container service provision and revocation events. |
| `tool.*` | `tool.registered`, `tool.invoked`, `tool.result`, `tool.error` | Agent tool calls and transactional execution outcomes. |
| `llm.*` | `llm.request`, `llm.response`, `llm.error` | Raw LLM token calls, latency benchmarks, and error responses. |
| `agent.*` | `agent.task_started`, `agent.step_completed`, `agent.task_failed` | High-level agent trajectory checkpoints and swarm wave transitions. |
| `ingestion.*`| `ingestion.fetch_started`, `ingestion.inspected`, `ingestion.converted` | External repository and document ingestion progress telemetry. |

---

## Programmatic Usage Example

```python
import asyncio
from harness.kernel.runtime import HarnessRuntime
from harness.events.bus import EVENT_BUS_KEY
from harness.events.types import EventType, HarnessEvent

async def monitor_tool_invocations():
    async with HarnessRuntime.create() as runtime:
        event_bus = runtime.context.require(EVENT_BUS_KEY)
        
        # Subscribe to all tool invocation events
        async def on_tool_event(event: HarnessEvent) -> None:
            print(f"[{event.timestamp}] Tool: {event.payload.get('tool_name')} - Source: {event.source}")
            
        event_bus.subscribe(EventType.TOOL_INVOKED, on_tool_event)
        
        # Keep subscriber active during task execution
        await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(monitor_tool_invocations())
```

---

## Related Documentation

- [Runtime Architecture](../../../docs/EXPLANATION.md#1-micro-kernel--ioc-architecture)
- [Kernel Package](../kernel/README.md)
- [UI Streaming Integration](../ui/README.md)
