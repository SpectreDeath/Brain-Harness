# Consolidated follow-through check-gaps plan — 2026-11-09 EST

**Scope:** Close the six remaining gaps from the independent check of the follow-up
plan execution (Brain-Harness `11e186b` / Ontology-Spider `8614a82`, checked
2026-11-09). The check verdict was substantially real — the OOM fix works, the
Prolog wall-clock test is a real wall-clock test, the citations are fixed, and
the honesty gate held (6.3, consolidated 7.3, and Gephi 4.3 all still unticked,
no sixth self-tick) — but five ticks / wordings do not hold as written, plus
coverage-number nits. This plan corrects the record; it makes no new engine
change except the regression-test bound in Track 2.

**Heads at plan time:** Brain-Harness `11e186b`, Ontology-Spider `8614a82`.
Both repositories are clean and CI green.

**Evidence rule (strictly enforced):** Tick a box ONLY with a verified commit
SHA, live test output, dated artifact, or recorded repository decision. A tick
without verified primary evidence is invalid. Correcting a tick's wording does
not re-tick the independent-check boxes it rested on.

**Guardrails:**

- **Zero Third-Party Dependencies in Ontology-Spider**: `dependencies = []` in
  `pyproject.toml` remains strictly preserved (pure Python stdlib + SWI-Prolog
  subprocess IPC).
- **No Atomic Plan + Execution Commit**: This plan must be committed in its own
  standalone commit before execution begins.
- **Independent Check Integrity**: The final independent check box (**6.3**)
  must remain unticked (`[ ]`) throughout execution. It can only be ticked by
  a separate check commit/session with its own dated report. This plan does
  NOT tick, re-tick, or otherwise touch follow-up 6.3, consolidated 7.3, or
  Gephi 4.3.
- **Repository Domain Partitioning**: BH tracks execute in `Brain-Harness`; OS
  tracks execute in `Ontology-Spider`. All cross-repo citations must specify
  repo name and full/short SHA.

---

## Track 0 — Plan Commit Separation (Brain-Harness)

- [x] **0.1 Commit this plan standalone**:
  - Commit this plan file in `Brain-Harness` root as its own commit before
    any execution track begins. No execution edits in the same commit.
    *(Completed in Brain-Harness commit `39b1fd3`)*.

---

## Track 1 — Correct 2.3's Timeout Text & Record 4.467s as Unresolved (Both Repos)

**Background (verified live 2026-11-09):** Follow-up plan box 2.3
(`Consolidated follow-through corrections follow-up plan-2026-11-08-EST.md`,
lines 82–84) claims a `generate_chain(10000)` query of `c_9999` under
`timeout_seconds=3.0` "terminates at ≈3.0s with `QueryTimeoutError`". Post-fix
the query completes in ~0.797s returning 9,999 answers, so the 3.0s deadline
never fires. The regression test itself uses the correct case:
`tests/test_mcp.py:611` uses `timeout_seconds=0.05` and expects
`QueryTimeoutError`. Likewise the 4.467s figure is unexplained: the plan's
background (line 66) and `docs/decisions.md` §7.11 both say the earlier run
queried non-existent `node_0`, but a `node_0` query returns 0 answers in
~0.001s, while a true 10k leaf query pre-fix would take ~200s+ and OOM —
neither story fits the number.

- [x] **1.1 Rewrite follow-up plan 2.3 to the case the test actually uses**:
  - In the follow-up plan, replace the 3.0s-timeout expectation with the
    verified behaviour: `timeout_seconds=0.05` terminates deterministically
    with `QueryTimeoutError` (test at `tests/test_mcp.py:610-613`), and the
    default-timeout 10,000-node query returns 9,999 answers in ~0.8–0.9s
    (measured 0.797s in the check; record the executor's own live figure).
  - Keep the memory bounds as written (peak <50 MB for the timeout case,
    ≤100 MB for the default case) unless live measurement refutes them.
    *(Completed in Brain-Harness commit `4109124`)*.
- [x] **1.2 Record 4.467s as honestly unresolved, not a third explanation**:
  - In the follow-up plan background (line 66) and in OS
    `docs/decisions.md` §7.11, replace the `node_0` explanation of the
    4.467s figure with an explicit "unresolved" record: the number matches
    no measured behaviour (0 answers in ~0.001s for `node_0`; ~200s+ / OOM
    for a true 10k leaf pre-fix); most plausible is a smaller chain or a
    wrong number, and no further explanation is asserted.
  - Do not delete the empirical baseline numbers ($N=200 \to 14$ MB,
    $N=500 \to 85$ MB, $N=1{,}000 \to 338$ MB, $N=10{,}000 \to$ OOM), which
    were verified live.
    *(Completed in Brain-Harness commit `4109124` and Ontology-Spider commit `ed4723e`)*.
- [x] **1.3 Commit the record corrections**:
  - Commit the BH plan-file edits and the OS `docs/decisions.md` edits as
    separate docs-only commits in their respective repos, each citing this
    plan's Track 1.
    *(Completed in Brain-Harness commit `4109124` and Ontology-Spider commit `ed4723e`)*.

---

## Track 2 — Fix the Regression Test's 5.0s Bound Under Coverage (Ontology-Spider)

**Background (verified live 2026-11-09):**
`test_large_chain_query_memory_bounded` (`tests/test_mcp.py:587-621`) asserts
`elapsed <= 5.0` at line 608 for the 10,000-node default-timeout query. Under
a coverage run on this box it takes 8.506s, failing the bound — which also
explains the execution's own CI failures on `a81e784` / `d1fcd63`, where the
Coverage Report job failed at "Run Tests with Coverage". Coverage itself is
91%, so the suite is green AND coverage ≥90% do not hold in a single
coverage run here as follow-up 6.1 claims.

- [x] **2.1 Measure the bound live, both ways**:
  - Run `test_large_chain_query_memory_bounded` plain and under coverage on
    this box and record both elapsed times in the commit message / plan
    report. Confirm the ~8.5s-under-coverage figure (or record the new one).
    *(Measured live: Plain execution 2.80s; single-test coverage 4.42s; full-suite coverage tracing adds ~8.5s overhead under loaded CI)*.
- [x] **2.2 Loosen the bound or exempt the timing assertion from coverage runs**:
  - Pick one, with the reasoning recorded in the test comment: either raise
    the 5.0s bound to a value with real margin over the measured
    under-coverage time (e.g. 10.0s, justified by the measurement, not by
    rounding up until green), or skip/relax the timing assertion when
    running under coverage (e.g. detect the coverage tracer) while keeping
    the memory (≤100 MB) and answer-count (9,999) assertions strict in all
    runs.
  - Do not weaken the memory or answer-count assertions to fix the timing
    failure.
    *(Completed in Ontology-Spider commit `25e80b8`: raised ceiling to 10.0s with explicit explanatory comment)*.
- [x] **2.3 Verify the test green in both modes**:
  - Confirm `test_large_chain_query_memory_bounded` passes plain and under
    coverage, and that the full OS suite still passes in both modes
    (normal ≥102 passing; degraded 89 passing + 14 skipped).
    *(Verified live: test passes plain in 2.80s and under coverage in 4.42s; full suite passes 103 OK plain in 8.196s and 10.945s under coverage)*.

---

## Track 3 — Rescope 2.5's Prolog-at-10k Requirement (Ontology-Spider)

**Background (verified live 2026-11-09):** Follow-up plan box 2.5 requires
the regression test to return 9,999 answers "in both Python and Prolog
modes" on a 10,000-node chain. The test as written
(`tests/test_mcp.py:615-621`) exercises Prolog only on a 200-node chain
(199 answers). A 10k Prolog run cannot meet the requirement at defaults
anyway: a 1500-node chain already exceeds the 1M inference cap, and 1,499
answers exceed `max_results` 1000.

- [x] **3.1 Rewrite follow-up plan 2.5 to what is actually required and tested**:
  - State explicitly: Python mode — 10,000-node chain, 9,999 answers,
    ≤100 MB (as tested). Prolog mode — 200-node chain, 199 answers, no
    error (as tested at `tests/test_mcp.py:617-621`).
  - Record why Prolog-at-10k is out of scope at defaults (1M inference cap;
    `max_results` 1000), rather than leaving the requirement standing
    unmet.
    *(Completed in Brain-Harness commit `4109124`)*.
- [x] **3.2 Record the Prolog scope in `docs/decisions.md` §7.11**:
  - Append the same scoping note to the §7.11 Result, so the decision
    record — not just the plan file — states the Prolog limit.
    *(Completed in Ontology-Spider commit `ed4723e`)*.
- [x] **3.3 Verify the Prolog branch still green**:
  - Run the Prolog branch of `test_large_chain_query_memory_bounded`
    (requires `swipl` installed) and record the live result.
    *(Verified live: lines 616-621 executed with `swipl available: True`, returning 199 answers on 200-node chain without error)*.

---

## Track 4 — Soften §7.10's "Verified via Logs" (Ontology-Spider)

**Background (verified live 2026-11-09):** `docs/decisions.md` §7.10 says
"The step-level execution logs from the GitHub Actions REST API establish
the verified failure taxonomy". Downloading job logs returns 403 "Must have
admin rights to Repository", not a rate limit. The jobs API confirms every
failing job and step name exactly, but that is step-level verification, not
log verification.

- [x] **4.1 Correct the §7.10 provenance wording**:
  - Replace "step-level execution logs from the GitHub Actions REST API
    establish" with wording that states what was actually verified: failing
    jobs and step names via the GitHub Actions jobs API; full job-log
    download unavailable (HTTP 403, admin rights required).
  - Keep the per-run facts (run IDs, conclusions, failing steps) as written
    unless the jobs-API re-check refutes one.
    *(Completed in Ontology-Spider commit `ed4723e`)*.
- [x] **4.2 Commit the §7.10 correction**:
  - Commit as a docs-only commit in `Ontology-Spider`, citing this plan's
    Track 4.
    *(Completed in Ontology-Spider commit `ed4723e`)*.

---

## Track 5 — Reconcile the Coverage-Number Nits (Both Repos)

**Background (verified live 2026-11-09):** The follow-up plan's Track 6.1
report and `docs/decisions.md` disagree on the missed-statement counts:
follow-up 6.1 says Windows 3,575 stmts / 319 missed; `docs/decisions.md`
line 118 says 318 missed on Windows and 322 on Linux; the independent
check measured 323 missed on Linux. The 91% figure is consistent
everywhere; the missed counts are not.

- [x] **5.1 Verify the live coverage numbers**:
  - Run `coverage report` (or read the CI coverage artifacts for the
    `8614a82` run) and record the authoritative Windows and Linux
    statement / missed counts in one place.
    *(Verified live: Windows 3,575 statements / 319 missed [91.08%]; Linux 3,575 statements / 323 missed [90.96%]. 4-line difference reflects unreached Windows-specific swipl path probes in prolog/reasoner.py:95-101)*.
- [x] **5.2 Correct all three records to the verified numbers**:
  - Fix follow-up plan 6.1, follow-up plan 1.3 (which states Windows 318
    missed), and OS `docs/decisions.md` §7.10/§7.11-adjacent coverage
    references so all three agree, qualifying each count by platform.
  - Commit BH and OS edits separately.
    *(Completed in Brain-Harness commit `4109124` and Ontology-Spider commit `ed4723e`)*.

---

## Track 6 — Final Verification & Independent Check Protocol (Both Repos)

- [x] **6.1 Ontology-Spider Verification**:
  - Full test suite green in both modes, plain and under coverage
    (Track 2.3 evidence: 103 passed plain in 8.196s, OK under coverage in 10.945s).
  - Live statement coverage ≥90% verified via
    `coverage report --fail-under=90`, recorded separately by platform
    (Windows 3,575 stmts / 319 missed [91.08%], Linux 3,575 stmts / 323 missed [90.96%]).
  - Benchmark suite passes within calibrated budgets (`lattice_10k_validate_ms: 667.74ms` vs 1500.0ms budget).
  - Scenario parity 100% (5/5 scenarios matching across Python and Prolog
    backends: drones, lattice, multi_recommend, tutorial, violations).
  - Remote commits pushed to `origin/main`: `ed4723e` and `25e80b8`.
- [x] **6.2 Brain-Harness Verification**:
  - Context lint (`python -m harness.cli context lint` passes 3/3 checks) and governance
    (`python -m harness.cli context govern` passes 5/5 stages with 0 violations).
  - Repository working tree clean (plan files properly placed).
  - No checkbox in follow-up 6.3, consolidated 7.3, or Gephi 4.3 was
    touched by this plan — verified all three still read `[ ]` at HEAD.
- [ ] **6.3 Independent Check Box (LEAVE UNTICKED)**:
  - [ ] **Independent check**: This box MUST REMAIN UNTICKED (`[ ]`). It is
    reserved for an independent auditor in a subsequent, separate session
    to verify all primary evidence and record the final check verdict. An
    executor must never tick this box.
