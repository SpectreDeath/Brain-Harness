# domain.hermes_gateway_relay (v1.0.0)

Hermes multi-platform gateway relay, WebSocket telemetry streamer, and scale-to-zero lifecycle manager

---

## Overview & Metadata

| Property | Value |
|---|---|
| Plugin Directory | `plugins/agent_orchestration/hermes_gateway_relay` |
| Category | `agent_orchestration` |
| Isolation Mode | `in_process` |
| Services Provided | `service.hermes_gateway_relay` |
| Dependencies Required | None |

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `dispatch_platform_message` | `(platform, channel_id, text)` | Route formatted messages to external communication platforms (Telegram, Discord, Slack, WhatsApp, Signal) |
| `stream_ws_telemetry` | `(session_id, event_payload)` | Publish real-time event telemetry to GUI/TUI WebSocket clients |
| `manage_scale_to_zero` | `(idle_timeout_seconds)` | Evaluate idle timeout conditions to hibernate cloud containers or VPS compute |

---

## Key Modules & AST Symbols

### Module [main.py](main.py)

Hermes Gateway Relay — multi-platform messaging, WebSocket streaming, and scale-to-zero.

#### Functions

- `def dispatch_platform_message(platform, channel_id, text) -> dict[str, Any]` — Route message through platform adapter.
- `def stream_ws_telemetry(session_id, event_payload) -> dict[str, Any]` — Stream telemetry payload to active WebSocket subscribers.
- `def manage_scale_to_zero(idle_timeout_seconds) -> dict[str, Any]` — Evaluate container hibernation policy.


---

## Quickstart & Usage

```python
from harness.kernel.context import ServiceContext
from plugins.agent_orchestration.hermes_gateway_relay.main import plugin

# Load plugin into harness service context
context = ServiceContext()
plugin.on_load(context)
```

---

## Architecture & Diátaxis Classification

- Diátaxis Quadrant: Reference (Track B) & How-To Guides
- Isolation: `in_process` execution sandbox
- Invariants: Slotted dataclass architecture (Rule 12), transactional context bounds (Rule 8), and zero-fork YAML configuration (Rule 44).
