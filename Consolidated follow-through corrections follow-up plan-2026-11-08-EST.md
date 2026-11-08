# Consolidated follow-through corrections follow-up plan — 2026-11-08 EST

**Scope:** Close the remaining gaps from the independent check of the corrections plan execution (BH `b94237d` / OS `113c5de`, checked 2026-11-08). The check verdict was: substantially real, Tracks 0–5 verify live, but the verification itself is not independent.

**Heads at plan time:** Brain-Harness `b94237d`, Ontology-Spider `113c5de`. Both CI green.

**Evidence rule (unchanged):** tick a box only with a commit SHA + test output, dated output, or a written decision recorded in the repo. A tick without its evidence is not a tick.

**Guardrails:**
- No new third-party dependencies without the user's explicit approval.
- No atomic plan+execution commit: a redraft of this plan and its execution land in separate commits.
- The independent check is never dropped and never self-asserted. The check must be a separate commit, by a different agent/session than the executor, with its own dated report. An executor claiming its own check does not close anything.
- OS tracks execute in the Ontology-Spider repo; BH tracks execute in the Brain-Harness repo. Cross-repo citations must name the repo and the SHA.

## Track 0 — Honesty gate: undo the self-asserted verdicts

- [ ] **0.1** Untick corrections-plan 6.3 back to pending (`[ ]`) in `Consolidated follow-through corrections plan-2026-11-08-EST.md`. Record in the plan file that the `b94237d` "Track 6.3 Independent Check Report" (claiming "Verdict: PASSED (ALL TRACKS 0–6 VERIFIED AND CLOSED)") is not accepted as an independent check: same author as the work, plan-files-only commit (66 insertions, 25 deletions), no code, no tests, no dated output artifact.
- [ ] **0.2** Untick consolidated-plan 7.3 back to pending in `Consolidated follow-through plan-2026-11-08-EST.md` (currently line 136, `[x] **7.3** Independent check box: **Verdict: PASSED**`). Record that the re-tick in `b94237d` rested on the self-asserted 6.3 and is withdrawn.
- [ ] **0.3** Untick Gephi follow-up plan 4.3 back to pending in `Gephi follow-up fixes plan-2026-11-07-EST.md` (currently line 40, `[x] **4.3** … **Verdict: PASSED**`), on the same basis as 0.2.
- [ ] **0.4** Verify by reading all three plan files at the new head that 6.3, 7.3, and 4.3 are unticked, and commit the unticks as a docs-only commit that changes no other box.

## Track 1 — Fix the evidence citations

- [ ] **1.1** Re-cite the eight boxes that cite commit `a8ecf26` (corrections plan 0.1, 3.1, 3.2, 3.3, 3.4, 5.1, 5.2, 5.3) to the real commit `ddc94ab` (Ontology-Spider), where the work was verified by diff. Verify each new citation resolves: `git cat-file -t ddc94ab` in the OS clone. `a8ecf26` is not a valid object in either repo (`git cat-file -t a8ecf26` → "fatal: Not a valid object name"); no box may cite it after this track.
- [ ] **1.2** Fix 5.4's commit citations: the Windows installer fix is `ddc94ab` / `ade6f78` / `96ebb1f`, not `27c3361` and `113c5de` (those two touched only `tests/test_mcp.py`, plus a blank line in `__main__.py`). Re-cite and verify each SHA resolves.
- [ ] **1.3** Fix the 6.3 report's unqualified "318 miss" coverage figure: qualify it as the Windows figure, with the Linux figure (3,566 statements, 322 missed, 91%, measured live 2026-11-08) alongside it.
- [ ] **1.4** Fix the stale `mcp/server.py` line numbers in the 5.1 disposition (401/441 → 396/431, verified live) and correct 2.3's "0 hits for '11'" wording — it is literally false ("Rule 11" hits exist); reword to state the intent (no remaining "11 clusters" / "ClusterEntry" references).
- [ ] **1.5** Verify by grep that no `a8ecf26` reference remains in any plan file, and commit the citation fixes.

## Track 2 — Fix the 5.3 OOM kink (Ontology-Spider)

Background (verified live 2026-11-08): the recorded `--timeout 3` run reproduces (3.001s, `QueryTimeoutError`). The default-timeout run on the 10,000-node chain never returns — OOM-killed (exit 137, ~85s, 6 GB box). Root cause in code: `python_backend.py:144-182` stores the full path + full assertion list per answer, and `engine.py:254-263` materializes `"provenance": [asrt.to_dict() …]` for all of them (~50M entries for a 10k chain). The timeout tracker (`python_backend.py:21-39`, `step()` at :155-160) guards only the reasoner phase, not the formatting phase.

- [ ] **2.1** Reproduce the OOM on a recorded machine: run the default-timeout 10,000-node chain query, record wall time, exit code, and peak memory (e.g. `/usr/bin/time -v` or equivalent). Record the numbers in the plan file or a note; do not carry the author's 4.467s figure as if it were reproducible everywhere.
- [ ] **2.2** Fix the kink: bound the per-answer path + provenance materialization (cap, stream, or summarize — record the chosen approach as a written decision before implementing), and apply the timeout/deadline to the formatting phase so a run cannot outlive its timeout in unbounded formatting work.
- [ ] **2.3** Re-run both 5.3 runs after the fix — `--timeout 3` and default timeout — on the 10,000-node chain, recording wall time, exit code, and peak memory for each. Both must terminate within their timeout + a stated margin, without OOM.
- [ ] **2.4** Fix the `docs/mcp.md` §2 off-by-one: a 10,000-node chain has 9,999 ancestors and 9,999 assertions, not 10,000. Correct the text ("10,000 assertions … returning all 10,000 ancestors").
- [ ] **2.5** Add a regression test that exercises the fixed behaviour (large chain, default timeout, bounded memory or bounded answer count) and confirm it passes in both modes (with and without swipl).

## Track 3 — Prolog timeout at the MCP layer (Ontology-Spider)

Background: `test_mcp_prolog_backend_query_caps` (`tests/test_mcp.py:522`) passes but tests only the inference cap (`max_inferences=2` → "Prolog query exceeded inference cap of 2 steps"; succeeds at 100,000). `timeout_seconds=5.0` is passed but never exercised. The mocked-clock timeout test (`113c5de`, `time.monotonic` mocked to `[100.0] + [200.0]*50`, `timeout_seconds=1.0`) proves plumbing (the tracker consults the clock; deadline exceeded → error), not wall-clock timing.

- [ ] **3.1** Add a real wall-clock timeout test at the MCP layer against the Prolog backend: a slow query with a small `--timeout` that must terminate with a timeout error in measured wall time. Record the measured wall time in the test output or a note.
- [ ] **3.2** Document the mocked-clock test as plumbing-only in a code comment or the test docstring: it cannot catch a real timing regression. The wall-clock proof is the new test in 3.1 (plus the live 3.001s run recorded in the check).
- [ ] **3.3** Confirm the existing Prolog cap test still passes, and the new timeout test passes in CI (not only locally).

## Track 4 — Bench calibration (Ontology-Spider)

Background: `python -m ontology_spider.harness bench --budget …` exits 2 on this box — "Budget exceeded for lattice_10k_validate_ms: 1126.36ms > 1000.0ms" — while passing in CI. Budgets are calibrated to the author's machine (Windows 11 Pro, AMD Ryzen 9, Python 3.13.0, SWI-Prolog 9.2.x, per `docs/harness.md`). The 6.1 "Benchmark suite within budgets" claim is environment-dependent.

- [ ] **4.1** Record the machine dependence explicitly: calibration machine named in `bench_budgets.json` or `docs/harness.md` alongside the budgets, and a statement that bench is CI-gated, not a local gate, if that is the decision.
- [ ] **4.2** Decide and record: either widen the budgets with a stated justification (and the new values), or mark bench as CI-only for the pass/fail gate. Do not silently widen a budget to make a red run green.
- [ ] **4.3** Re-run bench after the decision on the author's machine and on CI, and record both results with the machine named.

## Track 5 — Intermediate CI failures (Ontology-Spider)

Background: CI failed on `96ebb1f` (run 42517758361) and on `27c3361` (run 42518002144) before succeeding at `113c5de` (11/11 jobs green, run 42518342625). The reasons were never verified — the check's API calls were rate-limited (HTTP 403) and not retried.

- [ ] **5.1** Read the job logs for runs 42517758361 (`96ebb1f`) and 42518002144 (`27c3361`) and record the failing job(s) and step-level cause for each, with the run IDs cited.
- [ ] **5.2** If either failure was the same Windows installer issue the `96ebb1f` fix addressed, say so with the log evidence. If the cause is unknown or the logs are no longer available, say so honestly — do not assert a cause without the log.
- [ ] **5.3** Also record the step-level evidence for the OS CI failure on `7970a12` (run 42502698245: 7/11 succeeded, 4 Windows jobs failed; the choco `swi-prolog.org` 502/503 cause was executor-asserted, not independently verified). Same rule: log evidence or an honest "unverified".

## Track 6 — Verification

- [ ] **6.1** OS suite green in both modes, stated exactly: with swipl (101 passed at `113c5de`) and genuine degraded mode (88 passed + 13 skipped, including the new Prolog cap test) — not "101 unit tests in both modes". Coverage ≥ 90% (state statements/missed and the machine). Bench per the Track 4 decision. Parity 100% (5/5). New Prolog timeout test (3.1) and OOM regression test (2.5) passing.
- [ ] **6.2** BH `context lint` + `context govern` pass, drift tests green, unit gate no worse than the 11 pre-existing failures, CI green on both repos with job counts bound to SHAs.
- [ ] **6.3** Independent-check box: left unticked until a genuinely separate check of this plan's execution lands (separate commit, different agent/session, dated report). This box is never ticked by the executor.
