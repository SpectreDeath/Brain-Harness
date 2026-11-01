```ascii
┌──────────────────────────────────────────────────────────────────────┐
│ SKILL: token-economizer                                              │
│ Category: memory_and_epistemics / token_governance                   │
│ Version: 1.0.0                                                       │
│ Invocation: /token-economizer                                        │
│ Triggers: "token economizer", "token cost control", "micro-skills",  │
│           "tool pruning", "loop guard", "context waste reduction"    │
│ Requires: "headroom-context-optimizer", "prompt-pruning-architect"   │
│ Target: Experience-driven cost reduction across agent sessions       │
└──────────────────────────────────────────────────────────────────────┘
```

# TokenEconomizer — Companion Summary Card

## Stage Progression Table

| Stage | Core Responsibility | Primary Mechanism | Completion Gate |
|---|---|---|---|
| **Stage 1: Micro-Skills** | Extract & promote persistent repo facts | $K=3$ drifted confirms, $\lambda=5.0$ eviction | Fact promoted to ACTIVE & clears firing gate ($\ge 40\%$) |
| **Stage 2: Tool Pruning** | Prune loaded tools unused across tasks | $p=10$ prompts, $m=2$ sessions, $s=5$ sessions | Pruning set generated with protected primitives preserved |
| **Stage 3: Loop Guard** | Intervene during repetitive turn spirals | Tier-0 gate, heuristic conjunction, $2.5\times$ backstop | Mirroring nudge delivered or hard backstop executed |
| **Stage 4: Trace Federation** | Standardize multi-harness trajectories | Unified `DomainAdapter` & `load_trajectory` | Session parsed into normalized `TrajectoryTrace` |
| **Stage 5: Pricing Ledger** | Track token savings & optimization cost | Unified per-task and per-turn pricing ledger | Cumulative savings and ROI calculated |

---

## Vocabulary & Levers

- **The Micro-Skills Lifecycle**: 3-state state machine (`CANDIDATE` -> `ACTIVE` -> `RETIRED`) with drift-aware confirmations ($K=3$), exponential decay ($\gamma=0.8$), asymmetric contradiction eviction ($\lambda=5.0$), and a firing gate ($\ge 40\%$).
- **Protected Work-Surface**: Essential tool primitives (`read_file`, `edit_file`, `run_command`, `write_file`) permanently excluded from pruning regardless of inactivity.
- **Evidence-Based Pruning**: Elimination of unused tool JSONSchemas after $p=10$ prompts across $\ge 2$ sessions or $5$ total sessions.
- **TurnGuard Conjunction Cascade**: Conjunction of edit churn ($\ge 4$), file scatter ($\ge 3$), sustained errors ($\ge 6$), and repeat stagnation ($\ge 20\%$) over the task envelope ($1.25\times$).
- **Hard Backstop Invariant ($2.5\times$)**: Maximum turn limit beyond which a stuck trajectory aborts regardless of judge veto.
- **Non-Destructive Mirroring Nudge**: First loop intervention that redirects the agent by reflecting its own recent tool actions without injecting subjective bias.

---

## Mandatory Invariants Checklist

- [ ] **Protected Work-Surface Invariant**: Core file and execution tools (`read_file`, `edit_file`, `run_command`, `write_file`) must never be pruned.
- [ ] **Asymmetric Contradiction Invariant**: Contradictions must be penalized at $\lambda = 5.0$ times confirmation weight to prevent stale instruction leakage.
- [ ] **Drift Confirmation Invariant**: Code-level micro-skill facts must require confirmations across distinct edited files before promotion to ACTIVE.
- [ ] **Hard Backstop Invariant ($2.5\times$)**: Turns exceeding $2.5\times$ the resolved-task envelope must abort regardless of judge verdict.
- [ ] **Slotted & Frozen Dataclasses**: All domain models must enforce `slots=True, frozen=True` with explicit `__post_init__` assertions (Rule 12).
- [ ] **Unified Ledger Accounting**: All optimization mechanisms must record token overhead against the shared pricing ledger to prevent metric drift.

