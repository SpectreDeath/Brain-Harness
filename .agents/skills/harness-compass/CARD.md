# Skill Summary Card: `harness-compass`

```
┌────────────────────────────────────────────────────────┐
│               SKILL SUMMARY CARD                       │
├────────────────────────────────────────────────────────┤
│ SKILL:       harness-compass                           │
│ Category:    agent_orchestration / harness-evolution   │
│ Invocation:  /harness-compass                          │
│ Trigger:     "evolve harness", "harness compass",      │
│              "automatic harness evolution",            │
│              "generalization gate", "r3 integration",  │
│              "prevent harness overfitting"             │
│ Version:     1.0.0                                     │
│ Provides:    "automatic_harness_evolution"             │
├────────────────────────────────────────────────────────┤
│ Target:      Evolve, calibrate, and optimize AI agent  │
│              harnesses with mathematical bounds,       │
│              preventing overfitting and prompt bloat.  │
└────────────────────────────────────────────────────────┘
```

---

## The 5-Stage Harness Evolution Cycle

| Stage | Objective | Primary Mechanism | Completion Gate |
|---|---|---|---|
| **1. Seed Initialization** | Boot minimal seed harness $H_0$ and isolate test splits | Shell-only tool, minimal prompt, $k \ge 2$ rollouts | Seed operational, sample $D$ separated from held-out set |
| **2. Generalization Gate** | Enforce Content & Placement invariants across all 7 surfaces | Automated regex token scanner & placement validator | 100% edits task-agnostic; zero advisory code leaks |
| **3. Proactive Feedback** | Elicit first-person friction and ground against traces | Blind pre-report $\rightarrow$ Hindsight attribution $\rightarrow$ Grounding | Non-harness failures dropped; trace citations verified |
| **4. Dual-Track Evolution** | Partition exploration into disjoint Structural and Guidance tracks | Parallel track evaluation ($T_{struct}$ vs $T_{guidance}$) | Winner $H_w$ and Loser $H_\ell$ designated by Pass@1 |
| **5. R3 Integration** | Fuse loser gains onto winner base and purge duplicate advice | R3: Revision $\rightarrow$ Recombination $\rightarrow$ Refinement (Occam's) | Advisory rules duplicating code purged; manifest signed |

---

## The Three Pillars Cheat Sheet

### 1. Global Generalization Gate (Core Principle 1)
```python
# Content Invariant: REJECT task IDs, test files, private symbols, keyword branching
# Placement Invariant: Capability in Middleware/Tools; Guidance in Prompt/Memory
gate = GeneralizationGate()
result = gate.validate_edit(candidate_edit)
assert result.passed, f"Gate violations: {result.violations}"
```

### 2. Proactive First-Person Feedback (Core Principle 2)
```python
# Step 1: Blind Report (outcome hidden) -> friction + wished capabilities
# Step 2: Hindsight Report (verdict revealed) -> failure attribution
# Step 3: Reconciliation -> compute agreement (pre_post_agree / partial / conflict)
# Step 4: Trajectory Grounding -> verify trace evidence before admitting to evolution
```

### 3. R3 Integrator & Occam's Razor (Core Principle 3)
```python
# 1. Revision: Enumerate loser edits; keep independent positive; drop regressions
# 2. Recombination: Apply kept loser edits onto winner base
# 3. Refinement: HUNT for advisory prompt/memory rules duplicated by code; PURGE THEM
engine = R3IntegratorEngine()
manifest = engine.merge(winner, w_score, w_edits, loser, l_score, l_edits)
```

---

## Verification & Quality Checklist

- [ ] **Content Invariant**: Zero benchmark task IDs, test file paths, or private repo symbols in any component.
- [ ] **Placement Invariant**: Structural components execute deterministic actions; guidance text contains advice.
- [ ] **Attribution Hygiene**: Tasks failing from model reasoning errors or environment crashes are discarded.
- [ ] **Trajectory Grounding**: Every retained friction claim has verbatim turn citations verified against the trace.
- [ ] **Occam's Razor Purge**: Every advisory prompt rule duplicated by deterministic middleware is deleted.
- [ ] **Pre-Flight Validation**: Passes `harness skills validate` with zero errors.
