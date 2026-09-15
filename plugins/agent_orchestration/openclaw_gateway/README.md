# plugin.openclaw_gateway (v1.0.0)

WebSocket JSON-RPC gateway bridge connecting Harness agents to OpenClaw control plane, session placement, and channel routing.

---

## Overview & Metadata

| Property | Value |
|---|---|
| Plugin Directory | `plugins/agent_orchestration/openclaw_gateway` |
| Category | `agent_orchestration` |
| Isolation Mode | `in_process` |
| Services Provided | None |
| Dependencies Required | None |

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `openclaw_gateway_connect` | `(gateway_url, token)` | Connects to an OpenClaw Gateway instance over WebSocket and verifies pairing credentials. |
| `openclaw_gateway_list_sessions` | `()` | Lists active session trees and status from the OpenClaw Gateway session catalog. |
| `openclaw_gateway_create_session` | `(channel, permission_mode, metadata)` | Creates a new session placement on OpenClaw Gateway with specified channel and permission mode. |
| `openclaw_gateway_call_tool` | `(session_id, tool_name, arguments)` | Dispatches a tool execution request through the OpenClaw Gateway runtime. |
| `openclaw_gateway_send_message` | `(channel, message, recipient_id)` | Routes a message to external messaging channels (Slack, Discord, Telegram, etc.) via OpenClaw Gateway. |

---

## Key Modules & AST Symbols

### Module [main.py](main.py)

OpenClaw Gateway Plugin — WebSocket JSON-RPC bridge connecting Harness agents to OpenClaw control plane.

#### Classes

- `class OpenClawGatewayServiceImpl` — In-memory and WebSocket JSON-RPC client implementation for OpenClaw Gateway.
  - `def __init__() -> None`
  - `def connect(gateway_url, token) -> dict[str, Any]` — Connects and authenticates with OpenClaw Gateway.
  - `def list_sessions() -> list[OpenClawGatewaySession]` — Lists active session catalog on the gateway.
  - `def create_session(channel, permission_mode, metadata) -> OpenClawGatewaySession` — Creates a new session placement on the gateway.
  - `def call_tool(session_id, tool_name, arguments) -> dict[str, Any]` — Dispatches tool execution through the OpenClaw Gateway.
  - `def send_message(channel, message, recipient_id) -> dict[str, Any]` — Routes message to external chat channels via OpenClaw Gateway.
- `class OpenClawGatewayPlugin` — Harness plugin registering OpenClaw Gateway WebSocket client service and tool entrypoints.
  - `def __init__() -> None`
  - `def register_services(context) -> None` — Register the typed OpenClawGatewayService into the IoC container.
  - `def openclaw_gateway_connect(gateway_url, token) -> dict[str, Any]` — Tool handler for openclaw_gateway_connect.
  - `def openclaw_gateway_list_sessions() -> list[dict[str, Any]]` — Tool handler for openclaw_gateway_list_sessions.
  - `def openclaw_gateway_create_session(channel, permission_mode, metadata) -> dict[str, Any]` — Tool handler for openclaw_gateway_create_session.
  - `def openclaw_gateway_call_tool(session_id, tool_name, arguments) -> dict[str, Any]` — Tool handler for openclaw_gateway_call_tool.
  - `def openclaw_gateway_send_message(channel, message, recipient_id) -> dict[str, Any]` — Tool handler for openclaw_gateway_send_message.


---

## Quickstart & Usage

```python
from harness.kernel.context import ServiceContext
from plugins.agent_orchestration.openclaw_gateway.main import plugin

# Load plugin into harness service context
context = ServiceContext()
plugin.on_load(context)
```

---

## Architecture & Diátaxis Classification

- Diátaxis Quadrant: Reference (Track B) & How-To Guides
- Isolation: `in_process` execution sandbox
- Invariants: Slotted dataclass architecture (Rule 12), transactional context bounds (Rule 8), and zero-fork YAML configuration (Rule 44).
