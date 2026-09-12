# plugin.task_planner (v1.0.0)

Hierarchical Directed Acyclic Graph (DAG) goal decomposition and milestone dependency tracker

---

## Overview & Metadata

- **Plugin Directory**: `plugins/agent_orchestration/task_planner`
- **Isolation Mode**: `in_process`
- **Services Provided**: None
- **Dependencies Required**: None

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `plan_decompose_goal` | `(goal, subtasks)` | Create a new DAG execution plan for a goal with task dependencies |
| `plan_get_next_milestone` | `(plan_id)` | Get the next unblocked task(s) whose dependencies are completed |
| `plan_update_status` | `(plan_id, task_id, status, result)` | Update task status (pending, in_progress, completed, failed) and attach result |
| `plan_export_dag` | `(plan_id)` | Export the DAG plan in structured JSON and Mermaid graph format |

---

## Key Modules & AST Symbols

### Module [`main.py`](main.py)

Hierarchical DAG Task Planner and Milestone Tracker plugin for Brain Harness.

#### Functions

- `def plan_decompose_goal(goal, subtasks) -> dict[str, Any]`
  - Create a new DAG plan for a goal with task dependencies.
- `def plan_get_next_milestone(plan_id) -> dict[str, Any]`
  - Identify tasks whose dependencies are fully completed and are ready to execute.
- `def plan_update_status(plan_id, task_id, status, result) -> dict[str, Any]`
  - Update task status in the plan.
- `def plan_export_dag(plan_id) -> dict[str, Any]`
  - Export the DAG plan in structured JSON and Mermaid graph format.



---

## Related Documentation & Configuration
- Manifest: [`plugin.json`](plugin.json)
- Architecture Seams: [Context Architecture](../../../CONTEXT-MAP.md) | [User Manual](../../../USER_MANUAL.md)
