# Hierarchical StateStore Shadowing with Scope Isolation

**ID:** `ki_antigravity_003`  
**Category:** `agent_orchestration`  
**Origin:** `google-antigravity-sdk`  
**Provenance Lineage:** `google/antigravity/utils/state.py`

## Executive Summary
Antigravity's StateStore implements parent-child state shadowing across multi-agent hierarchies. Subagents transparently read inherited configuration and variables from parent sessions, but any state mutations or new keys remain isolated in child dictionary scopes, preventing state leakage or race conditions between parallel subagents.

## Architectural Invariants & Rules
1. Child agent scopes shadow parent state transparently on read operations.
2. Write operations in child scopes must never mutate the parent StateStore dictionary.
3. Subagent completion must merge only explicitly exported keys back to the parent session.
