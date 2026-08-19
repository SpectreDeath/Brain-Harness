# Quick Start Guide: `plugin.task_planner` (v1.0.0)

> Hierarchical Directed Acyclic Graph (DAG) goal decomposition and milestone dependency tracker

## 🎯 When to Use
Use this plugin when you need capabilities related to `general`.

Common trigger intents:
- **`plan_decompose_goal`**: Create a new DAG execution plan for a goal with task dependencies
- **`plan_get_next_milestone`**: Get the next unblocked task(s) whose dependencies are completed
- **`plan_update_status`**: Update task status (pending, in_progress, completed, failed) and attach result
- **`plan_export_dag`**: Export the DAG plan in structured JSON and Mermaid graph format

## 🛠️ How to Use (Agent & User)
### Python / Runtime Tool Call:
```python
result = await runtime.tools.invoke('plugin.task_planner.plan_decompose_goal', {'goal': '<goal>', 'subtasks': '<subtasks>'})
```

### CLI Quick Action:
```powershell
harness tool list --provider plugin.task_planner
harness plugin enable plugin.task_planner
```

## ⚡ Available Entrypoints & Skills
- **`plan_decompose_goal(goal: string, subtasks: array)`**
  Create a new DAG execution plan for a goal with task dependencies
- **`plan_get_next_milestone(plan_id: string)`**
  Get the next unblocked task(s) whose dependencies are completed
- **`plan_update_status(plan_id: string, task_id: string, status: string, result: string)`**
  Update task status (pending, in_progress, completed, failed) and attach result
- **`plan_export_dag(plan_id: string)`**
  Export the DAG plan in structured JSON and Mermaid graph format