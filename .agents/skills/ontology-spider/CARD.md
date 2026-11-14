```ascii
┌──────────────────────────────────────────────────────────────────────┐
│ SKILL: ontology-spider                                               │
│ Category: memory_and_epistemics                                      │
│ Version: 0.2.0                                                       │
│ Invocation: /ontology-spider                                         │
│ Triggers: "transitive dependencies", "proof explanation", "ontology",│
│           "shortest path", "isnad audit", "gruber competency"        │
│ Requires: SWI-Prolog or Pure-Python fallback reasoner                │
│ Target: Canonical vault traversal, entropy ranking, epistemic audit  │
└──────────────────────────────────────────────────────────────────────┘
```

# Ontology-Spider — Companion Summary Card

## Stage Progression Table

| Stage | Core Responsibility | Primary Mechanism | Completion Gate |
|---|---|---|---|
| **Stage 1: Ingestion** | Load canonical `.harness/knowledge/` items, `edges`, `isnad`, temporal slice | `HarnessVaultModelSource(as_of, min_confidence)` | Entities & edges loaded cleanly |
| **Stage 2: Traversal** | Transitive, taxonomic, `path`, `not`, `count`, and distance reranking | `OntologySpiderKernelService.query(..., rank_by_distance=True)` | Provable answers + hop scores |
| **Stage 3: Ranking & Competency** | Rank discriminating attributes (Shannon/Laya) and run Gruber suite | `rank_attributes()` / `evaluate_competency()` | Entropy & Gruber scorecard emitted |
| **Stage 4: Epistemic Audit** | Combine structural violations, `isnad_verified`, and coherence checks | `audit_vault_epistemics()` | Audit status verified or surfaced |

---

## Mandatory Invariants Checklist

- [ ] **Controlled Query Grammar**: All queries follow `.dialog` grammar (`transitive`, `ancestors`, `path`, `not`, `count`, `recommend`).
- [ ] **Canonical Vault Seam Integrity**: Ingestion parses canonical `edges`, `isnad`, `tags`, and bi-temporal `as_of` bounds without adding `harness` imports into `ontology_spider`.
- [ ] **Proof Path & Isnad Provenance**: Traversal answers preserve rules fired, paths, and `isnad_verified` entity metadata.
- [ ] **Dual-Engine Fallback**: Executes deterministic pure-Python BFS fallback whenever SWI-Prolog is unavailable.
- [ ] **Structural & Epistemic Audit**: Audits surface cycle, domain/range, disjointness, and unverified-claim findings deterministically.
