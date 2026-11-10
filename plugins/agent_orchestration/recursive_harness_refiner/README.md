# Recursive Harness Refiner Plugin

The `plugin.recursive_harness_refiner` plugin implements two levels of recursive agent harnessing without modifying underlying LLM weights, synthesized from Google Harness² (`google/harness2`, arXiv 2610.14224).

## Architecture & Responsibilities

1. **Task-Level Recursion (Propose-Probe-Compose)**:
   - Proposes orthogonal edits along two distinct dimensions: **INV** (procedural tool/completion invariants) and **DOM** (expert practitioner domain knowledge).
   - Probes proposed candidate harnesses by rolling them out on the task.
   - Composes final harnesses from behavioral contrasts across rollouts (`agg` parallel mode across $2k$ candidates; `seq` sequential mode over $k$ rounds).
2. **Budget Accounting**:
   - Enforces the strict $R = 4k$ rollouts and $P = 3k$ sessions budget identity.
   - Verifies duplicate label prevention before count evaluations.
3. **Blind Anonymized Selection**:
   - Compares delivered artifacts with harnesses and run labels stripped.
   - Assigns seeded, stable anonymous IDs ($A, B, \dots$) and handles non-answer dropping and neutral fallback.
4. **Harnessing-Level Recursion (Per-Domain Experience Library)**:
   - Stores complete adopted component trees alongside timestamped, evidence-backed lessons (`cue`, `lesson`, `evidence`, `confidence`).
   - Automatically rebuilds domain `INDEX.md` catalogs.

## Seams

- **Service Key**: `RECURSIVE_REFINER_SERVICE_KEY` (`service.recursive_refiner`)
- **Dependencies**: Requires `service.evidence_isolation`
- **Protocol**: `RecursiveRefinerService`
- **Resolver**: `resolve_recursive_refiner(context)`
