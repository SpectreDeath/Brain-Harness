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

- [ ] **0.1 Ask the user the six questions in chat and record the
  answers verbatim.** Depth (default 1, hard cap 3)? Merge-back
  (reviewed-only)? Budget (max_tokens=16,000, k=1→4 rollouts / 3
  sessions)? Lifetime (task + persistent)? Visibility (headless CLI)?
  Description / admission gate (who writes the description, what the
  k=1 probe gate admits)? Record each answer word-for-word with the
  date; an answer given on the laptop counts only if it is repeated
  in visible chat or quoted verbatim with its source named.
- [ ] **0.2 Record deferrals honestly.** For any question the user does
  not answer, write "deferred — executor default stands, pending
  confirmation" next to that default in the research doc. Do not
  present a deferred default as confirmed anywhere.

## Track 1 — Live HarnessProposer (Step 2)

- [ ] **1.1 Implement the existing `HarnessProposer` protocol with a
  live LLM-backed proposer.** An agentic session that edits a harness
  directory in place and replies with notes, per the protocol at
  `protocols.py:59`. `ScriptedProposer` stays as the test double; the
  live proposer is a separate implementation, not a rewrite of the demo.
- [ ] **1.2 Guards before spawn.** Every proposed tree passes
  `validate()` plus a trial run before it can spawn, behind the
  existing evidence-isolation guards (fail-closed tripwires, trial
  identity). A tree that fails validation or the trial cannot spawn,
  with the failure recorded, not silently skipped.
- [ ] **1.3 Diff-review seam.** Description → tree is a trust boundary:
  a proposer that writes arbitrary tree content can write arbitrary
  always-on guidance. Before a proposed tree can spawn with write
  permissions, present a human-readable diff for review. Treat a
  proposed tree the way the dock treats a manifest: parsed, approved
  by digest, drift-checked.
- [ ] **1.4 Tests.** The live proposer is covered by tests that run in
  CI (marked `@pytest.mark.unit` where they belong in the unit gate);
  the demo still passes with `ScriptedProposer` alone.

## Track 2 — Materialize as a dock-linked repo (Step 3)

- [ ] **2.1 `harness spawn --materialize`.** Writes the validated tree
  plus a `dock.yaml` to a directory and links it, so a description can
  produce a durable, auditable domain harness. Reuse the dock's
  existing link/inspect path; do not invent a second linking mechanism.
- [ ] **2.2 Drift-checked.** A materialized repo is drift-checked the
  way the dock manifest is: the linked tree matches the approved digest,
  and a changed tree is reported, not silently accepted.
- [ ] **2.3 Test.** Materialize → link → `dock inspect` → `dock run`
  passes end to end on a fresh checkout, with the materialized harness
  listed by `harness spawn list`.

## Track 3 — Merge-back policy (Step 4)

- [ ] **3.1 Record the policy as a decision.** What a child may propose
  (KIs, skills, config — each named), what the parent adopts and what
  it never auto-adopts, which partition the child writes to, and who
  reviews. Written in the research doc or a decisions note, dated,
  before any code changes to the merge flow.
- [ ] **3.2 Wire the policy into the existing merge code.** The
  `propose_merge_back` / `adopt_merge_proposal` flow enforces the
  policy (adopt is explicit and reviewed; nothing merges by default).
  No silent auto-adoption anywhere.
- [ ] **3.3 Test the full loop.** Child proposes, parent reviews and
  adopts, the adopted item lands in the parent store, a rejected
  proposal lands nowhere. Both outcomes tested.

## Track 4 — End-to-end acceptance

- [ ] **4.1 Full loop, one description.** Description → harness →
  spawn → run a task → retire → adopt. All in one dated run, with the
  outputs recorded. This is the capability working, not its parts.
- [ ] **4.2 Exercise the use cases.** Swarm worker (one bounded task,
  retire cleanly), domain harness (narrow skill set, one job), sandbox
  experiment (try it, adopt if good), ingestion harness (one repo, own
  partition). One run each, pass/fail recorded per use case.
- [ ] **4.3 Re-run the Step 1 acceptance test.** A swarm mini-harness
  that spawns, runs a task, and retires cleanly — the test the research
  doc named for Step 1 — still passes unchanged after Steps 2–4.

## Track 5 — Verification

- [ ] **5.1 Re-run the gates with dated outputs.** Full unit gate,
  drift gate, vault-integrity gate, ruff check + format, and the spawn
  test suites, each with a dated log. Record numbers that reproduce on
  a fresh checkout; note any that are machine-specific.
- [ ] **5.2 Independent check.** Left unticked until a genuinely
  separate check lands. The executor must not tick it.
