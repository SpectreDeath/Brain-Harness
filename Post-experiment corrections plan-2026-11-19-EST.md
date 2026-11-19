# Post-experiment corrections plan — 2026-11-19 EST

## Context

Two independent checks landed 2026-11-18/19 on Brain-Harness head `80cc08f`
(35 commits since `1340981`) and Ontology-Spider head `3dcd34f` (no new
commits). Both repos' CI is green at head. The experiment series and its
follow-up are mostly real work — but the checks found one integrity failure,
one false acceptance stamp, one unwired feature, and several records that
overstate what happened.

Verified findings this plan fixes (all checked live against the code):

- **Phase 4 picks are not from the shortlists the user was given in chat.**
  `results/p04/human_picks.json` records `dp_sgd_clipping, smart_eval,
  perturbations, norml, psycholab` with `selection_mode: human_shortlists`,
  one per domain. But the re-run (`eef2f6a`, committed 16:45 EST) regenerated
  its own lists — 5 single-domain lists of 8, pure random draw, no top-score
  seeding — 50 minutes *before* the chat shortlists were delivered (17:35
  EST). Only 2 of 5 picks (`perturbations`, `norml`) appear in the chat
  lists. Provenance (user vs agent on the laptop) is unevidenced in-repo.
  The comparison ceiling was 2, not 5 (only `poem` + `saccader` were ever
  available to pick) and is nowhere stated. The offered one-line plan fix
  was never applied (`PLAN.md:327` still says "5 shortlists, one per
  domain") and 4 domains got no shortlist at all.
- **Phase 5 stamped 12 wrong SHA-256 hashes inside VERIFIED claims
  (`757bc2e`).** Root cause proven live: the hashes were computed over the
  laptop's CRLF working-tree bytes, while git stores LF (e.g.
  `skill_graph/__init__.py`: claimed `4b08d0ac…` = CRLF hash, live LF hash
  `8634a7ad…`). 10 of 22 local-file hash claims are right; 12 are wrong.
  Worse, **no hash verification code exists anywhere**:
  `_claim_is_verified` (`adapter.py:69-88`) returns `True` for any
  non-empty hash string / `verified: true` / status `"verified"` without
  recomputing anything. Phase 5 added no verification code.
- **Phase 1 acceptance was never met, and the log says PASS.**
  At the phase-1 commit, hop1 macro was F1 0.8564 / precision 0.7889
  against bars F1 ≥0.85 / precision ≥0.90 — precision failed, yet
  ACTION_LOG stamps PASS. At head it regressed to F1 0.8209 / P 0.7527
  (extra canonical edges inflate hop1 retrieved counts) and nothing flagged
  it.
- **A cycle remains after phases 3+4.** `refactor_order.json` lists
  `spider_cycle_violations: ["services -> creator -> services"]` at head —
  the "0 violations" acceptance was never met. The boundary test
  grandfathers the exact edge via `ALLOWED_SERVICES_TO_CREATOR`
  (`reflection_worker.py:16` imports `harness.creator.reflection`).
  Phase 4 also ships a breaking import change (`harness.kernel.runtime`
  moved, no compat shim) and kernel/events are still inside the 6-unit SCC.
- **Phase 8's cache is never wired in.** The dual-capped LRU and bounded
  prefetcher are real code with passing tests, but `factory.py:139`
  constructs `VenvExecutor` without `artifact_cache`, no production call
  site passes one, and `BoundedArtifactPrefetcher` is never instantiated
  outside its test — zero runtime benefit.
- **Phase 2's grounding has no live caller.** `ki_verification_map`
  plumbing is real at all four ASPEST layers, but the only non-test caller
  is the experiment script itself; the 11/12 evaluation is still
  synthetic-dispute based.
- **`uv.lock` was never regenerated** after 11 dependabot bumps: mypy
  locked 1.15.0 vs `==2.4.1`, fastapi locked 0.141.1 vs `>=0.163.0`,
  watchdog locked 6.0.0 vs `>=7.1.0`. CI does not catch it (pip install
  ignores `uv.lock`).
- **README drift the gate doesn't catch:** entrypoints 690 vs 696 live,
  KIs 362 vs 382 live.
- **Validators test still unguarded** (`test_skill_and_plugin_validators_pass`
  has no `skip_if_no_engine`; fails on any checkout without the engine —
  moot in CI since `14c460f`, still the robust fix).
- **OS `max_results` is a parity hole** (`3dcd34f`): Prolog raises on
  exceed, Python silently ignores it (zero `max_results` in
  `python_backend.py`), MCP doesn't expose it. OS doc drift untouched and
  growing ("105 unit tests" vs 117, "16 tools" vs 19, "6 mutating" vs 9,
  dead `server.py` refs, §7.8/§7.13 stale). Rank 7 decision and the 5.5
  superseding decision still unrecorded.

This plan lives in the Brain-Harness root; its OS tracks execute in the
Ontology-Spider repo. **It supersedes the staged (never pushed)
`Cross-repo corrections plan-2026-11-14-EST.md`** — that plan's live items
(validators guard, unit markers, 5.5, OS doc drift, Rank 7 gate) are
absorbed here; do not push the staged file. The staged triad forge
citations plan stays separate (different scope, still unpushed).

## Scope and rules

- **Scope: the fixes below only.** Do not touch spawn provenance 0.3/3.3,
  BH corrections 5.3, check-gaps 6.3, consolidated 7.3, Gephi 4.3,
  Harness2 7.3, or follow-up check-gaps 7.3. Those are separate jobs,
  still pending.
- **Track 7.3 is a decision gate, not an execution track.** The Rank 7
  decision belongs to the user (the `.dialog` grammar is the joint their
  workflow reserves for the frontier model). The executor must obtain the
  decision in chat and record it — it must not assume ratification.
- **Evidence rule:** tick a box only with a commit + test, dated output,
  or a written decision. A claim in a commit message is not evidence.
  Verify every corrected line number, count, and hash against the live
  code — do not copy a number from this plan or from the check without
  re-verifying it.
- **No new third-party dependencies** without the user's explicit approval.
- **Do not tick the independent-check box (8.3).** A separate check session
  with its own dated report ticks it. The executor must never tick it.

## Track 0 — Phase 4 record correction (the picks)

- [ ] **0.1 State the ceiling.** In `results/p04/comparison.md` and
  `REPORT.md` §2.2, state that the maximum possible overlap was **2**,
  not 5 (only `poem` and `saccader` of the composite top-5 were in the
  regenerated shortlists; `tunas`, `t5_closed_book_qa`, `tf3d` were never
  available to pick). The "overlap@5 = 0" figures stay as measured, but
  must be presented with the ceiling next to them. Also qualify the
  "composite covers >2.0x more gap" framing: the human picks were
  constrained to 1-per-domain while the composite concentrates 4/5 in
  vision, so the gap-sum comparison structurally favors the composite.
- [ ] **0.2 Record the provenance honestly.** In the same files, record
  that the picks came from laptop-generated 8-item single-domain
  shortlists (seed `2026111841`, pure random draw), **not** from the
  shortlists delivered in chat (5 themed lists of 6, top-2 seeded), and
  that 4 domains (graph, privacy, science, speech) got no shortlist.
  Do not claim the chat lists were used. If the user confirms in chat
  that they personally made these 5 picks on the laptop, record their
  words and the date; if they do not, record the provenance as
  "unconfirmed — no transcript in-repo".
- [ ] **0.3 Apply the one-line plan fix.** Rewrite `PLAN.md` step 4.1
  (line 327): "draw 5 themed shortlists (one per domain group, together
  covering all domains) of 5–8 candidates each — the 2 highest-scored
  per group plus a seeded random draw from the rest, alphabetical, no
  scores shown." This fixes both the "one per domain" wording (there
  are 9 domains) and the partition impossibility (127 candidates cannot
  be partitioned into 5 lists of 5–8). Record the amendment with the
  date; ticks stay 81/81.

## Track 1 — Phase 5 hash integrity (the integrity failure)

- [ ] **1.1 Re-stamp the 12 wrong hashes from git-blob bytes.** The 12
  claims are in the 13 KIs `757bc2e` touched (verified list from the
  check: `ki_20261014_70_cycle_deepening_corpus`,
  `ki_agent_skills_progressive_disclosure` (2), `ki_google_repos_bridge`
  (7), `ki_self_20260907_02`, `ki_self_20260907_03` — re-verify the list
  live, do not trust this count blindly). Recompute each hash over the
  file's git-blob bytes (LF as stored in git) and record the corrected
  values with the date and the method.
- [ ] **1.2 Fix the stamping rule.** Wherever hashes are stamped (the
  stamping script/workflow that produced the CRLF hashes), change it to
  hash git-blob bytes — or normalize line endings to LF before hashing
  — and document the rule in the code and in the KI's provenance note.
  Never hash raw working-tree bytes again: a hash must be reproducible
  from the repo alone.
- [ ] **1.3 Add a real recomputing verifier.** Change `_claim_is_verified`
  (or the vault-integrity gate) so a hash claim is verified only if the
  hash recomputes from the file's git-blob bytes and matches. A non-empty
  hash string, `verified: true`, or status `"verified"` alone must no
  longer count as verified. Add a regression test that stamps a wrong
  hash and asserts the verifier rejects it, and one that stamps the
  CRLF hash of an LF file and asserts rejection.
- [ ] **1.4 Re-run the gate and all hash-bearing claims.** Run the
  vault-integrity gate live and recompute all 38 hash-bearing claims in
  the touched KIs (22 local + 16 upstream); record the counts — all must
  match, with zero `sha256_hash: null` inside a VERIFIED claim left
  unflagged (flag the pre-existing HTML-artifact nulls rather than
  silently passing them).

## Track 2 — Phase 1 acceptance, regression, and re-runnability

- [ ] **2.1 Correct the false PASS.** In `ACTION_LOG.md`, annotate the
  Phase 1 entry: precision 0.7889 was below the 0.90 bar at the phase-1
  commit, so the acceptance was **not met**; the PASS stamp was wrong.
  Do not rewrite history by deleting the stamp — annotate it as
  corrected with the date.
- [ ] **2.2 Fix or re-baseline the hop1 regression.** Investigate why
  hop1 regressed to F1 0.8209 / precision 0.7527 at head (suspect: extra
  canonical edges inflate hop1 retrieved counts). Either fix the cause
  and restore F1 ≥0.85 / precision ≥0.90, or record a new, justified
  baseline with the reason — do not leave the bars unmet and unmentioned.
  Re-run the retrieval eval live and record the numbers.
- [ ] **2.3 Prove the adapter tests with the engine.** Run the 3 tests
  in `tests/test_ontology_spider_adapter_fixes.py` with the engine
  installed (as CI does) and record pass/fail — they must pass, not
  skip, in the verification run.
- [ ] **2.4 Make the experiment scripts portable.** `common.py:14-19`
  hardcodes `d:\GitHub\projects\Brain Harness`; make the paths
  repo-root-relative (or env-var overridable) so `p01_bridge_after.py`
  and `p00_roundtrip_check.py` run on any checkout. Re-run both on a
  fresh checkout and record the results — the FP=0 claim and the 100%
  round-trip parity claim must be re-executed, not just re-read from
  committed JSON.

## Track 3 — The remaining cycle and the breaking move

- [ ] **3.1 Break the remaining cycle.** Remove the
  `services -> creator -> services` edge so `refactor_order.json` lists
  `spider_cycle_violations: []` — i.e. remove or reroute the
  `reflection_worker.py:16` import of `harness.creator.reflection`
  (move the shared helper to a lower layer, as Phase 3 did for the other
  two leaks). If it cannot be removed, record the blocker honestly in
  the plan and in `refactor_order.json` — do not claim 0 while 1 remains.
- [ ] **3.2 Settle the grandfathering.** Either remove the
  `ALLOWED_SERVICES_TO_CREATOR` exception in
  `test_services_never_imports_commands_or_creator` (once 3.1 lands) or
  record it as an explicit, dated exception in the test and in
  `ACTION_PLAN.md`, with a named trigger for its removal. A test comment
  alone is not a decision record.
- [ ] **3.3 Settle the breaking import.** Add a compat shim re-exporting
  `HarnessRuntime` from `harness.kernel.runtime` (with a deprecation
  note), or record the removal as an intentional, dated breaking change
  with a migration note in the release docs. External importers must not
  fail silently — one of the two, decided and recorded.
- [ ] **3.4 Re-run the boundaries and the cycle check.** Run the boundary
  tests live and regenerate `refactor_order.json`; record the violation
  list (target: empty) and the SCC size. Kernel/events remaining inside
  the SCC must be recorded as a known limitation, not hidden.

## Track 4 — Grounding and wiring (Phases 2 + 8)

- [ ] **4.1 Give CISC a live caller.** Wire `ki_verification_map` into
  at least one production path (e.g. swarm voting via
  `WeightedMajorityStrategy.evaluate()` / `_evaluate_cisc()`), with a
  live test proving a verified KI outranks an unverified one. If the
  wiring is deferred, record it as deferred-by-design with a named
  trigger — and stop citing the synthetic-dispute 11/12 as production
  grounding in any doc or summary.
- [ ] **4.2 Wire the cache into production.** Pass `artifact_cache` at
  `factory.py:139` (`VenvExecutor` construction) and instantiate
  `BoundedArtifactPrefetcher` on at least one lazy-plugin path. Prove it
  with a live smoke check that the cache is consulted on a lazy venv
  start (not just unit tests). Record the paths wired.
- [ ] **4.3 Fix the blocking submit.** `BoundedArtifactPrefetcher.submit(
  timeout=None)` blocks forever when the queue is full — give it a
  finite default timeout (or document the blocking behavior as
  intentional with the reason). Add a test that the queue-full case
  returns/errors instead of hanging.

## Track 5 — Lockfile, drift, and test hygiene

- [ ] **5.1 Regenerate `uv.lock`.** Run `uv lock` and verify mypy
  2.4.1, fastapi ≥0.163.0, and watchdog ≥7.1.0 all resolve in the lock.
  Add a CI step (`uv lock --check`) so a stale lock fails the build, or
  record why that step is not added. Verify the step (or the reason) on
  the fix commit's CI run.
- [ ] **5.2 Fix the counts and gate them.** README/USER_MANUAL:
  entrypoints 690 → **696**, KIs 362 → **382** (re-verify both live
  before editing). Extend the drift gate (`test_plugin_integration_drift.py`)
  to assert the entrypoint total and the KI total, so they cannot drift
  silently again. Run the gate live and record it green.
- [ ] **5.3 Guard the validators test.** Apply the file's own
  `skip_if_no_engine` (`tests/test_ontology_spider_service.py:24-27`)
  to `test_skill_and_plugin_validators_pass` (:161-179). Run it without
  the engine (must skip) and with the engine on `PYTHONPATH` (must
  pass); record both.
- [ ] **5.4 Add unit markers to the unmarked new tests.** Enumerate by
  grep every new test added by the audit/elevation commits (`6b1c31f`,
  `d763ad9`) and the follow-up phases that still carries zero
  `@pytest.mark.unit` markers, add the marker, and re-run the unit gate;
  record passed/failed/skipped.
- [ ] **5.5 Correct the Phase 9 figure.** `ACTION_SUMMARY.md` §5 claims
  `ruff format --check experiments/spider_decisions` → "26 files already
  formatted"; the live count is 57. Correct the figure and re-verify it
  live.

## Track 6 — OS: max_results parity

- [ ] **6.1 Thread the cap into both backends.** Add `max_results` to
  `PythonReasoner` with the same semantics as Prolog (raise on exceed —
  `reasoner.py:311-313`), wire it through `Engine.query`
  (`engine.py:465-470`, which currently falls back to a bare
  `PythonReasoner()`), and expose it on the MCP `query` tool
  (`schemas.py:138-146`). Add tests on both backends plus a parity
  probe (same query, same cap, same result on both). The default
  1000-result cap must apply on both backends, not Prolog only.
- [ ] **6.2 Record the semantics.** If the chosen semantics differ from
  Prolog's raise-on-exceed in any way, record the decision and the
  reason in `docs/decisions.md`; otherwise record that both backends
  raise, with the test names as evidence.

## Track 7 — OS: governance and doc drift (absorbed from the staged plan)

- [ ] **7.1 Record the 5.5 superseding decision.** In OS
  `docs/decisions.md`, add a new decision section superseding 5.5
  (`:148`, "remain single cohesive units… without artificial module
  fracturing"): the split stays — `mcp/server.py` 245 + `handlers.py`
  250, `elicitation.py` 615 + `elicitation_amend.py` 151 — with the
  rationale and the date. The old 5.5 text stays in the record
  (annotated as superseded); do not rewrite history by editing it away.
- [ ] **7.2 Doc-drift sweep.** Fix "16 tools" → 19
  (`docs/architecture.md:32`, `README.md:203,221,237`,
  `docs/mcp.md:40` heading), "6 mutating tools" → 9 (`docs/mcp.md:26`),
  "105 unit tests" → **117** (`README.md:70,216`) and update the
  `tests/test_docs_verbatim.py:69` literal so the test guards the true
  number. Fix the dead `mcp/server.py` refs (`docs/architecture.md:118`,
  decisions §7.9), annotate §7.8's stale budget (1000.0 vs 1500.0) as
  superseded, correct §7.13's phantom test files to the real ones, and
  update the `dialog.py:53` kind comment. Verify every count live
  before editing — do not copy the numbers from this plan.
- [ ] **7.3 Rank 7 decision gate.** Obtain the user's decision in chat:
  **ratify** (the Rank 7 work stays) or **revert** (remove the
  `path`/`count`/`not` kinds, `retract_turn`, `session_save`/
  `session_restore`). Present the options; do not pick for them. If
  ratify: record the decision with their words and date in
  `decisions.md` §7.15, and name the trigger — or record honestly "ratified
  without a recorded trigger" rather than inventing one. If revert:
  remove the three features with their tests/docs and re-run the suite
  in both modes (must return to its pre-`7323f11` shape, 105 tests,
  parity 100%).

## Track 8 — Verification

- [ ] **8.1 Re-run every gate live and record the numbers.** BH: drift
  gate (10/10), vault-integrity gate, unit gate (passed/failed/skipped),
  the 9-suite pytest from `ACTION_SUMMARY.md` §5 (target: 56 passed),
  `ruff check .` clean. OS: full suite with swipl and genuine degraded,
  coverage, parity 100%. CI green on the fix commits; record the run
  numbers.
- [ ] **8.2 Confirm the Phase 4 and hash records read correctly.** The
  comparison and report must state the ceiling (2), the provenance
  (laptop-generated shortlists, 4 domains dropped), and the plan fix
  must be in `PLAN.md`. All 38 hash-bearing claims must recompute
  correctly under the new verifier. One of the two, verified live —
  not asserted.
- [ ] **8.3 Independent check.** Left unticked until a genuinely
  separate check lands. The executor must not tick it.
