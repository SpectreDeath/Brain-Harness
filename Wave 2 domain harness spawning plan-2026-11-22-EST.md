# Wave 2 Domain Harness Spawning Plan — 2026-11-22 EST

Use Brain Harness's live skill knowledge graph (`19` clusters, `55` cross-cluster bridges), `114` workspace skills (`~8,392` est. catalog tokens), `OntologySpiderKernelService`, and Knowledge Vault (`382` KIs) to design, harden, document, and materialize **Wave 2** domain harnesses — centering explicitly on **Reverse Engineering**, **Ontology-Spider**, and **Knowledge Graphs** (plus optional bi-temporal memory and Tier-2 add-ons).

---

## Verified Starting State (BH `7be7a92`, 2026-11-22 EST)

What exists and is verified live after Wave 1 (`49b2d0a` -> `abe6bd0` -> `7be7a92`):

- **Wave 1 harnesses already materialized under `D:\GitHub\harnesses\`:**
  - `harness-repo-distiller` (`knowledge_bundle`, `5` of `114` skills)
  - `harness-security-forensics` (`record_library`, `5` of `114` skills)
  - `harness-arch-modernizer` (`system_map`, `5` of `114` skills)
  - `harness-context-economizer` (`context_map`, `5` of `114` skills)
- **Spawner, dock, and cold-walk infrastructure:**
  - `src/harness/services/harness_spawner/blueprints.py` + `src/harness/services/harness_spawner/_blueprint_catalog.py` (`CANONICAL_SPECS`)
  - Deterministic filesystem-independent `query_knowledge_and_skills()` (`src/harness/services/skill_graph/joint_query.py`) + `_collect_kis()` `pool_limit=24` and typed `linked_pairs` edge bonuses (`abe6bd0`)
  - Import-portable `_build_scrubbed_env()` (`src/harness/services/dock/safety.py`) absolutizing relative `PYTHONPATH` and appending Prime's package parent
  - Reproducible `docs_sha256` across re-materializations (`_doc_templates.py` omits volatile `created_utc`)
  - Runnable 8-Point Cold Walk verifier (`src/harness/services/harness_spawner/cold_walk.py`, CLI `harness spawn cold-walk`)
- **Live pre-flight dry-run validation (`BRAIN_SURFACE` + `guards.assert_tree_clean()` + live engine probes, 2026-11-22):**
  - `harness-reverse-engineering` (`13` surface files, `5` skills): `validate()` & `assert_tree_clean()` **PASS**
  - `harness-ontology-spider` (`13` surface files, `5` skills): `validate()` & `assert_tree_clean()` **PASS**; `OntologySpiderKernelService().audit_vault_epistemics(".harness/knowledge", min_confidence=0.8)` verified live (`status=verified`, `unverified=326`, top discriminating attributes: `created_at` `6.7219` bits, `source_target` `5.8625` bits, `category` `3.9118` bits)
  - `harness-knowledge-graph` (`15` surface files, `5` skills): `validate()` & `assert_tree_clean()` **PASS** (`score=47.0610`, `cluster_13_knowledge_graph_pipeline`, `cohesion=0.500`, `bridges=3`)
  - `harness-memory-graph` (`12` surface files, `5` skills — optional add-on): **PASS**
  - `harness-data-lakehouse` (`20` files, `score=36.5610`) & `harness-cloud-k8s` (`8` files, `score=32.2370`) — optional add-ons: **PASS**
  - `harness-skill-factory` (excluded/deferred): **BLOCKED pre-flight** by `EvidenceLeakError` in `.agents/skills/agent-skill-sdlc/scripts/validate_skill.py` (offset `3810`, `"passed_count"` grader-verdict marker); deferred out of Wave 2 unless fixed separately.

### Verified Code Gaps to Close in Track 1 Before Wave 2 Spawning

1. **`CANONICAL_SPECS` only registers `8` blueprints.** `harness-knowledge-graph` is already registered (Tier 2), whereas `harness-reverse-engineering`, `harness-ontology-spider`, and optional `harness-memory-graph` are not yet in `src/harness/services/harness_spawner/_blueprint_catalog.py`.
2. **Default blueprint `limit=8` caps discovery output.** Hardcoded across `src/harness/services/harness_spawner/blueprints.py`, `src/harness/commands/spawn.py`, `plugins/agent_orchestration/harness_spawner/main.py`, `plugins/agent_orchestration/harness_spawner/service.py`, `docs/reference/cli.md`, and `tests/test_harness_spawner_blueprints.py` (`assert len(first) == 8` / `payload["count"] == 8`). Must widen cleanly once new blueprints are registered.
3. **`ontology spider` keyword returns `0` KIs directly in `joint_query`.** `query_knowledge_and_skills("ontology spider")` yields `kis(0)`, whereas `query_keywords=("ontology", "trustgraph", "shacl", "gruber", "graphiti")` seeds `6` `VERIFIED` KIs cleanly.
4. **Standalone script path portability check needed for Wave-2 skill engines.** `.agents/skills/ontology-spider/scripts/ontology_spider_runner.py`, `.agents/skills/reconstruction-obligation-ledger/scripts/rol_engine.py`, `.agents/skills/trustgraph-ontology-governor/scripts/trustgraph_governor_engine.py`, and `.agents/skills/graphiti-zep-memory-governor/scripts/graphiti_zep_memory_engine.py` compute `_REPO_ROOT = Path(__file__).resolve().parents[4]` and import `harness.services.*` — verify standalone execution when materialized under `D:\GitHub\harnesses\<name>\` (using Prime's `.venv` + `PYTHONPATH` or safe fallback).

---

## Evidence Rule

Tick a box only with a commit + a passing test, a dated command output, or a written decision recorded verbatim from the user in chat. Never record a user pick that did not happen in visible conversation. Never tick `4.2 Independent check` yourself.

## Scope Limits

- No new third-party dependencies without the user's explicit approval.
- Do not change the confirmed spawn defaults (`Q2–Q7`) or weaken the merge-back policy (zero silent auto-adoption; never raw-`git merge` a trimmed domain branch back into `main`).
- Do not delete or move `.agents/skills/` directories on `main`.
- Do not touch any unticked box in any other plan (e.g. `Graph-driven domain harness follow-up corrections plan-2026-11-22-EST.md` items `1.4`, `3.2`, `5.2`) and do not re-open ticked boxes.
- Do not fix `.agents/skills/agent-skill-sdlc/scripts/validate_skill.py` or spawn `harness-skill-factory` as part of this Wave 2 plan.

---

## Mandatory Documentation, Digest & Cold-Walk Contract (Every Wave 2 Harness)

Every Wave 2 materialized harness follows the exact 7-part documentation & digest contract verified in Wave 1:

1. **Human & Agent Entry Bundle:** `README.md` (with Mission, Use Cases, Out of Scope, Lineage excluding volatile timestamps so `docs_sha256` stays deterministic), `<60`-line `AGENTS.md` + `CLAUDE.md` / `GEMINI.md` pointers, ICM `CONTEXT.md`, `"docs/USE_CASES.md"`, `"docs/PROVENANCE.md"` (zero `UNVERIFIED` KIs promoted as verified), `"docs/RUNBOOK.md"`, and companion `CARD.md` for all bundled skills.
2. **Declarative Manifest & Drift Digest:** `dock.yaml` with `permissions.write: false`, `permissions.push: false`, portable `validate`, `audit-docs`, `icm-audit`, and `icm-links` entrypoints; local `.harness/docks.json` mirror + `.harness/spawn_tree_digest.json`.
3. **8-Point Cold Walk Separation:** Execute `harness spawn cold-walk` so automated points (`#2 Exact Inputs`, `#3 Pure Disk Status`, `#4 No Content in Catalog`, `#6 Resolving Links`, `#7 Token Budget Under 8k`) are reported strictly separately from reader-judged points (`#1 Where am I <=2 reads`, `#5 Single Source of Truth`, `#8 Broken Invariants Explained`).

---

## Wave 2 Harness Portfolio & Boundary Matrix

### Core Required Wave 2 Harnesses (3)

| Priority | Harness Name | Graph Source (Live) | Included Skills (`5` of `114`, `95.61%` reduction) | Proposed ICM Form | Seeded `VERIFIED` KIs & Domain Query Keywords | Core Use Cases & Explicit Boundary |
|---:|---|---|---|---|---|---|
| **1** | `harness-reverse-engineering` | Bridge `cluster_09_mantis_security_review` -> `cluster_04_external_repo_bridge_forge` (`rea-reverse-engineering` -> `reconstruction-obligation-ledger`) | `icm-workspace-architect`, `rea-reverse-engineering`, `reconstruction-obligation-ledger`, `differential-facet-verifier`, `epistemic-isnad-audit` | `pipeline` (stages `01` dissect -> `02` ledger/diff -> `03` proof/seal) | Keywords: `("reverse engineering", "reconstruction", "obligation", "facet")` -> `ki-rea-reconstruction-obligations`, `ki-rea-facet-availability-semantics`, `ki_20261023_rea_03`, `ki_20261023_rea_04` | 1) Passively dissect binaries/PE/.NET/APK/JS/WASM/EVM via `harness rea` with strict 3-valued facet availability & absence-claimability guards. 2) Track behavioral obligations through ROL's 8-state FSM (`ev:<sha256>` -> `ReconstructionProof`) & multi-provider diff dossiers. **Out of scope:** Mantis commit-history SAST or active network packet recon (handled by `harness-security-forensics`). |
| **2** | `harness-ontology-spider` | `cluster_08_ebbinghaus_memory_governor` (`ontology-spider`, `trustgraph-ontology-governor`, `graphiti-zep-memory-governor`, `ontological-engineering-coach`) + bridges to `cluster_06` & `cluster_13` | `icm-workspace-architect`, `ontology-spider`, `trustgraph-ontology-governor`, `graphiti-zep-memory-governor`, `ontological-engineering-coach` | `system_map` (`objects/` entities/classes + `processes/` inference/policy checks) | Keywords: `("ontology", "trustgraph", "shacl", "gruber", "graphiti")` -> `ki_ontological_engineering_gruber_criteria`, `ki-trustgraph-shacl-af-policy-filter`, `ki-trustgraph-ontology-rag-subclass-validation`, `ki-trustgraph-provo-dual-named-graph-explainability`, `ki-trustgraph-laya-onnx-entropy-decision-scoring`, `ki-getzep-graphiti-bitemporal-edge-normalization` | 1) Run formal `.dialog` logic closures (`transitive`, `path`, `ancestors`, closed-world `not`, `count`), Laya attribute-entropy ranking, and vault epistemic audits via `OntologySpiderKernelService`. 2) Enforce SHACL-AF `PolicyFilter`, cycle-safe `subClassOf` validation, PROV-O dual named-graph traces, and bi-temporal `as_of` graph slicing. **Out of scope:** Neo4j batch ETL / recursive SQL CTE pipelines (handled by `harness-knowledge-graph`). |
| **3** | `harness-knowledge-graph` | `cluster_13_knowledge_graph_pipeline` (`cohesion=0.500`, `bridges=3`, existing Tier-2 spec `score=47.0610`) | `icm-workspace-architect`, `knowledge-graph-pipeline`, `neo4j-knowledge-graph-architect`, `sql-recursive-graph-traversal`, `ontological-engineering-coach` | `knowledge_bundle` (`sources/raw/`, verified graph patterns/schemas in `concepts/`) | Live seeded KIs (`6`): `ki_epistemic_graph_traversal_evidence_boundary`, `ki_ontological_engineering_gruber_criteria`, `ki-getzep-community-clustering-and-typed-ontology`, `ki-trustgraph-ontology-rag-subclass-validation`, `ki_20260824_repo_01`, `ki_self_20260903_02` | 1) Design backward Neo4j LPG schemas and lint idempotent Cypher `UNWIND`/`MERGE` batch ingestion queries (`cypher_linter.py`, `graph_pipeline_driver.py`). 2) Author cycle-guarded recursive SQL CTE pathfinding/BFS hierarchies grounded against Gruber criteria. **Out of scope:** Formal SWI-Prolog `.dialog` reasoning or SHACL-AF runtime filtering (handled by `harness-ontology-spider`). |

### Optional Wave 2b Add-Ons (Spawn Only If Selected in Track 0.1)

| Option | Harness Name | Graph Source & Cohesion | Included Skills (`3–5`) | Proposed ICM Form | Distinct Value vs Core 3 |
|---|---|---|---|---|---|
| **Opt A** | `harness-memory-graph` | `cluster_08_ebbinghaus_memory_governor` (`graphiti-zep`, `ebbinghaus`, `okf`) + bridge to `epistemic-memory-lifecycle` | `icm-workspace-architect`, `graphiti-zep-memory-governor`, `ebbinghaus-memory-governor`, `okf-memory-governor`, `epistemic-memory-lifecycle` | `context_map` | Temporal agent-memory operations: MinHash/LSH entity dedup, RRF/MMR reranking, Ebbinghaus decay, OKF BM25 scoping, and 8-state knowledge promotion. |
| **Opt B** | `harness-data-lakehouse` | `cluster_10_bigquery_augmented_analytics` (`cohesion=0.250`, existing Tier-2 `score=36.5610`) | `icm-workspace-architect`, `bigquery-augmented-analytics`, `data-management-architect`, `garf-reporting-architect`, `paperless-document-pipeline` | `pipeline` | Medallion/ODCS data contracts, BigQuery TVF attribution queries, and Garf SQL workflow DAGs. |
| **Opt C** | `harness-cloud-k8s` | `cluster_16_cloud_infrastructure_architect` (`cohesion=0.100`, existing Tier-2 `score=32.2370`) | `icm-workspace-architect`, `cloud-infrastructure-architect`, `kubernetes-drift-guardian` | `record_library` | Kubernetes manifest/RBAC drift and container sandbox policy records. |

*(Note: `harness-skill-factory` remains deferred due to `EvidenceLeakError` in `.agents/skills/agent-skill-sdlc/scripts/validate_skill.py`.)*

---

## Track 0 — User Decision Gate (Confirm Before Editing Code)

> **User Decision (2026-11-22 EST):** `"0.1 (b); 0.2 Confirmed; 0.3 sandbox adoption with committed evidence, no live promotion."`

- [x] **0.1 Confirm Wave 2 harness scope.** Resolved `2026-11-22`: selected **(b) Core 3 + `harness-memory-graph`** (`harness-reverse-engineering`, `harness-ontology-spider`, `harness-knowledge-graph`, and `harness-memory-graph`).
- [x] **0.2 Confirm ICM forms and storage layout.** Confirmed `2026-11-22`: standalone dock-linked directories under `D:\GitHub\harnesses\<name>\` with registry at `D:\GitHub\harnesses\.spawns\registry.json` (`harness-reverse-engineering` = `pipeline`, `harness-ontology-spider` = `system_map`, `harness-knowledge-graph` = `knowledge_bundle`, `harness-memory-graph` = `context_map`).
- [x] **0.3 Confirm Wave 2 KI adoption policy.** Confirmed `2026-11-22`: sandbox adoption into scratch `sandbox_parent_wave2` + committed self-contained evidence under [docs/reports](docs/reports/spawn-wave2-adoptions-2026-11-22.md), leaving live `.harness/knowledge/` untouched at `382` KIs.

## Track 1 — Blueprint Catalog Expansion & Standalone Script Portability

- [x] **1.1 Add the new Wave 2 specs to `_blueprint_catalog.py`.** (`2026-11-22`, commit `9918136`): Added `harness-reverse-engineering`, `harness-ontology-spider`, and `harness-memory-graph` (`tier=2`, `5` skills each, distinct `query_keywords`, `use_cases`, and `out_of_scope` guards) alongside `harness-knowledge-graph` in [\_blueprint\_catalog.py](src/harness/services/harness_spawner/_blueprint_catalog.py) (`11` total specs).
- [x] **1.2 Expand blueprint `limit` defaults and update tests + CLI docs together.** (`2026-11-22`, commit `9918136`): Raised default blueprint `limit` from `8` to `12` across [blueprints.py](src/harness/services/harness_spawner/blueprints.py), [spawn.py](src/harness/commands/spawn.py), [main.py](plugins/agent_orchestration/harness_spawner/main.py), [service.py](plugins/agent_orchestration/harness_spawner/service.py), [cli.md](docs/reference/cli.md), and [test_harness_spawner_blueprints.py](tests/test_harness_spawner_blueprints.py) (`test_wave2_blueprints_seed_verified_kis_and_pass_surface_and_guards` passes).
- [x] **1.3 Verify standalone script execution for Wave 2 skill runners.** (`2026-11-22`, commit `9918136`): Added Prime package fallback when `plugins` is absent in materialized directories to [okf\_engine.py](.agents/skills/okf-memory-governor/scripts/okf_engine.py), [ontology\_spider.py](src/harness/services/ontology_spider.py) (`_ensure_prime_plugins_on_path()` inside `_require_engine()`), and [ontology\_spider\_runner.py](.agents/skills/ontology-spider/scripts/ontology_spider_runner.py); verified `10` Wave-2 script entrypoints `rc=0` plus standalone `ontology_spider_runner.py` query execution from `D:\GitHub\harnesses\harness-ontology-spider`.

## Track 2 — Graph Discovery, Materialization & Digest Reproducibility

- [x] **2.1 Capture dated Wave 2 selection report.** (`2026-11-22`, commit `9918136`): Captured live `harness spawn blueprints --json` (`count=11`) in [spawn-wave2-blueprints-selection-2026-11-22.json](docs/reports/spawn-wave2-blueprints-selection-2026-11-22.json).
- [x] **2.2 Two-phase `review` -> `run --materialize` for every confirmed Wave 2 harness.** (`2026-11-22`): Materialized `harness-reverse-engineering` (`spawn_harness-reverse-engineering_dc4bd473`), `harness-ontology-spider` (`spawn_harness-ontology-spider_25c42a72`), `harness-knowledge-graph` (`spawn_harness-knowledge-graph_d6e459fd`), and `harness-memory-graph` (`spawn_harness-memory-graph_f6afb898`) under `D:\GitHub\harnesses\`.
- [x] **2.3 Prove reproducible `docs_sha256`, portable dock execution, and drift detection.** (`2026-11-22`): Confirmed identical consecutive `docs_sha256` & `tree_sha256` across all 4 harnesses (including re-materialized `harness-ontology-spider` `tree_sha256=dcb01c400bcd1c0d3ce8266bca04e4cdce701c2f3b0aa115598b4f98419b29d1`, `docs_sha256=535d0934b3a262f7542f5030d94a06db3bc6d8a3feefebfcffd03e331f776ac6`), clean standalone `dock inspect` and `dock run <name> validate/audit-docs/icm-audit/icm-links`, clean `spawn check-drift .`, and `RUNBOOK.md` tamper-and-restore detection (`drifted: true` -> restore -> `drifted: false`).

## Track 3 — 8-Point Cold Walk & Domain-Native Use-Case Proofs

- [ ] **3.1 Execute `harness spawn cold-walk` on every Wave 2 harness.**
  - **Automated + prechecks + agent cold reads complete (`2026-11-22`, commit `9918136`):** Executed `harness spawn cold-walk` across all 4 Wave-2 harnesses in [spawn-wave2-cold-walk-2026-11-22.md](docs/reports/spawn-wave2-cold-walk-2026-11-22.md) (automated `#2, #3, #4, #6, #7` = `PASS`; `IcmAuditor` `10` of `10` invariants clean; `IcmVerifier` `0` broken across `51`, `49`, `46`, and `53` links; `validate_harness_docs` clean; `check-drift` `drifted: false`; agent reader `Gemini 4 Neon` cold reads `AGENTS.md` `22L` + `CONTEXT.md` `23–27L` PASS).
  - **Remaining for checkbox closure:** Explicit human reader sign-off on qualitative points `#1`, `#5`, and `#8`.
- [x] **3.2 Run one real domain-native end-to-end use case per confirmed Wave 2 harness + reviewed `propose`/`adopt`/`reject`.** (`2026-11-22`, commit `9918136`, `WAVE2_TRACK3_OK`):
  - `harness-reverse-engineering` (`pipeline`): Passive `harness rea inspect` + `signatures` on `safety.cpython-313.pyc`, strict ROL closure (`c7c4eaf1c87c37f4`, `verified_count=1`), facet absence gate (`complete=True` allowed, `truncated=True` denied), stages `01`–`03` checked, sandbox-adopted `ki-re-rol-facet-closure-baseline` + rejected negative control.
  - `harness-ontology-spider` (`system_map`): Standalone `ontology_spider_runner.py` (Gruber coherence `1.0` across `56` verified + `326` unverified KIs, top attr `created_at`) + SHACL `PolicyFilter` (`dropped=1`) + PROV-O dual named graphs (`urn:graph:source` vs `urn:graph:explain`), indexed, sandbox-adopted `ki-onto-spider-prolog-shacl-audit` + rejected negative control.
  - `harness-knowledge-graph` (`knowledge_bundle`): Validated bounded `UNWIND`/`MERGE` Cypher & rejected unbounded `MATCH (a)-[*]->(b)` (`errors=1`) via `cypher_linter.py`, generated depth-8 SQL recursive CTE via `KnowledgeGraphPipelineEngine`, `icm quotes` verified `2` of `2` quotes + `icm index`, sandbox-adopted `ki-kg-bounded-cypher-and-cte-guards` + rejected negative control.
  - `harness-memory-graph` (`context_map`): Temporal normalization (`soft_deadline_cleared=False`), standalone `okf_engine.py` bundle validation (`valid=True`, `concepts=1`), `icm index teams` (`2` notes), sandbox-adopted `ki-mem-bitemporal-deadline-clamping` + rejected negative control.
- [x] **3.3 Commit self-contained Wave 2 adoption evidence.** (`2026-11-22`, commit `9918136`): Archived spawn IDs, reproducible digests, target hashes, sandbox proposals/rejections, and KI payloads in [spawn-wave2-adoptions-2026-11-22.md](docs/reports/spawn-wave2-adoptions-2026-11-22.md), leaving live `.harness/knowledge/` untouched at `382` KIs and all 4 materialized harnesses at `drifted: false`.

## Track 4 — Verification

- [x] **4.1 Re-run all gates with dated outputs.** (`2026-11-22`, verified on commit `9918136`):
  - Targeted 14-file pytest suite (`test_service_joint_query`, `test_service_dock`, `test_command_dock`, `test_layer_import_boundaries`, `test_icm_workspace_architect`, `test_harness_spawner_blueprints`, `test_harness_spawner_doc_bundle`, `test_harness_spawner_materialize`, `test_harness_spawner_e2e`, `test_harness_spawner_plugin_forwarding`, `test_plugin_integration_drift`, `test_cli_content_drift`, `test_ontology_spider_service`, `test_ontology_spider_adapter_fixes`): `97 passed`.
  - Full unit gate (`pytest -m "unit" -q --timeout=60`): `2356 passed, 885 deselected` (`.harness/config.json` restored cleanly).
  - `ruff check .` (`All checks passed!`) and CI-scoped + touched-file `ruff format --check` (`85 files already formatted`).
  - `mypy src/harness/kernel --ignore-missing-imports` (`27` files, zero issues) and `mypy` without `--ignore-missing-imports` on modified `src/` + `plugins/` modules (`6` source files, zero issues); `mypy --ignore-missing-imports --follow-imports=silent` on modified `test_harness_spawner_blueprints.py` + `ontology_spider_runner.py` (`2` source files, zero issues).
  - `harness context lint` (`[PASS] Context files healthy across 3 checks at: .`), `harness knowledge sync --strict` (`382 Knowledge Item(s)`), and `uv lock --check` (`Resolved 98 packages in 2ms`).
- [ ] **4.2 Independent check.** Left unticked until a genuinely separate check lands. The executor must not tick it.
