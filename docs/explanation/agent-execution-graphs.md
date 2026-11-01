# Agent Execution Graphs: The 3-Phase Lifecycle Architecture

## Overview

Complex multi-agent swarms require rigorous lifecycle management. Without strict architectural seams, planning, in-flight state tracking, and post-execution forensics blur together, causing state corruption and untracked token expenditures.

The Harness divides multi-agent thread execution into **three distinct phases**, each with its own slotted data model and persistence contract:

```
┌─────────────────────────────────────────────────────────────┐
│             Phase 1: Compile-Time Work Plan                 │
│         (SwarmDAG & Topological DependencyGraph)            │
└──────────────────────────────┬──────────────────────────────┘
                               │
                register_swarm_dag_in_graph()
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│            Phase 2: In-Flight Runtime Topology              │
│       (AgentExecutionGraphService & ThreadSpawnStatus)      │
└──────────────────────────────┬──────────────────────────────┘
                               │
                   tx.dispose() & Session Sync
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│          Phase 3: Persistent Trajectory Store & CLI         │
│          (AgentSessionManager & Headless CLI Seams)         │
└─────────────────────────────────────────────────────────────┘
```

---

## The Three Lifecycle Phases

### Phase 1: Compile-Time Plan (`SwarmDAG`)
- **Component**: `src/harness/agent/swarm/models.py`
- **Data Model**: Slotted/frozen static work plan (`SwarmDAG`, `SwarmNode`).
- **Responsibilities**:
  - Validates DAG acyclicity via `DependencyGraph`.
  - Computes parallel execution waves (`get_execution_plan()`).
  - Pre-allocates token budgets (`allocated_tokens`) per node before execution begins.

### Phase 2: In-Flight Runtime Topology (`AgentExecutionGraphService`)
- **Component**: `src/harness/services/agent_graph.py` (`AGENT_GRAPH_STORE_KEY`)
- **Data Model**: Directional parent-child spawn edges (`ExecutionGraphEdge`) and thread nodes (`ExecutionGraphNode`).
- **Responsibilities**:
  - Tracks live execution status transitions (`OPEN` → `COMPLETED` / `FAILED` / `CLOSED`).
  - Aggregates recursive token rollups across the active process tree (`Rule 17`).
  - Renders real-time hierarchical ASCII trees for CLI inspection.

### Phase 3: Persistent Trajectory Store & Forensics (`AgentSessionManager`)
- **Component**: `src/harness/agent/session.py` and `src/harness/commands/session.py`
- **Data Model**: Durable relational SQLite session records (`conversations/<cid>.db`).
- **Responsibilities**:
  - Implements canonical session lifecycle contracts: `task` (input), `final_answer` (success), `error_message` (failure) per `Rule 36`.
  - Exposes headless Click CLI inspection and export seams (`harness session list`, `harness session tree`, `harness session export`) per `Rule 10`.

---

## The Deterministic Bridge Helper

To prevent boilerplate and thread ID collisions across runs, `register_swarm_dag_in_graph` deterministically bridges a static `SwarmDAG` into `AgentExecutionGraphService`:

```python
from harness.agent.swarm.models import SwarmDAG, SwarmNode, register_swarm_dag_in_graph
from harness.services.agent_graph import DefaultAgentExecutionGraphService

dag = SwarmDAG()
dag.add_node(SwarmNode(id="research", role="researcher", task="Mine repos", dependencies=[]))
dag.add_node(SwarmNode(id="synthesize", role="writer", task="Write brief", dependencies=["research"]))

graph_svc = DefaultAgentExecutionGraphService()
# Automatically generates composite keys: f"{run_id}_{node_id}" (Rule 36)
registered_ids = register_swarm_dag_in_graph(dag, graph_svc, run_id="run_42")

print(graph_svc.render_ascii_tree())
```

Output:
```
└── [●] root (swarm_orchestrator) - 'Swarm Run run_42' [0 tok]
    └── [●] run_42_research (researcher) - 'Mine repos' [0 tok]
        └── [●] run_42_synthesize (writer) - 'Write brief' [0 tok]
```

---

## Headless CLI Inspection Seams

Inspect execution trees and session trajectories headlessly:
```bash
# Inspect session list
harness session list --json

# View hierarchical execution tree for a session
harness session tree <session-id>

# Export full session trajectory JSON
harness session export <session-id> --output trajectory.json
```

See the [CLI Reference](../reference/cli.md) and [Swarm Reflection Optimizer](../../.agents/skills/swarm-reflection-optimizer/SKILL.md) for further implementation details.
