# OpenClaw A2A Plugin Quickstart

The `plugin.openclaw_a2a` provides an A2A (Agent-to-Agent) v1.0 protocol adapter to enable federated multi-agent swarms, cross-network task dispatching, and distributed observation streaming.

## Key Capabilities

1. **`openclaw_a2a_send_task`**: Dispatches a structured task envelope to another agent in the swarm.
2. **`openclaw_a2a_poll_task`**: Inspects progress, status, and intermediate output of a delegated task.
3. **`openclaw_a2a_complete_task`**: Finalizes a task with observation data and token telemetry.
4. **`openclaw_a2a_resolve_capabilities`**: Queries capability archetypes and supported tools of an agent.

## Example Usage

```python
from harness.kernel.context import ServiceContext
from harness.services.openclaw_bridge import OPENCLAW_A2A_KEY

a2a_svc = context.resolve(OPENCLAW_A2A_KEY)

# Dispatch a task to a specialized worker agent
task = await a2a_svc.send_task(
    recipient_agent="openclaw_worker",
    task_payload={"action": "search_code", "query": "WebSocket RPC"},
    sender_agent="harness_lead",
)

# Complete the task
await a2a_svc.complete_task(
    task_id=task.task_id,
    observation={"results": ["src/gateway/server.ts"]},
    tokens_used=450,
)
```
