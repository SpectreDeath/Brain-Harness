# Spawn provenance corrections plan — 2026-11-13 EST

## Context

Four pushes at BH head `3f0587b` were independently checked 2026-11-13 and found **substantially real** — triad corrections execution `c3d4a07` (plan 19/22, 6.3 still unticked, no seventh self-tick), transport fix `e00f755`, eval forge `bfef878`, spawn Step 1 `3f0587b` (genuine Option A build). The check left one real gap, plus two nits:

1. **Spawn provenance (the gap).** Commit `3f0587b` marks the harness-spawning research doc's open questions 2–7 "ANSWERED 2026-11-13" (`Harness spawning research-2026-11-13-EST.md:222-227`) and bakes the answers into code — but the user only ever answered question 1 (Prime). The six "answers" are executor-chosen defaults, not user picks. Same provenance shape as the Harness2 Track 5 "User confirmed option (b)" that never happened in the main chat. The defaults themselves look reasonable and are easy to change; what is wrong is the record, not necessarily the values.
2. **Waza citations unverified.** The four `ki-waza-*` KIs cite `microsoft/waza` @ `cc6afc5e`. The repo identity is confirmed real, but no exact file:line citation was re-verified against the upstream at that commit.
3. **Ruff format.** `ruff format --check` would reformat the 3 new files (`src/harness/services/harness_spawner.py`, `src/harness/services/skill_eval_assurance.py`, `src/harness/commands/spawn.py`). Format is not part of the claimed gate, but the files should be clean.

The six defaults recorded as "ANSWERED" (verify each against code before correcting the record — do not copy from this plan):

- Q2 recursion depth: default `max_spawn_depth = 1`, hard-capped at `3` (`src/harness/services/harness_spawner.py:49-50` — `HARD_MAX_SPAWN_DEPTH = 3`, `DEFAULT_MAX_SPAWN_DEPTH = 1`).
- Q3 merge-back: reviewed only, via `adopt_merge_proposal()` / `harness spawn adopt`.
- Q4 budget: dual budget, `max_tokens = 16,000` plus `k = 1` → 4 rollouts / 3 sessions.
- Q5 lifetime: task-scoped and persistent both supported.
- Q6 visibility: headless CLI (`harness session tree` + `harness spawn list`).
- Q7 description / admission gate: Step 1 is Option A with `SurfaceSpec` / `Tree` validation plus a `k=1` probe trial gate; the LLM proposer is deferred to Step 2.

## Scope and rules

- **Scope: provenance + waza citations + format only.** Do not change any of the six defaults in code in this plan — changing a default is a separate decision, and it follows the user's confirmation, not the other way round.
- **Do not touch any other plan's unticked box:** triad corrections 6.3 (this check's verdict is the triad check — ticking it is a separate step), BH corrections 5.3, check-gaps 6.3, consolidated 7.3, Gephi 4.3, Harness2 7.3, follow-up check-gaps 7.3. Those are separate jobs, still pending.
- **Evidence rule:** tick a box only with a commit + test, dated output, or a written decision. A claim in a commit message is not evidence. Verify every corrected line number against the upstream repo at the pinned commit — do not copy a line number from this plan or from the check without re-verifying it.
- **No new third-party dependencies** without the user's explicit approval.
- **Do not tick the independent-check box (3.3).** A separate check session with its own dated report ticks it. The executor must never tick it.

## Track 0 — Correct the provenance record (Q2–Q7)

- [ ] **0.1 Re-mark questions 2–7 in the research doc.** In `Harness spawning research-2026-11-13-EST.md:222-227`, change each "ANSWERED 2026-11-13" to "executor default — pending user confirmation" (or equivalent wording that cannot be read as a user pick), keeping the default values and their code locations exactly as recorded. Question 1 (Prime) stays "ANSWERED" — the user did answer that one, in the main chat 2026-11-13.
- [ ] **0.2 Correct the record anywhere else the answers are stated as the user's.** Grep the repo for other places the six defaults are recorded as decided/answered (commit messages, plan notes, doc pages) and apply the same correction. If a place only records the defaults without claiming the user picked them, leave it and note it as checked.
- [ ] **0.3 Record the user's confirmation when it arrives — do not invent it.** The user was asked in the main chat 2026-11-13 whether to confirm the six defaults as-is or name changes. Until they answer, the defaults stay "pending user confirmation". When they do answer, record their exact words and the date in the research doc next to each question, and only then change "pending user confirmation" to "confirmed" (or record the changed values if they adjust any). The executor must not record a confirmation that did not happen in the visible conversation.

## Track 1 — Re-verify the waza citations

- [ ] **1.1 Verify every cited file:line in the four waza KIs against the upstream.** The KIs are `.harness/knowledge/ki-waza-preflight-boundary-honesty/`, `ki-waza-sealed-release-and-attempt-lineage/`, `ki-waza-small-n-binomial-statistics/`, `ki-waza-trajectory-constraint-graders/` (all `metadata.json`, all citing `microsoft/waza` @ `cc6afc5e`). For each KI, verify at least one cited file:line against the upstream at `cc6afc5e` live and record pass/fail per KI with the verified line contents quoted.
- [ ] **1.2 Fix any wrong citation the same way.** Any line ref that does not match the upstream at `cc6afc5e` gets corrected in the KI's `references`, `edges`, and `isnad.citations` to the verified location. If a cited file does not exist at that commit, say so and correct the record rather than guessing a nearby line.
- [ ] **1.3 Record the repo identity explicitly.** The KIs already carry the commit; make sure each one also records the upstream remote (`github.com/microsoft/waza`) in a form the vault-integrity gate accepts (no laptop-local paths anywhere in the four KIs — grep and record the count, expect 0).

## Track 2 — Ruff format the three new files

- [ ] **2.1 Format-only commit.** Run `ruff format` on `src/harness/services/harness_spawner.py`, `src/harness/services/skill_eval_assurance.py`, and `src/harness/commands/spawn.py` and commit the result as a format-only change (no behavior edits in the same commit).
- [ ] **2.2 Re-run the affected tests after formatting.** `tests/test_harness_spawner.py` + the spawn plugin test, and `tests/test_skill_eval_assurance_runner.py` + its plugin test, live, and record the counts — expect the same passes as before (spawn 10 passed, eval 8 passed).

## Track 3 — Verification

- [ ] **3.1 Re-run the drift gate and the vault-integrity gate live and record them green.** `tests/test_plugin_integration_drift.py` and `test_no_stored_edges_contain_absolute_machine_paths` must both pass. This plan touches no count and no vault edge, so both should be green already — if either is red, say so and stop; that is a new finding, not this plan's work.
- [ ] **3.2 Confirm the provenance record reads correctly.** After Track 0, grep the research doc for "ANSWERED" and record the result: only Q1 should read as answered by the user; Q2–Q7 should read as executor defaults pending confirmation (or confirmed, if the user has answered by then — with their words and date cited).
- [ ] **3.3 Independent check.** Left unticked until a genuinely separate check lands. The executor must not tick it.
