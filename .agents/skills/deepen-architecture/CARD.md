# 🧠 Skill Summary Card: `deepen-architecture`

```
┌────────────────────────────────────────────────────────┐
│               SKILL SUMMARY CARD                       │
├────────────────────────────────────────────────────────┤
│ Name:        deepen-architecture                       │
│ Category:    engineering / architecture                │
│ Invocation:  /deepen-architecture                      │
│ Trigger:     "deepen the architecture", "run the loop" │
│ Version:     1.0.0                                     │
├────────────────────────────────────────────────────────┤
│ Target:      Transform shallow, leaky modules into     │
│              deep abstractions with pure seams.        │
└────────────────────────────────────────────────────────┘
```

---

## 🔄 The 6-Stage Loop at a Glance

| Stage | Objective | Primary Artifact / Output | Completion Gate |
|---|---|---|---|
| **1. Analyze** | Audit codebase for shallow modules & leaky abstractions | File/line friction list | 2–4 concrete friction sites identified |
| **2. Assess** | Score candidates across Locality, Leverage & Testability | Strength classification | `Strong`, `Worth exploring`, or `Speculative` |
| **3. Recommend** | Generate visual brief with interactive Mermaid diagrams | `%TEMP%\architecture-review-*.html` | Temp HTML report written & path surfaced |
| **4. Plan** | Formulate detailed component modification diffs | `implementation_plan.md` | User review & explicit approval |
| **5. Execute & Verify**| Refactor seams and run full automated test suite | `pytest -v` | **100% pass rate** (zero regressions) |
| **6. Record** | Document architectural changes & test verification | `walkthrough.md` | Walkthrough artifact updated & delivered |

---

## 🧰 Vocabulary & Levers Cheat Sheet

- **Deep Module**: Small interface that hides large implementation complexity (high leverage).
- **Shallow Module**: Thin wrapper that adds cognitive overhead without hiding complexity.
- **Seam**: The clean public boundary where components interact and tests attach.
- **Locality**: Co-locating state and its mutation invariants in one authoritative place.
- **Leverage**: The ratio of hidden functionality to interface surface area.
- **Visual Brief**: Decision-ready temporary HTML report rendering before/after architecture topologies.

---

## 🚫 Guardrails & Invariants

- [ ] **Backward Compatibility**: Always preserve public contract backward compatibility unless deprecation was explicitly planned.
- [ ] **Mandatory Plan Approval**: Never execute code modifications without an approved `implementation_plan.md`.
- [ ] **Zero-Regression Verification**: Always verify 100% test pass rate before completing the cycle.

