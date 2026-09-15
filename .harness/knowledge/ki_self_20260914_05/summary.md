# Authoritative Swarm Thread DAG Lifecycle & Session State Keying

## Executive Summary
This Knowledge Item defines the authoritative contracts governing swarm wave coordination, execution graph persistence, and session manager state transitions, formalized under **Rule 17** (*Authoritative Thread DAG & Execution Graph Lifecycle*) and **Rule 36** (*Swarm Thread DAG Keying & Session Manager Contract Invariant*).

## Architectural Mechanics
1. **Composite Thread Keying Invariant**:
   - To eliminate node ID collisions across parallel swarm runs or re-entrant waves, `AgentExecutionGraphService` indexes thread DAG nodes via `f"{run_id}_{node_id}"`.
   - Node lookups and relationship traversals strictly adhere to this composite format.
2. **Session Manager State Transition Contract**:
   - In `AgentSessionManager`, session creation requires `task: str` as the primary argument (prohibiting ambiguous `goal` or `agent_name` parameters).
   - Session completion requires `final_answer: str` (prohibiting `summary`).
   - Session failure requires `error_message: str` (prohibiting `error`).
3. **Hierarchical Token Rollups & ASCII Tree Export**:
   - Child agent tokens (prompt, completion, thinking) are recursively rolled up to parent nodes along directional spawn edges.
   - Session inspection seams expose headless ASCII and JSON tree export commands (`harness session tree`) conforming to Rule 10.

## Verifiable Isnad Lineage
- **Source Seams**: `src/harness/services/agent_graph.py:25-175`, `src/harness/agent/session.py:40-120`.
- **Governing Invariants**: `AGENTS.md` Rule 10, Rule 17, Rule 36.
