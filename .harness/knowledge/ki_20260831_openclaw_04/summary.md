# Deterministic Session Tree Branching & Compaction with UUIDv7

## Context
Standard agent execution frameworks represent conversation history as flat linear message arrays. When sub-agents explore alternative problem hypotheses or rollback failed tool executions, linear structures either destroy the alternative branch history or contaminate the main prompt context with dead ends.

## Distilled Learning
Adopt a tree-structured session architecture with UUIDv7:
1. **Time-Ordered UUIDv7 Node Keys**:
   - Every turn, fork, and compaction snapshot receives a UUIDv7 identifier combining a 48-bit millisecond timestamp with cryptographically random bits.
   - Enables monotonic ordering across distributed nodes and fast range queries in relational/document stores without secondary timestamp indices.
2. **Branch Provenance**:
   - Each session node points to its `parent_id` and tracks a `branch_id`.
   - Creating a speculative fork is an $O(1)$ operation that creates a new child node referencing the ancestor commit.
3. **Progressive Compaction**:
   - Completed or pruned branches are summarized via `collectEntriesForBranchSummaryFromBranches` into condensed branch summary nodes, shrinking context budgets while preserving lineage.

## Triggers & Seam Choices
- **Trigger**: Multi-branch speculative execution, agent rollback transactions, and session tree exports.
- **Seam Choice**: Integrate with Harness `AgentExecutionGraphService` (`AGENT_GRAPH_STORE_KEY`) and `ContextCompactorService`.
