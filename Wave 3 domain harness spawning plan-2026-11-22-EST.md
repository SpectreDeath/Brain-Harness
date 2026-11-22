# Wave 3 Domain Harness Spawning Plan — 2026-11-22 EST

Use Brain Harness's live skill knowledge graph (`19` clusters, `55` cross-cluster bridges, `22` emergent macro-capabilities), `114` workspace skills, and Knowledge Vault (`382` KIs) to design, harden, document, and materialize **Wave 3** domain harnesses covering the highest-value remaining uncovered engineering domains: **Lakehouse & Analytical SQL**, **Agent Harness Reliability & Calibration**, **Multi-Agent Swarm Orchestration**, and **AST Docs-as-Code & Diagrams** (plus optional Wave 3b add-ons `harness-cloud-k8s`, `harness-geospatial-gis`, and unblocking options for `harness-skill-factory`).

---

## Verified Starting State (BH `b94d7d4`, 2026-11-22 EST)

What exists and is verified live after Waves 1 & 2 (`9918136` -> `34ef570` -> `6bbf3e9` -> `fea8c82` -> `1061156` -> `8097d57` -> `b94d7d4`):

- **Already materialized (`8` harnesses under `D:\GitHub\harnesses\`):**
  - **Wave 1 (`4`):** `harness-repo-distiller` (`knowledge_bundle`), `harness-security-forensics` (`record_library`), `harness-arch-modernizer` (`system_map`), `harness-context-economizer` (`context_map`)
  - **Wave 2 (`4`):** `harness-reverse-engineering` (`pipeline`), `harness-ontology-spider` (`system_map`), `harness-knowledge-graph` (`knowledge_bundle`), `harness-memory-graph` (`context_map`, refreshed in `fea8c82` -> `1061156` to authoritative `tree_sha256=99ad28e7dec61b21b68f219be2b5b09f7069a338496a16e9eee58cdf157f7abb`)
- **Existing unspawned catalog specs (`3` of `11` in `src/harness/services/harness_spawner/_blueprint_catalog.py`):**
  - `harness-data-lakehouse` (`score=36.5610`, `cluster_10_bigquery_augmented_analytics`, `cohesion=0.25`, `bridges=1`, `6` verified KIs, `pipeline`) — pre-flight clean
  - `harness-cloud-k8s` (`score=32.2370`, `cluster_16_cloud_infrastructure_architect`, `cohesion=0.10`, `bridges=1`, `6` verified KIs, `record_library`) — pre-flight clean
  - `harness-skill-factory` (`score=48.9190`, `cluster_05_deep_skill_forge`, `cohesion=0.11`, `bridges=14`, `6` verified KIs, `pipeline`) — blocked pre-flight by literal `"passed_count"` at `.agents/skills/agent-skill-sdlc/scripts/validate_skill.py` line `115` (`src/harness/services/recursive_harnessing/guards.py` line `25` `GRADER_VERDICT_MARKERS`)
- **Repo-wide `EvidenceLeakError` tripwire audit (`2026-11-22`):** Across all `114` workspace skills under `.agents/skills`, only `3` files match `GRADER_VERDICT_MARKERS` (`.agents/skills/agent-skill-sdlc/scripts/validate_skill.py` line `115`, `.agents/skills/recursive-harness-refiner/SKILL.md` line `44`, and `.agents/skills/ts-agent-harness-constructor/scripts/ts_harness_constructor.py` line `200`). All Core 4 Wave 3 skills are clean.
- **Dynamic `plugins` import audit (`2026-11-22`):** None of the Core 4 Wave 3 skills or their backing `src/harness/services` modules import `plugins` dynamically. Optional `harness-geospatial-gis` (`gods-eye-view`) imports `plugins.geospatial_and_osint.gods_eye_view.main` inside `src/harness/services/gods_eye_view/resolvers.py` (lines `301` and `305`), requiring a Prime-root path guard in Track `1.3` if selected.

### Verified Code Gaps & Wave 2 Operational Lessons to Close in Track 1

1. **`CANONICAL_SPECS` currently registers `11` blueprints (`limit=12`).** Adding `3` new Core Wave 3 specs (`harness-agent-reliability`, `harness-swarm-orchestrator`, `harness-docs-architect` -> `14` total, or `15` with optional `harness-geospatial-gis`) requires raising default blueprint `limit` from `12` to `16` across `src/harness/services/harness_spawner/blueprints.py`, `src/harness/commands/spawn.py`, `plugins/agent_orchestration/harness_spawner/main.py`, `plugins/agent_orchestration/harness_spawner/service.py`, `docs/reference/cli.md`, and `tests/test_harness_spawner_blueprints.py`.
2. **Standalone `parents[4]` script portability check required for Wave 3 runners.** Scripts in Core 4 candidate skills (`.agents/skills/data-management-architect/scripts/engine.py`, `.agents/skills/garf-reporting-architect/scripts/garf_cli.py`, `.agents/skills/multi-bot-desk-orchestrator/scripts/multi_bot_desk_engine.py`, `.agents/skills/hf-doc-builder-architect/scripts/doc_builder_engine.py`) and optional add-ons (`.agents/skills/open-source-gis-architect/scripts/engine.py`, `.agents/skills/skill-eval-assurance-runner/scripts/skill_eval_assurance_engine.py`) must be smoke-tested from an external materialized child directory outside Prime.
3. **Pre-Materialization Format Lock (Wave 2 Digest Fix Lesson):** In Wave 2, running `ruff format` on `.agents/skills/okf-memory-governor/scripts/okf_engine.py` *after* Track 2 materialization caused a 2-byte `tree_sha256` drift (`651e3357…` vs `99ad28e7…`). Wave 3 introduces a mandatory Track `1.4` gate requiring `ruff format`, `ruff check .`, `mypy`, and blueprint unit tests to finish **before** Track 2 materialization begins.

---

## Evidence Rule

Tick a box only with a commit + a passing test, a dated command output, or a written decision recorded verbatim from the user in chat. Never record a user pick that did not happen in visible conversation. Never tick `4.2 Independent check` yourself.

## Scope Limits

- No new third-party dependencies without the user's explicit approval.
- Do not weaken `src/harness/services/recursive_harnessing/guards.py` (`GRADER_VERDICT_MARKERS` is a leak tripwire on the adapter read boundary; never remove markers or bypass it).
- Do not weaken the confirmed spawn defaults (`Q2–Q7`) or merge-back policy (zero silent auto-adoption; never raw-`git merge` a trimmed domain branch back into `main`).
- Do not delete or move `.agents/skills` directories on `main`.
- Do not touch any unticked box in any earlier plan (e.g. Wave 2 `3.1`, Wave 1 follow-up `1.4`, `3.2`, `5.2`) and do not re-open ticked boxes.

---

## Mandatory Documentation, Digest & Cold-Walk Contract (Every Wave 3 Harness)

Every Wave 3 materialized harness follows the exact 7-part documentation & digest contract verified in Waves 1 & 2:

1. **Human & Agent Entry Bundle:** `README.md` (with Mission, Use Cases, Out of Scope, Lineage excluding volatile timestamps so `docs_sha256` stays deterministic), `<60`-line `AGENTS.md` + `CLAUDE.md` & `GEMINI.md` pointers, ICM `CONTEXT.md`, `"docs/USE_CASES.md"`, `"docs/PROVENANCE.md"` (zero `UNVERIFIED` KIs promoted as verified), `"docs/RUNBOOK.md"`, and companion `CARD.md` files for all bundled skills.
2. **Declarative Manifest & Drift Digest:** `dock.yaml` with `permissions.write: false`, `permissions.push: false`, portable `validate`, `audit-docs`, `icm-audit`, and `icm-links` entrypoints; local `.harness/docks.json` mirror + `.harness/spawn_tree_digest.json`.
3. **8-Point Cold Walk Separation:** Execute `harness spawn cold-walk` so automated points (`#2 Exact Inputs`, `#3 Pure Disk Status`, `#4 No Content in Catalog`, `#6 Resolving Links`, `#7 Token Budget Under 8k`) are reported separately from reader-judged points (`#1 Where am I <=2 reads`, `#5 Single Source of Truth`, `#8 Broken Invariants Explained`).

---

## Wave 3 Harness Portfolio & Boundary Matrix

### Core Wave 3 Harnesses (4)

| Priority | Harness Name | Graph Source & Capability | Included Skills (`5` of `114`, `95.61%` reduction) | ICM Form | Verified KIs & Query Keywords | Core Use Cases & Explicit Boundary |
|---:|---|---|---|---|---|---|
| **1** | `harness-data-lakehouse` | Existing Tier-2 spec (`cluster_10_bigquery_augmented_analytics`, `cohesion=0.25`, `bridges=1`, `score=36.5610`, Emergent Cap `#11`) | `icm-workspace-architect`, `bigquery-augmented-analytics`, `data-management-architect`, `garf-reporting-architect`, `paperless-document-pipeline` | `pipeline` (`"stages/01..03/"`) | Live seeded (`6`): `ki_garf_reporting_engine`, `ki_solla_contract_first_medallion_lakehouse`, `ki-hf-datasets-arrow-streaming`, `ki_solla_dikw_data_asset_continuum`, `ki_agentwikis_governance`, `ki_audit_20260908_07` | 1) Validate ODCS data contracts and quality profiles via `harness data` + `data_contract_validator.py`. 2) Generate BigQuery anomaly/attribution TVFs (`harness bigquery`) and declarative Garf SQL reporting DAGs (`harness garf`). **Out of scope:** Neo4j Cypher ETL / recursive SQL CTE hierarchies (handled by `harness-knowledge-graph`) or live production OLTP mutations. |
| **2** | `harness-agent-reliability` | New spec (`cluster_03_agent_harness_architect`, Size `22`, Emergent Cap `#4`) | `icm-workspace-architect`, `agentic-reliability-harness`, `self-evaluating-ai-pipeline`, `coding-harness-calibrator`, `uncertainty-aware-ai-architect` | `pipeline` (`"stages/01..03/"`) | Keywords: `("reliability", "evaluation", "compass", "uncertainty")` -> `ki_self_20260917_02`, `ki_google_research_uq_benchmark_2019_calibration_shift`, `ki-harnesscompass-evolution`, `ki_aslanyan_canonical_failures_antidotes`, `ki_techwithrj_harness_engineering`, `ki-harness2-recursive-harnessing` | 1) Run 3-layer LLM eval suites (`harness eval`), PEP gateway / calibration checks (`harness architect`, `harness calibrate`), and 4-gate harness governance (`harness gate`). 2) Enforce 3-layer semantic & entropy uncertainty gates (`harness uncertainty`). **Out of scope:** `AGENTS.md` prompt token budgeting (handled by `harness-context-economizer`) or multi-agent worktree deliberation (handled by `harness-swarm-orchestrator`). |
| **3** | `harness-swarm-orchestrator` | New spec (`cluster_03_agent_harness_architect` + `cluster_06` bridge, Emergent Cap `#3`) | `icm-workspace-architect`, `orca-orchestrator`, `swarm-reflection-optimizer`, `game-theoretic-swarm-deliberator`, `multi-bot-desk-orchestrator` | `context_map` (`"teams/"`) | Keywords: `("orca", "swarm", "consensus", "backprop")` -> `ki_orca_orchestration_engine`, `ki_google_research_cisc_confidence_voting`, `ki_20260913_claude_coord_02`, `ki_self_20260916_01`, `ki_self_20260829_04`, `ki_20260831_strategify_04` | 1) Coordinate multi-bot serial queues, hop-depth guards, and Orca worktree settlements (`multi_bot_desk_engine.py`, `orca_coordinator.py`). 2) Resolve Borda/consensus payoff matrices and textual DAG backpropagation (`swarm_optimizer_driver.py`). **Out of scope:** Single-agent eval/uncertainty gates (`harness-agent-reliability`) or binary reverse engineering (`harness-reverse-engineering`). |
| **4** | `harness-docs-architect` | New spec (Emergent Cap `#22` bridging `cluster_04`, `cluster_05`, `cluster_07`, `cluster_11`) | `icm-workspace-architect`, `developer-docs-architect`, `repo-doc-synchronizer`, `hf-doc-builder-architect`, `python-diagrams-architect` | `system_map` (`"objects/"`, `"processes/"`) | Keywords: `("diataxis", "diagram", "doc_builder", "documentation")` -> `ki_self_20260914_02`, `ki_hira_python_system_design_diagrams`, `ki_hf_autodoc_mock_virtualization`, `ki_hf_doc_anchor_graph_integrity`, `ki_hf_mdx_component_pipeline`, `ki_20260913_pr_lens_eli5_pedagogy` | 1) Audit AST code-to-doc symbol drift (`harness doc`, `doc_ast_inspector.py`), lint Diátaxis/OpenAPI specs (`doc_linter.py`), and compile MDX/anchor graphs (`harness doc-builder`). 2) Render & validate Python Diagrams-as-Code topologies (`pda_diagram_cli.py`). **Out of scope:** Rule 11 context file pruning (`harness-context-economizer`) or monolith code splitting (`harness-arch-modernizer`). |

### Optional Wave 3b Add-Ons (Spawn Only If Selected in Track 0)

| Option | Harness Name | Graph Source & Status | Included Skills (`3–4`) | Proposed ICM Form | Distinct Value & Technical Notes |
|---|---|---|---|---|---|
| **Opt A** | `harness-cloud-k8s` | Existing Tier-2 spec (`cluster_16_cloud_infrastructure_architect`, `score=32.2370`, `6` verified KIs) | `icm-workspace-architect`, `cloud-infrastructure-architect`, `kubernetes-drift-guardian` | `record_library` | Audits Kubernetes manifests, RBAC least-privilege posture, and sandbox isolation metrics (`"records/"` + `"records/_index.md"`). Pre-flight clean today. |
| **Opt B** | `harness-geospatial-gis` | New spec (`8` verified geospatial KIs across Open Source GIS & Earth/GEV engines) | `icm-workspace-architect`, `open-source-gis-architect`, `geospatial-disaster-simulation`, `gods-eye-view` | `system_map` | Routes 14 open-source GIS engines with CRS safety gates (`harness gis`), disaster tile physics, and planetary OSINT (`harness gev`). Requires Prime-root path guard in `src/harness/services/gods_eye_view/resolvers.py` if selected. |
| **Opt C** | `harness-skill-factory` | Existing Tier-2 spec (`cluster_05_deep_skill_forge`, `score=48.9190`, `bridges=14`, `6` verified KIs) | `icm-workspace-architect`, `crafting-skills`, `agent-skill-sdlc` (or `agent-skills-architect`), `skill-eval-assurance-runner` | `pipeline` | Deep-module skill scaffolding, Wilson CI / `pass^k` assurance (`skill_eval_assurance_engine.py`), and skill validation. Currently blocked by `EvidenceLeakError` unless Track `0.2(ii)` or `0.2(iii)` is chosen. |

---

## Track 0 — User Decision Gate (Confirm Before Editing Code)

- [ ] **0.1 Confirm Wave 3 harness scope.** Choose one:
  - **(a) Core 4 only** (`harness-data-lakehouse`, `harness-agent-reliability`, `harness-swarm-orchestrator`, `harness-docs-architect`), or
  - **(b) Core 4 + `harness-cloud-k8s`** (completes all remaining unblocked Tier-2 catalog specs), or
  - **(c) Core 4 + `harness-geospatial-gis`** (adds the GIS & spatial simulation harness), or
  - **(d) Custom subset** naming any combination with Opt A (`harness-cloud-k8s`), Opt B (`harness-geospatial-gis`), or Opt C (`harness-skill-factory`).
- [ ] **0.2 Confirm `harness-skill-factory` unblocking policy.** Choose one:
  - **(i) Keep deferred** (do not touch `.agents/skills/agent-skill-sdlc/scripts/validate_skill.py`), or
  - **(ii) Non-invasive swap** — update `harness-skill-factory` in `_blueprint_catalog.py` to bundle `agent-skills-architect` instead of `agent-skill-sdlc` (leaving `validate_skill.py` and `guards.py` untouched), or
  - **(iii) Rename verdict field in `validate_skill.py`** — rename `"passed_count"` -> `"checks_passed"` in `.agents/skills/agent-skill-sdlc/scripts/validate_skill.py` line `115` + its tests (never modifying `guards.py`).
- [ ] **0.3 Confirm ICM forms and storage layout.** Confirm standalone dock-linked directories under `D:\GitHub\harnesses\<name>\` (matching Waves 1 & 2) with registry at `D:\GitHub\harnesses\.spawns\registry.json` and the ICM forms above (`harness-data-lakehouse` = `pipeline`, `harness-agent-reliability` = `pipeline`, `harness-swarm-orchestrator` = `context_map`, `harness-docs-architect` = `system_map`; optional `harness-cloud-k8s` = `record_library`, `harness-geospatial-gis` = `system_map`, `harness-skill-factory` = `pipeline`).
- [ ] **0.4 Confirm Wave 3 KI adoption policy.** Confirm whether Wave 3 worked use-case adoptions follow Waves 1 & 2 (**sandbox adoption into scratch `sandbox_parent_wave3` + committed self-contained evidence under `"docs/reports/"`**, leaving live `.harness/knowledge` untouched at `382` KIs) or require explicit per-KI promotion review into live `.harness/knowledge`.

## Track 1 — Blueprint Catalog Expansion, Limit Widening, Script Portability & Format Lock

- [ ] **1.1 Add confirmed new Wave 3 specs to `_blueprint_catalog.py`.** Register `harness-agent-reliability`, `harness-swarm-orchestrator`, `harness-docs-architect` (and optional `harness-geospatial-gis` / updated `harness-skill-factory` per Track `0.1`–`0.2`) in `src/harness/services/harness_spawner/_blueprint_catalog.py` with bounded `1..6` skill tuples, domain-tuned `query_keywords`, explicit `use_cases` and `out_of_scope` guards, and clean boundaries separating Core 4 from Waves 1 & 2.
- [ ] **1.2 Expand blueprint `limit` defaults and update tests + CLI docs together.** Raise the default `limit` from `12` to `16` across `src/harness/services/harness_spawner/blueprints.py`, `src/harness/commands/spawn.py`, `plugins/agent_orchestration/harness_spawner/main.py`, `plugins/agent_orchestration/harness_spawner/service.py`, `docs/reference/cli.md`, and `tests/test_harness_spawner_blueprints.py` so `harness spawn blueprints --json` returns the full catalog; add Wave 3 unit tests asserting derived `len(CANONICAL_SPECS)`, verified KI seeding (`>= 4` verified KIs per spec, `0` unverified leaked), `BRAIN_SURFACE` validation, and `guards.assert_tree_clean()`.
- [ ] **1.3 Verify standalone script execution for Wave 3 skill runners.** Test Wave 3 skill scripts (`.agents/skills/data-management-architect/scripts/engine.py`, `.agents/skills/garf-reporting-architect/scripts/garf_cli.py`, `.agents/skills/multi-bot-desk-orchestrator/scripts/multi_bot_desk_engine.py`, `.agents/skills/hf-doc-builder-architect/scripts/doc_builder_engine.py`, and any optional add-on scripts including `src/harness/services/gods_eye_view/resolvers.py` if Opt B selected) from an isolated external child directory using Prime's `.venv`, adding Prime-root `plugins` path fallback only where needed.
- [ ] **1.4 Pre-Materialization Format & Static Gate (Wave 2 Digest Lesson).** Run `ruff format` + `ruff format --check`, `ruff check .`, `mypy`, and targeted blueprint unit tests on ALL modified `.py` files **before** starting Track 2 materialization so committed source trees and materialized `tree_sha256` digests match bit-for-bit on the first pass.

## Track 2 — Graph Discovery, Materialization & Digest Reproducibility

- [ ] **2.1 Capture dated Wave 3 selection report.** Run `harness spawn blueprints --json` and commit the dated selection report under `"docs/reports/spawn-wave3-blueprints-selection-<date>.json"` capturing scores, cohesion, bridge counts, skill-count savings, and seeded KIs for the expanded catalog.
- [ ] **2.2 Two-phase `review` -> `run --materialize` for every confirmed Wave 3 harness.** Execute `harness spawn review --blueprint <name> --json` followed by `harness spawn run --blueprint <name> --save-dir D:\GitHub\harnesses\.spawns --materialize D:\GitHub\harnesses\<name> --approve-dock --write-permitted --approve-digest <sha>` for each confirmed Wave 3 harness.
- [ ] **2.3 Prove reproducible `docs_sha256` & `tree_sha256`, portable dock execution, and drift detection.** Re-materialize each Wave 3 harness a second time confirming byte-identical `docs_sha256` and `tree_sha256`; run `dock inspect . --json`, `dock run <name> validate`, `audit-docs`, `icm-audit`, `icm-links`, and `spawn check-drift .` from inside each materialized directory; test tamper-and-restore on `"docs/RUNBOOK.md"` (`drifted: true`, `docs_drifted: true` -> restore -> `drifted: false`).

## Track 3 — 8-Point Cold Walk & Domain-Native Use-Case Proofs

- [ ] **3.1 Execute `harness spawn cold-walk` on every Wave 3 harness.** Run `harness spawn cold-walk <dir> --dock-name <name> --json` on each confirmed Wave 3 harness and record `"docs/reports/spawn-wave3-cold-walk-<date>.md"` separating automated points (`#2, #3, #4, #6, #7`) + underlying gates (`IcmAuditor`, `IcmVerifier`, `validate_harness_docs()`, `check-drift`) from qualitative reader judgments (`#1 <=2 reads`, `#5`, `#8`); leave checkbox `3.1` unticked until explicit human sign-off on `#1, #5, #8`.
- [ ] **3.2 Run one real offline domain-native end-to-end use case per confirmed Wave 3 harness + reviewed `propose`/`adopt`/`reject`.**
  - `harness-data-lakehouse` (`pipeline`): Validate a sample Open Data Contract (ODCS) + data quality profile (`harness data` / `.agents/skills/data-management-architect/scripts/engine.py`), generate a BigQuery anomaly/attribution TVF query (`harness bigquery`) & validate a declarative Garf workflow (`harness garf`), write `"stages/01..03/"` + `check.md`, pass `icm audit` & `icm links`, stage 2 proposals -> adopt 1 into isolated sandbox parent store + reject 1 negative control.
  - `harness-agent-reliability` (`pipeline`): Execute a 3-layer deterministic/eval check (`harness eval`), harness reliability / calibration audit (`harness architect` / `harness calibrate`), and 3-layer uncertainty check (`harness uncertainty`), write `"stages/01..03/"` + `check.md`, pass `icm audit` & `icm links`, stage/adopt/reject 2 proposals.
  - `harness-swarm-orchestrator` (`context_map`): Validate multi-bot serial queues & hop-depth bounds (`multi_bot_desk_engine.py`), simulate an Orca worktree/inbox settlement (`orca_coordinator.py`), and resolve a Borda/majority payoff matrix (`swarm_optimizer_driver.py`), write domain contracts under `"teams/"`, rebuild `"teams/_index.md"`, pass `icm audit` & `icm links`, stage/adopt/reject 2 proposals.
  - `harness-docs-architect` (`system_map`): Audit AST symbol drift (`harness doc` / `doc_ast_inspector.py`), run Diátaxis/OpenAPI lint & MDX builder checks (`doc_linter.py`, `harness doc-builder`), and validate a Diagrams-as-Code graph (`pda_diagram_cli.py`), write findings under `"objects/"` & `"processes/"`, rebuild indexes, pass `icm audit` & `icm links`, stage/adopt/reject 2 proposals.
  - *(If selected in `0.1`:)* Execute offline worked use cases + 2 proposals each for `harness-cloud-k8s` (`record_library`, manifest/RBAC drift audit -> `"records/"` + `"records/_index.md"`), `harness-geospatial-gis` (`system_map`, offline CRS safety gate via `harness gis` + GEV check -> `"objects/"` + `"processes/"`), or `harness-skill-factory` (`pipeline`, Wilson CI `skill_eval_assurance_engine.py` + `harness skills validate` -> `"stages/01..03/"`).
- [ ] **3.3 Commit self-contained Wave 3 adoption evidence.** Archive spawn IDs, reproducible `tree_sha256` & `docs_sha256` digests, target artifact hashes, sandbox proposals/rejections, and KI payloads under `"docs/reports/spawn-wave3-adoptions-<date>.md"` (or adopt into live vault only if `0.4` explicitly chose live promotion), and verify `check-drift` remains `drifted: false` across all Wave 3 harnesses.

## Track 4 — Verification

- [ ] **4.1 Re-run all gates with dated outputs and environment-explicit counts.**
  - Targeted spawner + ICM + joint-query + blueprint + doc-bundle + drift + layer-boundary suites (`pytest`, recording exact `passed`, `skipped`, `failed` counts and `.venv` optional-engine state)
  - Full unit gate (`pytest -m "unit" -q --timeout=60`, restoring `.harness/config.json` if mutated)
  - `ruff check .`, CI-scoped `ruff format --check`, and touched-file `ruff format --check`
  - `mypy src/harness/kernel --ignore-missing-imports` and strict `mypy` on all modified `src/harness` and `plugins` `.py` modules
  - `harness context lint`, `harness knowledge sync --strict`, and `uv lock --check`
- [ ] **4.2 Independent check.** Left unticked until a genuinely separate check lands. The executor must not tick it.
