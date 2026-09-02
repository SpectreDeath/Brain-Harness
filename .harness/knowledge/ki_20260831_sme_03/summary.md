# 4-Stage Candidate Block Validation Filter & SQLite WAL Candidate Pool Storage

## Context
When agents autonomously generate or optimize sub-agent team structures, unconstrained generation risks invalid node definitions, disconnected edges, circular deadlocks, or performance regressions.

## Distilled Learning
Implement a 4-stage validation pipeline and persistent pool architecture:
1. **Stage 1 (Node Validation)**: Verifies all declared nodes have valid agent roles, non-empty prompts, and supported capabilities.
2. **Stage 2 (Edge Validation)**: Ensures all edge source and target nodes exist within the candidate block, rejecting dangling connections.
3. **Stage 3 (Structural Acyclicity & Deduplication)**:
   - Validates that directed edges form a strictly acyclic DAG.
   - Prevents duplicate structures from polluting candidate pools.
4. **Stage 4 (Performance Baseline)**: Confirms the candidate's projected loss score improves upon baseline execution metrics.
5. **Persistent Storage (`CandidatePoolStorage`)**:
   - Persists validated candidate team blocks into SQLite WAL-backed tables indexed by layer and block ID.
   - Supports $O(1)$ dynamic team block selection during execution.

## Triggers & Seam Choices
- **Trigger**: Gating any autonomously synthesized sub-agent topology before deployment.
- **Seam Choice**: Place in `src/harness/agent/candidate_pool.py` to manage swarm archetypes.
