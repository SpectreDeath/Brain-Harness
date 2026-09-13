# Hierarchical Sub-Agent Task Coordination & Lifecycle States

## Context
In complex multi-agent workflows, spawning uncoordinated background agents leads to race conditions, overlapping tool calls, and lost diagnostic state when subtasks fail or stall.

## Distilled Learning
Enforce a formal Coordinator-Task lifecycle state machine across hierarchical agent executions:
- Tasks transition through explicit states: `Pending` → `Running` → (`Completed` | `Failed` | `Cancelled`).
- Each task maintains an isolated conversation transcript, execution context, and token accounting budget.
- Sub-agents communicate structured event streams (progress, tool observations, intermediate decisions) back to the parent coordinator.
- Parent coordinators maintain cancellation tokens and transactional rollback handlers if any child branch encounters an unrecoverable failure.

## Triggers & Seam Choices
- **Trigger**: Multi-agent swarms, parallel PR reviews, or delegated research sub-agents.
- **Seam Choice**: Register in `harness.services.agent_execution_graph` (Rule 17) with composite node thread identifiers (`{run_id}_{node_id}`).
