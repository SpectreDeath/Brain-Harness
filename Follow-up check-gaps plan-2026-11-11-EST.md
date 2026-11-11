# Follow-up check-gaps plan — 2026-11-11 EST

## Context

Two independent checks landed 2026-11-11, both substantially real, both with a tail of small gaps:

- **BH corrections check** (BH `2ba3055`): the REA/MemGraphRAG corrections plan execution is substantially real — parser fixes proven by parent-vs-fix comparison on the real files, dossiers regenerated, GNN item fixed, five-file set 39/39, CI green on all 7 jobs, honesty gate held (5.3 still unticked). Remaining gaps are Tracks 0–3 below.
- **OS audit-fix check** (OS `bb37fac`): the `01d1ca6` audit fixes are substantially real — recursion crash genuinely fixed, suite 105/105 with swipl and 91+14 degraded, coverage 91%, parity 100%, ruff + mypy clean, CI 11/11 green. Remaining gaps are Tracks 4–6 below.

This plan closes those gaps. It does not re-open anything either check confirmed.

## Scope and rules

- **Scope: the gaps listed below only.** BH tracks execute in the Brain-Harness repo; OS tracks execute in the Ontology-Spider repo.
- **Do not touch any independent-check box:** BH corrections 5.3, check-gaps 6.3, consolidated 7.3, Gephi 4.3, Harness2 7.3. All stay unticked. Ticking any of them is a later step's job, never this plan's.
- **Evidence rule:** tick a box only with a commit + test, dated output, or a written decision. A claim in a commit message is not evidence.
- **No new third-party dependencies** without the user's explicit approval.
- **Do not tick the independent-check box (7.3).** A separate check session with its own dated report ticks it. The executor must never tick it.

## Track 0 — BH: give the real-file test signal (corrections 2.2)

The corrections check found the real-file test vacuous in CI: the laptop-path branches are `if Path(r"D:\GitHub\...").exists():` with no `else` and no assertions, so off the laptop the test asserts nothing and passes trivially. The real-file behavior itself verified live (TFLite 7 tensors / 0 junk; H5 4 tensors), but the committed test cannot catch a regression in CI.

- [ ] **0.1 Verify the branch structure.** Read the laptop-path branches in `tests/test_service_rea_toolkit.py` (4 hits at lines 422, 450, 475, 492 — verify each) and confirm which ones are guard-only with no `else` and no assertions. Record the exact lines.
- [ ] **0.2 Give the test signal.** Either vendor small real fixtures (or real-file-derived minimal fixtures) under `tests/` so the test runs everywhere, or add `else`-branch assertions that fail loudly when the real files are absent. The plan's original allowance ("or vendor small real fixtures") still stands — the executor did neither; pick one and do it.
- [ ] **0.3 Prove the test can fail.** Show the test failing when the parser is reverted (or the fixture corrupted) and passing after, in CI conditions — not only on the laptop. Record the run.

## Track 1 — BH: fix the already-stale citation (corrections 4.1)

The corrections plan's 4.1 fix (60-400 → 60-412) landed exactly as instructed, but the same commit grew `model_artifact.py` 412 → 507 lines, so the range no longer covers the parsers claim_002 names. Verified live at HEAD `2ba3055`: `_parse_tflite` 245, `_parse_hdf5` 378, `_parse_protobuf_model` 417, `_parse_tfjs_shard` 454 (file is 507 lines, so the TF.js parser runs 454–507).

- [ ] **1.1 Correct the range.** In `.harness/knowledge/ki_self_20261110_01_rea_managed_serialization_and_memgraphrag_partition_invariant/metadata.json:69`, change `model_artifact.py:60-412` → **60-507**. Check `summary.md` too (it carries no `model_artifact` citation today — record that as a no-op, don't invent one).
- [ ] **1.2 Decide line ranges vs symbol names.** Record a written decision: keep line ranges (and accept re-staling on every parser change) or cite parser symbol names instead. Either is fine; silence is not.

## Track 2 — BH: reconcile the gate figures (corrections 5.2)

The corrections plan's 5.2 evidence cites "pytest -m unit yielded 2,210 passed, 0 failed, 862 deselected in 233.23s" and "Full test run across 3,072 tests yielded 3,071 passed, 1 skipped, 0 failed". The independent check ran the gate twice with identical results: **11 failed / 2132 passed / 69 skipped / 839 deselected**. The 11 failures are exactly the known pre-existing set (transport stderr drain ×2, fetcher bounds/cache/remote-zip ×3, magika ×1, repo-triad ×2, ingestion PyPI/GitLab ×3), and passed is +1 vs `0c97c29`'s 2131 (the new line-bounds test) — so 5.2's substance holds, but "0 failed" does not reproduce on this box. The likely cause is environment (bare `python` on PATH, proxy-mangled fetcher URLs, missing magika model on this box vs the laptop), but that is an inference, not a verified fact.

- [ ] **2.1 Record the reproducible figures per environment.** Run the unit gate live on the author machine and on this box (or CI) and record both: counts, deselected, and duration, each with its environment named.
- [ ] **2.2 Name the 11 pre-existing failures** in the plan's 5.2 evidence (test names, not just counts), and reconcile the "3,072 tests, 0 failed" full-run claim against the gate's 11 — either the full run excludes them (say how) or the figure is corrected.
- [ ] **2.3 Record which environment is authoritative** for the gate (CI, per the bench decision's precedent) and why the figures differ, as a written note in the plan — not as a silent edit to the numbers.

## Track 3 — BH: record the deferred decisions durably

Three decisions from the corrections execution exist only in thin places and will be lost when the plan is archived:

- [ ] **3.1 Move the `rea_toolkit.py` deferral trigger.** The 2,200-LOC trigger for splitting `src/harness/services/rea_toolkit.py` (1,906 lines) exists only in the corrections plan's evidence annotation and the `f0460de` commit message — verified live: grep for `2,200`/`2200` in `src/`, `plugins/`, `docs/`, and the ki_self item returns nothing. Record it in a decision note or a code comment, with the trigger and the reason.
- [ ] **3.2 Record the `managed_pe.py` exemption in the same place.** `plugins/security_and_forensics/rea_managed_runtime/engine/managed_pe.py` (335 lines) was exempted with a written rationale in the test ("pre-existing legacy PE/CLI parser; out of scope for cf0300a") — documented, not silent, but undiscussed in the plan. Record it alongside 3.1 so the second exemption precedent is visible.
- [ ] **3.3 Decide `model_artifact.py` (507 lines).** It grew 412 → 507 in the fix itself; the exemption is recorded, but the trajectory (each precision fix adds ~100 lines) means the next fix pushes it further. Either split it now, or record the exemption with an explicit trajectory note and a re-trigger (e.g. a line count at which the split is revisited).

## Track 4 — OS: fix the memory-test bound (audit-fix gap 1)

The check-gaps plan raised the `test_large_chain_query_memory_bounded` ceiling to 10.0s on a "~8.5s under coverage" measurement. The audit-fix check refuted it live: **15.98s under coverage on this box** (`tests/test_mcp.py:614`, `assertLessEqual(elapsed, 10.0)`; the "~8.5s" comment is at line 612). Plain run passes (3.10s); CI's Coverage job is green on faster runners. This is a slow-box flake, not a CI blocker — but the bound is too tight here and the comment justifying it is wrong.

- [ ] **4.1 Measure under coverage on the author machine and in CI**, and record the numbers (plain run, coverage run, per platform if they differ).
- [ ] **4.2 Either raise the bound to a measured value with the numbers cited, or record a decision that CI is authoritative and the local failure is expected.** Do one, in writing. Fix the "~8.5s" comment either way — it is refuted and must not stand.
- [ ] **4.3 Re-run the coverage suite live after the change** and record the result on this box and in CI.

## Track 5 — OS: lint/type scope honesty (audit-fix gaps 3–4)

- [ ] **5.1 `ruff format --check` flags 31 files** (verified live at `bb37fac`; was 39 before `01d1ca6` — improved, not clean, and format is not enforced by CI, only `ruff check`). Either add format to the Lint & Type Check job and fix the 31 files, or record a written decision that only `ruff check` is enforced. Do one, in writing.
- [ ] **5.2 Correct the mypy scope claim.** CI runs `mypy src` only (workflow: `ruff check src tests`, `mypy src`) and the `01d1ca6` message says "across src and tests". Either expand mypy to tests or correct the claim where it is recorded. Record which was chosen.
- [ ] **5.3 Verify both live after the change** (`ruff check src tests`, `ruff format --check`, `mypy` over whatever scope was decided) and record the outputs.

## Track 6 — OS: record the behavior decisions (audit-fix gap 5)

`docs/decisions.md` (latest section §7.12, line 183) has no new records for this commit's behavior decisions. The plan evidence rule wants them written down.

- [ ] **6.1 Add a new decisions section (§7.13 or next)** recording, at minimum: the iterative validation algorithms (BFS `get_all_superclasses`, iterative Tarjan SCC — why iterative, what semantics were preserved), `Session.retract_assertion` returning bool, the runner `ValueError` for unsupported transport (a behavior change the commit message doesn't mention), and `Explanation` gaining `to_dict` in the unification (superset, not a pure move).
- [ ] **6.2 Confirm or adjust the bench lattice note.** The lattice budget (1500ms, §7.12, CI authoritative) was exceeded on some runs on the review box at both `25e80b8` and `bb37fac` (856–2692ms, 3x run-to-run variance on the shared box; no slowdown attributable to `01d1ca6`). Either leave §7.12 as is with a dated confirmation, or adjust the recorded calibration. Record the choice.

## Track 7 — Verification

- [ ] **7.1 Re-run the BH checks live** (five-file REA+MemGraphRAG set, unit gate, lint + govern + drift) and record exact counts against the baselines (11 failed / 2132 passed / 69 skipped at `2ba3055`).
- [ ] **7.2 Re-run the OS checks live** (suite both modes, coverage run including the memory test, ruff + mypy per the decided scope, parity) and record exact numbers against the `bb37fac` baselines (105 passed / 91+14 degraded, coverage 91%, parity 100%).
- [ ] **7.3 Independent check.** A separate check session with its own dated report verifies Tracks 0–6 against code and tests. Left unticked until that check lands.
