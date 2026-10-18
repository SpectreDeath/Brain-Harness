---
name: reconstruction-obligation-ledger
description: Govern, track, and verify reverse-engineered software surfaces into immutable CanonicalEvidence records and cryptographic ReconstructionProof certificates. Do not use for generic code summarization, one-shot static analysis without evidence retention, or documentation generation where no formal obligation closure is required.
---

# Reconstruction Obligation Ledger: Evidence & Obligation Verification

`reconstruction-obligation-ledger` formalizes reverse-engineered software understanding into an immutable, content-addressed evidence ledger and a finite state machine of behavioral obligations across 10 architectural layers.

Synthesized from REA (`morluto/rea`), this skill transforms reverse-engineering assumptions into machine-verifiable `ReconstructionProof` certificates.

See [CARD.md](CARD.md) for the companion summary card, stage progression table, and mandatory invariants checklist.
Consult [evidence-schema.md](references/evidence-schema.md) for evidence data structures and [obligation-states.md](references/obligation-states.md) for the 8-state FSM transition graph.

---

## The Visual Brief

When auditing reconstruction progress across complex binaries or monorepos, agents must generate a self-contained HTML visual brief in `%TEMP%` displaying:
1. **Obligation Disposition Breakdown**: Interactive pie/bar charts showing `verified`, `implemented`, `characterized`, `unowned`, and `contradicted` surface ratios.
2. **Layer Distribution Matrix**: 10-layer coverage heatmap (`cli`, `protocol`, `electron`, `persistence`, `process`, `runtime`, `packaging`, `native-abi`, `application`, `other`).
3. **Evidence Lineage Graph**: Directed graph mapping tool observations (`ev:<sha256>`) to behavioral obligations and reconstructed code owners.

---

## Mandatory Checkpoint Gates

- **Evidence Ingestion Gate**: All tool observations must produce a deterministic `ev:<sha256>` identity and explicit `facet_availability` map before ledger mutation.
- **Surface Ownership Gate**: No obligation can be marked `implemented` without declaring an `owner_path` and `owner_sha256`.
- **Contradiction Quarantine Gate**: Detection of contradictory observations halts progression and quarantines the affected obligation until reviewed.
- **Sealed Closure Gate**: Cryptographic `ReconstructionProof` cannot be claimed while any obligation remains `unowned` or `contradicted`.

---

## 1. Evidence Ingestion & Canonicalization

Ingest raw or normalized observations from reverse-engineering tools (Ghidra, Rizin, Wakaru, Hopper):

1. Format observation into normalized dictionary representation.
2. Declare explicit facet availability map (`available: bool`, `reason: str | None`).
3. Compute deterministic SHA-256 digest using canonical JSON sorting.
4. Record frozen `CanonicalEvidence` in the ledger.

```sh
harness rol ingest <observation.json> --provider ghidra --format elf
```

> **Completion criterion**: Unique `ev:<sha256>` evidence ID generated and reproducible from identical payload.
Primary artifact: `CanonicalEvidence` record

---

## 2. Obligation Surface Registration

Deconstruct target application surfaces into discrete behavioral contracts across 10 architecture layers:

1. Identify exposed endpoints, CLI arguments, IPC channels, persistence schemas, and ABI boundaries.
2. Register an `ObligationItem` for each discrete surface with initial `unowned` disposition.
3. Specify `case_kind` as `positive` (expected behavior) or `negative` (error handling / boundary rejection).

```sh
harness rol obligation add "CLI rejects --timeout with non-numeric value" --layer cli --kind negative
```

> **Completion criterion**: All observed behavioral surfaces registered with `unowned` disposition and unique IDs.
Primary artifact: `ObligationItem` record

---

## 3. Evidence Attachment & Characterization

Ground declared obligations against empirical observations:

1. Link one or more `evidence_ids` (`ev:<sha256>`) to the target obligation.
2. Detect potential contradictions between static analysis and dynamic runtime traces.
3. Transition disposition from `unowned` to `characterized`.

```sh
harness rol obligation transition ob_cli_0001 --to characterized --evidence ev:a8f9c...
```

> **Completion criterion**: Every characterized obligation is linked to $\ge 1$ evidence record with zero unquarantined contradictions.
Primary artifact: Characterized `ObligationItem`

---

## 4. Implementation Tracking & Parity Verification

Track reconstructed code artifacts against characterized obligations:

1. Map obligation to target source file (`owner_path`) and content digest (`owner_sha256`).
2. Transition disposition from `characterized` to `implemented`.
3. Execute parity test contracts against reference fixtures.
4. Transition disposition to `verified` upon passing test execution.

```sh
harness rol obligation transition ob_cli_0001 --to implemented --owner-path src/cli/args.py
harness rol obligation transition ob_cli_0001 --to verified
```

> **Completion criterion**: Implementation mapped to verified owner path and confirmed by passing test execution.
Primary artifact: Verified `ObligationItem`

---

## 5. Ledger Closure & Cryptographic Proof Synthesis

Synthesize verifiable certificate proving reconstruction completeness:

1. Compute canonical SHA-256 closure digest across all sorted obligations.
2. Verify that `unowned_count == 0` and `contradicted_count == 0`.
3. Emit machine-readable certificate with `is_closed: true`.

```sh
harness rol verify --strict
harness rol export > reconstruction_proof.json
```

> **Completion criterion**: Machine-verifiable `ReconstructionProof` certificate emitted with `is_closed: true`.
Primary artifact: `ReconstructionProof` certificate

---

## Anti-Patterns

- **Facet Conflation** — Treating a missing facet observation as an empty collection instead of explicitly declaring availability.
- **Premature Closure** — Marking reconstruction complete while unowned or contradicted obligations remain active.
- **Speculative Obligation Registration** — Creating obligations without empirical observation or grounding in canonical evidence.
- **Non-Deterministic Digest** — Serializing evidence records with unstable key orderings or non-canonical encodings.
