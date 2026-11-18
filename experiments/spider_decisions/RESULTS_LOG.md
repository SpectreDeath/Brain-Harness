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

## Phase 5 — Entropy-Driven Question Selection (2026-11-18T16:11:29+00:00)
- Outcome: PASS
- Key metric(s): On top-20 grm candidates: entropy policy mean=1.80 questions (max=2, 100.0% unique); random policy mean=3.65 questions (max=7, 100.0% unique).
- Finding(s): Shannon/Laya classification_score halved average narrowing questions (1.80 vs 3.65) and cut worst-case depth from 7 to 2 with 20/20 unique identification.
- Follow-ups: Run Phase 6.1 draft answer key for Brain Harness module KI retrieval.

## Phase 6 — KI Retrieval for a Code Change (2026-11-18T16:13:54+00:00)
- Outcome: PASS
- Key metric(s): Macro P/R/F1 across 5 modules -> hop0: 0.4000/0.2500/0.2800; hop1: 0.4000/0.3000/0.3333; grep_baseline: 0.8476/0.9500/0.8769.
- Finding(s): 6/13 unique gold KIs have zero references_code edges, and others target file/engine identifiers (src_*_py, ontology_spider_engine) or use applicable_to rather than canonical dotted module ids; proposed 12 backfill edges without mutating vault.
- Follow-ups: Run Phase 7 evidence gathering and design-choice arbitration memos.

## Phase 7 — Design-Choice Arbitration Memos (2026-11-18T16:17:14+00:00)
- Outcome: PASS
- Key metric(s): memo_q1 cited 11 valid KIs, 87.5% (7/8) cited claims verified, 2 conflicts/2 gaps; memo_q2 cited 4 valid KIs, 100.0% (8/8) cited claims verified, 2 conflicts/1 gap; human_ratings recorded (unrated/proceed).
- Finding(s): Unverified claims (ki_self_20260922_02, ki-hf-datasets-arrow-streaming) and warm-load vs lazy-staging conflicts were surfaced cleanly; Q2 missed ki_njoku_uncertainty_aware_systems via graph retrieval because references_code is absent.
- Follow-ups: Generate Phase 8 Plugin vs KI-only vs Skip ground-truth sheet (8.1-8.2 checkpoint).

## Phase 8 — Plugin vs KI-Only vs Skip Classifier (2026-11-18T16:59:38+00:00)
- Outcome: PASS (exploratory finding)
- Key metric(s): 2/14 accuracy (0.1429); Confusion matrix: plugin->{plugin:2, ki_only:7, skip:1}, ki_only->{plugin:2, ki_only:0, skip:2}.
- Finding(s): Most informative misclassifications: (1) Non-Python/TS/Go repos (adk-web, magika, earthengine-api, styleguide) were built as plugins despite primary_language != python; (2) harness2 & tunix-main missed has_tests under 60-file portfolio cap; (3) airllm & grm/imp look Python+tested+packaged yet were kept ki_only based on architectural domain rather than syntax.
- Follow-ups: Run Phase 9 Brain Harness refactor ordering (9.1-9.4).

## Phase 9 — Brain Harness Refactor Ordering (2026-11-18T18:04:23+00:00)
- Outcome: PASS
- Key metric(s): Ordered all 11 src/harness units: commands, ui, mcp, agent, creator, bridges, services, plugins, ingestion, kernel, events; 1 spider cycle (ui -> commands -> ui); 11-unit Tarjan SCC (all blast_radius=10); 6/10 hotspot KI overlap (commands, mcp, agent, creator, services, plugins).
- Finding(s): ui <-> commands cycle originates in ui/server/routes/skills.py; 11-unit Tarjan SCC is caused by kernel/runtime/* composition-root imports (defaults.py, factory.py, services.py, tools.py, plugins.py); full AST scan also found 2 upward leaks in services/ (skill_graph/joint_query.py -> commands, storage/vault_retrieval.py -> creator) missed by the 60-file snapshot cap. Verdict: sensible (8.5/10).
- Follow-ups: Run Phase 10 Steps 10.1-10.2 skill routing recipe and 20-task draft sheet for Checkpoint 10.3.

## Phase 10 — Spider-Assisted Skill Routing vs route_intent (2026-11-18T18:08:25+00:00)
- Outcome: PASS
- Key metric(s): Baseline route_intent Hit@1=19/20 (95.0%), Hit@3=19/20 (95.0%); Spider-assisted Hit@1=2/20 (10.0%), Hit@3=4/20 (20.0%); Hybrid rerank top-3 Hit@1=13/20 (65.0%), Hit@3=19/20 (95.0%); Hybrid union Hit@1=8/20 (40.0%), Hit@3=11/20 (55.0%).
- Finding(s): Unweighted +1 per supporting KI acts as a hub attractor toward broad tags (ai-agent-engineer, epistemic-memory-lifecycle, architecture-deepening-workflow) and hurts calibrated route_intent@1 (95%->65%); Baseline only missed task #2 (ontology-spider -> research).
- Follow-ups: Run Phase 11 evidence-grounded swarm voting.

## Phase 11 — Evidence-Grounded Swarm Voting (2026-11-18T18:09:30+00:00)
- Outcome: PASS
- Key metric(s): Raw CISC accuracy=2/12 (0.1667); Evidence-grounded accuracy=11/12 (0.9167); total_flips=9 (flips_toward_correct=9, flips_toward_incorrect=0).
- Finding(s): Multiplying CISC confidence by vault isnad_verified status (1.0/0.6/0.4) corrected 9 unverified-majority disputes with zero regressions while keeping 4-to-1 overwhelming plurality bounded (dispute #12).
- Follow-ups: Collect all headline metrics and author final Phase 12 REPORT.md.
