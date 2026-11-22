# Wave 2 Spawn Adoption & Provenance Evidence — 2026-11-22 EST

- **Generated (UTC):** `2026-11-22T19:36:45Z`
- **Decision Policy (`0.3`, 2026-11-22):** `"0.3 sandbox adoption with committed evidence, no live promotion."`
- **Live Knowledge Vault Status:** `.harness/knowledge/` remains untouched at `382` KIs (`test_readme_and_manual_knowledge_item_count_matches_live` passes).

## Wave 2 Harness Digests & Worked Domain Outputs

| Harness | Spawn ID | Tree SHA-256 | Docs SHA-256 | Worked Output Summary |
|---|---|---|---|---|
| `harness-reverse-engineering` | `spawn_harness-reverse-engineering_dc4bd473` | `753c104ad2f68884e9b9d6377bd6dd463db5f637fd5f8d7b184376873a426223` | `7ee103165617a00e5c7b1013172d5c4bcb8a96f2956ebd26184c3d2de5583aea` | passive REA inspect on safety.cpython-313.pyc; ROL verified c7c4eaf1c87c37f4 (strict closed); facet absence complete=True, truncated=False; stages 01-03 check=pass |
| `harness-ontology-spider` | `spawn_harness-ontology-spider_25c42a72` | `dcb01c400bcd1c0d3ce8266bca04e4cdce701c2f3b0aa115598b4f98419b29d1` | `535d0934b3a262f7542f5030d94a06db3bc6d8a3feefebfcffd03e331f776ac6` | Ontology-Spider Gruber coherence 1.0 (56 verified, 326 unverified); top attr created_at; SHACL dropped=1; PROV-O dual graphs isolated |
| `harness-knowledge-graph` | `spawn_harness-knowledge-graph_d6e459fd` | `41ad1c4bf5be855494a2f57dfe2c433e7a53542a64c98b2e2984692bd876983b` | `2cde324f2688818e275120e568209f110e48047705934faf36c340f389811e0a` | cypher_linter clean on bounded UNWIND/MERGE (rejected unbounded pattern with 1 errors); SQL CTE depth=8 generated; icm quotes 2 of 2 verified |
| `harness-memory-graph` | `spawn_harness-memory-graph_f6afb898` | `99ad28e7dec61b21b68f219be2b5b09f7069a338496a16e9eee58cdf157f7abb` | `d02294cc7b174a1c47a3da6e8c38c3ac6f3e2f8a7d50a784c085cde73c10a9f5` | Graphiti soft_deadline_cleared=False; standalone okf_engine validate=True (concepts=1); teams indexed (2 note). *(Digest updated 2026-11-22 after independent check on 34ef570 found pre-ruff-format 651e3357... vs committed 99ad28e7...)* |

## Merge-Back Proposals & Decisions (Wave 2 Sandbox Parent Store)

| Proposal ID | Spawn ID | Task ID | Kind | Status | KI ID | Reviewer | Note / Reason |
|---|---|---|---|---|---|---|---|
| `prop_re-rol-facet-1_97b016b0` | `spawn_harness-reverse-engineering_dc4bd473` | `re-rol-facet-1` | `ki` | `adopted` | `ki-re-rol-facet-closure-baseline` | `operator-sandbox` | Verified with strict ROL ReconstructionProof closure and facet absence gate. |
| `prop_re-rol-facet-2_3a600352` | `spawn_harness-reverse-engineering_dc4bd473` | `re-rol-facet-2` | `ki` | `rejected` | `ki-spawn-reverse_engineering-re-rol-facet-2` | `operator-sandbox` | Conflating truncated/unobserved facets with absence violates REA facet semantics. |
| `prop_onto-spider-audit-1_8b53ffed` | `spawn_harness-ontology-spider_25c42a72` | `onto-spider-audit-1` | `ki` | `adopted` | `ki-onto-spider-prolog-shacl-audit` | `operator-sandbox` | Confirmed across .dialog closures, entropy ranking, SHACL PolicyFilter, and PROV-O trace. |
| `prop_onto-spider-audit-2_90866688` | `spawn_harness-ontology-spider_25c42a72` | `onto-spider-audit-2` | `ki` | `rejected` | `ki-spawn-ontology_reasoning-onto-spider-audit-2` | `operator-sandbox` | Writing per-query explainability into urn:graph:source violates PROV-O dual named-graph isolation. |
| `prop_kg-dual-traversal-1_31a60bb6` | `spawn_harness-knowledge-graph_d6e459fd` | `kg-dual-traversal-1` | `ki` | `adopted` | `ki-kg-bounded-cypher-and-cte-guards` | `operator-sandbox` | Verified via CypherLinter, KnowledgeGraphPipelineEngine, and ICM verbatim quote check. |
| `prop_kg-dual-traversal-2_ac021ecd` | `spawn_harness-knowledge-graph_d6e459fd` | `kg-dual-traversal-2` | `ki` | `rejected` | `ki-spawn-data_engineering-kg-dual-traversal-2` | `operator-sandbox` | Unbounded variable-length Cypher patterns risk OOM and fail static CypherLinter safety checks. |
| `prop_mem-bitemporal-okf-1_07216eea` | `spawn_harness-memory-graph_f6afb898` | `mem-bitemporal-okf-1` | `ki` | `adopted` | `ki-mem-bitemporal-deadline-clamping` | `operator-sandbox` | Backed by live Graphiti temporal test + standalone okf_engine.py bundle validation. |
| `prop_mem-bitemporal-okf-2_39b6ca65` | `spawn_harness-memory-graph_f6afb898` | `mem-bitemporal-okf-2` | `ki` | `rejected` | `ki-spawn-memory_and_epistemics-mem-bitemporal-okf-2` | `operator-sandbox` | Merging low-entropy identifiers without Shannon entropy gating corrupts unrelated memory nodes. |

## Adopted KI Payloads (Archived Evidence Only; Not in Live Vault)

### `ki-kg-bounded-cypher-and-cte-guards`

#### metadata.json

```json
{
  "id": "ki-kg-bounded-cypher-and-cte-guards",
  "title": "Spawn Learning: data_engineering (kg-dual-traversal-1)",
  "summary": "when emitting Neo4j batch ingestion Cypher or recursive SQL graph queries -> enforce upper hop bounds (*1..k) and UNWIND/MERGE static Cypher linting alongside ANY(path) cycle detection in recursive SQL CTEs",
  "domain": "data_engineering",
  "status": "adopted",
  "tags": [
    "spawn",
    "data_engineering"
  ],
  "created_at": "2026-11-22T19:36:21.456780+00:00",
  "updated_at": "2026-11-22T19:36:21.456780+00:00",
  "source_spawn_id": "spawn_harness-knowledge-graph_d6e459fd",
  "source_proposal_id": "prop_kg-dual-traversal-1_31a60bb6",
  "task_id": "kg-dual-traversal-1",
  "isnad_claim": {
    "cue": "when emitting Neo4j batch ingestion Cypher or recursive SQL graph queries",
    "lesson": "enforce upper hop bounds (*1..k) and UNWIND/MERGE static Cypher linting alongside ANY(path) cycle detection in recursive SQL CTEs",
    "evidence": "cypher_linter.py passed bounded query and rejected unbounded query (errors=1); icm quotes=2/2 verified"
  }
}
```

#### summary.md

```markdown
# Spawn Learning: data_engineering (kg-dual-traversal-1)

- **KI ID**: `ki-kg-bounded-cypher-and-cte-guards`
- **Domain**: `data_engineering`
- **Status**: `adopted`
- **Source Spawn**: `spawn_harness-knowledge-graph_d6e459fd` (`kg-dual-traversal-1`)
- **Proposal ID**: `prop_kg-dual-traversal-1_31a60bb6`

## Transferable Claim
- **Cue**: when emitting Neo4j batch ingestion Cypher or recursive SQL graph queries
- **Lesson**: enforce upper hop bounds (*1..k) and UNWIND/MERGE static Cypher linting alongside ANY(path) cycle detection in recursive SQL CTEs
- **Evidence**: cypher_linter.py passed bounded query and rejected unbounded query (errors=1); icm quotes=2/2 verified

## Rationale
Prevents graph OOM explosions and infinite SQL CTE recursion on cyclic graphs.
```

### `ki-mem-bitemporal-deadline-clamping`

#### metadata.json

```json
{
  "id": "ki-mem-bitemporal-deadline-clamping",
  "title": "Spawn Learning: memory_and_epistemics (mem-bitemporal-okf-1)",
  "summary": "when normalizing scheduled or deadline-bearing assertions into temporal knowledge graphs -> clear soft delivery deadlines from invalid_at and isolate OKF bundle validation via Prime package fallback when materialized",
  "domain": "memory_and_epistemics",
  "status": "adopted",
  "tags": [
    "spawn",
    "memory_and_epistemics"
  ],
  "created_at": "2026-11-22T19:36:42.870201+00:00",
  "updated_at": "2026-11-22T19:36:42.870201+00:00",
  "source_spawn_id": "spawn_harness-memory-graph_f6afb898",
  "source_proposal_id": "prop_mem-bitemporal-okf-1_07216eea",
  "task_id": "mem-bitemporal-okf-1",
  "isnad_claim": {
    "cue": "when normalizing scheduled or deadline-bearing assertions into temporal knowledge graphs",
    "lesson": "clear soft delivery deadlines from invalid_at and isolate OKF bundle validation via Prime package fallback when materialized",
    "evidence": "graphiti_zep_memory_engine.py normalize-temporal soft_deadline_cleared=False; okf_engine.py standalone validate=True (concepts=1)"
  }
}
```

#### summary.md

```markdown
# Spawn Learning: memory_and_epistemics (mem-bitemporal-okf-1)

- **KI ID**: `ki-mem-bitemporal-deadline-clamping`
- **Domain**: `memory_and_epistemics`
- **Status**: `adopted`
- **Source Spawn**: `spawn_harness-memory-graph_f6afb898` (`mem-bitemporal-okf-1`)
- **Proposal ID**: `prop_mem-bitemporal-okf-1_07216eea`

## Transferable Claim
- **Cue**: when normalizing scheduled or deadline-bearing assertions into temporal knowledge graphs
- **Lesson**: clear soft delivery deadlines from invalid_at and isolate OKF bundle validation via Prime package fallback when materialized
- **Evidence**: graphiti_zep_memory_engine.py normalize-temporal soft_deadline_cleared=False; okf_engine.py standalone validate=True (concepts=1)

## Rationale
Prevents active plans with Friday deadlines from expiring prematurely and proves OKF portability.
```

### `ki-onto-spider-prolog-shacl-audit`

#### metadata.json

```json
{
  "id": "ki-onto-spider-prolog-shacl-audit",
  "title": "Spawn Learning: ontology_reasoning (onto-spider-audit-1)",
  "summary": "when auditing formal vault closures and policy-filtered retrieval graphs -> pair deterministic .dialog closures and Laya entropy ranking with sh:order-sorted SHACL-AF filtering and dual PROV-O named graphs",
  "domain": "ontology_reasoning",
  "status": "adopted",
  "tags": [
    "spawn",
    "ontology_reasoning"
  ],
  "created_at": "2026-11-22T19:36:02.963308+00:00",
  "updated_at": "2026-11-22T19:36:02.963308+00:00",
  "source_spawn_id": "spawn_harness-ontology-spider_25c42a72",
  "source_proposal_id": "prop_onto-spider-audit-1_8b53ffed",
  "task_id": "onto-spider-audit-1",
  "isnad_claim": {
    "cue": "when auditing formal vault closures and policy-filtered retrieval graphs",
    "lesson": "pair deterministic .dialog closures and Laya entropy ranking with sh:order-sorted SHACL-AF filtering and dual PROV-O named graphs",
    "evidence": "ontology_spider_runner.py count/negation queries + Laya top_attr=created_at (6.7219b) + SHACL filter allowed=1 dropped=1"
  }
}
```

#### summary.md

```markdown
# Spawn Learning: ontology_reasoning (onto-spider-audit-1)

- **KI ID**: `ki-onto-spider-prolog-shacl-audit`
- **Domain**: `ontology_reasoning`
- **Status**: `adopted`
- **Source Spawn**: `spawn_harness-ontology-spider_25c42a72` (`onto-spider-audit-1`)
- **Proposal ID**: `prop_onto-spider-audit-1_8b53ffed`

## Transferable Claim
- **Cue**: when auditing formal vault closures and policy-filtered retrieval graphs
- **Lesson**: pair deterministic .dialog closures and Laya entropy ranking with sh:order-sorted SHACL-AF filtering and dual PROV-O named graphs
- **Evidence**: ontology_spider_runner.py count/negation queries + Laya top_attr=created_at (6.7219b) + SHACL filter allowed=1 dropped=1

## Rationale
Prevents ungrounded vector retrieval from bypassing logical closure and retrieval provenance separation.
```

### `ki-re-rol-facet-closure-baseline`

#### metadata.json

```json
{
  "id": "ki-re-rol-facet-closure-baseline",
  "title": "Spawn Learning: reverse_engineering (re-rol-facet-1)",
  "summary": "when sealing reverse-engineered behavioral obligations -> require ROL CanonicalEvidence ev:<sha256> and complete non-truncated facet coverage before claiming absence or closure",
  "domain": "reverse_engineering",
  "status": "adopted",
  "tags": [
    "spawn",
    "reverse_engineering"
  ],
  "created_at": "2026-11-22T19:35:22.690537+00:00",
  "updated_at": "2026-11-22T19:35:22.690537+00:00",
  "source_spawn_id": "spawn_harness-reverse-engineering_dc4bd473",
  "source_proposal_id": "prop_re-rol-facet-1_97b016b0",
  "task_id": "re-rol-facet-1",
  "isnad_claim": {
    "cue": "when sealing reverse-engineered behavioral obligations",
    "lesson": "require ROL CanonicalEvidence ev:<sha256> and complete non-truncated facet coverage before claiming absence or closure",
    "evidence": "harness rea inspect safety.cpython-313.pyc + harness rol verify strict=True (closure=c7c4eaf1c87c37f4); facet absence gate complete=True, truncated=False"
  }
}
```

#### summary.md

```markdown
# Spawn Learning: reverse_engineering (re-rol-facet-1)

- **KI ID**: `ki-re-rol-facet-closure-baseline`
- **Domain**: `reverse_engineering`
- **Status**: `adopted`
- **Source Spawn**: `spawn_harness-reverse-engineering_dc4bd473` (`re-rol-facet-1`)
- **Proposal ID**: `prop_re-rol-facet-1_97b016b0`

## Transferable Claim
- **Cue**: when sealing reverse-engineered behavioral obligations
- **Lesson**: require ROL CanonicalEvidence ev:<sha256> and complete non-truncated facet coverage before claiming absence or closure
- **Evidence**: harness rea inspect safety.cpython-313.pyc + harness rol verify strict=True (closure=c7c4eaf1c87c37f4); facet absence gate complete=True, truncated=False

## Rationale
Prevents false-negative claims on truncated decompiler outputs.
```
