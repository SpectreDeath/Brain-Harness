# Quick-Reference Summary Card: icm-workspace-architect

```
┌────────────────────────────────────────────────────────────────────────┐
│ SKILL: icm-workspace-architect                                         │
├────────────────────────────────────────────────────────────────────────┤
│ Method:     Interpretable Context Methodology (arXiv:2603.16021)       │
│ Role:       Folder Structure as Agent Architecture                     │
│ Primitives: Sequence (Numbered Stages), Shelf (Uniform Records),       │
│             Catalog (Small Routing Pointers)                           │
│ Forms:      Pipeline, Record Library, Knowledge Bundle, Context Map,   │
│             System Map                                                 │
│ Budget:     Max Step Tokens < 8,000 | Entry AGENTS.md < 60 lines       │
└────────────────────────────────────────────────────────────────────────┘
```

## The 5-Layer Context Hierarchy

| Layer | File / Location | Question Answered | Role | Token Budget |
|---|---|---|---|---|
| **L0** | `AGENTS.md` | Where am I? | Identity & Routing | < 60 lines (~500 tokens) |
| **L1** | root `CONTEXT.md` | Where do I go? | Pipeline / Schema Map | 200–500 tokens |
| **L2** | stage `CONTEXT.md` | What do I do? | The Control Point | 200–500 tokens |
| **L3** | `_shared/`, `references/` | What rules apply? | Factory (Stable Reference) | 500–2,000 tokens |
| **L4** | `stages/*/output/` | What am I making? | Product (Per-Run Working) | Bounded |

## Operational Progression

| Stage | Focus | Primary Artifact | Completion Gate |
|---|---|---|---|
| **1. Scope & Form** | Build vs Restructure | Target Architecture | Form selected from 3 primitives |
| **2. Contracts** | L0–L4 Context Scaffold | `AGENTS.md`, `CONTEXT.md` | Inputs, Process, Outputs, Check declared |
| **3. Verification** | Tooling Deployment | `_tools/` / CLI commands | Zero broken links or unverified quotes |
| **4. Cold Walk** | 8-Point Cold Agent Test | Walk Test Scorecard | All 8 points passing |
| **5. Finalize** | Compliance Audit | Audit Report | `harness icm audit` passes clean |

## Mandatory Invariants Checklist

- [ ] `AGENTS.md` exists at workspace root, routes to stages/shelves, and remains strictly under 60 lines.
- [ ] Numbered folders (`01_`, `02_`) encode execution sequence wherever order matters.
- [ ] Every working stage carries a `CONTEXT.md` specifying Inputs, Process, Outputs, and Check.
- [ ] Factory references (`_shared/`, schemas) live apart from working outputs (`output/`, records).
- [ ] Every stage handoff terminates at an explicit check emitting `check.md` (`pass` or `fail: <why>`).
- [ ] Full step context (contract + references + inputs) remains strictly under 8,000 tokens.
- [ ] All relative links, contract inputs, and `@import` pointer files resolve cleanly without breakage.
- [ ] System status is readable directly from disk files and generated `_index.md` files.
- [ ] New records or stages are instantiated by copying templates from `_templates/`.
