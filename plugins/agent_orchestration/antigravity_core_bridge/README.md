# domain.antigravity_core_bridge (v1.0.0)

Google Antigravity SDK core bridge providing LocalConnection proactor transport, streaming step ingestion, and subagent orchestration

---

## Overview & Metadata

| Property | Value |
|---|---|
| Plugin Directory | `plugins/agent_orchestration/antigravity_core_bridge` |
| Category | `agent_orchestration` |
| Isolation Mode | `in_process` |
| Services Provided | `service.antigravity.connection` |
| Dependencies Required | None |

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `connect_proactor` | `(host, port)` | Establish Antigravity proactor connection |
| `dispatch_local_step` | `(session_id, prompt)` | Dispatch prompt to proactor and return step observation stream |
| `get_session_telemetry` | `(session_id)` | Retrieve telemetry metrics for session |

---

## Key Modules & AST Symbols

### Module [main.py](main.py)

Antigravity Core Bridge Entrypoints.

#### Functions

- `def connect_proactor(host, port) -> dict[str, Any]` — Establish Antigravity proactor connection.
- `def dispatch_local_step(session_id, prompt) -> dict[str, Any]` — Dispatch prompt to proactor and return step observation stream.
- `def get_session_telemetry(session_id) -> dict[str, Any]` — Retrieve telemetry metrics for session.

### Module [__init__.py](__init__.py)

Antigravity Core Bridge Plugin Package.
### Module [service.py](service.py)

Google Antigravity Core Bridge Service & Plugin Implementation.

#### Classes

- `class LocalStepObservation`
- `class AntigravityConnectionService` — Authoritative service managing Antigravity WebSocket connection and step streams.
  - `def __init__(host, port) -> None`
  - `def is_connected() -> bool`
  - `def connect() -> bool` — Establish proactor WebSocket channel.
  - `def disconnect() -> None` — Gracefully drain and close proactor channel.
  - `def create_session(session_id, system_instruction) -> dict[str, Any]` — Initialize a new conversation session on the proactor.
  - `def dispatch_step(session_id, prompt) -> list[LocalStepObservation]` — Send prompt to proactor and return sequence of streaming step observations.
  - `def get_session_status(session_id) -> dict[str, Any] | None` — Retrieve telemetry and step count for active session.
- `class AntigravityCoreBridgePlugin` — In-process Harness plugin providing Antigravity connection service.
  - `def __init__(host, port) -> None`
  - `def provides() -> list[ServiceKey[Any]]`
  - `def on_load(ctx) -> None`
  - `def on_enable() -> None`
  - `def on_disable() -> None`
  - `def on_unload() -> None`


---

## Quickstart & Usage

```python
from harness.kernel.context import ServiceContext
from plugins.agent_orchestration.antigravity_core_bridge.main import plugin

# Load plugin into harness service context
context = ServiceContext()
plugin.on_load(context)
```

---

## Architecture & Diátaxis Classification

- Diátaxis Quadrant: Reference (Track B) & How-To Guides
- Isolation: `in_process` execution sandbox
- Invariants: Slotted dataclass architecture (Rule 12), transactional context bounds (Rule 8), and zero-fork YAML configuration (Rule 44).
