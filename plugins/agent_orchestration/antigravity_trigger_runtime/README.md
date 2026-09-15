# domain.antigravity_trigger_runtime (v1.0.0)

Google Antigravity reactive trigger scheduling engine providing async interval and file watcher wakeup without polling

---

## Overview & Metadata

| Property | Value |
|---|---|
| Plugin Directory | `plugins/agent_orchestration/antigravity_trigger_runtime` |
| Category | `agent_orchestration` |
| Isolation Mode | `in_process` |
| Services Provided | `service.antigravity.trigger_runtime` |
| Dependencies Required | None |

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `register_interval_trigger` | `(trigger_id, interval_seconds)` | Register an asynchronous interval wakeup trigger |
| `register_file_change_trigger` | `(trigger_id, file_path)` | Register a reactive file-change wakeup trigger |
| `fire_reactive_trigger` | `(trigger_id, payload)` | Simulate reactive trigger wakeup |

---

## Key Modules & AST Symbols

### Module [main.py](main.py)

Antigravity Trigger Runtime Entrypoints.

#### Functions

- `def register_interval_trigger(trigger_id, interval_seconds) -> dict[str, Any]` — Register an asynchronous interval wakeup trigger.
- `def register_file_change_trigger(trigger_id, file_path) -> dict[str, Any]` — Register a reactive file-change wakeup trigger.
- `def fire_reactive_trigger(trigger_id, payload) -> dict[str, Any]` — Simulate reactive trigger wakeup.

### Module [__init__.py](__init__.py)

Antigravity Trigger Runtime Plugin Package.
### Module [service.py](service.py)

Google Antigravity Reactive Trigger Runtime Service & Plugin Implementation.

#### Classes

- `class RegisteredTrigger`
- `class AntigravityTriggerService` — Authoritative reactive trigger runtime engine.
  - `def __init__() -> None`
  - `def register_interval(trigger_id, interval_seconds) -> RegisteredTrigger` — Register an asynchronous cron/interval wakeup trigger.
  - `def register_file_watcher(trigger_id, file_path) -> RegisteredTrigger` — Register a reactive file-change wakeup trigger.
  - `def fire_trigger(trigger_id, payload) -> bool` — Simulate or execute reactive firing of a registered trigger.
  - `def get_trigger(trigger_id) -> RegisteredTrigger | None`
  - `def list_triggers() -> list[RegisteredTrigger]`
  - `def get_notifications() -> list[dict[str, Any]]`
- `class AntigravityTriggerRuntimePlugin` — In-process Harness plugin providing Antigravity reactive trigger service.
  - `def __init__() -> None`
  - `def provides() -> list[ServiceKey[Any]]`
  - `def on_load(ctx) -> None`
  - `def on_enable() -> None`
  - `def on_disable() -> None`
  - `def on_unload() -> None`


---

## Quickstart & Usage

```python
from harness.kernel.context import ServiceContext
from plugins.agent_orchestration.antigravity_trigger_runtime.main import plugin

# Load plugin into harness service context
context = ServiceContext()
plugin.on_load(context)
```

---

## Architecture & Diátaxis Classification

- Diátaxis Quadrant: Reference (Track B) & How-To Guides
- Isolation: `in_process` execution sandbox
- Invariants: Slotted dataclass architecture (Rule 12), transactional context bounds (Rule 8), and zero-fork YAML configuration (Rule 44).
