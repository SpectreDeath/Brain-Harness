```ascii
┌──────────────────────────────────────────────────────────────────────┐
│ SKILL: trustgraph-ontology-governor                                  │
│ Category: memory_and_epistemics / knowledge_graph                    │
│ Version: 1.0.0                                                       │
│ Invocation: /trustgraph-ontology-governor                            │
│ Triggers: "trustgraph", "PolicyFilter", "OntologyRAG",               │
│           "TripleConverter", "PROV-O", "Laya", "urn:graph:policy"    │
│ Requires: "epistemic-memory-lifecycle"                               │
│ Target: SHACL-AF triple policies, ontology validation & PROV-O/Laya  │
└──────────────────────────────────────────────────────────────────────┘
```

# TrustGraph Ontology Governor — Companion Summary Card

## Pipeline Stages

| Stage | Operation | Output Model |
| --- | --- | --- |
| **1. Policy Filter** | `evaluate_shacl_policy_filter()` | `ShaclPolicyFilterReport` (`open_mode`, `blocked_subjects`, `allowed_triples`) |
| **2. Ontology Check** | `validate_ontology_extractions()` | `OntologyValidationReport` (`selector_bypassed`, `accepted_triples`, `cycles_detected`) |
| **3. PROV-O Trace** | `build_provenance_trace()` | `ProvenanceTraceEnvelope` (`source_graph`, `retrieval_graph`, `stage_uris`) |
| **4. Laya Scoring** | `score_laya_decision()` | `LayaDecisionScoreReport` (`clamped_temperature`, `confidence`, `opt_budget`) |

---

## Mandatory Invariants Checklist

- [ ] **SHACL Order & Open Fallback**: `sh:NodeShape` policies sort ascending by `sh:order` (`99` default), first-match wins with `blocks=True` default, and empty rules enter explicit open mode.
- [ ] **Small-Schema Bypass & Cycle Guard**: Ontologies with total elements `< 5` bypass vector selection (`selector_bypassed=True`), and `subClassOf` closure terminates cleanly on cycles.
- [ ] **Dual Named-Graph Isolation**: Source extraction triples live exclusively in `urn:graph:source` while 5-stage query explainability and token triples live in `urn:graph:retrieval`.
- [ ] **Temperature Clamp & Entropy Guard**: Temperatures clamp to `[0.5, 5.0]` (`NaN`/`Inf` -> `1.0`), $k < 2$ returns confidence `1.0`, and `opt_budget < 16` raises `shrink_warning=True`.
- [ ] **Slotted & Frozen Models**: All four report dataclasses use `slots=True, frozen=True` (Rule 12).
