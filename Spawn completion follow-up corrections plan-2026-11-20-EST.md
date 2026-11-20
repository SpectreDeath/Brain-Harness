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

- [x] **1.1 Stop hardcoding bare `python` in generated `dock.yaml`.**
  `build_spawn_dock_yaml` (`materialize.py:62–66`) writes
  `python -c "import os; assert ..."` into every materialized repo's
  entrypoint. Use `sys.executable` (or `python3`) so a materialized
  repo works on a box with no bare `python` on PATH. Same ambient-
  `python` residual documented since the Nov 5 vault-stats fix; do not
  bake it into new artifacts.
  *(Done `2026-11-20`, commit `a9d8221`: `build_spawn_dock_yaml` now emits the quoted `sys.executable` via `_python_invocation()`. Residual: the path is absolute, so a materialized repo moved to a different box/venv path needs re-materializing; it no longer needs a bare `python` on PATH. New unit test `test_generated_dock_yaml_does_not_depend_on_bare_python`.)*
- [x] **1.2 Re-run the new tests with no bare `python` on PATH.** The 7
  new spawn tests (`test_live_harness_proposer.py`,
  `test_harness_spawner_materialize.py`, and the materialize/drift
  paths in `test_harness_spawner.py`) must pass with `python` removed
  from PATH. The 2 that failed with exit 127 (`test_materialize_link_
  inspect_run_list_and_drift`, `test_four_use_cases_pass_cleanly`)
  are the acceptance bar.
  *(Done `2026-11-20`: with every PATH dir containing python removed (`where python` -> not found), `test_live_harness_proposer.py` + `test_harness_spawner_materialize.py` + `test_harness_spawner.py` + `test_harness_spawner_e2e.py` -> `15 passed`. Baseline on the pre-fix code, same stripped PATH: `test_materialize_link_inspect_run_list_and_drift` and `test_four_use_cases_pass_cleanly` FAILED (`'python' is not recognized`); both pass after the fix. Runner: scratch `run_no_python.py`. Windows run — the original exit 127 was POSIX; same root cause.)*
- [x] **1.3 Re-run the drift + dock end-to-end checks.** `harness spawn
  check-drift` and the materialize → link → `dock inspect` → `dock run`
  path pass on the fixed code, with dated outputs.
  *(Done `2026-11-20T17:34`: real CLI, python stripped from PATH, isolated docks state: `spawn run --materialize --approve-dock` exit 0 -> `dock inspect` exit 0 -> `dock run validate` exit 0 with `DOCK_HARNESS_OK` -> `spawn check-drift` clean exit 0 / drifted=False -> tamper `AGENTS.md` -> `check-drift` exit 1 / drifted=True. Log: scratch `e2e_dock_drift_2026-11-20.log`.)*
## Track 2 — Diff-review CLI surface

- [x] **2.1 Add a CLI surface that presents the diff for review.**
  `build_tree_diff_review` is Python-API-only: today an operator must
  compute the approval digest in Python to pass `--approve-digest`.
  Add a CLI command (e.g. `harness spawn review` or a `--show-diff`
  on `spawn run`) that prints the human-readable diff and its canonical
  SHA-256 digest, so the review step the plan requires has somewhere to
  happen.
  *(Done `2026-11-20`, commit `a9d8221`: `harness spawn review --name --domain [--task --harness-dir --base-dir --approve-digest --json]` prints files added/modified/removed, the unified diff and the canonical SHA-256 approval digest; `--approve-digest` mismatch exits 1. It shares `_resolve_proposed_tree` with `spawn run`, so the digests agree.)*
- [x] **2.2 Document it in `cli.md` in the same commit.** New
  subcommands land with their docs — the `5d7a8fa` CI failure was a
  `spawn reject` / `spawn check-drift` pair with zero `cli.md` hits.
  Do not repeat it: the docs and the command land together.
  *(Done `2026-11-20`, commit `a9d8221` contains `commands/spawn.py` and `docs/reference/cli.md` together; `tests/test_cli_content_drift.py` passes.)*
- [x] **2.3 Test the full approve flow through the CLI.** Present the
  diff, approve the digest, spawn with `write_permitted=True` — and
  the negative cases (no digest, drifted digest) still land FAILED.
  Marked `@pytest.mark.unit` where they belong in the unit gate.
  *(Done `2026-11-20`, commit `a9d8221`: `tests/test_harness_spawner_review_cli.py`, 5 `@pytest.mark.unit` tests — review text/digest, base-dir diff + digest mismatch, full review -> approve -> `--write-permitted` spawn RUNNING, no digest -> FAILED, drifted digest -> FAILED. All pass.)*
## Track 3 — Real-work proof

- [ ] **3.1 Run the live proposer against a real LLM.** The full loop
  and use-case tests stub the proposer's completion function, so the
  parsing/validation/diff-review/spawn wiring is proven but no
  real-model run is recorded anywhere. Run `LiveHarnessProposer`
  against the real in-repo LLM service on one description, with a
  dated run log, and record the proposed tree and whether it passed
  `validate()` + the trial gate.
  *(BLOCKED `2026-11-20`, left unticked: the in-repo `LiteLLMService` needs the optional `litellm` package (not installed in `.venv`; installing it is a new dependency needing explicit user approval) and a provider API key (none set in the environment). Ready-to-run script: scratch `run_live_proposer.py <model>` — runs `propose_tree_from_description` (includes `validate()`), prints the tree, then the k=1 trial gate.)*
- [x] **3.2 Run a real ingestion through the child partition.** The
  ingestion use case proves partition isolation (child library root
  contains the spawn id, parent KI absent), not an actual ingest.
  Ingest one real repo through a spawned child and adopt at least one
  resulting KI, with the run recorded.
  *(Done `2026-11-20T17:33`, scratch `ingest_real_repo.py`, log `ingest_run_2026-11-20.log`: real repo `D:\GitHub\cloned\andrej-karpathy-skills` @ `2c606141936f`, ingested with `RepoTriadForgeService.inspect` (9 files, 30 entities) inside spawned child `spawn_ingest-andrej-karpathy-skills_686f4af0`; child library root contained the spawn id; proposal `prop_ingest-andrej-karpathy-skills_af61e8e6` staged then adopted as KI `ki-spawn-repo-andrej-karpathy-skills-ingest-andrej-karpathy-skills` (`metadata.json` + `summary.md`). Caveats: parent stores were an isolated sandbox under the scratch dir, not the live `.harness/knowledge`; reviewer recorded as `executor-agent (pending human review)`; the KI content is thin (inspection facts only, no LLM).)*
- [x] **3.3 Correct the stale research-doc line.** `Harness spawning
  research-2026-11-13-EST.md:62` still says "the only implementation
  is `ScriptedProposer` … There is no live proposer" — false since
  `5d7a8fa`. Correct it to name `LiveHarnessProposer` and where it
  lives.
  *(Done `2026-11-20`, commit `a9d8221`: line 62 now names `LiveHarnessProposer` at `src/harness/services/recursive_harnessing/proposer.py:55` and states that no real-model run is recorded yet.)*
## Track 4 — Verification

- [x] **4.1 Re-run the gates with dated outputs and reconcile the
  record.** Full unit gate, drift gate, vault-integrity gate, ruff
  check + format, spawn test suites. Reconcile the ruff format count
  the parent plan records as "17 files" against the checker's exact
  touched set of 13 — show the recompute. Record numbers that
  reproduce on a fresh checkout; note any that are machine-specific.
  *(Done `2026-11-20`, head `a9d8221` + dirty-free tree: `pytest -m unit -q --timeout=60` -> `2321 passed, 885 deselected, 3 warnings in 282.64s` (log: scratch `unit_gate.log`; was 2313 before this plan); `ruff check .` -> `All checks passed!` (ruff 0.11.0); CI-scoped `ruff format --check` -> `73 files already formatted`; `harness context lint` -> PASS; `knowledge sync --strict` -> 382 KIs synced; drift gate `test_plugin_integration_drift.py` + `test_cli_content_drift.py` -> `14 passed`; vault integrity `verify_track8_records.py` -> `81/0`, 28 KIs / 103 claims = 22+16+62+3, 0 local mismatches; spawn suites (proposer/materialize/spawner/e2e/review CLI) pass. **Format recompute:** `git diff --name-only 105ba03 5d7a8fa -- '*.py'` = **13** files, all `already formatted` (the checker's number). The parent plan's `17` is not reproducible as a touched set — it was a hand-picked module/test list; the 13-file touched set is canonical. (75535c8 additionally touched `tests/test_cli_content_drift.py`, which is outside the CI format scope and would be reformatted.) Whole-repo `ruff format --check .` = 966 would reformat — pre-existing, CI only checks the scoped paths. Machine-specific: the 282 s unit time; the Windows PATH-strip stands in for the POSIX 127.)*
- [ ] **4.2 Independent check.** Left unticked until a genuinely
  separate check lands. The executor must not tick it.
