# Follow-up analysis and plan — 2026-11-03

**Head:** `7774930` ("integrate REditorSupport and Agent-Reach via repo-triad-forge").
**Built from:** the Nov 1 review of `380cd64` and the Nov 2 reviews of `c5cea93` and `7774930`,
with every claim below re-verified against the local clone on 2026-11-03 before writing.
No new full analysis round was run; this plan consolidates verified findings into pickable work.
**Boundary:** read-only analysis except this plan doc itself. No deletions, no repo edits
beyond the track the user picks. The user works in the repo in parallel; tracks are written
so they can be picked one at a time without colliding.

## Current state, verified 2026-11-03 at `7774930`

- Canonical plugins: **138** (depth-3 manifests, `category != external`), external bundles: **1**.
  The drift gate (`tests/test_plugin_integration_drift.py:101`) allows `(134, 135, 136)` and
  therefore **fails**: `Expected 134-136 canonical plugins, found 138` (reproduced by test run).
- Skill directories: **103**. Vault items: **301** (289 `ACTIVE`, **12 with no `status`**).
- Stored edges still **188**. Items with `retrieval_count >= 5`: **0** — no lifecycle
  transition has fired on disk yet.
- `hyperframes_renderer/plugin.json` is invalid JSON: a literal `\n` after the closing brace
  (pre-existing, commit `223a424`, not from a recent push). Loader impact not proven by a live run.
- Plan checkbox states, unchanged since Nov 1: plugin integration **16/44**, REA toolkit **3/35**,
  Agent Dock **33/40** (7 unticked are Track 7 deferred-by-design, correct), post-KG **31/31**.
- Standing gaps from Nov 1, all still present: Gephi never actually opened (headless validation
  twice); dock enforcement is string-pattern filtering with `shell=True`, not a sandbox;
  `dock tools` names unverified against ToolRegistry; joint-query KI side is a hand-rolled
  directory scan, not the real KI query service; `integrated-toolkits.md` REA row is wrong
  (`service.rea`, nonexistent commands); README counts drifted again (plugins "135" vs 138+1,
  skills "95" vs 103); dock test holes and non-hermetic CLI tests.
- New pattern since Nov 2: triad-forge-created vault items systematically lack `status`
  (4 TokenEconomizer + 4 R + 4 agent-reach = 12), while EGM/ICM items from the same period
  carry `ACTIVE`. The forge skill spec itself requires `status` in `metadata.json`
  (`.agents/skills/repo-triad-forge/SKILL.md:88`) — the writer drops it, the spec does not.

## Suggested order

Track 0 first (CI is red), then Tracks 1–2 (tiny, fast), then Tracks 3–4 (paperwork batch),
then Tracks 5–7 in order. The user picks one track at a time; nothing here is started unasked.

## Track 0 — Drift gate: derive the count, don't widen it again

The gate has now been widened twice (exactly 134, then 134–136) and broken twice, once per
plugin-adding push. A third widening repeats the cycle and is a stopgap only.

- [ ] Reproduce the failure: run `test_canonical_plugin_counts_and_exclusion` (fails, 138 found).
- [ ] Replace the magic range with a derived expectation: the test should compute the expected
      count from the same discovery the loader uses (or from a single shared scanner), so adding
      a plugin changes the count in exactly one place — the tree itself — and the test passes
      without a test edit. Keep the `.claude-plugin` exclusion and the external-bundle assertions.
- [ ] Alternative, explicitly labeled stopgap if the derived form is deferred: widen the range to
      cover 138, with a comment naming it a stopgap and pointing at this track.
- [ ] Verify: drift test passes; adding a throwaway manifest changes the derived count without
      touching the test (or, for the stopgap, the widened range passes and the stopgap comment exists).

## Track 1 — Hyperframes manifest: one-character fix plus a live load check

- [ ] Remove the literal `\n` after the closing brace in
      `plugins/developer_tooling/hyperframes_renderer/plugin.json`; confirm it parses as JSON.
- [ ] Run the loader live against the fixed manifest and record whether the plugin loads or is
      skipped with a warning — settle the open loader question instead of leaving it inferred.
- [ ] Add a manifest-validity check to the drift gate (every `plugin.json` in the tree parses
      as JSON) so this class cannot recur silently. Keep it to parsing only; no new validation
      schema unless a real limitation is hit.

## Track 2 — Status backfill plus a creation-path default

- [ ] Backfill `status: "ACTIVE"` on the 12 status-less items, after confirming none of them is
      meant to be non-ACTIVE (they are all newly created; none carries edges or retrieval history
      suggesting otherwise).
- [ ] Locate the triad-forge vault-item creation path (not yet located) and find where `status`
      is dropped despite the skill spec requiring it. Check what the EGM/ICM creation path does
      differently and copy that rather than inventing a new mechanism.
- [ ] Add the `status` default at that one creation point, so new forge items carry it from birth.
- [ ] Re-run the census: 301/301 items with `status`, 0 without. Record the result in the plan.

## Track 3 — Checkbox reconciliation (paperwork, no code)

The Nov 1 finding stands: plugin integration and REA work is ~85–90% built, but the plans say
16/44 and 3/35. Until the plans are reconciled, every future round re-verifies the same work.

- [ ] Tick the plugin-plan build items verified Nov 1 (gev/mantis/rea/memory/context CLI + facade
      + skill, REA learn loop, facet-verifier integration, joint query, memory-partition and
      DAG-layering decisions, external-bundle trust/counting rule), annotating each with its file.
- [ ] Tick the REA-plan build items verified Nov 1 (CLI group, facade, skill, learn loop, facet
      integration, aliases, MCP resources), annotating the same way.
- [ ] Annotate, don't tick, the verified exceptions: REA panel is API-only (no React panel);
      joint-query KI side is hand-rolled (see Track 6); `integrated-toolkits.md` REA row is wrong
      (see Track 4). The GEV control-room decision (file-based rendering, no dashboard view) is
      recorded in docs and can be ticked.
- [ ] Verify: a reader can check any ticked item against its cited file without re-running the
      Nov 1 review.

## Track 4 — Doc drift: fix the rows, then decide the rule

- [ ] Fix the `integrated-toolkits.md` REA row: service key `service.rea_toolkit` (not
      `service.rea`), command list the real 10 `harness rea` subcommands (not
      `dissect|obligations|report`). Extend a drift test to cover this file — the current gates
      check the how-to and `cli.md` only, which is why the mismatch escapes.
- [ ] Fix the README counts under the locked counting rule: plugins "135" → 138 canonical + 1
      external bundle; skills "95" → 103.
- [ ] Decide the durable rule and record it: either extend a drift gate to assert README counts,
      or mark README counts as "as of <commit>" snapshots that are allowed to drift. Leaving the
      rule undecided is what produced the current drift; either decision is acceptable, ambiguity
      is not.

## Track 5 — Dock trust hardening

The dock design matches its plan and is fine for trusted repos. These items close the gap
between what the trust story claims and what the code enforces, for untrusted docks.

- [ ] Verify `dock tools` against real ToolRegistry names, or relabel the output as "declared
      tool names, unverified" — the current `cli.md` wording ("callable tools") overclaims.
- [ ] Harden approval: show full step commands at `link` time (or require `dock inspect` output
      before approval), so approval is informed rather than digest-only.
- [ ] Close the generic-dock drift hole: give generic docks a synthesized SHA (e.g. hash of the
      synthesized manifest) so drift protection applies uniformly, or document why generic docks
      are exempt.
- [ ] Close the test holes: env scrubbing, step-failure-stops-later-steps, `expected_output`
      mismatch, boundary refusal through `run()` (not just the `check_command_safety` unit test),
      generic fallback via CLI `inspect`, `list` showing `manifest_changed`.
- [ ] Make dock CLI tests hermetic (isolated state file / isolated filesystem) so running them
      cannot write link records into a real checkout.
- [ ] Correct the docs traversal claim (`agent-dock.md` trust point 4): what is enforced is
      workdir confinement of the step's cwd, not general `../` refusal of command arguments —
      or extend enforcement to command path arguments if the claim is intended to hold.
- [ ] Record the honest boundary in the doc: enforcement is string-pattern filtering, not a
      sandbox; approval of an untrusted dock means approving shell. No Track 7 item is built here
      unless a limitation is hit (see Track 8).

## Track 6 — Joint query: route through the real KI service, or record why not

- [ ] Route the KI side of `query_knowledge_and_skills` through the storage/retrieval or
      `KnowledgeGraphQueryService` path instead of the hand-rolled `metadata.json` directory scan
      (`joint_query.py:31-34`), so lineage links are `became_skill` edges rather than heuristic
      `domain_lineage` string matches.
- [ ] Or, if the direct scan is intentional (e.g. latency, dependency), record the reason in the
      module and in the plan, and close the item as decided — not as silently divergent.
- [ ] Verify: joint-query output is unchanged for the documented cases, or the differences are
      recorded.

## Track 7 — Lifecycle proof and Gephi, actually done this time

- [ ] Prove the lifecycle loop end-to-end on real data: either wait for retrieval traffic to push
      items past `min_retrievals=5` (currently 0 items qualify), or lower the threshold in a test
      run and record the outcome. The daemon hook exists; the observable transition does not yet.
- [ ] Open the post-backfill GEXF in Gephi (and GraphML in Cytoscape/yEd) and replace the
      headless-validation note with a render report. This is the third round this item appears;
      a human seeing the graph render is the verification, not another schema re-parse.
- [ ] Line-verify the 7-tuple temporal evidence properties on IsnadClaim nodes in the Cypher
      exporter, or amend the spec to what the exporter actually emits.

## Track 8 — Deferred by design (no action)

The Agent Dock plan's Track 7 items (strict schema rejection, policy engine, central registry,
multi-harness spec, MCP exposure, conditional/loop/matrix steps, manifest versioning) stay
unbuilt unless a real limitation is hit. The user's rule stands: simplicity first, no upfront
over-engineering. If any Track 7 item gets built without a documented limitation, that is scope
drift and should be called out in the next round.

## §11 — Verification backlog (live runs still owed)

- [ ] REA `learn` end-to-end on a real artifact (unit/CLI tests exist; a live run does not).
- [ ] GEV live feeds and the full mantis pipeline (same status: tested, not live-run).
- [ ] Hyperframes load after the Track 1 fix (see Track 1).
- [ ] Lifecycle transition on disk (see Track 7).
- [ ] Gephi/Cytoscape/yEd render report (see Track 7).
- [ ] Triad-forge creation path location (see Track 2) — the one structural unknown in this plan.
