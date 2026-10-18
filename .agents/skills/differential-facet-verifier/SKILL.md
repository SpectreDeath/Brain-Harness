---
name: differential-facet-verifier
description: Audit, compare, and verify multi-provider evidence dossiers using explicit facet availability semantics, absence claimability gates, and 3-valued differential outcomes. Do not use for generic line text diffing or single-provider analysis without differential evidence.
---

# Differential Facet Verifier & Availability Semantics

The **differential-facet-verifier** skill enforces rigorous epistemic comparison across multi-provider reverse-engineering and security evidence dossiers. Rather than assuming that an unobserved dimension represents zero occurrences, this skill mandates explicit facet availability maps, enforces formal absence claimability gates, decouples raw provider syntax variations from canonical semantics, and synthesizes 3-valued differential reports (`unchanged`, `changed`, `unknown`).

---

## 1. Trigger Bounds & Deflection

### Activation Triggers
- Comparing output across multiple reverse-engineering tools (e.g. Ghidra vs IDA vs Binary Ninja vs Rizin).
- Auditing decompiler and disassembler observations for unobserved vs empty facets.
- Evaluating absence claims for symbols, vulnerabilities, or backdoor procedures.
- Verifying differential reports for strict unknown propagation.

### Negative Deflection (When NOT to Use)
- **Do not use for generic line text diffing** — Use standard Git diff or difflib.
- **Do not use for single-provider analysis without differential evidence** — Use `reconstruction-obligation-ledger` instead.
- **Do not use for fuzzy heuristic text matching** lacking explicit provider coverage declarations.

---

## 2. Operational Progression (The Shu Stages)

| Stage | Name | Key Activity | Completion Gate |
|---|---|---|---|
| **1** | **Declare & Ingest** | Ingest observation dossiers; parse `facet_availability` and `coverage`. | Every facet carries boolean `available`; `available: false` has non-empty reason. |
| **2** | **Validate Absence** | Evaluate formal absence claimability rule against coverage state. | Claims rejected unless `status == 'complete'` and clean traversal. |
| **3** | **Project Dimensions** | Project comparable structural facets into canonical sorted representations. | Syntax variations recorded in `limitations`; representations normalized. |
| **4** | **Evaluate Outcomes** | Map dimensions to 3-valued statuses (`unchanged`, `changed`, `unknown`). | Zero unresolved facets assigned non-`null` comparison counts. |
| **5** | **Synthesize & Seal** | Aggregate overall status and compute canonical SHA-256 summary digest. | `DifferentialReport` emitted with reproducible `rep:<sha256>` digest. |

---

## 3. Diagnostic Coaching Scorecards

| Dimension | Pass Condition | Fail Symptom | Repair Action |
|---|---|---|---|
| **Facet Conflation Guard** | Empty facet has explicit `{ available: true }` | Missing/empty facet treated as 0 occurrences | Force `status: unknown`, set counts to `null`, append explanation to `limitations` |
| **Absence Claimability Guard** | `absence_claimable == True` before claiming absence | Absence asserted when `truncated == True` or `status != 'complete'` | Reject assertion; return `unresolved` with limitation reason |
| **Mandatory Reason Invariant** | Non-empty string for every `available: false` | `reason: null` or whitespace on unavailable facet | Hard-block via `__post_init__`; raise `ValueError` at construction time |
| **Format Decoupling Guard** | Raw syntax deltas isolated from structural semantics | Provider disassembly syntax differences flagged as functional change | Record `providersDiffer` limitation notice; equate only normalized canonical projections |
| **Digest Determinism Guard** | Identical inputs produce identical `rep:<sha256>` | Non-canonical JSON drift across runs | Enforce `canonicalize_json` for all digest inputs |

---

## 4. CLI Execution Seam

Execute via the unified `harness` CLI:

```bash
# Compare two multi-provider observation dossiers
harness facet compare left_ghidra.json right_rizin.json --provider-differ --format rich

# Validate formal absence claimability
harness facet claim-absence coverage_dossier.json

# Audit differential report integrity
harness facet verify differential_report.json --strict

# Export machine-parseable JSON certificate
harness facet export differential_report.json
```

Or execute via the co-located runner script:

```bash
python scripts/facet_engine.py compare left.json right.json
```

---

## Anti-Patterns

- **Facet Conflation** — Treating an unobserved or undeclared facet as an empty collection (`[]`), producing false zero-deltas in dimension comparison.
- **Undeclared Absence Fallacy** — Asserting that an entity is absent when the provider's traversal coverage was truncated, partial, or `unknown`.
- **Provider Text False Contradiction** — Equating raw provider formatting (e.g. differing disassembly syntaxes) and asserting functional disparity rather than projecting structural semantics.
- **Limitation Erasure** — Silently dropping failure and limitation reasons when propagating unresolved dimension outcomes to the summary report.
- **Premature `unchanged` Verdict** — Concluding `unchanged` on the overall report when any dimension carries `unknown` status — overall verdict must be the strictest across all dimension outcomes.

---

## 5. References & Documentation

- [Differential Facet JSON Wire Schema](references/facet-schema.md)
- [Formal Absence Claimability Rules](references/absence-rules.md)
- Companion Card: [CARD.md](CARD.md)
