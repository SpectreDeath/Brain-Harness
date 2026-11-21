# Spawn capability completion plan — 2026-11-20 EST

Finish the harness-spawning capability end to end. Step 1 (child-context
spawn) is built and real; the rest is not. This plan completes Steps 2–4
of the spawning research (`Harness spawning research-2026-11-13-EST.md`).

## Verified starting state (BH `e17749b`, 2026-11-20)

What exists:

- Step 1, Option A: `src/harness/services/harness_spawner/` (10 modules),
  `harness spawn run/list/retire/propose/adopt`, k=1 probe gate,
  SPAWNED → VALIDATED → RUNNING. Tree is written to the child's working
  dir at spawn time (`lifecycle_mixin.py:206`) — runtime materialization,
  not a durable repo.
- `HarnessProposer` protocol exists
  (`src/harness/services/recursive_harnessing/protocols.py:59`,
  `propose(mission, evidence_root, label)`). Its only implementation is
  `ScriptedProposer` (`demo.py:88`) — a scripted demo double, not a live
  proposer. Evidence isolation, `validate_harness`, and the ledger all
  exist around it.
- Merge-back code exists: `propose_merge_back` / `adopt_merge_proposal` /
  `list_proposals` (`merge_mixin.py:33,112,179`), reviewed-only adopt.
  The policy — what a child may propose, what the parent adopts, the
  partition rules — is undecided and untested end to end.

What does not exist:

- Step 2: no live LLM-backed proposer.
- Step 3: no `harness spawn --materialize`; no durable dock-linked repo
  output. ("Materialize" in the codebase means writing the tree to the
  child's working dir, nothing more.)
- Step 4: no merge-back policy decision and no tested adopt loop.
- The six spawn defaults (depth 1 / hard cap 3; merge-back reviewed-only;
  dual budget max_tokens=16,000 + k=1→4 rollouts / 3 sessions; task +
  persistent lifetimes; headless CLI) are executor defaults, still pending
  user confirmation (spawn provenance plan box 0.3, unticked).

## Evidence rule

Tick a box only with a commit + a passing test, a dated command output,
or a written decision recorded verbatim from the user in chat. Never
record a user pick that did not happen in visible conversation. Never
tick the independent-check box (5.2) yourself.

## Scope limits

- No new third-party dependencies without the user's explicit approval.
- Do not change any of the six spawn defaults in code until Track 0
  records the user's confirmation of that default.
- Do not touch spawn provenance 0.3 or 3.3 directly: Track 0's answers
  are the evidence for 0.3, but ticking 0.3 is a later step's job on the
  user's word, never this plan's executor. Do not touch BH 5.3,
  check-gaps 6.3, consolidated 7.3, Gephi 4.3, Harness2 7.3, follow-up
  check-gaps 7.3, or the staged triad forge citations plan.
- Do not re-open any ticked box in any other plan.

## Track 0 — Settle the defaults (decision gate, do first)

- [x] **0.1 Ask the user the six questions in chat and record the
  answers verbatim.** Depth (default 1, hard cap 3)? Merge-back
  (reviewed-only)? Budget (max_tokens=16,000, k=1→4 rollouts / 3
  sessions)? Lifetime (task + persistent)? Visibility (headless CLI)?
  Description / admission gate (who writes the description, what the
  k=1 probe gate admits)? Record each answer word-for-word with the
  date; an answer given on the laptop counts only if it is repeated
  in visible chat or quoted verbatim with its source named.
  *(Corrected `2026-11-21` on the user's word (`"Correct it"`): asked all 6 defaults in visible chat; no verbatim reply appears in the visible `2026-11-20` chat record — the user did not say `"leave all 6 on default"` there. Subsequently confirmed `2026-11-21` in visible chat: user replied verbatim `"keep all six as-is"`.)*
- [x] **0.2 Record deferrals honestly.** For any question the user does
  not answer, write "deferred — executor default stands, pending
  confirmation" next to that default in the research doc. Do not
  present a deferred default as confirmed anywhere.
  *(Corrected `2026-11-21`: no verbatim confirmation happened on `2026-11-20`, so all 6 defaults were re-marked pending; then on `2026-11-21` in visible chat the user answered verbatim `"keep all six as-is"`, recorded against Q2–Q7 in `Harness spawning research-2026-11-13-EST.md` lines 222–235 with zero defaults altered in code.)*

## Track 1 — Live HarnessProposer (Step 2)

- [x] **1.1 Implement the existing `HarnessProposer` protocol with a
  live LLM-backed proposer.** An agentic session that edits a harness
  directory in place and replies with notes, per the protocol at
  `protocols.py:59`. `ScriptedProposer` stays as the test double; the
  live proposer is a separate implementation, not a rewrite of the demo.
  *(Verified `2026-11-20`: implemented `LiveHarnessProposer` in
  `src/harness/services/recursive_harnessing/proposer.py` [`185` lines],
  exported in `__init__.py`, backed by `LLMService` / `LLM_SERVICE_KEY`
  or `complete_fn`, leaving `ScriptedProposer` in `demo.py` untouched.)*
- [x] **1.2 Guards before spawn.** Every proposed tree passes
  `validate()` plus a trial run before it can spawn, behind the
  existing evidence-isolation guards (fail-closed tripwires, trial
  identity). A tree that fails validation or the trial cannot spawn,
  with the failure recorded, not silently skipped.
  *(Verified `2026-11-20`: enforced `guards.assert_no_verdicts`,
  `guards.assert_tree_clean`, `surface_ops.normalize_rel`/`is_allowed`,
  `surface_ops.validate`, and `k=1` `probe_fn` in `proposer.py` &
  `lifecycle_mixin.py`; failed validations/probes record `SpawnLifecycleState.FAILED`.)*
- [x] **1.3 Diff-review seam.** Description → tree is a trust boundary:
  a proposer that writes arbitrary tree content can write arbitrary
  always-on guidance. Before a proposed tree can spawn with write
  permissions, present a human-readable diff for review. Treat a
  proposed tree the way the dock treats a manifest: parsed, approved
  by digest, drift-checked.
  *(Verified `2026-11-20`: added `TreeDiffReview`, `build_tree_diff_review`,
  `compute_tree_sha256`, and `verify_diff_approval` in
  `src/harness/services/harness_spawner/diff_review.py` [`105` lines];
  wired `write_permitted` / `approved_tree_digest` fail-closed gate into
  `SpawnSpec`, `lifecycle_mixin.py`, and `harness spawn run --write-permitted --approve-digest`.)*
- [x] **1.4 Tests.** The live proposer is covered by tests that run in
  CI (marked `@pytest.mark.unit` where they belong in the unit gate);
  the demo still passes with `ScriptedProposer` alone.
  *(Verified `2026-11-20`: added `@pytest.mark.unit` suite
  `tests/test_live_harness_proposer.py`; `tests/test_service_recursive_harnessing.py`
  with `ScriptedProposer` demo passes alongside it [`88 passed in 6.44s`
  across 6 suites].)*

## Track 2 — Materialize as a dock-linked repo (Step 3)

- [x] **2.1 `harness spawn --materialize`.** Writes the validated tree
  plus a `dock.yaml` to a directory and links it, so a description can
  produce a durable, auditable domain harness. Reuse the dock's
  existing link/inspect path; do not invent a second linking mechanism.
  *(Verified `2026-11-20`: added `materialize_spawn_as_dock` in
  `src/harness/services/harness_spawner/materialize.py` [`151` lines]
  reusing `DefaultDockService.link()`, wired `--materialize` / `--approve-dock`
  onto `harness spawn run` in `src/harness/commands/spawn.py`.)*
- [x] **2.2 Drift-checked.** A materialized repo is drift-checked the
  way the dock manifest is: the linked tree matches the approved digest,
  and a changed tree is reported, not silently accepted.
  *(Verified `2026-11-20`: added `check_materialized_drift()` and
  `harness spawn check-drift` comparing live tree SHA-256 against
  `.harness/spawn_tree_digest.json` AND `DefaultDockService.list_docks()`
  approval status, exiting non-zero on drift.)*
- [x] **2.3 Test.** Materialize → link → `dock inspect` → `dock run`
  passes end to end on a fresh checkout, with the materialized harness
  listed by `harness spawn list`.
  *(Verified `2026-11-20`: `tests/test_harness_spawner_materialize.py::TestSpawnMaterializeAndMergePolicy::test_materialize_link_inspect_run_list_and_drift`
  passes end-to-end including `DOCK_HARNESS_OK` and drift detection.)*

## Track 3 — Merge-back policy (Step 4)

- [x] **3.1 Record the policy as a decision.** What a child may propose
  (KIs, skills, config — each named), what the parent adopts and what
  it never auto-adopts, which partition the child writes to, and who
  reviews. Written in the research doc or a decisions note, dated,
  before any code changes to the merge flow.
  *(Verified `2026-11-20`: recorded `## Merge-Back Policy Decision (2026-11-20 — Track 3.1)`
  in `Harness spawning research-2026-11-13-EST.md` covering child partition,
  `ki`/`skill`/`config` kinds, protected targets never auto-adopted, and human review.)*
- [x] **3.2 Wire the policy into the existing merge code.** The
  `propose_merge_back` / `adopt_merge_proposal` flow enforces the
  policy (adopt is explicit and reviewed; nothing merges by default).
  No silent auto-adoption anywhere.
  *(Verified `2026-11-20`: added `proposal_kind`, `reviewer`, `review_note`,
  `_validate_merge_tree_policy()`, and `reject_merge_proposal()` across
  `models.py`, `merge_mixin.py`, `persistence_mixin.py`, and `harness spawn reject` CLI.)*
- [x] **3.3 Test the full loop.** Child proposes, parent reviews and
  adopts, the adopted item lands in the parent store, a rejected
  proposal lands nowhere. Both outcomes tested.
  *(Verified `2026-11-20`: `tests/test_harness_spawner_materialize.py::TestSpawnMaterializeAndMergePolicy::test_merge_back_policy_adopt_reject_and_protected_block`
  verifies both adopt and reject + protected-target blocking.)*

## Track 4 — End-to-end acceptance

- [x] **4.1 Full loop, one description.** Description → harness →
  spawn → run a task → retire → adopt. All in one dated run, with the
  outputs recorded. This is the capability working, not its parts.
  *(Verified `2026-11-20`: `tests/test_harness_spawner_e2e.py::TestHarnessSpawnerEndToEndAcceptance::test_full_loop_from_one_description`
  passed end-to-end.)*
- [x] **4.2 Exercise the use cases.** Swarm worker (one bounded task,
  retire cleanly), domain harness (narrow skill set, one job), sandbox
  experiment (try it, adopt if good), ingestion harness (one repo, own
  partition). One run each, pass/fail recorded per use case.
  *(Verified `2026-11-20`: `tests/test_harness_spawner_e2e.py::TestHarnessSpawnerEndToEndAcceptance::test_four_use_cases_pass_cleanly`
  passed all 4 use cases.)*
- [x] **4.3 Re-run the Step 1 acceptance test.** A swarm mini-harness
  that spawns, runs a task, and retires cleanly — the test the research
  doc named for Step 1 — still passes unchanged after Steps 2–4.
  *(Verified `2026-11-20`: `tests/test_harness_spawner.py` re-run unchanged;
  all `8/8` Step 1 tests pass inside the `88 passed in 6.44s` run.)*

## Track 5 — Verification

- [x] **5.1 Re-run the gates with dated outputs.** Full unit gate,
  drift gate, vault-integrity gate, ruff check + format, and the spawn
  test suites, each with a dated log. Record numbers that reproduce on
  a fresh checkout; note any that are machine-specific.
  *(Verified `2026-11-20`:
  6 spawn/proposer/dock/recursive suites -> `88 passed in 6.44s`;
  `ruff check .` -> `All checks passed!`;
  `ruff format --check` on touched modules/tests -> `17 files already formatted`;
  `harness.cli knowledge sync --strict` -> `382 Knowledge Item(s)` synced;
  `scripts/verification/verify_track8_records.py` -> `PLAN.md` `81/0`, `28` KIs / `103` claims = `22 + 16 + 62 + 3`, `0` local mismatches;
  `tests/test_plugin_integration_drift.py` -> `12 passed in 9.27s`;
  `pytest -m "unit" -q --timeout=60` -> `2313 passed, 887 deselected, 3 warnings in 279.69s`.)*
- [ ] **5.2 Independent check.** Left unticked until a genuinely
  separate check lands. The executor must not tick it.
