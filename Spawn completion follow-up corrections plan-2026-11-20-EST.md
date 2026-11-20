# Spawn completion follow-up corrections plan — 2026-11-20 EST

Fix the gaps the independent check of the spawn completion execution found
(BH `75535c8`, checked 2026-11-20: substantially real, 16/17 ticked, only
5.2 unticked). Head CI is green; the execution commit `5d7a8fa` failed CI
and was fixed by `75535c8` — that is history, not a live defect, and needs
no fix here.

## Evidence rule

Tick a box only with a commit + a passing test, a dated command output,
or a written decision recorded verbatim from the user in chat. Never
record a user pick that did not happen in visible conversation. Never
tick the independent-check box (4.2) yourself.

## Scope limits

- No new third-party dependencies without the user's explicit approval.
- Do not change any spawn default in code; Track 0 only records what the
  user said.
- Do not touch spawn provenance 3.3, BH 5.3, check-gaps 6.3, consolidated
  7.3, Gephi 4.3, Harness2 7.3, follow-up check-gaps 7.3, or the staged
  triad forge citations plan. Do not re-open any ticked box in any other
  plan. Do not re-run the full capability build — this plan fixes the
  gaps only.

## Track 0 — Defaults confirmation gate

- [ ] **0.1 Ask the user in chat the one question and record the answer
  verbatim.** Did they say `"leave all 6 on default"` on the laptop in
  answer to the six Track 0 questions? Record their reply word-for-word
  with the date. An answer given on the laptop counts only if it is
  repeated in visible chat or quoted verbatim with its source named.
- [ ] **0.2 Correct the record to match the answer.** If the user
  confirms, the research doc lines 222–227 and the plan's 0.1 annotation
  stand as written. If they did not say it, or said something else,
  correct both records to what they actually said and re-mark any
  default they did not confirm as "executor default — pending
  confirmation". If they answer the six separately, record each answer
  against its question instead of the blanket quote.
- [ ] **0.3 Tick spawn provenance 0.3 only on the user's word.** The
  answers recorded in 0.1–0.2 are the evidence for spawn provenance
  plan box 0.3. The executor must not tick it; ticking is a later
  step's job on the user's word.

## Track 1 — Materialize portability

- [ ] **1.1 Stop hardcoding bare `python` in generated `dock.yaml`.**
  `build_spawn_dock_yaml` (`materialize.py:62–66`) writes
  `python -c "import os; assert ..."` into every materialized repo's
  entrypoint. Use `sys.executable` (or `python3`) so a materialized
  repo works on a box with no bare `python` on PATH. Same ambient-
  `python` residual documented since the Nov 5 vault-stats fix; do not
  bake it into new artifacts.
- [ ] **1.2 Re-run the new tests with no bare `python` on PATH.** The 7
  new spawn tests (`test_live_harness_proposer.py`,
  `test_harness_spawner_materialize.py`, and the materialize/drift
  paths in `test_harness_spawner.py`) must pass with `python` removed
  from PATH. The 2 that failed with exit 127 (`test_materialize_link_
  inspect_run_list_and_drift`, `test_four_use_cases_pass_cleanly`)
  are the acceptance bar.
- [ ] **1.3 Re-run the drift + dock end-to-end checks.** `harness spawn
  check-drift` and the materialize → link → `dock inspect` → `dock run`
  path pass on the fixed code, with dated outputs.

## Track 2 — Diff-review CLI surface

- [ ] **2.1 Add a CLI surface that presents the diff for review.**
  `build_tree_diff_review` is Python-API-only: today an operator must
  compute the approval digest in Python to pass `--approve-digest`.
  Add a CLI command (e.g. `harness spawn review` or a `--show-diff`
  on `spawn run`) that prints the human-readable diff and its canonical
  SHA-256 digest, so the review step the plan requires has somewhere to
  happen.
- [ ] **2.2 Document it in `cli.md` in the same commit.** New
  subcommands land with their docs — the `5d7a8fa` CI failure was a
  `spawn reject` / `spawn check-drift` pair with zero `cli.md` hits.
  Do not repeat it: the docs and the command land together.
- [ ] **2.3 Test the full approve flow through the CLI.** Present the
  diff, approve the digest, spawn with `write_permitted=True` — and
  the negative cases (no digest, drifted digest) still land FAILED.
  Marked `@pytest.mark.unit` where they belong in the unit gate.

## Track 3 — Real-work proof

- [ ] **3.1 Run the live proposer against a real LLM.** The full loop
  and use-case tests stub the proposer's completion function, so the
  parsing/validation/diff-review/spawn wiring is proven but no
  real-model run is recorded anywhere. Run `LiveHarnessProposer`
  against the real in-repo LLM service on one description, with a
  dated run log, and record the proposed tree and whether it passed
  `validate()` + the trial gate.
- [ ] **3.2 Run a real ingestion through the child partition.** The
  ingestion use case proves partition isolation (child library root
  contains the spawn id, parent KI absent), not an actual ingest.
  Ingest one real repo through a spawned child and adopt at least one
  resulting KI, with the run recorded.
- [ ] **3.3 Correct the stale research-doc line.** `Harness spawning
  research-2026-11-13-EST.md:62` still says "the only implementation
  is `ScriptedProposer` … There is no live proposer" — false since
  `5d7a8fa`. Correct it to name `LiveHarnessProposer` and where it
  lives.

## Track 4 — Verification

- [ ] **4.1 Re-run the gates with dated outputs and reconcile the
  record.** Full unit gate, drift gate, vault-integrity gate, ruff
  check + format, spawn test suites. Reconcile the ruff format count
  the parent plan records as "17 files" against the checker's exact
  touched set of 13 — show the recompute. Record numbers that
  reproduce on a fresh checkout; note any that are machine-specific.
- [ ] **4.2 Independent check.** Left unticked until a genuinely
  separate check lands. The executor must not tick it.
