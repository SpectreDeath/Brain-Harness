┌────────────────────────────────────────────────────────────────────────┐
│ SKILL: differential-facet-verifier                                     │
├────────────────────────────────────────────────────────────────────────┤
│ Differential Facet Verifier & Availability Semantics                   │
│ Provenance: REA (morluto/rea) v6.5.0 commit 7016951394                 │
│ Domain: security_and_forensics / reverse_engineering                   │
└────────────────────────────────────────────────────────────────────────┘

## Operational Stages

| Stage | Name | Description | Gate |
|---|---|---|---|
| 1 | Declare & Ingest | Ingest multi-provider dossiers with explicit availability | Explicit boolean available on all facets |
| 2 | Validate Absence | Evaluate absence claimability rule against coverage state | status == complete and clean traversal |
| 3 | Project Dimensions | Project comparable structural facets to canonical formats | Isolate provider representation divergence |
| 4 | Evaluate Outcomes | Map dimensions to 3-valued status (unchanged/changed/unknown) | Unknown dimensions have null counts |
| 5 | Synthesize & Seal | Aggregate overall report and compute SHA-256 digest | Emit rep:<sha256> verified report |

## Anti-Patterns Defended

- **Facet Conflation**: Treating unobserved facets as zero occurrences.
- **Undeclared Absence Fallacy**: Claiming absence without complete coverage.
- **Provider Text False Contradiction**: Flagging formatting syntax deltas as functional changes.
- **Limitation Erasure**: Discarding failure reasons during report rollup.
- **Premature unchanged Verdict**: Declaring unchanged when unknown dimensions exist.

## Mandatory Invariants Checklist

- [ ] Every unavailable facet (`available: false`) must declare a non-empty `reason` string.
- [ ] An absence claim is rejected unless `coverage.status == 'complete'` and `truncated == false` and `omitted_count == 0`.
- [ ] Any dimension with status `unknown` must carry `left_digest == None`, `right_digest == None`, `left_count == None`, `right_count == None`.
- [ ] Overall report status cannot be `unchanged` if any dimension is `unknown`.
- [ ] Report ID must carry the cryptographic prefix `rep:<sha256>`.
