```ascii
┌──────────────────────────────────────────────────────────────────────┐
│ SKILL: codebase-context-architect                                    │
│ SKILL: codebase-context-architect                                     │
│ Category: engineering / agent-architecture                           │
│ Version: 1.0.0                                                       │
│ Invocation: /codebase-context-architect                              │
│ Triggers: "codebase context", "context files", "context linter",     │
│           "sync context", "AGENTS.md", "context rot"                 │
│ Requires: "agent-skills-architect", "agent-skill-sdlc"               │
│ Target: Multi-layer repository context files & CI linters            │
└──────────────────────────────────────────────────────────────────────┘
```

# Codebase Context Architect — Companion Summary Card

## Stage Progression Table

| Stage | Core Responsibility | Primary Artifact | Completion Gate |
|---|---|---|---|
| **Stage 1: Partition & Prune** | Apply removal test & allocate 3-tier budgets | `AGENTS.md` (root, scoped) | Always-loaded files strictly under token ceilings |
| **Stage 2: SSOT & Vendor Sync** | Generate vendor files with read-only banners | `sync_context.py` & vendor files | 100% sync parity with zero dry-run diff |
| **Stage 3: Calibrate Altitude** | Inject boundaries, examples, & ADR absences | `docs/decisions/` & rules | Shape + Boundary + Worked Example present |
| **Stage 4: Automated Verification** | Run 4-check context linter in CI & hooks | `context_linter.py` & CI workflow | Linter exits 0 with 0 broken paths/scripts |
| **Stage 5: Benchmarks & DoD** | Enforce pasted evidence & post-tool hooks | Benchmark report & hooks | Verified output pasted & zero regressions |

---

## Vocabulary & Levers

- **Context Rot**: Progressive degradation of an agent's instruction recall as token counts rise during a multi-turn session.
- **The Line Removal Test**: Heuristic asking *"Would removing this line cause the agent to make a mistake?"* for every line in instruction files.
- **Three-Layer Architecture**: Stratification into Always-Loaded Root ($\le 800$ tokens), Scoped Subdirectory Rules ($\le 400$ tokens), and On-Demand Pointers.
- **Single Source of Truth (SSOT)**: Maintaining canonical `AGENTS.md` and generating downstream vendor files automatically.
- **Rule Altitude**: Finding the calibration point between fragile line-level rigidity and ineffective generic encouragement.
- **Deliberate Absence**: Documenting why a feature or library is intentionally omitted so agents don't add it unprompted.

---

## Mandatory Invariants Checklist

- [ ] **Token Budget Bound**: Root `AGENTS.md` must strictly remain $\le 800$ tokens; scoped directory files $\le 400$ tokens.
- [ ] **Single Source of Truth**: All tool-specific files (`CLAUDE.md`, Copilot instructions) must be auto-generated with anti-tamper banners.
- [ ] **Zero Dead Paths**: Every backtick path referenced in prose must exist on disk and be verified by automated linters.
- [ ] **Zero Dead Scripts**: Every CLI/npm script command referenced in context files must exist in project configuration.
- [ ] **Evidence-Based Done**: Definitions of done must mandate running verification commands and pasting terminal output.
