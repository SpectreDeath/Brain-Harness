---
name: ebbinghaus-memory-governor
description: Govern conversational agent working memory retention using Ebbinghaus forgetting curves, channel decay multipliers, and non-linear recall stability reinforcement. Do not use for permanent database storage or ungrounded cache purges.
cluster: memory_and_epistemics
---

# Ebbinghaus Memory Governor

## Overview

The Ebbinghaus Memory Governor provides mathematical forgetting curve retention management for agent working memory. By modeling non-linear stability growth upon repeated recall, foundational instructions remain protected indefinitely while ephemeral tool outputs decay and soft-evict predictably.

```
┌─────────────────────────────────────────────────────────────┐
│                 Turn Advance: step_turn()                   │
└──────────────────────────────┬──────────────────────────────┘
                               │
       ┌───────────────────────┴───────────────────────┐
       ▼                                               ▼
┌──────────────────────────────┐        ┌──────────────────────────────┐
│ is_foundational = True       │        │ is_foundational = False      │
│ (Immune to Eviction)         │        │ R(t) = exp(-Δt / (S / m))    │
└──────────────────────────────┘        └──────────────┬───────────────┘
                                                       │
                                        ┌──────────────┴───────────────┐
                                        ▼                              ▼
                         ┌─────────────────────────────┐ ┌─────────────────────────────┐
                         │ R(t) >= 0.20                │ │ R(t) < 0.20                 │
                         │ ACTIVE IN WORKING SET       │ │ SOFT EVICTION               │
                         │ Included in recall & prompt │ │ item.evicted = True         │
                         │ S_new = S * (1 + ln(1 + n)) │ │ Preserved in item history   │
                         └─────────────────────────────┘ └─────────────────────────────┘
```

---

## Verified Soft-Demotion Semantics

Forgetting in this engine is **soft eviction (demotion from active working set), NOT permanent deletion**:
1. **Turn-Based Retention Calculus**:
   At each dialogue step $\Delta t$, retention is computed as:
   $$R(t) = \exp\left(-\frac{\Delta t}{S / m_{\text{channel}}}\right)$$
2. **Channel Decay Multipliers**:
   Channel multipliers $m_{\text{channel}}$ scale the rate of decay across 5 semantic channels (aligned with [Context Type System](../context-type-system/SKILL.md)):
   - `instruction`: $0.25\times$ (ultra-slow decay)
   - `foundational`: $0.35\times$ (slow decay)
   - `evidence`: $0.70\times$ (moderate decay)
   - `memory`: $1.00\times$ (standard baseline)
   - `tool_output`: $1.75\times$ (rapid decay)
3. **Soft Eviction (`item.evicted = True`)**:
   When $R(t) < 0.20$, the item is marked as `evicted = True`. It is excluded from active `working_set()` and `recall()`, but **remains in memory storage** (`engine.items`) and is fully preserved in exported snapshot files and recoverable via `memory_query_working_set(include_evicted=True)`.
4. **Foundational Immunity**:
   Items with `is_foundational=True` bypass the retention check and are **never evicted**.
5. **Non-Linear Stability Reinforcement**:
   Recalling an active item increases its stability monotonically:
   $$S_{\text{new}} = S_{\text{old}} \cdot (1 + \ln(1 + n_{\text{recalls}}))$$

---

## Visual Brief

### Architecture
- **Logical Turn Clock**: Decay is evaluated strictly against turn increments, never system wall-clock time.
- **Channel Partitioning**: Decay speeds mirror data reliability, prioritizing validated evidence over ephemeral tool output.
- **State Serialization**: Session states export to portable JSON snapshots for cross-run reproducibility.

### Verification Flow
1. Register memory items via `harness memory register`.
2. Advance conversation turns via `harness memory step`.
3. Inspect active vs soft-evicted items via `harness memory working-set`.
4. Run comparative decay benchmarks via `harness memory benchmark`.

---

## Operational Workflow

```bash
# 1. Register foundational instruction (immune to eviction)
harness memory register --key "rule-1" --content "Preserve docstrings" --channel instruction --foundational

# 2. Register ephemeral tool output (fast decay)
harness memory register --key "temp-grep" --content "Grep returned 4 lines" --channel tool_output --stability 2.0

# 3. Advance turns
harness memory step --turns 5

# 4. Recall and reinforce an item
harness memory recall "rule-1"

# 5. Inspect working set (active only)
harness memory working-set --ranked

# 6. Inspect complete history (including soft-evicted items)
harness memory working-set --include-evicted
```

---

## Mandatory Checkpoints

- [ ] **Deterministic Turn Clock**: Verify that decay occurs only upon explicit `step_turn()`, never wall-clock time.
- [ ] **Foundational Immunity**: Verify that items with `is_foundational=True` remain in `working_set()` regardless of turn count.
- [ ] **Soft Demotion Invariant**: Verify that soft-evicted items remain retrievable via `include_evicted=True`.

---

## Anti-Patterns

- **Recency-Only Purging** — Evicting frequently recalled foundational facts simply because they were not touched in the most recent turn.
- **Hard Item Deletion** — Permanently dropping items from session history upon eviction instead of setting `item.evicted = True`.
- **Wall-Clock Decay Coupling** — Relying on real-time system timestamps instead of logical conversation turn steps for deterministic reproducibility.
- **Unweighted Decay Rates** — Subjecting raw tool output and system instructions to identical decay schedules.

---

## Related Skills & Docs

- [Context Type System](../context-type-system/SKILL.md)
- [OKF Memory Governor](../okf-memory-governor/SKILL.md)
- [Learning Core Lifecycle Narrative](../../docs/explanation/learning-core-lifecycle.md)
- [Memory Architecture Explanation](../../docs/explanation/memory-architecture.md)
