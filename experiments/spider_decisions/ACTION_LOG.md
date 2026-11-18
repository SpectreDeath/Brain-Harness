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
