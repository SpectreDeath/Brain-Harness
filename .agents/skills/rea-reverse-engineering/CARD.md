┌────────────────────────────────────────────────────────────────────────┐
│ SKILL: rea-reverse-engineering                                         │
├────────────────────────────────────────────────────────────────────────┤
│ REA Reverse-Engineering Toolkit & Unified Dissection Gateway           │
│ Provenance: REA (morluto/rea) v6.5.0 commit ffaf2c12f17                │
│ Domain: security_and_forensics / reverse_engineering                   │
└────────────────────────────────────────────────────────────────────────┘

## Operational Stages

| Stage | Name | Description | Gate |
|---|---|---|---|
| 1 | Detect & Route | Inspect magic bytes and container headers across 13 kinds | Target resolved to verified artifact kind |
| 2 | Dissect & Probe | Dispatch inspection through specialized domain sub-engines | Every facet carries explicit 3-valued status |
| 3 | Extract Signatures | Distill normalized semantic signatures and hash digests | Signatures carry deterministic canonical hashes |
| 4 | Differential Audit | Compare multi-provider outputs via differential facet verifier | Dimension outcomes mapped to 3-valued status |
| 5 | Seal & Distill | Mint ev:<sha256> record and commit dual-file Knowledge Item | Closed dual-file vault directory committed |

## Anti-Patterns Defended

- **Target Code Execution** — Running or executing untrusted target binaries, DLLs, or scripts in-process.
- **Facet Conflation** — Treating an unobserved or undeclared facet as zero occurrences.
- **Premature Absence Claim** — Claiming absence when traversal was partial, truncated, or unknown.
- **Provider Text False Contradiction** — Equating raw provider disassembly formatting differences with semantic disparity.
- **Secret Bleed into Vault** — Storing raw authorization headers, tokens, or embedded binaries in Knowledge Items.

## Mandatory Invariants Checklist

- [ ] Inspection must be strictly offline and non-executing; targets must never be executed or imported in-process.
- [ ] PE binaries must inspect Optional Header Directory #14 (CLR RVA) to route managed assemblies to `rea_managed_runtime`.
- [ ] An absence claim is rejected unless `coverage.status == 'complete'` and `truncated == false` and `omitted_count == 0`.
- [ ] Every unavailable facet (`state == 'unknown'`) must declare a non-empty `reason` string.
- [ ] Knowledge Vault items must be persisted in canonical dual-file directory format (`metadata.json` + `summary.md`).
- [ ] Tool aliases must resolve transparently without duplicating tool schemas in LLM context windows.

