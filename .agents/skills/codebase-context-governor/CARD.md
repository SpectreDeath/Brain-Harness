```ascii
┌──────────────────────────────────────────────────────────────────────┐
│ SKILL: codebase-context-governor                                     │
│ SKILL: codebase-context-governor                                      │
│ Category: software_engineering / meta-skills                         │
│ Version: 1.0.0                                                       │
│ Invocation: /codebase-context-governor                               │
│ Triggers: "codebase context governor", "context governance",         │
│           "audit instruction files", "sync context", "govern context"│
│ Requires: "codebase-context-architect",                              │
│           "agent-instruction-architect", "agent-skills-architect",   │
│           "compute-model-assessor"                                   │
│ Target: Multi-layer context file governance, sync & CI linting       │
└──────────────────────────────────────────────────────────────────────┘
```

# Codebase Context Governor — Companion Summary Card

## Stage Progression Table

| Stage | Core Responsibility | Primary Artifact | Completion Gate |
|---|---|---|---|
| **Stage 1: Smell Audit** | Scan instruction files for bloat & lint leaks | Smell Audit Report | Bloat, leakage & contradictions identified |
| **Stage 2: Three-Layer Partitioning** | Classify context into Constitution, SSOT, Task | Partition Map | Strict altitude separation achieved |
| **Stage 3: SSOT Synchronization** | Generate derived files from primary source | Synchronized Files | Zero drift between AGENTS.md & clients |
| **Stage 4: CI Linter Enforcement** | Run linter on size, formatting & links | CI Linter Results | 100% linter rules pass with zero criticals |
| **Stage 5: Compute Calibration** | Score 5D complexity & route reasoning tier | Compute Budget Plan | Reasoning tier & timeout calibrated |

---

## Vocabulary & Levers

- **Three-Layer Context Architecture**: Strict separation between Constitution (Layer 1), SSOT Execution (Layer 2), and Ephemeral Task (Layer 3).
- **Context Rot**: Degradation of agent performance caused by stale rules, lint leakage, or contradictory instructions.
- **Instruction Altitude**: Writing instructions at the right level of abstraction (negative boundaries and execution seams, not tutorials).
- **Single Source of Truth (SSOT)**: Deriving agent configs from active code manifests to eliminate synchronization drift.
- **5D Compute Assessment**: Calibrating model thinking budgets based on Span, Depth, Concurrency, Rigor, and Heterogeneity (Rule 25).
- **Slotted/Frozen Domain Entities**: Ensuring transformed data models use `slots=True, frozen=True` (Rule 12).

---

## Mandatory Invariants Checklist

- [ ] **Instruction File Budget Guard**: Instruction files (`AGENTS.md`) must not exceed 150 lines (Rule 11).
- [ ] **Zero Lint Leakage**: Never commit transient compiler/linter error dumps into instruction files.
- [ ] **Explicit Negative Boundaries**: Every instruction file must define clear "what NOT to touch" boundaries.
- [ ] **SSOT Single-Source Sync**: Always generate derived client rules from active manifests without manual copy-paste.
- [ ] **5D Compute Complexity Gate**: Automatically scale reasoning tier to High when 5D score $\ge 0.75$ (Rule 25).
