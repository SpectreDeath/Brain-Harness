# CARD: agent-instruction-architect

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ SKILL: agent-instruction-architect                                         │
│ CATEGORY: Agent Configuration & Context Optimization                        │
│ INVOCATION: /agent-instruction-architect                                    │
│ TRIGGERS: "agents.md best practices", "audit agents.md", "claude.md config",│
│           "agent instruction bloat", "dependency guardrails", "smell audit" │
│ TARGET: High-Density, Constraint-First Repository Instruction Design        │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 5-Stage Progression Matrix

| Stage | Focus Area | Primary Output / Mechanism | Passing Completion Gate |
| :--- | :--- | :--- | :--- |
| **1. Smell Audit** | Configuration Smells Purge | Lint leakage & bloat removal | Raw linter rules, generic tutorials, and contradictions purged. |
| **2. Seam Specification**| Developer Tooling Commands | Install, Build, Test, Lint commands | Exact, non-interactive shell commands specified for all seams. |
| **3. Negative Boundaries**| Scope & Permission Controls| "What NOT to touch" + Dependency policy | Critical boundaries locked; third-party package adds gatekept. |
| **4. Exemplar Binding** | Concrete Code References | Exemplar file paths and patterns | Abstract adjectives replaced with concrete file path references. |
| **5. Post-Mortem Loop** | Iterative Rule Hardening | Post-incident instruction diff | Instruction file updated post-mistake to prevent regression. |

---

## The Three Core Pillars

```
┌─────────────────────────────────────────────────────────────┐
│ 1. LEAN TOKEN BUDGET (UNDER 150 LINES)                      │
│ - Every token in AGENTS.md competes with task reasoning.    │
│ - Purge all generic programming knowledge the model knows.  │
├─────────────────────────────────────────────────────────────┤
│ 2. CONSTRAINT-FIRST NEGATIVE BOUNDARIES                     │
│ - Clearly demarcate generated code and legacy zones.        │
│ - Enforce dependency approval policies and safe diffs.      │
├─────────────────────────────────────────────────────────────┤
│ 3. POST-MORTEM INSTRUCTION HARDENING                        │
│ - When agent makes a mistake, don't just patch the code.    │
│ - Patch the instruction that permitted the mistake.         │
└─────────────────────────────────────────────────────────────┘
```

---

## Anti-Pattern Invariants Checklist

- [ ] **Token Budget Bound**: `AGENTS.md` is strictly under 300 lines (target: 80–150 lines).
- [ ] **No Generic Tutorials**: Zero explanations of standard Python/JS/framework concepts.
- [ ] **Verified Execution Commands**: Install, test, build, and lint commands tested and verified.
- [ ] **Protected Zones Declared**: Explicit "Do Not Touch" list for generated or legacy files.
- [ ] **Dependency Gate Enabled**: Explicit policy requiring approval before adding dependencies.
