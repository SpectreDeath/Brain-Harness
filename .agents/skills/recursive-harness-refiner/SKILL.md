---
name: recursive-harness-refiner
description: Refine autonomous agent harnesses through contrastive Propose-Probe-Compose task-level recursion, blind anonymized selection, and per-domain experience library retention. Do not use for model weight training, superficial prompt tweaking, or single-turn chat scripts.
---

# Recursive Harness Refiner: Task-Level & Harnessing-Level Adaptation

`recursive-harness-refiner` executes recursive agent harnessing without altering underlying model weights, synthesized from Google Harness² (`google-research/harness2`, arXiv:2610.14224).

It connects two levels of recursion:
1. **Task-Level Recursion**: Proposes orthogonal harness edits along Invariant (**INV**) and Domain (**DOM**) dimensions, probes them on identical task executions, and composes refined harnesses from behavioral contrasts across trajectories.
2. **Harnessing-Level Recursion**: Retains adopted harnesses and evidence-supported lessons (`cue`, `lesson`, `evidence`, `confidence`) in a persistent per-domain experience library.

See [CARD.md](CARD.md) for the companion summary card, stage progression table, and mandatory invariants checklist.
Consult [references/recursion-modes.md](references/recursion-modes.md) for detailed scheduling topologies.

---

## The Visual Brief

When auditing or reviewing recursive refinement sweeps across benchmark suites, agents must generate a self-contained HTML visual brief in `%TEMP%` displaying:
1. **Recursion Topology Graph**: Parallel width ($2k \rightarrow k$) or sequential depth ($C_1 \dots C_k$) DAG visualizing proposal branches, rollout states, and composition gates.
2. **Budget Accounting Gauge**: Verification of the $R = 4k$ rollout and $P = 3k$ session mathematical identity with duplicate label alerts.
3. **Diversity & Collapse Matrix**: Pairwise line-Jaccard heatmap over candidate harness trees indicating whether proposals maintained distinct operational mechanisms.
4. **Blind Selection Ladder**: Anonymized candidate ranking with conformance drops, artifact fidelity scores, and selection rationales.

---

## Mandatory Checkpoint Gates

- **Evidence Isolation Gate**: Context directories must pass fail-closed answer-key and grader-verdict tripwires before model inspection.
- **Surface Conformance Gate**: Proposed edits must fall strictly within the declared `SurfaceSpec` (paths, caps, frontmatter, compilable scripts).
- **Autotrigger Gate**: Any newly introduced skill must be registered with an action trigger line in always-on context (`AGENTS.md`).
- **Identity Marker Gate**: Every finished rollout must be sealed with an atomic `.refine_complete` marker encoding input and harness digests.
- **Supported Lesson Gate**: No adopted harness may enter the per-domain library without concrete, citation-backed `cue`, `lesson`, and `evidence` fields.

---

## 1. Evidence Isolation & Sandbox Staging

Prepare the task evidence workspace while enforcing strict anti-leak tripwires:

1. Copy the task prompt and source material, omitting declared answer-key glob patterns.
2. Scan the evidence directory in 1MB chunks with boundary overlap for grader verdict markers (`pass_rate`, `deterministic_eval_summary`).
3. Scrub ambient environment variables to prevent accidental credential leakage into untrusted runners.

```sh
harness refine scan runs/task_001/context --leak-glob "answer_key*"
```

> **Completion criterion**: Clean evidence directory verified with zero verdict or answer-key markers.
Primary artifact: Sealed `context/` tree

---

## 2. Orthogonal Proposal Generation (INV & DOM)

Propose candidate harness modifications partitioned across two independent dimensions:

1. **Invariant (INV)**: Focus on workflow mechanics, deterministic script extraction (`scripts/<name>.py`), tool error recovery, bounded retries, and autotrigger lines.
2. **Domain (DOM)**: Focus on practitioner subject matter, output structure contracts, field cross-checks, and domain validation skills.
3. Validate candidate trees in a single pass; if errors occur, feed back validator prose for exactly one bounded retry.

```sh
harness refine validate runs/task_001/harnesses/inv1 --brain
```

> **Completion criterion**: $2k$ candidate harnesses validated, compiling cleanly with autotrigger lines present.
Primary artifact: Candidate trees (`inv1..k`, `dom1..k`)

---

## 3. Probing & Trial Identity Sealing

Execute rollouts under each candidate harness on the identical task:

1. Materialize candidate trees to isolated staging directories.
2. Execute runs using the configured solver substrate.
3. Upon normal process completion, write atomic `.refine_complete` markers containing harness and input SHA-1 fingerprints.
4. Track run metrics in the `BudgetLedger`, verifying no duplicate run labels occur.

```sh
harness refine fingerprint runs/task_001/harnesses/inv1
```

> **Completion criterion**: All rollouts recorded with valid completion markers and non-empty deliverables.
Primary artifact: `RunView` records and `.refine_complete` markers

---

## 4. Contrastive Harness Composition

Synthesize the refined harness from behavioral contrasts observed across trajectories:

1. Compare rollouts against shared baseline executions, identifying where candidate behaviors diverged.
2. In parallel mode (`agg`), compose $k$ independent final harnesses merging successful INV and DOM mechanisms while resolving conflicts.
3. In sequential mode (`seq`), compose checkpoint $C_t$ incorporating lessons from round $t$ and all prior rounds.
4. In decision notes, explicitly cite trajectory moments for every kept, revised, or dropped edit.

> **Completion criterion**: Refined harness synthesized with verified pairwise diversity Jaccard index.
Primary artifact: Composed final tree (`agg1..k` or `c1..k`)

---

## 5. Blind Selection & Experience Retention

Deliver the best artifact and commit verified learnings to the per-domain library:

1. Anonymize candidate deliverables with stable, seeded shuffled IDs ($A, B, \dots$).
2. Drop incomplete deliverables or non-answers before evaluation.
3. Select the best output based strictly on delivery, conformance, fidelity, and consistency without seeing harness code.
4. Distill the outcome: if supported by evidence, record a transferable lesson (`cue`, `lesson`, `evidence`) and store the full adopted tree in the per-domain experience library (`<domain>/harnesses/<task>/`).

```sh
harness refine budget --k 1
```

> **Completion criterion**: Selection committed to `selection.json` and supported lesson indexed in domain `INDEX.md`.
Primary artifact: `Selection` record and `EXPERIENCE.md`

---

## Anti-Patterns

- **Measurement Conflation** — Writing grader criteria, test names, or score targets into harness prompts or skills instead of describing practitioner work.
- **Untriggered Skill Bloat** — Authoring skills without registering trigger lines in always-on context, leaving dead code in the repository.
- **Label Leakage in Selection** — Exposing run IDs, harness code, or provenance metadata to candidate output selectors.
- **Unattributed Folklore Commits** — Writing speculative experience lessons to the library without citing specific trajectory moments.
- **Silent Candidate Overwriting** — Reusing run labels across stages, causing ledger desynchronization and unobserved candidate drops.
- **Shallow Module Proliferation** — Implementing recursion logic as detached one-off scripts rather than slotted domain services and typed IoC plugins.
