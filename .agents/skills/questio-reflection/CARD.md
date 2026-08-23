# Skill Summary Card: `questio-reflection`

```
┌────────────────────────────────────────────────────────┐
│               SKILL SUMMARY CARD                       │
├────────────────────────────────────────────────────────┤
│ Name:        questio-reflection                        │
│ Category:    architecture / epistemic-governance       │
│ Invocation:  /questio-reflection                       │
│ Trigger:     "adversarial reflection", "questio check",│
│              "stress test plan", "pre-commit reflection│
│ Version:     1.0.0                                     │
│ Requires:    "crafting-skills"                         │
│ Provides:    "adversarial_gate"                        │
├────────────────────────────────────────────────────────┤
│ Target:      Force Aquinas-style adversarial self-     │
│              reflection and tri-vector failure mode    │
│              mitigation prior to mutating code/state.  │
└────────────────────────────────────────────────────────┘
```

---

## The 5-Stage Questio Loop

| Stage | Objective | Primary Artifact / Output | Completion Gate |
|---|---|---|---|
| **1. Propositio** | Formulate core thesis, affected files, and invariant bounds | Thesis declaration block | Exact file links and candidate blast radius |
| **2. Videtur Quod Non** | Construct 3 adversarial failure modes (Coupling, Runtime, Epistemic) | Tri-vector objection list | 3 non-trivial failure scenarios defined |
| **3. Sed Contra** | Counter-ground viability with verified workspace code lines | Verified file URI links | Every premise linked to file/line references |
| **4. Visual Brief** | Render interactive HTML attack tree & objection matrix | `%TEMP%\questio-review-*.html` | Dark-mode HTML written and delivered |
| **5. Respondeo** | Embed mitigations in implementation plan and await user approval | `implementation_plan.md` | `RequestFeedback: true` approved by user |

---

## Tri-Vector Adversarial Matrix

```
┌─────────────────────────────────────────────────────────────────┐
│                      TRI-VECTOR CRITIQUE                        │
├────────────────────────────────┬────────────────────────────────┤
│ Vector A: Architectural Seams  │ Cyclic deps, leaking internals,│
│                                │ IoC violations, contract churn │
├────────────────────────────────┼────────────────────────────────┤
│ Vector B: Runtime & Hardware   │ Async deadlocks, concurrency,  │
│                                │ memory leaks, sandbox failures │
├────────────────────────────────┼────────────────────────────────┤
│ Vector C: Epistemic Drift      │ Stale cache, unverified state, │
│                                │ missing edge-case verification │
└────────────────────────────────┴────────────────────────────────┘
```

---

## Anti-Patterns Cheat Sheet

- **Strawman Objections**: Formulating trivial, easily dismissed objections instead of severe failure modes.
- **Phantom Grounding**: Citing conceptual patterns without linking to active code lines.
- **Unmitigated Invariants**: Proceeding with a plan when one or more objections remain unresolved.
- **Rubber-Stamping**: Generating the questio block as commentary rather than a blocking gate.

---

## Invariants & Guardrails

- [ ] **No Unanchored Claims**: Every Sed Contra point must link to exact workspace files (`file:///path/to/file.py#L1-L20`).
- [ ] **Blocking Gate**: Never execute modifying tools if any of the three objections is unmitigated.
- [ ] **Visual Brief Delivery**: Always emit the `%TEMP%` HTML report with Mermaid before modifying production state.
- [ ] **Explicit Checkpoint**: Always pause with `RequestFeedback: true` on `implementation_plan.md`.
