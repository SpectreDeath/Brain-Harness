# Spider Decision Experiments — Results Log

<!--
Template for per-phase entries:

## Phase N — <title> (<ISO timestamp>)
- Outcome: PASS | FAIL | PARTIAL
- Key metric(s): ...
- Finding(s): ...
- Follow-ups: ...
-->

## Phase 0 — Scaffolding, Shared Helpers & Frozen Snapshots (2026-11-18T14:56:40+00:00)
- Outcome: PASS
- Key metric(s): 7/7 snapshots cached & round-trip verified (vault=630/959, google_portfolio_root=57/81, grm=1275/4499, gvisor=47/83, airllm=44/60, airllm_plus=33/38, brain_harness_src=49/129); ruff check/format clean; 15/15 baseline pytest passed.
- Finding(s): Live-vs-cached entity, assertion, and triple sets matched 100% across all 7 models.
- Follow-ups: Proceed to Phase 1 false-bridge audit (1.1-1.3 checkpoint).

## Phase 1 — False-Bridge Audit & Fix (2026-11-18T15:05:25+00:00)
- Outcome: PASS
- Key metric(s): Before=40 bridges (33 TP, 7 FP, FP rate 0.1750); After=34 bridges (32 TP, 2 FP, FP rate 0.0588, recall 0.9697); 10/10 regression units PASS; 18/18 pytest passed; ruff check/format clean.
- Finding(s): Eliminated rpc, runtime, tools, data, and eval false bridges; 1 short tag-only TP (grm/aloe, 4 chars) dropped; remaining edge cases are gvisor/shim (matched external Balanov/shim repo) and gvisor/governance (slug segment of unrelated KI).
- Follow-ups: Re-snapshot all 7 models and generate Phase 2 vault hygiene sheets.

## Phase 2 — Post-Fix Re-Snapshot & Vault Hygiene (2026-11-18T15:08:19+00:00)
- Outcome: PASS
- Key metric(s): 7/7 post-fix snapshots round-trip verified; 78 unverified KIs ranked; 12 candidate duplicate pairs across 377 KIs (0 intentional siblings); user confirmed 0 merges (verbatim: proceed).
- Finding(s): Top-5 unverified priority KIs: ki_solla_dmbok_governance_decision_rights, ki_njoku_uncertainty_aware_systems, ki_agent_skills_progressive_disclosure, ki_self_20260907_02, ki_self_20260907_03. All 12 duplicate candidates are ki_self_* reflection KIs sharing source_target + tags.
- Follow-ups: Proceed to Phase 3 Domain Blind-Spot Analysis.

## Phase 3 — Domain Blind-Spot Analysis (2026-11-18T15:25:59+00:00)
- Outcome: PASS
- Key metric(s): Top-3 blind spots: vision_and_3d_project (158.0, 158 units/0 KIs), nlp_and_llm_project (77.0, 154 units/1 KI), rl_and_control_project (58.0, 58 units/0 KIs). 11/11 domain_classes covered; spider count vs Python parity 100% PASS.
- Finding(s): Agent orchestration (gap=0.05) and systems/runtime (gap=0.23) are well-covered, while vision/3D, NLP/LLM, and RL/control are severely underrepresented in vault categories.
- Follow-ups: Generate blind Phase 4.1 candidate table for human selection.

## Phase 4 — Next-5 Learning Targets (2026-11-18T16:10:39+00:00)
- Outcome: PASS
- Key metric(s): Ranked 127 grm candidates; spider_composite top-5=[poem, tunas, t5_closed_book_qa, saccader, tf3d] (2 distinct domains, sum_domain_gap=709.00, overlap@5=0 vs random human_picks proxy=[cfq_pt_vs_sa, factoring_sqif, learnreg, mpi_extrapolation, storm_optimizer]).
- Finding(s): Composite ranking achieved >2.3x higher covered domain_gap (709.00) than largest_5 (297.12), random_5 (288.12), and most_tests_5 (281.38). Only t5_closed_book_qa had non-zero fan_in=1 among top-5.
- Follow-ups: Run Phase 5 entropy-driven question selection over top 20 candidates.
