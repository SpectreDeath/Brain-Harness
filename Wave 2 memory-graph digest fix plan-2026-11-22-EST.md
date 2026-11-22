# Wave 2 Memory-Graph Digest Fix Plan — 2026-11-22 EST

The Wave 2 independent check (2026-11-22, BH `34ef570`, verdict: substantially real) found exactly one real discrepancy: the recorded `harness-memory-graph` tree digest does not reproduce from committed code. Re-materializing with the recorded spawn ID gives tree `99ad28e7…`, but the record says `651e3357…`. The other three Wave 2 digests reproduce exactly, and the check ruled out the obvious cause (rebuilding with the pre-`9918136` `okf_engine.py` gives `b1c98118…`, not the recorded value) — so the laptop's memory-graph tree at materialization time differed from committed code in a way not recoverable from the repo. This plan re-materializes from committed code, re-records the authoritative digest, and corrects the one counting nit from the same check. *(Superseded by Track `0.2` on execution: comparing the materialized tree against committed `9918136` isolated the exact cause as 2 blank lines (`9512` vs `9514` bytes) added to [okf\_engine.py](.agents/skills/okf-memory-governor/scripts/okf_engine.py) by pre-commit `ruff format` after Track 2 had materialized `harness-memory-graph`.)*

---

## Evidence Rule

Tick a box only with a commit + a passing test, a dated command output, or a written decision recorded verbatim from the user in chat. Never record a user pick that did not happen in visible conversation. Never tick `3.2 Independent check` yourself.

## Scope Limits

- No new third-party dependencies without the user's explicit approval.
- Do not touch Wave 2 plan box `3.1` (still unticked, awaiting human reader sign-off on cold-walk points #1/#5/#8) or any unticked box in any other plan.
- Do not adopt anything into live `.harness/knowledge/` (vault stays at `382` KIs); this is a record correction, not a re-execution of Wave 2.
- If the re-materialization reveals a code defect (not just a stale record), record it and stop — fixing code is a separate decision, not part of this plan.

---

## Track 0 — Re-materialize from Committed Code

> **User Clarification (2026-11-22 EST):** `"1. Yes — re-materialize fresh first, then refresh the docked copy and registry.json to match 99ad28e7… 2. Yes — record the 2-byte ruff cause in 0.2/2.3, and in 1.3 record both sets of suite numbers as a reconciliation, not a miscount. 3. Commit and push."`

- [x] **0.1 Re-materialize `harness-memory-graph` from committed code.** (`2026-11-22T21:45:49Z` / commit `6bbf3e9` matching committed tree from `34ef570`):
  - Fresh two-phase CLI (`harness spawn review --blueprint harness-memory-graph --json` -> `harness spawn run` into `scratch/mem_graph_fresh_verify`): generated `spawn_harness-memory-graph_36f36687` with live `tree_sha256=99ad28e7dec61b21b68f219be2b5b09f7069a338496a16e9eee58cdf157f7abb` (`docs_sha256=6ee48ff0771a9abc497649faf2776896b9c1e77d14a9d4e80398970969915770` reflecting new `spawn_id` and HEAD commit `6bbf3e9`).
  - Re-materialized with recorded `spawn_id=spawn_harness-memory-graph_f6afb898` and `prime_commit=87a1a2b` into `D:\GitHub\harnesses\harness-memory-graph` (and updated `D:\GitHub\harnesses\.spawns\registry.json`, `fingerprint=375a5f27a904a028`, `tree_sha256=99ad28e7dec61b21b68f219be2b5b09f7069a338496a16e9eee58cdf157f7abb`): reproduced `docs_sha256=d02294cc7b174a1c47a3da6e8c38c3ac6f3e2f8a7d50a784c085cde73c10a9f5` identically across two consecutive runs.
- [x] **0.2 Determine and record why the recorded digest differed.** (`2026-11-22`, verified via `Compare-Object` and `build_blueprint_tree`): Exact cause recovered from the repo and materialized tree — **2 blank lines (`9512` vs `9514` bytes)** added to [okf\_engine.py](.agents/skills/okf-memory-governor/scripts/okf_engine.py) at lines 59 and 118 by pre-commit `ruff format` right before commit `9918136`, *after* Track 2 had already materialized `harness-memory-graph` following Track 1.3's Prime-fallback edit (whereas `87a1a2b` lacked the Track 1.3 edit and gave `b1c98118…`). Hashing the committed tree with the `9512`-byte `okf_engine.py` reproduces `651e3357703ca48e04f213b036d4f9ac3824f669348f961ff0e17e31da6e8ae0` bit-for-bit. Recorded in [Wave 2 domain harness spawning plan-2026-11-22-EST.md](Wave%202%20domain%20harness%20spawning%20plan-2026-11-22-EST.md) (`2.3`).

## Track 1 — Correct the Record

- [x] **1.1 Correct the digest in `docs/reports/spawn-wave2-adoptions-2026-11-22.md`.** (`2026-11-22`, commit `fea8c82`): Replaced `651e3357…` on line 14 of [spawn-wave2-adoptions-2026-11-22.md](docs/reports/spawn-wave2-adoptions-2026-11-22.md) with `99ad28e7dec61b21b68f219be2b5b09f7069a338496a16e9eee58cdf157f7abb`, kept `docs_sha256=d02294cc7b174a1c47a3da6e8c38c3ac6f3e2f8a7d50a784c085cde73c10a9f5` unchanged, and annotated the correction date and independent check (`34ef570`).
- [x] **1.2 Correct the Wave 2 plan 2.3 annotation.** (`2026-11-22`, commit `fea8c82`): Appended the dated digest-reconciliation note to `2.3` in [Wave 2 domain harness spawning plan-2026-11-22-EST.md](Wave%202%20domain%20harness%20spawning%20plan-2026-11-22-EST.md) without rewriting original text; repo-wide grep for `651e3357` confirmed no other live report occurrences (leaving historical `4.2` independent-check notes intact).
- [x] **1.3 Correct the Wave 2 plan 4.1 counting.** (`2026-11-22`, commit `fea8c82`): Appended the two-environment reconciliation sub-bullet under `4.1` in [Wave 2 domain harness spawning plan-2026-11-22-EST.md](Wave%202%20domain%20harness%20spawning%20plan-2026-11-22-EST.md) (recording this workstation's live `97 passed` targeted and `2356 passed, 885 deselected` full-unit runs with installed engines alongside the independent check environment's `88 passed + 9 engine skips` and `2257 passed, 90 skipped, 9 failed, 885 deselected` runs).

## Track 2 — Re-verify the Re-materialized Harness

- [x] **2.1 Re-run the dock and drift gates on the re-materialized `harness-memory-graph`.** (`2026-11-22T21:45:49Z`): Executed `dock inspect . --json`, `dock run harness-memory-graph validate`, `audit-docs`, `icm-audit`, `icm-links`, `spawn check-drift .` (`dock_status=approved`, `drifted=False`, `tree_drifted=False`, `docs_drifted=False`), and `spawn cold-walk . --dock-name harness-memory-graph --json` (`automated_passed=True`, points `#2,#3,#4,#6,#7` `passed`; `#1,#5,#8` `pending_human_judgment`) on BOTH the fresh CLI directory (`spawn_harness-memory-graph_36f36687`) and refreshed `D:\GitHub\harnesses\harness-memory-graph` (`spawn_harness-memory-graph_f6afb898`).

## Track 3 — Verification

- [x] **3.1 Re-run the gates with dated outputs.** (`2026-11-22`, commit `fea8c82`): Targeted 12-file pytest suite (`test_service_joint_query`, `test_service_dock`, `test_command_dock`, `test_layer_import_boundaries`, `test_icm_workspace_architect`, `test_harness_spawner_blueprints`, `test_harness_spawner_doc_bundle`, `test_harness_spawner_materialize`, `test_harness_spawner_e2e`, `test_harness_spawner_plugin_forwarding`, `test_plugin_integration_drift`, `test_cli_content_drift`): `86 passed in 101.62s`; `harness context lint` (`[PASS]`); `harness knowledge sync --strict` (`382 Knowledge Item(s)`); `tests/test_plugin_integration_drift.py -k "documentation_relative_links"` (`1 passed`).
- [x] **3.2 Independent check.** (`2026-11-22`, head `1061156`): Independent check PASSED — verdict **substantially real**, verified live by a genuinely separate check session. Adoptions report now `99ad28e7…` with the correction annotated; 2.3 amended with the exception + cause; 4.1 records both environments explicitly (laptop 97/2356, 0/0; check env 88+9 skips / 2257+90+9 failed); fresh re-materialization (new spawn `36f36687`) + recorded-spawn_id refresh of the docked copy + registry.json to `99ad28e7…`, docs `d02294cc…` reproduced twice; dock/drift/cold-walk gates clean on both dirs. Spot-checks in the check environment: 12-file suite 86 passed (exact), tree at head `99ad28e7…`, vault 382 KIs. CI green on head `1061156` (run 45074209080). Nit: fix plan intro's "cause not recoverable" is now superseded by 0.2's finding. **Ticked on the user's word, not by the executor.**
