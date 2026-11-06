```ascii
┌──────────────────────────────────────────────────────────────────────┐
│ SKILL: ontology-spider                                               │
│ Category: memory_and_epistemics                                      │
│ Version: 0.2.0                                                       │
│ Invocation: /ontology-spider                                         │
│ Triggers: "transitive dependencies", "proof explanation", "ontology",│
│           "schema integrity", "vault query", "swi-prolog"            │
│ Requires: SWI-Prolog or Pure-Python fallback reasoner                │
│ Target: Knowledge vault traversal, formal reasoning, schema checks  │
└──────────────────────────────────────────────────────────────────────┘
```

# Ontology-Spider — Companion Summary Card

## Stage Progression Table

| Stage | Core Responsibility | Primary Mechanism | Completion Gate |
|---|---|---|---|
| **Stage 1: Ingestion** | Load vault export or on-disk items | `OntologySpiderService.load()` | Structured JSON loaded into reasoner |
| **Stage 2: Traversal** | Transitive and taxonomic closure queries | Controlled `.dialog` syntax | Provable answers extracted |
| **Stage 3: Validation** | Enforce schema integrity and acyclicity | `validate()` rules | Zero unexpected structural violations |
| **Stage 4: Explanation** | Surface formal proof paths and rules fired | `explain()` trace | Provenance chain verified |

---

## Mandatory Invariants Checklist

- [ ] **Controlled Query Grammar**: All queries must follow the controlled grammar (`query transitive ...`, `query ancestors ...`).
- [ ] **Proof Path Provenance**: Traversal answers must include rules fired and graph traversal paths.
- [ ] **Dual-Engine Fallback**: Must execute pure-Python fallback if SWI-Prolog is unavailable.
- [ ] **Schema Integrity Enforcement**: Invariant checks must detect cycles, domain/range mismatches, and disjoint classes.

