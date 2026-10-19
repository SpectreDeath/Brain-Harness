```
┌────────────────────────────────────────────────────────┐
│               SKILL SUMMARY CARD                       │
├────────────────────────────────────────────────────────┤
│ SKILL:        prompt-pruning-architect                 │
│ Category:     agent_orchestration                      │
│ Invocation:   /prompt-pruning-architect                │
│ Triggers:     "prompt pruning", "3-pass pruner",       │
│               "token optimization", "context reduction"│
│ Version:      1.0.0                                    │
│ Isolation:    subprocess                               │
│ Provides:     "strategy.deterministic_prompt_pruner"   │
├────────────────────────────────────────────────────────┤
│ Target:       Apply deterministic 3-pass prompt pruning│
│               with expired tool elimination, duplicate │
│               dedup, and fixed-point idempotence.      │
└────────────────────────────────────────────────────────┘
```

# Prompt Pruning Architect — Companion Summary Card

## Stage Progression Table

| Stage | Core Responsibility | Primary Artifact | Completion Gate |
| --- | --- | --- | --- |
| **1. Expired Elimination** | Discard superseded intermediate tool observations | `pass1_pruned.json` | Only latest result per resource key retained |
| **2. Duplicate Dedup** | Collapse identical/near-identical retrieved passages | `pass2_deduped.json` | Redundant passages collapsed to canonical |
| **3. Dependency Restoration**| Restore DEFINE targets referenced by surviving REF tags | `pass3_restored.json` | Zero unresolved REF dependencies in working set |
| **4. Fixed-Point Audit** | Prove mathematical idempotence $f(f(x)) = f(x)$ | `pruning_audit.json` | Pruning twice yields identical message set |

---

## Mandatory Invariants Checklist

- [ ] **Fixed-Point Idempotence Invariant**: Applying the pruning pipeline twice sequentially must yield an identical output sequence.
- [ ] **Chronological Ordering Invariant**: Message sequences must preserve original relative turn ordering after dependency restoration.
- [ ] **Dependency Safety Invariant**: A message defining a key referenced by any surviving message must never remain evicted.
- [ ] **Slotted Immutability Invariant**: All message models and audit reports must use slotted frozen dataclasses.
