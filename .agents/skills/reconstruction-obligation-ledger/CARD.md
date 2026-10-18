```ascii
┌──────────────────────────────────────────────────────────────────────┐
│ SKILL: reconstruction-obligation-ledger                              │
│ Category: security-and-forensics                                     │
│ Version: 1.0.0                                                       │
│ Invocation: /reconstruction-obligation-ledger                        │
│ Triggers: "reconstruction obligation ledger", "reverse engineering   │
│           evidence", "verify reconstruction", "prove software parity",│
│           "software obligation tracking", "audit reconstruction"     │
│ Requires: "adversarial-agent-verifier", "epistemic-isnad-audit",     │
│           "deep-skill-forge"                                         │
│ Target: Cryptographic closure & evidence-backed obligation tracking  │
└──────────────────────────────────────────────────────────────────────┘
```

# Reconstruction Obligation Ledger — Companion Summary Card

## Stage Progression Table

| Stage | Objective | Primary Artifact | Completion Gate |
|---|---|---|---|
| **Stage 1: Ingest** | Ingest observation & compute canonical digest | CanonicalEvidence record | Unique `ev:<sha256>` digest with explicit facet availability |
| **Stage 2: Register** | Declare behavioral surfaces across 10 layers | ObligationItem record | All declared surfaces appear with `unowned` disposition |
| **Stage 3: Characterize** | Attach evidence & detect contradictions | Characterized Obligation | Linked to $\ge 1$ evidence record; contradictions quarantined |
| **Stage 4: Implement & Verify** | Track parity to owner path & distribution | Verified Obligation | Mapped to verified `owner_path` and distributed package |
| **Stage 5: Close** | Compute cryptographic closure digest | ReconstructionProof certificate | Zero unowned or contradicted surfaces; `is_closed == True` |

---

## Vocabulary & Levers

- **CanonicalEvidence Record**: Content-addressed, frozen observation envelope keyed by SHA-256 (`ev:<digest>`).
- **Facet Availability Map**: Explicit `{ available: bool, reason: str }` structure preventing false equivalences on missing facets.
- **8-State Disposition FSM**: Transition graph governing behavioral obligations from `unowned` to `verified` or `contradicted`.
- **ReconstructionProof Certificate**: Machine-verifiable cryptographic certificate proving software reconstruction completeness.
- **Closure Digest**: SHA-256 checksum over canonically serialized, sorted obligations sealing the ledger state.

---

## Mandatory Invariants Checklist

- [ ] **Content-Addressed Determinism**: Every tool observation must be digested using canonical JSON key sorting into `ev:<sha256>`.
- [ ] **Facet Availability Invariant**: Unobserved facets must never be represented as empty collections; explicit availability is mandatory.
- [ ] **Evidence Grounding Gate**: Transitioning to `characterized` strictly requires linking to at least one valid `CanonicalEvidence` record.
- [ ] **Implementation Traceability Gate**: Transitioning to `implemented` strictly requires declaring a valid `owner_path`.
- [ ] **Zero-Unowned Closure Gate**: `ReconstructionProof.is_closed` is false whenever `unowned_count > 0` or `contradicted_count > 0`.
- [ ] **Single-Source Click Seams**: Command invocations must use headless Click CLI seams under `harness rol ...` (Rule 10).
