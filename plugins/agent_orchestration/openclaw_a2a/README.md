# plugin.openclaw_a2a (v1.0.0)

A2A v1.0 Agent-to-Agent protocol adapter for cross-host swarm federation, task delegation, and distributed observation streaming.

---

## Overview & Metadata

| Property | Value |
|---|---|
| Plugin Directory | `plugins/agent_orchestration/openclaw_a2a` |
| Category | `agent_orchestration` |
| Isolation Mode | `in_process` |
| Services Provided | None |
| Dependencies Required | None |

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `openclaw_a2a_send_task` | `(recipient_agent, task_payload, sender_agent)` | Dispatches an asynchronous subtask to a federated remote or local A2A agent runtime. |
| `openclaw_a2a_poll_task` | `(task_id)` | Polls the status, observation, and token telemetry of an active A2A task. |
| `openclaw_a2a_complete_task` | `(task_id, observation, tokens_used)` | Completes an A2A task and records observation output and token rollups. |
| `openclaw_a2a_resolve_capabilities` | `(agent_id)` | Queries supported capabilities, tools, and archetype roles for a registered A2A agent. |

---

## Key Modules & AST Symbols

### Module [main.py](main.py)

OpenClaw A2A Plugin — A2A v1.0 Agent-to-Agent protocol adapter for multi-agent swarm federation.

#### Classes

- `class OpenClawA2AServiceImpl` — In-memory and remote federation implementation of A2A v1.0 protocol.
  - `def __init__() -> None`
  - `def send_task(recipient_agent, task_payload, sender_agent) -> OpenClawA2ATask` — Dispatches an asynchronous task to a remote or local A2A agent.
  - `def poll_task(task_id) -> OpenClawA2ATask` — Polls the execution status and observation of an A2A task.
  - `def complete_task(task_id, observation, tokens_used) -> OpenClawA2ATask` — Marks a local or federated task as completed with observation payload.
  - `def resolve_agent_capabilities(agent_id) -> dict[str, Any]` — Resolves registered capabilities and tool archetypes for an agent.
- `class OpenClawA2APlugin` — Harness plugin registering OpenClaw A2A protocol federation service and tools.
  - `def __init__() -> None`
  - `def register_services(context) -> None` — Register the typed OpenClawA2AService into the IoC container.
  - `def openclaw_a2a_send_task(recipient_agent, task_payload, sender_agent) -> dict[str, Any]` — Tool handler for openclaw_a2a_send_task.
  - `def openclaw_a2a_poll_task(task_id) -> dict[str, Any]` — Tool handler for openclaw_a2a_poll_task.
  - `def openclaw_a2a_complete_task(task_id, observation, tokens_used) -> dict[str, Any]` — Tool handler for openclaw_a2a_complete_task.
  - `def openclaw_a2a_resolve_capabilities(agent_id) -> dict[str, Any]` — Tool handler for openclaw_a2a_resolve_capabilities.


---

## Quickstart & Usage

```python
from harness.kernel.context import ServiceContext
from plugins.agent_orchestration.openclaw_a2a.main import plugin

# Load plugin into harness service context
context = ServiceContext()
plugin.on_load(context)
```

---

## Architecture & Diátaxis Classification

- Diátaxis Quadrant: Reference (Track B) & How-To Guides
- Isolation: `in_process` execution sandbox
- Invariants: Slotted dataclass architecture (Rule 12), transactional context bounds (Rule 8), and zero-fork YAML configuration (Rule 44).
