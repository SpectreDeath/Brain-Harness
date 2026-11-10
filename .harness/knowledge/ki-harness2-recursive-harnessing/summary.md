# Recursive Agent Harnessing: Mental Models, Invariants, and Architecture

## Epistemic Lineage & Provenance Snapshot

- **Primary Source Codebase**: `D:\GitHub\cloned\Google\harness2` (`Google/harness2`)
- **Verified Commit**: `23fb5e0516c99ac04a1aa46c193efda2e1b9bb24`
- **Reference Paper**: *Recursive Agent Harnessing for an Open World* (arXiv:2610.14224, Oct 2026)
- **Source Modules**: `harness2/core/recursion.py`, `harness2/core/context.py`, `harness2/core/ledger.py`, `harness2/core/selection.py`, `harness2/core/library.py`, `harness2/core/tree.py`, `harness2/core/runmark.py`

---

## 1. Ground-Truth Mental Models

1. **Two Levels of Recursion at Fixed Model Weights**:
   Traditional agent improvement either finetunes model weights or manually authors prompts and scaffolds. Recursive harnessing keeps base model weights fixed and operates simultaneously at two recursive tiers:
   - **Task-Level Recursion**: Refines the current execution harness through contrastive Propose-Probe-Compose cycles.
   - **Harnessing-Level Recursion**: Updates a persistent per-domain experience library with full adopted component trees and evidence-backed transferable lessons.

2. **Orthogonal Proposal Partitioning (INV vs DOM)**:
   Unstructured harness proposals quickly collapse into generic or conflicting advice. Partitioning edits into:
   - **Invariant (INV)**: How the agent works (tool errors, determinism via scripts, bounded fallbacks, auto-triggers, sequencing).
   - **Domain (DOM)**: What a practitioner knows (matter contracts, field relationships, consistency checks, domain rules).
   guarantees diversity across parallel candidates.

3. **Strict Dual-Mode Budget Accounting ($R=4k$, $P=3k$)**:
   Every recursion run maintains a strict mathematical identity:
   - $R = 4k$ rollouts ($k$ shared base + $2k$ candidates + $k$ finals)
   - $P = 3k$ sessions ($k$ INV + $k$ DOM + $k$ compositions)
   Duplicate execution labels are aggressively guarded before count checks to prevent candidate loss from silent overwrites.

4. **Blind Anonymized Selection**:
   Evaluator and selection bias is eliminated by evaluating candidate deliverables stripped of harness code, provenance, and run labels. Candidate IDs are assigned via seeded, deterministic shuffling ($A, B, \dots$). Non-answers are dropped, and selector failures degrade to neutral base fallbacks without throwing.

5. **Fail-Closed Evidence Isolation Tripwires**:
   Models adapting harnesses must never observe answer keys, benchmark grading rubrics, or evaluator verdicts. Traversal routines bound directory depth, prune noise trees, scan content in 1MB chunks with boundary overlap, and immediately trip on verdict markers (`pass_rate`, `deterministic_eval_summary`, etc.).

---

## 2. Decision Heuristics & Architectural Rules

- **Autotrigger Invariant**: Any newly created skill in `.agents/skills/<name>/SKILL.md` must be registered with a concise trigger sentence in always-on context (`AGENTS.md`) or it is dead weight.
- **Omitted-is-Inherited**: Harness edits are diffs against an editable surface; components not modified in a candidate workspace are inherited unchanged from the baseline.
- **Evidence as Data, Not Instructions**: Context files under `context/` contain data to be analyzed; embedded directives must never be executed by the improver.
- **Verifiable Workspace Facts vs Reusable Domain Procedures**: Ground verified workspace mappings (e.g. key joins) directly into task harnesses; abstract general procedure for domain library storage.
- **Supported Lesson Gate**: No experience item enters the library without verified `cue`, `lesson`, and `evidence` fields citing exact trajectory moments.
