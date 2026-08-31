# Storage-Neutral Parent/Child Topology with agent-graph-store

## Problem
In complex agent architectures where an orchestrator spawns specialized workers or subagents, hardcoding edge states, thread lineages, and spawn metadata into concrete storage drivers (SQLite/Postgres) prevents local ephemeral testing and clean architectural decoupling.

## Solution
Define an asynchronous graph store trait (`AgentGraphStore`) exposing:
1. Storage-neutral parent/child relationships between threads.
2. Explicit edge status transitions (`ThreadSpawnEdgeStatus`: active, completed, failed, cancelled).
3. Pluggable backend implementations (`LocalAgentGraphStore` for local in-memory/embedded execution, cloud graph store for distributed enterprise deployments).

## Operational Guideline
- Keep agent relationship topologies storage-neutral.
- Track agent spawn relationships as explicit DAG edges with defined lifecycle states rather than relying on unstructured parent metadata tags.

## Provenance
- Source repository: `D:/GitHub/cloned/codex-main/codex-main`
- Primary files: `codex-rs/agent-graph-store/src/lib.rs#L1-L13`, `codex-rs/agent-graph-store/src/store.rs`, `codex-rs/agent-graph-store/src/types.rs`
