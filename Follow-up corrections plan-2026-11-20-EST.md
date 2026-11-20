# Follow-up corrections plan — 2026-11-20-EST

Small follow-up to the post-experiment corrections plan
(`Post-experiment corrections plan-2026-11-19-EST.md`, BH `56d2672`).
Parent plan now reads 30/31 ticked, only 8.3 (the independent check) unticked.

Heads checked: Brain-Harness `e6cf4f1`, Ontology-Spider `fe9d6ac`.
Both CI green. Verdict on the execution: substantially real.

This plan fixes only what that check found still open: one false figure
(5.5), one unconfirmed user decision (7.3), one arithmetic slip (8.2),
two scripts cited but absent from the repo, and the next cycle the
Track 3 work exposed (3.1). Nothing else. It does not re-open any
ticked box, and it does not touch the spawn provenance boxes, the
triad forge citations plan, or any other unticked box.

Staged, not pushed. Needs the user's word in chat to push it to the
Brain-Harness root so it can be pulled on the laptop and handed to
Flash. Track 0 cannot execute until the user answers the one question
in 0.1; Tracks 1–2 can run without that answer.

Evidence rule, same as the parent plan: tick a box only with a commit
plus a test, a dated live output, or a written decision. Never tick
an independent-check box yourself; never record a user pick that did
not happen in visible conversation.

## Track 0 — Rank 7 / 7.3 confirmation gate (user decision)

The record in Ontology-Spider `docs/decisions.md` §7.15 (lines 239–242,
OS `fe9d6ac`) says Rank 7 was "Ratified by the user in chat (2026-11-19
interactive `ask_question` prompt — option: 'Ratify: Keep path/count/not
+ retract_turn/session_save/restore & record in decisions §7.15')",
and honestly notes it was "ratified without a recorded trigger". That
pick does not appear in the main chat, and there is no session,
transcript, or user words anywhere in either repo. Same shape as the
Harness2 "User confirmed option (b)" and the spawn Q2–Q7 claims, both
previously proven false. One line from the user settles it.

- [ ] **0.1 Ask the user, in chat, one question.** Did you answer an
  `ask_question` prompt in Antigravity on 2026-11-19 and pick "Ratify:
  Keep path/count/not + retract_turn/session_save/restore"? Record the
  answer verbatim. Do not proceed to 0.2 on an assumption.
- [ ] **0.2 Record the answer in `docs/decisions.md` §7.15.**
  If yes: keep "Ratified", add the session/transcript reference (or
  record honestly that none exists), and record the trigger status as
  stated. If no: correct the record to "unconfirmed — no transcript
  in-repo", and re-open the ratify-or-revert decision as the user's
  call. Either way the record must match what the user actually said.
- [ ] **0.3 Tick 7.3 in the parent plan only on the user's word.**
  The executor must not tick it. If the answer is "no", 7.3 stays
  unticked until the ratify-or-revert call is made and recorded.

## Track 1 — 5.5 figure: "26 files already formatted" is wrong

`experiments/spider_decisions/ACTION_SUMMARY.md:64` quotes
`ruff format --check experiments/spider_decisions` as
"26 files already formatted", with a parenthetical added 2026-11-19
claiming 26 `.py` files and a "CI scoped format check covers 70 files".
Re-checked live 2026-11-20 (BH `e6cf4f1`, via the dock venv ruff):
the command reports **57 files already formatted**. The mechanism,
from `ruff --verbose`: this repo's ruff config formats Markdown too,
so the 57 is 26 `.py` + 31 `.md` files. The parenthetical is wrong on
both counts as an explanation of the quoted command — the command
covers 57 files, not 26 and not 70, and the "70" figure is sourced
nowhere.

- [ ] **1.1 Correct the quoted figure in `ACTION_SUMMARY.md:64`.**
  `26 files already formatted` → `57 files already formatted`, from a
  live run of the exact quoted command. Quote the command and its
  output, dated.
- [ ] **1.2 Fix the parenthetical.** Replace it with the verified
  breakdown: 26 `.py` + 31 `.md` = 57 files. Remove the "70 files"
  claim unless a live run sources it.
- [ ] **1.3 Annotate the same quote in `ACTION_LOG.md`.** The
  "26 files already formatted" quote appears six times
  (lines 22, 29, 35, 41, 53, 71). Annotate each as superseded by the
  57 figure; do not silently rewrite the historical quotes, same
  precedent as the parent plan's Track 2.1 (annotate, don't delete).

## Track 2 — 8.2 arithmetic and the missing scripts

- [ ] **2.1 Reconcile the 103-claim total.** The parent plan (lines
  172 and 412) says 28 KIs / 103 claims audited, with
  `local_verified=22`, `external_verified=16`,
  `missing_hash_flagged=62`. 22 + 16 + 62 = 100, not 103 — and
  38 hash-bearing claims (22 + 16) + 62 missing-hash = 100 as well.
  Account for the 3 missing claims, or correct the total to 100, in
  both places, with the recompute shown.
- [ ] **2.2 Commit the hash restamping script(s) to the repo.**
  The 12 hashes were re-stamped and the values verify, but the script
  that did it is not in the repo, so the restamp cannot be re-run.
  Commit it and re-run the restamp from the committed copy to prove
  reproducibility.
- [ ] **2.3 Commit `verify_track8_records.py` or correct the
  citation.** The parent plan line 171 cites it as Track 8 evidence,
  but no file of that name exists in the repo at `e6cf4f1`. Commit it
  from wherever it lives, or correct the citation to where it lives.

## Track 3 — 3.1 next cycle: scope it, do not fix it here

Breaking the services→creator edge exposed the next cycle, recorded
honestly in the parent plan's fallback. Verified live 2026-11-20 in
`experiments/spider_decisions/results/p09/refactor_order.json` at
`e6cf4f1`: `spider_cycle_violations` is
`["services -> plugins -> services"]`, inside the intact 6-unit
Tarjan SCC (`creator`, `events`, `ingestion`, `kernel`, `plugins`,
`services`), alongside `kernel <-> events`, `kernel <-> plugins`,
`creator <-> ingestion`, and `plugins <-> ingestion`. This is the
next, bigger job — a scope-and-decision track, not a fix track.

- [ ] **3.1 Confirm the cycle live and write the options.** Re-run
  the model validation, confirm the witness cycle, and write up the
  options with their costs: break the services↔plugins edge, accept
  the 6-unit SCC with a recorded decision, or defer it with a reason.
- [ ] **3.2 Get the user's pick on scope.** Do not start breaking the
  cycle in this plan. The pick (fix next / accept / defer) is recorded
  as a decision before any follow-up plan is written.

## Track 4 — Verification

- [ ] **4.1 Re-run the gates.** `ruff check`, the format check with
  its live count, the vault-integrity gate over the touched KIs, and
  the affected test suites. Record dated outputs.
- [ ] **4.2 Independent check.** Left unticked until a genuinely
  separate check lands. The executor must not tick it.
