# Harness2 follow-up plan — 2026-11-10 EST

**Scope:** Close the six gaps from the independent review of Brain-Harness
`4cf398d` ("integrate Google Harness2 recursive agent harnessing architecture",
arXiv:2610.14224, 38 files, +4,538 lines), reviewed 2026-11-10. The review
verdict was **partially real — a working framework, not the full integration
the commit message claims.** What verified cleanly: all 60 new tests pass
live, the demo runs end-to-end in both modes, the CLI works
(`refine budget --k 2` → 8 rollouts, 6 sessions), both plugins load, kernel
wiring is real (typed ServiceKeys, resolvers), lint + govern + Ruff pass, no
new dependencies, and the arXiv reference checks out (Xu et al., Google Cloud
AI Research + Northwestern, Oct 2026; upstream `ledger.py` near-verbatim the
source of the BH one). This plan fixes what did not verify; it makes no claim
the framework is a finished integration until Track 5's scope decision lands
and Track 7's verification runs.

**Heads at plan time:** Brain-Harness `4cf398d`. CI on that head is red
(unit gate 13 failed / 2066 passed, vs the 11 / 2068 baseline).

**Evidence rule (strictly enforced):** Tick a box ONLY with a verified commit
SHA, live test output, dated artifact, or recorded repository decision. A tick
without verified primary evidence is invalid. Do not re-tick, untick, or
otherwise touch the independent-check boxes of any other plan.

**Guardrails:**

- **No Atomic Plan + Execution Commit**: This plan must be committed in its
  own standalone commit before execution begins.
- **No new third-party dependencies** without explicit user approval
  (repo AGENTS.md dependency guardrail).
- **Independent Check Integrity**: The final independent check box (**7.3**)
  must remain unticked (`[ ]`) throughout execution. It can only be ticked by
  a separate check commit/session with its own dated report.
- **Derived counts over hard-coded counts**: Where a count is asserted by a
  test or a doc, the executor measures it live first and records the measured
  value. Widening a hard-coded expectation without measuring is not a fix —
  the 104→105 drift failure was the same failure mode.
- **Honest provenance**: A citation must resolve live (repo + commit exist,
  file + line exist) at the time it is written. A SHA that returns "No commit
  found" or a 404 org fails its track, however genuine the distilled code is.

---

## Track 0 — Plan Commit Separation (Brain-Harness)

- [ ] **0.1 Commit this plan standalone**:
  - Commit this plan file in `Brain-Harness` root as its own commit before
    any execution track begins. No execution edits in the same commit.

---

## Track 1 — Drift Counts Green (Brain-Harness)

**Background (verified live 2026-11-10):** Both drift tests fail at
`4cf398d` — `tests/test_plugin_integration_drift.py`: 2 failed, 4 passed.
Canonical plugins measured live: 142 (`plugins/*/*/plugin.json`, excluding
`external`); workspace skills measured live: 106
(`.agents/skills/*/SKILL.md`). The docs still say 140 plugins / 105 skills.
The new `refine` group is registered at `src/harness/cli.py:148`
(`("refine", refine_group)`), so the 45-group expectation is stale too.

- [ ] **1.1 CLI groups**: Measure `len(_CANONICAL_GROUPS)` live, then update
  the expectation in `tests/test_plugin_integration_drift.py`
  (`test_canonical_cli_groups_count`, currently asserts 45) to the measured
  value, and correct the docstring on line 4 if it still says 45.
- [ ] **1.2 Plugin + skill counts in docs**: Update the measured counts in
  every place the drift test asserts them — `README.md` (currently
  "**140 Canonical Harness Plugins**" and "**105 Workspace Skills packages
  (140 Skill Graph nodes)**"), `USER_MANUAL.md` (same two strings),
  `plugins/README.md` ("140 Plugins"), `.agents/skills/README.md`
  ("105 production-grade AI agent skills").
- [ ] **1.3 Neighbouring counts**: Check the other hard-coded numbers on the
  same README lines — "650 tool entrypoints" and "140 Skill Graph nodes" —
  against live measurements. Correct any that drifted with the measured
  value, or record with evidence that they are still correct. Do not guess.
- [ ] **1.4 Drift gate green**: Re-run
  `tests/test_plugin_integration_drift.py` in full; all 6 tests pass.

---

## Track 2 — Re-Pin the Upstream Citation (Brain-Harness)

**Background (verified live 2026-11-10):** Both plugin manifests and the
vault item cite `source_repo: https://github.com/Google/harness2` and
`verified_commit: 23fb5e0516c99ac04a1aa46c193efda2e1b9bb24`. `Google/harness2`
is a 404 — the real org is `google-research` — and the SHA lookup returns
"No commit found". Same phantom-commit failure mode as `a8ecf26`. The
distillation itself is genuine (upstream `ledger.py` near-verbatim), so this
track fixes the evidence, not the code. Files carrying the bad citation:
`plugins/agent_orchestration/recursive_harness_refiner/plugin.json`,
`plugins/security_and_forensics/evidence_isolation_guard/plugin.json`,
`.harness/knowledge/ki-harness2-recursive-harnessing/metadata.json` (line 5)
and `summary.md` (lines 5–6, which also record the laptop-local path
`D:\GitHub\cloned\Google\harness2`), and
`.agents/skills/recursive-harness-refiner/SKILL.md` (line 8, `Google/harness2`).

- [ ] **2.1 Resolve the real upstream**: Against
  `github.com/google-research/harness2` (confirmed real by web search
  2026-11-10; paper arXiv:2610.14224, code at that org), identify the actual
  commit the distillation was taken from — compare the BH `ledger.py`
  against upstream history — and verify live (clone or GitHub API) that the
  SHA exists in that repo. A secondary write-up mentions commit `1cfe254`;
  do NOT take that as verified — check it live or find the right one.
- [ ] **2.2 Re-pin or retract**: If a matching upstream commit is found,
  update `source_repo` / `verified_commit` / `source_url` / `commit_hash`
  in both `plugin.json` files and the vault item's `metadata.json` +
  `summary.md` to the verified org + SHA. If no matching commit can be
  identified, drop the `verified_commit` claim and record instead the
  upstream HEAD checked, the check date, and that the distillation was
  matched by content, not by pinned commit. Either way the laptop-local
  `D:\GitHub\...` path is removed or replaced with the repo URL.
- [ ] **2.3 Skill text**: Fix the `Google/harness2` reference in
  `.agents/skills/recursive-harness-refiner/SKILL.md` to
  `google-research/harness2`.
- [ ] **2.4 No phantom citations remain**: Grep the repo for `Google/harness2`
  and `23fb5e05` — zero hits outside this plan's own record of the fix.

---

## Track 3 — Line Bound + Unit-Gate Membership (Brain-Harness)

**Background (verified live 2026-11-10):** Five files in
`src/harness/services/recursive_harnessing/` break the 200-line
per-subpackage decomposition convention — `selection.py` 212,
`surface.py` 228, `evidence.py` 230, `prompts.py` 236, `recursion.py` 243
(`wc -l`, all at `4cf398d`). There is no line-limit test for this package.
The new tests also carry no `@pytest.mark.unit` markers:
`tests/test_service_recursive_harnessing.py` is 802 lines with 57 test
functions (60 collected cases, 3 parametrized) and zero `pytest.mark.unit`
hits, so none of them run in the unit gate. (Correction to the review's first telling: the 200-line bound is the
per-subpackage decomposition convention, not Rule 11 — Rule 11 is the
AGENTS.md <150-line hygiene rule.)

- [ ] **3.1 Split the five files**: Decompose each of the five files to
  ≤200 lines, following the existing decomposition-test pattern in the repo
  (e.g. `tests/test_codebase_context_decomposition.py`). No behaviour change;
  the 60 collected cases must pass before and after with identical outcomes.
- [ ] **3.2 Line-limit test**: Add a test enforcing the ≤200-line bound for
  the `recursive_harnessing` package, mirroring the existing decomposition
  tests, so a future over-long file fails the gate instead of shipping.
- [ ] **3.3 Unit markers**: Add `@pytest.mark.unit` to the tests in
  `tests/test_service_recursive_harnessing.py` (or the class, if the file's
  tests are class-grouped — verify first). Record the before/after count:
  60 collected cases (57 test functions, 3 of them parametrized) — none
  lost, all now counted in the unit gate.

---

## Track 4 — `refine validate . --brain` Fails on Brain-Harness Itself

**Background (verified live 2026-11-10):** `AGENTS.md` is 27,537 chars
(109 lines) at `4cf398d`. The brain surface caps always-on files at
`always_on_max=24_000` (`src/harness/services/recursive_harnessing/models.py:46-47`,
used by `BRAIN_SURFACE` and the `validate --brain` path in
`src/harness/commands/refine.py`). So the feature fails on its own host
repo. Note AGENTS.md is 109 lines — under Rule 11's 150-line limit — so
this is the port's own char cap, not an AGENTS.md hygiene violation.

- [ ] **4.1 Record the decision**: Decide, with a written rationale in the
  plan or a repo decision note, which side is wrong: (a) raise / derive the
  cap (e.g. from the actual host file, or a documented higher bound),
  (b) trim `AGENTS.md` below 24,000 chars, or (c) scope `--brain`
  validation to exclude the root `AGENTS.md`. Do not silently raise the cap
  without recording why.
- [ ] **4.2 Implement the decision** and re-run
  `harness refine validate . --brain` from the repo root — exit 0, with the
  output recorded.

---

## Track 5 — Live Proposer + `refine run`: Implement or Defer by Design

**Background (verified live 2026-11-10):** The only proposer
implementations are the demo's scripted one and a facade. Nothing outside
demo/tests calls `ExperienceLibrary.add` (only call site:
`src/harness/services/recursive_harnessing/demo.py:137`) or the
`experience()` prompt (`prompts.py:216`), so the second recursion level
never executes in the product. `harness refine` has five subcommands
(`budget`, `validate`, `scan`, `fingerprint`, `demo` —
`src/harness/commands/refine.py`) and no `run`. End-to-end recursive
harnessing with a real model cannot be run from `4cf398d`.

- [ ] **5.1 Scope decision (recorded before any Track 5 code)**: Either
  (a) implement — a real model-backed proposer seam plus a
  `harness refine run` command, wired through the kernel's existing model
  seam with no new dependencies, with a demo-mode guard so it cannot run
  without a model; or (b) defer by design, with the trigger that would
  reopen it (as Track 10 was deferred in Ontology-Spider). The user picks
  (a) or (b); if (b), Tracks 5.2–5.3 are struck with the decision recorded
  and the commit message / docs must not claim end-to-end recursive
  harnessing.
- [ ] **5.2 (only if 5.1 is implement) Real proposer + `refine run`**:
  Wire a model-backed proposer, `ExperienceLibrary.add` /
  `prompts.experience()` called from product code (not demo/tests only),
  and the `refine run` command. Acceptance: a real-model run executes at
  least one Propose-Probe-Compose step end to end, respecting the budget
  identity (Rule 59: R=4k rollouts, P=3k sessions) and fail-closed evidence
  isolation, with the run recorded.
- [ ] **5.3 (only if 5.1 is implement) Guard the demo boundary**: The
  scripted demo proposer must stay clearly demo-only — a real-model run
  must not silently fall back to the scripted proposer. A test asserts the
  boundary.

---

## Track 6 — Docs Page (Brain-Harness)

**Background (verified live 2026-11-10):** Zero mentions of
`recursive_harness`, `Harness2`, or `harness2` in `docs/`, `README.md`,
`USER_MANUAL.md`, or `CONTEXT-MAP.md` (grep, all four locations).

- [ ] **6.1 Docs page**: Add a docs page (how-to or explanation, following
  the repo's docs layout) covering: what recursive harnessing is, the
  `harness refine` subcommands with an example (`budget`, `validate`,
  `scan`, `fingerprint`, `demo`), the budget identity (R=4k / P=3k),
  fail-closed evidence isolation, and the current limits — including the
  Track 5 outcome (no live proposer / no `refine run` if deferred).
- [ ] **6.2 Link it in**: Link the page from `README.md` and/or
  `USER_MANUAL.md` and the docs index, as the repo's other features are
  linked. Verify no broken relative links (Rule 47).

---

## Track 7 — Verification (Brain-Harness)

- [ ] **7.1 Unit gate restored**: Full unit gate back to the 11 pre-existing
  failures (13 → 11), with the 60 recursive-harnessing cases now counted
  in the gate — passed count must rise by 60, not fall. Record the live
  gate numbers.
- [ ] **7.2 Gates green**: `tests/test_plugin_integration_drift.py` all
  pass; lint + govern + Ruff pass; `harness refine demo` and
  `harness refine budget --k 2` still run end to end (8 rollouts,
  6 sessions); `harness refine validate . --brain` green per Track 4.
- [ ] **7.3 Independent check (left unticked)**: A separate check session
  re-verifies Tracks 1–6 live against the execution head and records its
  own dated verdict. This box stays `[ ]` until that check lands.
