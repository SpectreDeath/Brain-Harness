# Spider Follow-Up Action Log

<!--
## Phase N — <title> (<ISO timestamp>)
- Outcome: PASS | FAIL | PARTIAL
- Key metric(s): ...
- Changes: ...
- Verification: ...
-->

## Phase 0 — Baseline Verification & Action Log Scaffolding (2026-11-18T22:51:30+00:00)
- Outcome: PASS
- Key metric(s): 9/9 experiment input artifacts verified on disk; ruff check . passed; 35/35 baseline pytest passed in 29.13s across 7 test suites.
- Changes: Initialized `experiments/spider_decisions/ACTION_LOG.md`.
- Verification: `ruff check .` (0 errors); `pytest` across `test_repo_ontology_seam.py`, `test_ontology_spider_service.py`, `test_ontology_spider_adapter_fixes.py`, `test_swarm_cisc_integration.py`, `test_uncertainty_cisc_calibration.py`, `test_ui_server.py`, `test_service_storage_vault_integrity.py` (`35 passed`).


## Phase 1 — P0: Vault `references_code` Backfill & Module-ID Edge Normalization (2026-11-18T23:07:30+00:00)
- Outcome: PASS
- Key metric(s): `hop0` macro P/R/F1 `0.4000/0.2500/0.2800 -> 1.0000/1.0000/1.0000`; `hop1` macro P/R/F1 `0.4000/0.3000/0.3333 -> 0.7889/1.0000/0.8564`; gold KIs with zero `references_code` edges `6/13 -> 0/13`; `12/12` approved backfill edges added; `vault.json` refreshed (`666` entities, `1058` assertions, round-trip parity PASS).
- Changes: Added `_canonical_code_module_id()` normalization in `plugins/memory_and_epistemics/ontology_spider/adapter.py`, added 2 contract tests in `tests/test_ontology_spider_adapter_fixes.py`, applied 12 user-approved canonical `references_code` edges across 11 KIs under `.harness/knowledge/`, and refreshed `results/p06/{answer_key.json,metrics.json,summary.md,edge_backfill_proposal.md}` and `results/snapshots/vault.json`.
- Verification: `ruff check .` passed; `ruff format --check experiments/spider_decisions` (`26 files already formatted`); `pytest tests/test_ontology_spider_adapter_fixes.py tests/test_ontology_spider_service.py tests/test_repo_ontology_seam.py tests/test_service_storage_vault_integrity.py tests/test_track4_track5_vault_integrity.py -q` (`32 passed in 15.22s`).

## Phase 2 — P1: Evidence-Grounded CISC Swarm Voting & ASPEST Escalation Band (2026-11-18T23:11:45+00:00)
- Outcome: PASS
- Key metric(s): `p11_grounded_voting.py` via production `ConsensusEngine.evaluate_cisc_consensus(..., ki_verification_map=...)` -> Raw acc `2/12` (`0.1667`), Grounded acc `11/12` (`0.9167`), `9` flips toward correct, `0` flips toward incorrect; ASPEST 3-zone band (`ABSTAIN | ESCALATE_HUMAN | ACCEPT`) exposed on engine, protocol, IoC plugin, and fallback CLI adapter.
- Changes: Added `ki_verification_map` and `provenance_multipliers=(1.0, 0.6, 0.4)` to `src/harness/agent/swarm/consensus.py`; added slotted frozen `ConfidenceBandDecision` + `evaluate_confidence_band()` to `.agents/skills/uncertainty-aware-ai-architect/scripts/uncertainty_guard_engine.py`, `src/harness/services/uncertainty_guard.py`, `plugins/agent_orchestration/uncertainty_guard/{main.py,config.default.yaml}`, and `src/harness/commands/uncertainty/adapter.py`; added contract tests in `tests/test_swarm_cisc_integration.py` and `tests/test_uncertainty_cisc_calibration.py`; updated `experiments/spider_decisions/p11_grounded_voting.py`.
- Verification: `ruff check .` passed; `ruff format --check experiments/spider_decisions` (`26 files already formatted`); `pytest tests/test_swarm_cisc_integration.py tests/test_uncertainty_cisc_calibration.py tests/test_uncertainty_aware_deepened.py tests/test_uncertainty_aware_ai_architect.py tests/test_uncertainty_commands_decomposition.py -q` (`49 passed in 3.29s`).

## Phase 3 — P1: Break `ui <-> commands` Cycle & `services/` Upward Leaks (2026-11-18T23:15:50+00:00)
- Outcome: PASS
- Key metric(s): Zero `ui/services/creator -> commands` imports; `ui <-> commands` and `ui -> creator -> commands -> ui` cycles eliminated; `commands` `in_degree=0` (`blast_radius=0`); Tarjan cyclic SCC shrunk from `11` to `8` units (`commands`, `ui`, and `mcp` exited the SCC; remaining `services <-> kernel` and internal 8-unit SCC deferred to Phase 4).
- Changes: Created `src/harness/services/skill_graph/operations.py`, `src/harness/services/storage/async_bridge.py`, and `tests/test_layer_import_boundaries.py`; repointed `src/harness/ui/server/routes/skills.py`, `src/harness/services/skill_graph/joint_query.py`, `src/harness/services/storage/vault_retrieval.py`, `src/harness/creator/validator/base.py`, and `src/harness/creator/introspection.py` (removing `harness.commands.plugins` imports); refreshed `results/snapshots/brain_harness_src.json` and `results/p09/{refactor_order.json,summary.md}`.
- Verification: `ruff check .` passed; `ruff format --check experiments/spider_decisions` (`26 files already formatted`); `pytest tests/test_layer_import_boundaries.py tests/test_ui_server.py tests/test_ui_dashboard_extended.py tests/test_ui_skill_clustering_seam.py tests/test_commands_skills_decomposition.py tests/test_deepened_skills_commands.py tests/test_service_storage_vault_integrity.py tests/test_skill_graph_service_decomposition.py -q` (`40 passed in 17.11s`).

## Phase 4 — P1 (Arch): Decouple `kernel/runtime/` Composition Root & Verify SCC Reduction (2026-11-18T23:22:30+00:00)
- Outcome: PASS
- Key metric(s): `src/harness` Tarjan cyclic SCC shrunk from `11` (baseline) -> `8` (Phase 3) -> `6` (`creator, events, ingestion, kernel, plugins, services`); `6/12` packages now acyclic (`commands=0`, `ui=1`, `mcp=1`, `runtime=2`, `agent=3`, `bridges=3` blast radius); `services <-> kernel` cycle eliminated (`kernel` `Out-Deg=2`, importing only `events` and `plugins`); zero remaining `harness.kernel.runtime` references.
- Changes: Clean-cut moved all 11 modules + `README.md` from `src/harness/kernel/runtime/` to `src/harness/runtime/` (preserving `RUNTIME_SERVICE_KEY = ServiceKey("kernel.runtime")` and `ServiceContext` / `PluginLifecycle` contracts unchanged); updated `src/harness/kernel/{__init__.py,reconciler.py}`, 9 `src/harness/{commands,ui}` callers, and 17 test files; added `test_kernel_only_imports_events_and_plugins()` in `tests/test_layer_import_boundaries.py`; refreshed `results/snapshots/brain_harness_src.json` and `results/p09/{refactor_order.json,summary.md}`.
- Verification: `ruff check .` passed; `ruff format --check experiments/spider_decisions` (`26 files already formatted`); `pytest` across all 18 affected test files (`127 passed in 116.73s`).

## Phase 5 — P2: Vault Hygiene — Verify Top-8 Central Unverified KIs & Triage 12 Duplicate Pairs (2026-11-18T23:27:35+00:00)
- Outcome: PASS
- Key metric(s): Unverified KIs dropped `78 -> 70` (zero remaining unverified KIs with `in_degree > 0`); duplicate candidate pairs across `377` KIs dropped `12 -> 0` (`intentional_siblings=12`); `vault.json` refreshed (`666` entities, `1070` assertions, round-trip parity PASS).
- Changes: Verified all 8 user-approved top central KIs under `.harness/knowledge/` using live workspace SHA-256 file hashes and verified git commits (`728caf7`, `ddbb658`, `c8f80dd`); added 12 user-approved `related_to` intentional sibling edges across `ki_self_20260826_*`–`20260908_*`; refreshed `results/p02/{unverified_priority.json,unverified_priority.md,duplicate_candidates.json,duplicate_review_sheet.md}` and `results/snapshots/vault.json`.
- Verification: `ruff check .` passed; `pytest tests/test_service_storage_vault_integrity.py tests/test_track4_track5_vault_integrity.py tests/test_ontology_spider_adapter_fixes.py -q` (`15 passed in 9.45s`).

## Phase 7 — P3: Polish `ontology_spider` — Zero Residual False Bridges, Reverse Blast Radius & Uncapped Self-Scan (2026-11-18T23:37:25+00:00)
- Outcome: PASS
- Key metric(s): Residual false bridges dropped `2/34 (0.0588)` -> `0/32 (0.0000)` (`TP=32`, `FP=0`, `unknown_new_bridges=0`); true-bridge recall `0.9697` (`>= 0.95`); `10/10` regression units `PASS` (`structured`); `compute_blast_radius()` added to service/protocol; `max_files_per_unit=None` uncapped non-pruned scan supported.
- Changes: Filtered generic slug stopwords and tag-only matches, added GitHub repo-scope disambiguation and primary-anchor strength check in `plugins/memory_and_epistemics/ontology_spider/repo_adapter.py`; added `compute_blast_radius(model, *, predicate="depends_on_project")` to `src/harness/services/ontology_spider.py`; widened `load_repo_model(..., max_files_per_unit: int | None = 60)` in `experiments/spider_decisions/common.py`; added 4 tests across `tests/test_repo_ontology_seam.py` and `tests/test_ontology_spider_service.py`; refreshed `results/p01/{bridges_after.json,metrics_after.json,summary.md}` and 5 repo snapshots.
- Verification: `p01_bridge_after.py` exited 0 (`FP_rate=0.0000`, `recall=0.9697`, `reg_passed=True`); `ruff check .` passed; `ruff format --check experiments/spider_decisions` (`26 files already formatted`); `pytest tests/test_repo_ontology_seam.py tests/test_ontology_spider_service.py tests/test_ontology_spider_adapter_fixes.py -q` (`24 passed in 10.88s`).

## Phase 8 — P4: Dual-Capped LRU Eviction & Bounded Prefetch for Lazily-Staged Plugin Artifacts (2026-11-19T10:22:02+00:00)
- Outcome: PASS
- Key metric(s): Implemented 4-part Memo Q1 eviction/prefetch design + TTL/broken-venv invalidation (Gap #4) in `src/harness/plugins/artifact_cache/` (`__init__.py`=25, `models.py`=83, `lru.py`=141, `prefetch.py`=82, `offset_index.py`=96 lines; all `<= 200` lines) + `src/harness/plugins/sandbox/venv.py` (`195` lines `<= 200`), preserving Rule 7 lazy startup.
- Changes: Created slotted frozen records (`ArtifactCacheEntry`, `ArtifactOffsetRecord`), thread-safe dual-capped `OrderedDict` LRU with oversized clean skip and TTL/health invalidation (`PluginArtifactCache`), depth-bounded worker (`BoundedArtifactPrefetcher`), and O(1) seek/read binary bundle index (`OffsetManifestIndex`); integrated cache reuse and `is_venv_healthy` check non-invasively into `VenvExecutor` and exported symbols in `src/harness/plugins/__init__.py`; added contract tests in `tests/test_plugin_artifact_cache.py`.
- Verification: `ruff check .` passed (`All checks passed!`); `pytest tests/test_plugin_artifact_cache.py tests/test_sandbox.py tests/test_sandbox_decomposition.py tests/test_track0_sandbox_restrictions.py tests/test_layer_import_boundaries.py -q` (`33 passed in 8.18s`).
