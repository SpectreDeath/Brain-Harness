# Hierarchical DAG Task Planning

## Overview

Complex autonomous operations cannot be achieved in a single prompt. The `task_planner` plugin breaks long-horizon goals into a Directed Acyclic Graph (DAG) of interdependent subtasks.

```
       [task_1_research]
              │
              ▼
       [task_2_execute]
              │
              ▼
        [task_3_verify]
```

## Key Operations

1. `plan_decompose_goal`: Defines tasks and explicit `depends_on` lists.
2. `plan_get_next_milestone`: Queries the graph for unblocked tasks whose dependencies are completed.
3. `plan_update_status`: Transitions task status and unblocks downstream tasks.
4. `plan_export_dag`: Exports Mermaid and JSON representations.
