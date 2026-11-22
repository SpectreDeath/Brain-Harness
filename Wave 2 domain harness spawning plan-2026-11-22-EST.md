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

- [ ] **0.1 Confirm Wave 2 harness scope.** Choose one:
  - **(a) Core 3 only** (`harness-reverse-engineering`, `harness-ontology-spider`, `harness-knowledge-graph`), or
  - **(b) Core 3 + `harness-memory-graph`** (adds the dedicated bi-temporal agent-memory graph harness alongside Ontology-Spider and Neo4j/SQL Knowledge Graph), or
  - **(c) Custom subset** naming any combination with `harness-data-lakehouse` / `harness-cloud-k8s`.
- [ ] **0.2 Confirm ICM forms and storage layout.** Confirm standalone dock-linked directories under `D:\GitHub\harnesses\<name>\` (matching Wave 1 `0.1(a)`) and the proposed ICM forms above (`harness-reverse-engineering` = `pipeline`, `harness-ontology-spider` = `system_map`, `harness-knowledge-graph` = `knowledge_bundle`; optional `harness-memory-graph` = `context_map`), noting that existing Tier-2 defaults use `harness-knowledge-graph` = `knowledge_bundle`.
- [ ] **0.3 Confirm Wave 2 KI adoption policy.** Confirm whether Wave 2 worked use-case adoptions follow Wave 1 decision `4.1` (**sandbox adoption + committed self-contained evidence under `docs/reports/`**, leaving live `.harness/knowledge/` untouched at `382` KIs) or require explicit per-KI promotion review into live `.harness/knowledge/`.

## Track 1 — Blueprint Catalog Expansion & Standalone Script Portability

- [ ] **1.1 Add the new Wave 2 specs to `_blueprint_catalog.py`.** Register `harness-reverse-engineering`, `harness-ontology-spider`, and (if selected in `0.1`) `harness-memory-graph` in `src/harness/services/harness_spawner/_blueprint_catalog.py` with bounded `1..6` skill tuples, domain-tuned `query_keywords`, explicit `use_cases` and `out_of_scope` guards, and clean boundary separation from Wave 1 harnesses and each other.
- [ ] **1.2 Expand blueprint `limit` defaults and update tests + CLI docs together.** Raise the default `limit` across `src/harness/services/harness_spawner/blueprints.py`, `src/harness/commands/spawn.py`, `plugins/agent_orchestration/harness_spawner/main.py`, `plugins/agent_orchestration/harness_spawner/service.py`, `docs/reference/cli.md`, and `tests/test_harness_spawner_blueprints.py` so `harness spawn blueprints --json` returns the full expanded catalog cleanly, plus unit tests verifying keyword seeding (`>= 4` `VERIFIED` KIs for `harness-reverse-engineering`, `6` `VERIFIED` KIs for `harness-ontology-spider` & `harness-knowledge-graph`, `0` unverified KIs leaked, and `BRAIN_SURFACE` + `guards.assert_tree_clean()` passing).
- [ ] **1.3 Verify standalone script execution for Wave 2 skill runners.** Test `.agents/skills/ontology-spider/scripts/ontology_spider_runner.py`, `.agents/skills/reconstruction-obligation-ledger/scripts/rol_engine.py`, `.agents/skills/trustgraph-ontology-governor/scripts/trustgraph_governor_engine.py`, and `.agents/skills/knowledge-graph-pipeline/scripts/graph_pipeline_driver.py` (+ `graphiti_zep_memory_engine.py` if selected) when invoked from a materialized child directory outside Prime using Prime's `.venv`, adding Prime-root fallback (matching the `8919e2a` `network_diagnostics.py` fix) where any script's `_REPO_ROOT / "src"` lookup breaks standalone.

## Track 2 — Graph Discovery, Materialization & Digest Reproducibility

- [ ] **2.1 Capture dated Wave 2 selection report.** Run `harness spawn blueprints --json` and commit the dated selection report under `"docs/reports/spawn-wave2-blueprints-selection-<date>.json"` capturing scores, cohesion, bridge counts, skill-count savings, and seeded KIs for the expanded catalog.
- [ ] **2.2 Two-phase `review` -> `run --materialize` for every confirmed Wave 2 harness.** Execute `harness spawn review --blueprint <name> --json` followed by `harness spawn run --blueprint <name> --save-dir D:\GitHub\harnesses\.spawns --materialize D:\GitHub\harnesses\<name> --approve-dock --write-permitted --approve-digest <sha>` in the user-confirmed order.
- [ ] **2.3 Prove reproducible `docs_sha256`, portable dock execution, and drift detection.** Re-materialize each Wave 2 harness a second time confirming byte-identical `docs_sha256`; run `dock inspect`, `dock run <name> validate`, `audit-docs`, `icm-audit`, `icm-links`, and `spawn check-drift .` from inside each materialized directory; test tamper-and-restore on `"docs/RUNBOOK.md"` (`drifted: true`, `docs_drifted: true` -> restore -> `drifted: false`).

## Track 3 — 8-Point Cold Walk & Domain-Native Use-Case Proofs

- [ ] **3.1 Execute `harness spawn cold-walk` on every Wave 2 harness.** Run `harness spawn cold-walk <dir> --dock-name <name> --json` on each confirmed Wave 2 harness and record a dated report under `"docs/reports/spawn-wave2-cold-walk-<date>.md"` separating automated points (`#2, #3, #4, #6, #7`) + underlying gates (`IcmAuditor` `10/10`, `IcmVerifier` `0` broken links, `validate_harness_docs()` clean, `check-drift` clean) from qualitative reader judgments (`#1 <=2 reads`, `#5`, `#8`, naming reader and tracking human sign-off explicitly).
- [ ] **3.2 Run one real domain-native end-to-end use case per confirmed Wave 2 harness + reviewed `propose`/`adopt`/`reject`.**
  - `harness-reverse-engineering` (`pipeline`): Dissect one real binary/bundle target passively via `harness rea inspect` & `harness rea signatures`, register/characterize an obligation in ROL (`harness rol`), run differential facet check, write stage outputs + `check.md` under `"stages/01..03/"`, pass `icm audit` & `icm links`, stage 2 proposals -> adopt 1 into isolated sandbox parent store + reject 1 negative control.
  - `harness-ontology-spider` (`system_map`): Execute real `.dialog` transitive/shortest-path/negation/count queries, Laya entropy attribute ranking, and vault epistemic audit via `OntologySpiderKernelService` over `.harness/knowledge/`, run a SHACL-AF / `subClassOf` / PROV-O check via `trustgraph_governor_engine.py`, record findings under `"objects/"` & `"processes/"`, rebuild indexes, pass `icm audit` & `icm links`, and stage/adopt/reject 2 proposals.
  - `harness-knowledge-graph` (`knowledge_bundle`): Capture verified graph pattern source excerpts under `"sources/raw/"`, validate backward Neo4j LPG + idempotent Cypher `UNWIND`/`MERGE` + cycle-guarded recursive SQL CTE output via `cypher_linter.py` & `graph_pipeline_driver.py`, pass `harness icm quotes .` + `icm index concepts` + `icm audit`, and stage/adopt/reject 2 proposals.
  - *(If `harness-memory-graph` selected in `0.1`:)* Run bi-temporal clamping, entropy-gated MinHash/LSH dedup, and OKF BM25 scope check, record domain boundary contracts under `"teams/"`, rebuild `"teams/_index.md"`, and stage/adopt/reject 2 proposals.
- [ ] **3.3 Commit self-contained Wave 2 adoption evidence.** Archive spawn IDs, reproducible digests, target artifact hashes, proposals/rejections, and KI payloads under `"docs/reports/spawn-wave2-adoptions-<date>.md"` (or adopt into live vault only if `0.3` explicitly chose live promotion), and verify `check-drift` remains `drifted: false` across all harnesses.

## Track 4 — Verification

- [ ] **4.1 Re-run all gates with dated outputs.**
  - Targeted spawn + ICM + joint-query + blueprint + doc-bundle + drift + layer-boundary suites (`pytest`)
  - Full unit gate (`pytest -m "unit" -q --timeout=60`)
  - `ruff check .`, CI-scoped `ruff format --check`, and touched-file `ruff format --check`
  - `mypy src/harness/kernel --ignore-missing-imports` and `mypy` on all modified `.py` modules (without `--ignore-missing-imports`)
  - `harness context lint`, `harness knowledge sync --strict`, and `uv lock --check`
- [ ] **4.2 Independent check.** Left unticked until a genuinely separate check lands. The executor must not tick it.
