# Problem: Store and Recall Memory via Memtext Bridge

## Objective

Load `MemtextServicePlugin` into a `ServiceContext`, store key facts, log a decision in the audit ledger, and recall memories matching a search query.

## Tasks

1. Load `ToolRegistryPlugin` and `MemtextServicePlugin`.
2. Enable the bridge.
3. Save two memories with `remember()`.
4. Log a decision with `log_decision()`.
5. Recall matching memories.
