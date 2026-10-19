```
┌────────────────────────────────────────────────────────┐
│               SKILL SUMMARY CARD                       │
├────────────────────────────────────────────────────────┤
│ SKILL:        ebbinghaus-memory-governor               │
│ Category:     memory_and_epistemics                    │
│ Invocation:   /ebbinghaus-memory-governor              │
│ Triggers:     "memory decay", "ebbinghaus retention",  │
│               "forgetting curve", "working set decay", │
│               "cognitive eviction"                     │
│ Version:      1.0.0                                    │
│ Isolation:    subprocess                               │
│ Provides:     "service.memory_decay"                   │
├────────────────────────────────────────────────────────┤
│ Target:       Govern cognitive memory decay curves,    │
│               reinforce stability on recall, and       │
│               evict sub-threshold working set items.   │
└────────────────────────────────────────────────────────┘
```

# Ebbinghaus Memory Governor — Companion Summary Card

## Stage Progression Table

| Stage | Core Responsibility | Primary Artifact | Completion Gate |
| --- | --- | --- | --- |
| **1. Observation Intake** | Ingest tool output or instruction with channel classification | `memory_node.json` | Node registered with initial stability $S \ge 1.0$ |
| **2. Decay Simulation** | Compute retention score $R = e^{-\Delta t / S}$ across active nodes | `decay_report.json` | All active items scored against current turn |
| **3. Non-Linear Recall** | Reinforce stability non-linearly upon explicit recall | `reinforced_node.json` | Stability increases monotonically with recall count |
| **4. Sub-Threshold Eviction** | Evict items dropping below retention threshold into history | `eviction_decision.json` | Working set bounded strictly $\le$ max nodes |

---

## Mandatory Invariants Checklist

- [ ] **Deterministic Turn Step Invariant**: Decay must strictly depend on logical turn counts, never system wall-clock timestamps.
- [ ] **Monotonic Stability Invariant**: Every recall event must monotonically increase stability $S$ without regression.
- [ ] **Foundational Immunity Invariant**: Items flagged as `is_foundational=True` must never be evicted by automatic decay routines.
- [ ] **Slotted Immutability Invariant**: All domain nodes and decision records must adhere to slotted frozen dataclass contracts.
