---
name: prompt-pruning-architect
description: Architect and apply compiler-style 3-pass deterministic prompt pruning with expired tool elimination, duplicate reduction, and fixed-point idempotence. Do not use for subjective narrative editing or semantic summarization.
---

# Prompt Pruning Architect

The Prompt Pruning Architect implements a deterministic, multi-pass optimization pipeline over conversational agent messages before model dispatch. Mirroring compiler dead-code elimination, it guarantees fixed-point idempotence ($f(f(x)) = f(x)$) and bounded token consumption.

## Operational Workflow

1. **Pass 1 — Expired Tool Context Elimination**: Identifies resource keys (files, URLs, query IDs) across tool invocations and discards superseded intermediate outputs, preserving only the most recent state.
2. **Pass 2 — Duplicate Context Elimination**: Normalizes whitespace and casing across retrieved document chunks and collapses redundant passages to their canonical first occurrence.
3. **Pass 3 — Dependency Restoration**: Evaluates survivor messages for explicit references (`REF:<id>`) and restores any evicted message declaring a matching definition (`DEFINE:<id>`).
4. **Idempotence & Token Audit**: Validates that re-running the pruner generates zero additional message drops and records audit diagnostics.

## Anti-Patterns

- **Heuristic Truncation Drift** — Arbitrarily slicing character counts without respecting tool call boundaries and dependency references.
- **Non-Idempotent Cascades** — Applying sequential filter rules where subsequent passes re-evict or re-introduce unstable message sequences.
- **Lossy Dependency Eviction** — Dropping early schema or tool parameter definitions required by later user queries.

## Diagnostic Verification

Verify pruning reduction and idempotence using `harness.services.context_optimizer.DeterministicPromptPruner` or the plugin tools `prune_messages` and `estimate_prompt_reduction`.
