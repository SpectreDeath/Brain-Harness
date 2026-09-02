# Skill Summary Card: `sme-ann-backprop`

```
┌────────────────────────────────────────────────────────┐
│               SKILL SUMMARY CARD                       │
├────────────────────────────────────────────────────────┤
│ Name:        sme-ann-backprop                          │
│ Category:    agentic / self-evolution / backprop       │
│ Invocation:  /sme-ann-backprop                         │
│ Trigger:     "ann backprop", "textual gradient",       │
│              "optimize agent dag", "momentum buffer"   │
│ Version:     1.0.0                                     │
│ Requires:    "data-topology-mapper", "crafting-skills" │
│ Provides:    "ann_textual_backpropagation"             │
├────────────────────────────────────────────────────────┤
│ Target:      Autonomous multi-agent DAG optimization   │
│              via textual loss backpropagation,         │
│              momentum smoothing, and 4-stage filters.  │
└────────────────────────────────────────────────────────┘
```

---

## The 5-Stage ANN Backpropagation Progression

| Stage | Objective | Primary Artifact / Output | Invariant Gate |
|---|---|---|---|
| **1. Trajectory Analysis** | Compute global loss signal ($G_{\text{global}}$) | `GlobalGradient` object | Loss bounded in $[0, 1]$ |
| **2. Layerwise Gradients** | Synthesize node/edge/prompt updates ($G_{\text{local}}$) | `LocalGradient` per layer | Schema constraint appended |
| **3. Momentum Smoothing** | Smooth update velocity across iterations | Smoothed $G'_{t}$ ($\alpha=0.7$) | Zero prompt thrashing |
| **4. 4-Stage Validation** | Filter candidate team blocks ($f'_{\ell}$) | Validation Report | Node &rarr; Edge &rarr; Structure &rarr; Perf |
| **5. Pool Commit & Route** | Store validated block in SQLite WAL pool | `candidate_pools` DB Record | $O(1)$ dynamic retrieval |

---

## Key Mathematical Formulations

- **Combined Loss**: $\text{Loss}_{\text{combined}} = \beta \cdot \text{Loss}_{\text{global}} + (1 - \beta) \cdot \text{Loss}_{\text{local}}$ (with $\beta=0.5$)
- **Momentum Smoothing**: $G'_{t,\ell} = \alpha \cdot G_{t,\ell} + (1 - \alpha) \cdot G_{t-1,\ell}$ (with $\alpha=0.7$)
- **Candidate Pool Retrieval**: $\text{Select}(F_{\ell}) = \arg\min_{f \in F_{\ell}} \text{Loss}(f)$

---

## Invariants & Guardrails

- [ ] **Strict DAG Acyclicity**: Candidate team blocks must pass DFS/topological cycle detection.
- [ ] **4-Stage Verification**: Never insert unverified agent structures into persistent candidate pools.
- [ ] **SQLite WAL Isolation**: All candidate pool reads and writes must execute under SQLite WAL mode (`PRAGMA journal_mode=WAL`).
- [ ] **Isnad Provenance**: All distilled prompt optimizations must retain lineage back to primary execution trajectories.
