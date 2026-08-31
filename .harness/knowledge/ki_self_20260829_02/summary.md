# KI: Authoritative Thread DAG Lifecycle & Execution Graph Store

## Operational Summary
Multi-agent swarms and hierarchical sub-agent executions must not rely on ephemeral in-memory variables or untracked list fields. The `AgentExecutionGraphService` (`AGENT_GRAPH_STORE_KEY`) provides an authoritative, persistent DAG store tracking threads, directional spawn edges, lifecycle transitions, and instant tree exports.

## Core Capabilities
1. **Directional Spawn Edges**: Every sub-agent spawn establishes a directional `ExecutionGraphEdge` connecting `parent_id -> child_id` with `ThreadSpawnStatus` (`Open`, `Closed`, `Completed`, `Failed`).
2. **Resource & Token Rollups**: Automatically aggregates total token usage and execution durations across complete sub-agent trees.
3. **Hierarchical ASCII Tree Export**: Renders formatted ASCII execution trees on demand for CLI commands (`harness session tree`) and debugging telemetry.
4. **Structured JSON Exports**: Emits machine-readable DAG models for UI dashboards and cross-session audits.

## Key Code References
- Implementation: [`src/harness/services/agent_graph.py`](file:///D:/GitHub/projects/Brain%20Harness/src/harness/services/agent_graph.py)
- Unit Tests: [`tests/test_agent_graph_store.py`](file:///D:/GitHub/projects/Brain%20Harness/tests/test_agent_graph_store.py)
