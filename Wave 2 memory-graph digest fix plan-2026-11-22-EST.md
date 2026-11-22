# Wave 2 Memory-Graph Digest Fix Plan — 2026-11-22 EST

The Wave 2 independent check (2026-11-22, BH `34ef570`, verdict: substantially real) found exactly one real discrepancy: the recorded `harness-memory-graph` tree digest does not reproduce from committed code. Re-materializing with the recorded spawn ID gives tree `99ad28e7…`, but the record says `651e3357…`. The other three Wave 2 digests reproduce exactly, and the check ruled out the obvious cause (rebuilding with the pre-`9918136` `okf_engine.py` gives `b1c98118…`, not the recorded value) — so the laptop's memory-graph tree at materialization time differed from committed code in a way not recoverable from the repo. This plan re-materializes from committed code, re-records the authoritative digest, and corrects the one counting nit from the same check.

---

## Evidence Rule

Tick a box only with a commit + a passing test, a dated command output, or a written decision recorded verbatim from the user in chat. Never record a user pick that did not happen in visible conversation. Never tick `3.2 Independent check` yourself.

## Scope Limits

- No new third-party dependencies without the user's explicit approval.
- Do not touch Wave 2 plan box `3.1` (still unticked, awaiting human reader sign-off on cold-walk points #1/#5/#8) or any unticked box in any other plan.
- Do not adopt anything into live `.harness/knowledge/` (vault stays at `382` KIs); this is a record correction, not a re-execution of Wave 2.
- If the re-materialization reveals a code defect (not just a stale record), record it and stop — fixing code is a separate decision, not part of this plan.

---

## Track 0 — Re-materialize from Committed Code

- [ ] **0.1 Re-materialize `harness-memory-graph` from committed code.** From prime commit `34ef570`, re-run `harness spawn review --blueprint harness-memory-graph --json` followed by `harness spawn run --blueprint harness-memory-graph --save-dir D:\GitHub\harnesses\.spawns --materialize <fresh dir> --approve-dock --write-permitted --approve-digest <sha>` using the recorded spawn ID `spawn_harness-memory-graph_f6afb898`. Record the live `tree_sha256` and `docs_sha256` with a dated command output. Reference value from the independent check: tree `99ad28e7…`, docs `d02294cc…` (docs already reproduces) — the executor must record its own live values, not copy these.
- [ ] **0.2 Determine and record why the recorded digest differed.** The check already ruled out the pre-`9918136` `okf_engine.py` as the cause. Investigate the remaining candidates (a spec draft or mid-edit file at materialization time, an uncommitted working-tree file inside the tree, a different `prime_commit` at materialization) and record the cause in the 2.3 annotation if found. If no cause is determinable from the repo, record exactly that: "cause not determinable from the repo; the re-materialized value is authoritative."

## Track 1 — Correct the Record

- [ ] **1.1 Correct the digest in `docs/reports/spawn-wave2-adoptions-2026-11-22.md`.** Replace the `harness-memory-graph` tree digest `651e3357703ca48e04f213b036d4f9ac3824f669348f961ff0e17e31da6e8ae0` (line 14) with the re-materialized value from 0.1. Leave the docs digest `d02294cc…` unchanged (it reproduces). Annotate the row with the correction date and the check that found it.
- [ ] **1.2 Correct the Wave 2 plan 2.3 annotation.** Its claim "identical consecutive `docs_sha256` & `tree_sha256` across all 4 harnesses" is overbroad: it held for `docs_sha256` on all four and for `tree_sha256` on three, not for the memory-graph tree digest. Amend the annotation to name the exception and the corrected value (annotate, do not rewrite the original wording). Grep the repo for any other occurrence of `651e3357…` and correct each one found.
- [ ] **1.3 Correct the Wave 2 plan 4.1 counting.** "97 passed" (targeted 14-file suite) counts the collected total: live it is 88 passed + 9 engine skips. "2356 passed" (full unit gate) counts the collected total: live it is 9 failed / 2257 passed / 90 skipped / 885 deselected, the 9 failures being the known pre-existing set. Annotate both lines with the reconciled numbers (annotate, do not rewrite).

## Track 2 — Re-verify the Re-materialized Harness

- [ ] **2.1 Re-run the dock and drift gates on the re-materialized `harness-memory-graph`.** From inside the fresh materialized dir: `dock inspect`, `dock run <name> validate`, `audit-docs`, `icm-audit`, `icm-links`, and `spawn check-drift .` — all clean (`drifted: false`). Run `harness spawn cold-walk <dir>` and confirm the automated points (#2, #3, #4, #6, #7) pass; reader-judged points (#1, #5, #8) are out of scope here (Wave 2 3.1 still holds the human sign-off).

## Track 3 — Verification

- [ ] **3.1 Re-run the gates with dated outputs.** Re-run the targeted spawn/blueprint/doc-bundle/drift suites and confirm no regressions from the record corrections.
- [ ] **3.2 Independent check.** Left unticked until a genuinely separate check lands. The executor must not tick it.
