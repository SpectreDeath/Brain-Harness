```ascii
┌────────────────────────────────────────────────────────────────────────┐
│ SKILL: recursive-harness-refiner                                       │
│ Category: agent-orchestration                                          │
│ Version: 1.0.0                                                         │
│ Invocation: /refine                                                    │
│ Triggers: "recursive harnessing", "propose probe compose",             │
│           "refine harness", "task level recursion", "improve harness", │
│           "blind selection", "experience library"                      │
│ Requires: "agent-harness-architect", "epistemic-isnad-audit",          │
│           "adversarial-agent-verifier"                                 │
│ Target: Contrastive Propose-Probe-Compose task-level recursion         │
└────────────────────────────────────────────────────────────────────────┘
```

# Recursive Harness Refiner — Companion Summary Card

## Stage Progression Table

| Stage | Objective | Primary Artifact | Completion Gate |
|---|---|---|---|
| **Stage 1: Isolate & Budget** | Establish fail-closed evidence sandbox & verify $R=4k$, $P=3k$ budget | Isolated evidence tree (`context/`) & BudgetLedger | Zero verdict/leak markers detected; strict ledger identity confirmed |
| **Stage 2: Propose (INV & DOM)** | Generate orthogonal invariant and domain harness proposals | Candidate trees (`inv1..k`, `dom1..k`) | Single-pass validation passed; skills auto-triggered in always-on text |
| **Stage 3: Probe** | Execute rollouts across candidate harnesses | Full trajectories & deliverables (`rollouts/`, `deliverables/`) | Atomic `.refine_complete` markers written with matching configuration fingerprints |
| **Stage 4: Compose** | Synthesize refined harness from behavioral contrasts | Final harness (`agg1..k` or `c1..k`) | Diversity Jaccard verified; decisions cite exact trajectory divergence moments |
| **Stage 5: Select & Retain** | Blindly evaluate anonymous deliverables and distill experience | Selection record (`selection.json`) & Experience item | Chosen deliverable verified; supported lesson (`cue`, `lesson`, `evidence`) added to library |

---

## Vocabulary & Levers

- **Editable Surface (`SurfaceSpec`)**: The strict component boundary (always-on files, skills, scripts, subagents) open to model adaptation.
- **Propose-Probe-Compose**: The contrastive adaptation triad: propose orthogonal edits, probe on the identical task, compose from behavioral contrast.
- **Orthogonal Levers (INV vs DOM)**: Invariant levers (tool handling, deterministic scripts, auto-triggers) separated from Domain levers (matter contracts, field relationships).
- **Budget Identity ($R=4k$, $P=3k$)**: Mathematical accounting constraint governing rollout and session allocations across parallel (`agg`) and sequential (`seq`) modes.
- **Blind Selection**: Anonymized artifact-only evaluation under seeded shuffled IDs ($A, B, \dots$) with non-answer dropping and neutral fallback.
- **Per-Domain Experience Library**: Persistent store of full adopted component trees indexed with verifiable, transferable lessons.

---

## Mandatory Invariants Checklist

- [ ] **Fail-Closed Evidence Isolation Gate**: Pre-execution scans must verify zero answer keys, grader rubrics, or verdict markers in model context.
- [ ] **Budget Accounting Invariant**: Every recursion sweep must satisfy $R = 4k$ rollouts and $P = 3k$ sessions with zero duplicate labels.
- [ ] **Autotrigger Invariant**: All candidate skills must have explicit trigger lines in always-on context; untriggered skills are rejected or auto-repaired.
- [ ] **Single-Pass Validation Gate**: Harness validation must evaluate all path, syntax, script reference, and cap constraints in a single pass.
- [ ] **Deterministic Trial Identity**: Completed runs must be sealed with atomic `.refine_complete` markers containing input and harness digests.
- [ ] **Blind Selection Gate**: Candidate selection must evaluate deliverables only with harness files and run labels completely hidden.
- [ ] **Supported Experience Gate**: Adopted harnesses may only enter the per-domain experience library if accompanied by verified `cue`, `lesson`, and `evidence` fields.
