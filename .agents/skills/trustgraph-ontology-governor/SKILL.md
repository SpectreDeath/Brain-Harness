---
name: trustgraph-ontology-governor
description: Govern knowledge graphs, SHACL-AF triple policies, OntologyRAG subclass validation, PROV-O dual named graphs, and Laya entropy decision scoring. Do not use for relational SQL queries or generic web scraping.
---

# TrustGraph Ontology Governor

`trustgraph-ontology-governor` distills SHACL-AF `PolicyFilter` triple filtering, `OntologySelector` + `TripleConverter` small-schema bypass and cycle-safe `subClassOf` validation, dual named-graph PROV-O query explainability, and Laya ONNX normalized-entropy decision scoring from `trustgraph-ai/trustgraph` (`17e5d742`).

See [CARD.md](CARD.md) for the companion summary card, pipeline stages, and mandatory invariants checklist.
Consult [config.default.yaml](config.default.yaml) for baseline cache, threshold, and temperature bounds.

---

## 1. SHACL-AF Subject-IRI Policy Filtering

Enforce triple-level read/retrieval authorization over `urn:graph:policy` without unbounded cache growth:

1. **Deterministic Order & First-Match-Wins (`evaluate_shacl_policy_filter`)**: Sort `sh:NodeShape` policies ascending by `sh:order` (default `99`), evaluate subject IRIs first-match-wins with `tg-pol:blocks` defaulting `True`, and strip any triple whose subject is blocked.
2. **Open-Mode & Bounded Cache Spec**: Enter explicit `open_mode=True` when zero policies exist and advertise bounded query (`30s` / `256`), SPARQL (`64`), and node (`60s` / `1024`) cache ceilings.

> **Completion criterion**: `ShaclPolicyFilterReport` separates `allowed_triples` from `dropped_triples` with deterministic `policy_evaluations`.

---

## 2. OntologyRAG Small-Schema Bypass & Subclass Validation

Prevent lossy ontology pruning on compact schemas while guaranteeing cycle-safe inheritance validation:

1. **Small-Schema Bypass (`validate_ontology_extractions`)**: Compute `classes + object_properties + datatype_properties`; bypass vector selection (`selector_bypassed=True`) whenever total elements fall below `bypass_selector_below` (`5`).
2. **Cycle-Safe Ancestor Closure**: Guard `subClassOf` traversal with visited-set tracking, checking both `domain` and `range` on relationship triples and `domain` on datatype attribute triples.

> **Completion criterion**: `OntologyValidationReport` accepts compliant triples, rejects schema violations with reasons, and terminates safely on cyclic hierarchies.

---

## 3. Dual Named-Graph PROV-O Explainability & Laya Decision Scoring

Isolate ingestion lineage from query traces and quantify discrete routing confidence:

1. **Dual Named-Graph Provenance (`build_provenance_trace`)**: Partition extraction triples (`https://trustgraph.ai/...`) into `urn:graph:source` and 5-stage query explainability traces (`question`, `grounding`, `exploration`, `focus`, `synthesis` under `urn:trustgraph:...`) into `urn:graph:retrieval`, attaching prompt/completion/total token triples on `synthesis`.
2. **Entropy Calibration & Head Budgeting (`score_laya_decision`)**: Clamp temperatures into `[0.5, 5.0]` (`NaN`/`Inf` -> `1.0`), score `choice`/`score`/`noul` candidates with normalized Shannon entropy confidence $1 - H(p)/\ln(k)$, and warn when option token budgets drop below `16` inside the `192`-token head slice.

> **Completion criterion**: `ProvenanceTraceEnvelope` isolates named graphs cleanly and `LayaDecisionScoreReport` returns finite calibrated confidence and sequence budgets.

---

## The Three Foundational Pillars

### 1. Ordered First-Match Subject Policies with Explicit Open Fallback
Evaluate access control rules deterministically by integer `sh:order`, defaulting `tg-pol:blocks` to `True`, while preserving explicit open-mode semantics when unconfigured.

### 2. Cycle-Safe Ontology Closure & Thresholded Pruning
Short-circuit lossy similarity pruning below small-schema element thresholds and enforce `domain`/`range` constraints over cycle-guarded `subClassOf` hierarchies.

### 3. Named-Graph Lineage Isolation & Calibrated Entropy Confidence
Separate source ingestion provenance from multi-stage query explainability traces and ground routing decisions in clamped-temperature normalized Shannon entropy.

---

## Anti-Patterns

- **Unordered SHACL Rule Evaluation** — Evaluating `sh:NodeShape` constraints without sorting by `sh:order` (default `99`) and breaking on first match yields non-deterministic allow/deny decisions.
- **Unguarded `subClassOf` Recursion** — Walking superclass edges without a visited set causes infinite loops on cyclic schemas.
- **Cross-Graph Lineage Pollution** — Writing per-query `urn:trustgraph:prov:...` explainability triples into `urn:graph:source` corrupts corpus ingestion provenance.
- **Unclamped Entropy Division** — Computing $1 - H(p)/\ln(k)$ without handling $k < 2$ or non-finite `NaN`/`Inf` temperatures triggers division-by-zero and calibration NaNs.
