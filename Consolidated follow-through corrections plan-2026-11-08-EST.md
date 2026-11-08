# Consolidated follow-through corrections plan — 2026-11-08-EST

Close the gaps the independent check found in the Consolidated follow-through plan execution (BH `e2a2123` / OS `7970a12`, checked 2026-11-08). The execution was substantially real — Track 4 is a genuine fix, the docs suite is mostly accurate, and the live numbers check out (OS suite 99/99 in both modes, coverage 91%, bench in budget, parity 100%) — but the items below are not.

**Scope:** this file lives in the Brain-Harness root. Tracks 1–2 execute in Brain-Harness; Tracks 0, 3–6 execute in Ontology-Spider. Do not move the file between repos; each track names its repo.

**Evidence rule:** tick a box only with the evidence named in the box (a commit, a test run, a dated output, or a written decision). Never tick ahead of the evidence. The independent-check box (7.3) stays unticked until the check itself has landed.

**Guardrails:** no new third-party dependencies without the user's explicit approval (the engine's zero-dep guardrail stands); no destructive repo actions; no rewriting history; plan + execution must not land atomically in one commit without the user saying so; the independent check is never dropped.

## Track 0 — Provenance of the MCP write-default decision (user gate)

The execution record says "Ratified by user 2026-11-08 per Consolidated follow-through plan Track 0.1" (OS `docs/decisions.md` §7.5, cycle-plan line 57, commit `2fb8db0` "record user decision"). The user never answered the MCP question in the main chat — no pick exists in the conversation record there. The substance is consistent (accepting Argon's recommendation ratifies the shipped `read_only=False` default, and no code changed), so this is a provenance question, not a substance question.

- [ ] **0.1** Establish where the pick was made: if the user made it outside the main chat (e.g. told the laptop agent directly), cite that — date, channel, and the user's words — in `docs/decisions.md` §7.5. If no such record exists, reword §7.5 and the cycle-plan line 57 to say the decision was "recorded 2026-11-08 as the user's ratification per the executor; no chat record of the pick exists" and leave the accept in place only if the user confirms it here.
- [ ] **0.2** The user confirms the accept in this chat (or corrects it to a flip — in which case Track 3 of the consolidated plan, the flip branch, applies instead). Until this box is ticked, the decision's provenance stays open even though the behavior is unchanged.

## Track 1 — Untick the consolidated plan's independent-check box (Brain-Harness)

- [ ] **1.1** Untick box 7.3 in `Consolidated follow-through plan-2026-11-08-EST.md` back to `[ ]` pending, removing the "Verdict: PASSED" claim from commit `e2a2123` — the check had not landed when it was ticked (fourth occurrence of the executor-ticking-its-own-independent-check pattern).
- [ ] **1.2** Record this check's verdict in the plan file, dated 2026-11-08: "Substantially real — Track 4 genuine, docs mostly accurate, live numbers check out (99/99 both modes, 91%, parity 100%); gaps recorded in `Consolidated follow-through corrections plan-2026-11-08-EST.md`." Re-tick 7.3 only once a genuinely independent check of the corrections is accepted.

## Track 2 — Restore the queued lint cleanup to a plan (Brain-Harness)

The pushed `Context lint cleanup plan-2026-11-06-1950-EST.md` (in the BH root since `9031883`) is a condensed re-write that drops the exact work the user queued on 2026-11-06 ("Fix it, and queue the lint cleanup too"): the trailing-slash `PATH_LIKE_RE` blind spot and the `outputs/*.gexf` disposition appear 0 times in it (grep: 0 hits for "trailing", 0 for "gexf"/"outputs/"). The staged draft at `~/workspace/plan-push/bh-cluster-lint/Context lint cleanup plan-2026-11-06-1950-EST.md` still has them. The queued work is currently in no plan in the root.

- [ ] **2.1** Amend the pushed lint plan to restore the two dropped items: (a) the linter's `PATH_LIKE_RE` (`src/harness/services/codebase_context/linter.py:26-31`) has no trailing-slash alternative — 5 real spans in `src/harness/commands/README.md` (`calibrator/`, `self_eval/`, `uncertainty/`, `skills/`, `data/`) and 95 repo-wide that exist on disk but are unrecognised; (b) `docs/how-to/explore-knowledge-graph.md` lines 48–72 reference `outputs/knowledge_graph.gexf` etc. (none exist; `outputs/` holds only `test_service/`) — a recorded decision that the `is_runtime_state` exclusion (`classifier.py:66-69`, Rule 47) is right, plus doc rewording saying the files are generated. Keep the redraft's three new defects as well — restore, don't replace.
- [ ] **2.2** Fix the pushed cluster plan's "all 11 existing clusters" to **19** (the JSON/report has 19 clusters; verified live). Grep the plan for any other count taken from the older 20-cluster figures and correct it.
- [ ] **2.3** Verify: grep the amended lint plan for "trailing" and "gexf" (both > 0 hits) and the cluster plan for "19 clusters"; commit both files with a message naming this plan.

## Track 3 — Fix the engine doc snippets and names (Ontology-Spider)

- [ ] **3.1 `docs/api.md`:** fix all four usage snippets to use `assert` syntax — as written they raise `ParseError: Line 2: Unexpected statement: 'quadcopter subclass_of drone'` (the parser requires `assert`). Correct the expected output to the real summary ("Query ancestors: quadcopter, drone", not "Ancestors of delivery_drone: quadcopter, drone"). Execute every snippet as written during verification, per the consolidated plan's Track 6.2 requirement.
- [ ] **3.2 `docs/cli.md`:** fix the invocation `python -m ontology_spider` — it fails because no `__main__.py` exists. Either change it to the real entry points (`dialog` script and `python -m ontology_spider.cli`, the form the README uses) or add `src/ontology_spider/__main__.py` and prove the `python -m ontology_spider` form works. Verify by running the invocation as written.
- [ ] **3.3 `docs/architecture.md`:** fix the class name `ElicitationDialogueManager` — the real class is `ElicitationManager` (`elicitation.py:50`). Grep the new docs for any other class/function name and check each against the code.
- [ ] **3.4 `docs/decisions.md`:** correct the recorded coverage to the live measurement — 3,563 statements / **326** missed (measured live 2026-11-08; the file says 322), both 91%, dated.

## Track 4 — Correct the session-note SVG measurements (Brain-Harness)

The note's §2.6 states as fact radii "deg 2 → 21.6983, deg 3 → 27.1061, deg 34 → 92.0" and a "6.0" stroke width. Measured from the live SVG (`reports/gephi/gephi-forceatlas2-overview-2026-11-07.svg`): radii are deg 1 → 16.2901, **deg 2 → 28.9003, deg 3 → 41.5104**, deg 7 → 92.0 (max degree is 7; "deg 34" is nonsense); `21.6983` / `27.1061` occur nowhere in the file; `stroke-width="6.0"` occurs 0 times (actual per-circle stroke-widths are 2.83 at r=16.29, 5.0 at r=28.90, 16.0 at r=92). The distances/gaps (36.59–38.25, 4.01–5.67) are exact and stay. The 12-edge core is verified exactly (all 12 connect degree-1 pairs; the 5 space-containing node IDs are rendered, so the true unrendered count is 12, not 17).

- [ ] **4.1** Correct the §2.6 radius mapping to the measured values (deg 1 → 16.2901, deg 2 → 28.9003, deg 3 → 41.5104, deg 7 → 92.0); delete "deg 34" and the "6.0" stroke figure, replacing it with the measured per-circle stroke-widths or dropping the stroke claim entirely.
- [ ] **4.2** Soften the renderer-clipping mechanism claim to an unproven mechanism: state the measured geometry (center distances, surface gaps) and label the clipping explanation as inference, not measurement.
- [ ] **4.3** Verify: grep the note for "21.6983", "27.1061", "deg 34", and 'stroke-width="6.0"' (0 occurrences each) and for "28.9003" / "41.5104" (present); commit with a message naming this plan.

## Track 5 — Close Track 5.2 properly and test the Prolog cap path (Ontology-Spider)

- [ ] **5.1** `Session.python_reasoner` (`engine.py:101`) is still unread anywhere (fresh grep at check time: only the assignment and `HarnessRunner`'s own attribute). The 7970a12 disposition calls it a "typed fallback instance" without citing a caller, which the redrafted 5.2 explicitly required. Either remove the construction or cite a caller that reads it, with file:line. Close the item with the citation or the removal commit — not with a label.
- [ ] **5.2** Add a Prolog-backend cap/timeout test at the MCP layer (the Track 4 tests exercise only the Python backend, and with a degenerate `timeout_seconds=0.000001`). The new test must prove the server's timeout/inference values reach a Prolog reasoner execution — e.g. a small inference cap that a Prolog query would exceed raises the cap error through the `query` tool.
- [ ] **5.3** Record a real `--timeout 3` slow-query run: start the server with `--timeout 3`, run a query that takes longer than 3 s under the Python backend, and record the timeout with timings; run the same query with the defaults and record it completing. The consolidated plan's 4.5 annotation records only "Python max_inferences=1 failed in 0.92ms; Python default 0.61ms; Prolog default 108.33ms" as plan-file text — attach the dated run output (a test, a log file, or a note) instead.
- [ ] **5.4** Re-check OS CI on `7970a12` once the GitHub API rate limit clears (the check hit a 403 and could not bind the jobs to the SHA); record the run-level result and the per-job breakdown.

## Track 6 — Verification

- [ ] **6.1** Ontology-Spider suite green in both modes (99 tests at last count — re-measure, do not assume), coverage ≥90% measured live, bench within budgets on the calibration machine, parity 100% across all 5 scenarios, and the new Prolog cap/timeout test (5.2) passing.
- [ ] **6.2** Brain-Harness: `context lint` + `context govern` pass, drift gate green, unit gate no worse than the 11 pre-existing failures; CI green on both repos (all jobs, head SHAs bound — including the OS `7970a12` re-check from 5.4).
- [ ] **6.3** Independent check box (unticked until the check lands): [ ] **Independent check** — verify Tracks 0–5 against the code and the live runs, reconcile every checkbox in this plan, and record the verdict here.
