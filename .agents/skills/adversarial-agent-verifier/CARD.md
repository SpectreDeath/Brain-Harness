# CARD: adversarial-agent-verifier

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ SKILL: adversarial-agent-verifier                                           │
│ CATEGORY: Verification & Quality Assurance                                  │
│ INVOCATION: /adversarial-agent-verifier                                     │
│ TRIGGERS: "adversarial review", "dag seam testing", "inspect before edit", │
│           "test as contract", "clean-up commit", "stress test ai code"      │
│ TARGET: Rigorous Seam Testing, Adversarial Audits, and Contract Verification│
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 5-Stage Progression Matrix

| Stage | Focus Area | Primary Artifact / Mechanism | Passing Completion Gate |
| :--- | :--- | :--- | :--- |
| **1. Inspect-Before-Edit** | Architecture & Seam Locality | Non-modifying Inspection Summary | Root cause located; smallest safe diff bounded before edit. |
| **2. DAG Seam Analysis** | Boundary Failure Modeling | DAG Seam Opportunity Table | Component seams mapped; high-risk failure modes identified. |
| **3. Test Contract** | Reproducible Red-State Tests | Failing test suite execution | Tests written first; failure mode verified and contract locked. |
| **4. Minimal-Diff Edit** | Bounded Implementation | Green test suite run (`pytest`) | Minimal fix implemented; 100% of test suite passing green. |
| **5. Adversarial Review** | Harsh Quality Audit & Cleanup | 1–10 Grading Scale + Clean Diff | Polite fluff eliminated; edge cases audited; debris purged. |

---

## The Three Core Pillars

```
┌─────────────────────────────────────────────────────────────┐
│ 1. INSPECT BEFORE EDIT (ZERO BLIND EDITS)                   │
│ - Never modify files before locating the architectural seam.│
│ - Formulate smallest safe change before touching source code│
├─────────────────────────────────────────────────────────────┤
│ 2. DAG SEAM TESTING (MICHAEL FEATHERS SEAMS)                │
│ - Model component workflows as directed acyclic graphs.     │
│ - Focus tests on boundaries where 40% of AI bugs occur.     │
├─────────────────────────────────────────────────────────────┤
│ 3. UNCOMPROMISING ADVERSARIAL REVIEWS                       │
│ - Reject polite generic compliments.                        │
│ - Demand 1-10 severity grading and actionable git diffs.    │
└─────────────────────────────────────────────────────────────┘
```

---

## Anti-Pattern Invariants Checklist

- [ ] **No Blind Editing**: Agent must inspect and summarize relevant files before modifying code.
- [ ] **Tests As Contract**: Failing tests written first; never mutate tests to force a pass.
- [ ] **No Polite Rubber-Stamping**: Code review scored on harsh 1-10 scale with concrete failure points.
- [ ] **Seam Vulnerability Checked**: Serialization, database transactions, and error boundaries audited.
- [ ] **Clean-Up Commit Verified**: Zero `TODO`, `FIXME`, or debug print statements left in final diff.
