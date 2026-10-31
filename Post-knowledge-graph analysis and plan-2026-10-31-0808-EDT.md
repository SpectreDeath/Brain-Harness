# Brain Harness — Post-Knowledge-Graph Analysis and Plan

**Created:** 2026-10-31 08:08 EDT
**Repo:** `SpectreDeath/brain-harness`
**HEAD analyzed:** `0ef3a44` ("feat(knowledge-graph): complete Tracks 0-8 of knowledge graph interaction plan")
**Purpose:** Second round in the established cycle: verify the 2026-10-29 knowledge-graph interaction plan's completion, analyze the current state, and set the next plan. The plan file on main shows 48/49 items ticked; the only unticked item is the conditional Neo4j verification (line 183).
**Method:** Read-only pass over a local clone, four area passes (exports/derivation, edges-real/learning loop, CLI/UI/Neo4j/timeline, hygiene/docs/health). No test-suite run this pass; one area ran targeted non-suite checks in a scratch venv (full sync, double-backfill, round-trip export to /tmp). Counts are disk reads or grep-based unless marked empirical. The highest-severity claims were spot-checked by the author against the clone (SQLite engine callers, `shared_category`, sync backfill call, `--apply-contradictions` branch).
**Baseline census (2026-10-31, local clone):** 282 items (281 + the Headroom item from `77ceb2f`), all with status/category/tags, 79 items carrying edges, 188 total stored edges (108 `references_code`, 54 `same_domain`, 18 `became_skill`, 8 `became_plugin`; 161 derived, 27 asserted). All 282 items are `ACTIVE`; only 15 carry retrieval stats; zero `supersedes`/`contradicts` edges exist on disk.

## Verdict

The knowledge-graph plan genuinely landed. The vault went from zero stored edges to a real, typed, queryable graph with five export formats, six new CLI commands, a control-room view, and a drift gate — and the migration preserved every existing metadata key. But this round's pattern is different from the last one: the engines are real, while the *claims about them* are ahead of reality in several places. The plan file says "complete" for items that are test-only, display-only, or verified against stale numbers, and there is one live data-loss path left. The next plan is therefore mostly a hardening and honesty pass, not a new feature build.

## 1. What genuinely closed

### Exports and derivation (Tracks 0–1)

- `harness knowledge export` exists with five formats (`json | gexf | graphml | html | cypher`, `reflection.py:353`) and the plan's flags (`--out` defaulting to `outputs/`, `--nodes all|ki-only`, `--include-single-tag-edges` off by default, `--include-shared-source` off by default, `--max-tag-freq` 0.15, `--min-confidence`, `--dynamic`, `--open`).
- One derivation engine, no per-format re-implementation: `derive_graph` (`vault_graph.py:59`) delegates to `derive_knowledge_graph` (`vault_derivation.py:19`); all writers take a `DerivedKnowledgeGraph` via `export_knowledge_graph` (`vault_exporters.py:170`). The CLI, the API route, and the MCP read path all call the same function.
- Edge rules as specified: stored edges included unconditionally (subject only to node filter / min confidence); `same_domain` requires same non-`general` domain plus 2+ shared non-mega tags (confidence 0.80), or 1 shared tag with the flag on (0.60). The mega-tag cap is real and reported (exactly `{endogenous_memory, self_reflection}` excluded at 0.15 on the current vault, reported in the summary object, CLI stdout, JSON, and HTML cards).
- Rule 40 holds: `.gitignore` ignores `.harness/*` except `knowledge/`/`config.json`/`*.py` and ignores `outputs/`; `validate_export_path` rejects targets inside the vault, is wired into the CLI, and is test-covered; no generated export lives inside `.harness/knowledge/`.
- Test coverage is substantial: fixture graph per-format tests (zero dangling edges, attribute checks), CLI end-to-end fixture-vault test, derivation tests including a live-vault integrity test, and a doc-drift test pinning documented commands and attribute names against live code.

### Edges real and the learning loop (Track 2)

- `propose_links` is wired into the save path: `creator/reflection/engine.py:74-80` calls it before saving, with a dedupe guard; both distillation entries (`knowledge reflect`, daemon worker) funnel through it. Skill-scaffold write-back is real: `scaffold.py:227-244` appends a `became_skill` edge (`derived=False`, confidence 1.0, deduped) to the source KI.
- Backfill includes `same_domain` plus `--dry-run`/`--commit` (`vault_backfill.py:52-140`), with mega-tag exclusion, `references_code` from `references`, `became_skill` from `skill:` tags, `became_plugin`, and canonical-direction `supersedes`. Bare invocation modifies nothing (dry-run is the default).
- Disk migration preserved everything: comparing key sets at `f0eb2b3` vs now, zero items lost a key; in-place export is a genuine read-modify-write merge (`vault_operations.py:105-138`).
- Retrieval exclusion is exactly per plan: `ARCHIVED` and `SUPERSEDED` skipped, `CHALLENGED` ×0.25, `PROMOTED` ×1.25, `DEMOTED` ×0.5 (`vault_retrieval.py`).
- Lifecycle command and contradiction-apply exist as commands: `knowledge lifecycle` (`reflection.py:548`) runs `evaluate_vault_lifecycle` and displays `audit_contradictions`, persisting status to store and disk; `knowledge resolve <a> <b> --action supersede|contradict|dismiss` (`reflection.py:599+`) writes the edge and updates `status`/`superseded_by` on disk.
- The plan's own flagged sync failures are fixed: `str` isnad normalized (`vault_taxonomy.py`, empirically 282/282 synced, zero missing); `LEGACY_CATEGORY_MAP` expanded (empirically zero items collapsing to `general` despite a non-empty raw category); backfill idempotent (re-runs add zero edges).

### CLI, control room (Tracks 3–4)

- All six CLI query commands exist (`stats` 654, `neighbors` 702, `path` 746, `topic` 795, `dependents` 829, `orphans` 854 in `reflection.py`), alongside the Oct 29 set plus new `export`, `backfill`, `lifecycle`, `resolve`, `hygiene`, `timeline`.
- Rule 55 holds in code: `find_path` → plain BFS over stored graph edges with no fallback and no synthesis; all failure modes return `{status: "no_path", chain: [], length: 0, hops: []}` and the CLI prints the explicit no-synthetic-edges message.
- Control-room must-verify resolved: frontend source is repo-root `frontend/`; `app.py` serves `frontend/dist` when built, falling back to `ui/static/index.html` for pip installs. API routes are real and single-sourced (`routes/knowledge.py`: `GET /graph`, `GET /graph/html`, `GET /contradictions`, `POST /contradictions/resolve`, all via the same `derive_graph`).
- React graph tab is real with contradiction review built in, not deferred (`GraphView.tsx`: `'knowledge'` mode, contradiction queue with Supersede/Conflict/Dismiss actions, zero new npm dependencies). The static dashboard has parity (Knowledge Vault Graph view with resolve buttons).
- MCP parity: `harness://knowledge/graph` and `harness://knowledge/contradictions` registered, read path calls the same `derive_graph`.

### Hygiene and docs (Tracks 7–8)

- Hygiene is real: 0 uncategorized (was 160), 0 untagged (was 21), 188 stored edges, zero keys stripped. `knowledge hygiene` prints suggestions by default and persists only with explicit `--apply` — the human-confirm gate the plan required.
- How-to doc exists and matches: `docs/how-to/explore-knowledge-graph.md` documents 9 core commands, all present in the live registry; the drift test asserts doc commands ⊆ live registry, core commands ⊆ doc, and attribute names match dataclass fields.
- `docs/reference/cli.md:249-267` documents 17 knowledge subcommands. The post-plan analysis gained `[RESOLVED 2026-10-30]` markers on the §2 High items and the graph item.
- Headroom interaction is clean: `77ceb2f`'s vault item was the only pre-KG item carrying edges (4 asserted edges, including the `became_plugin` vocabulary the KG commit generalized), and the KG commit preserved all 4 byte-for-byte in spirit.

## 2. What is overstated, partial, or broken, ranked

### High

- **Fresh-directory export strips historical keys — the one live data-loss path.** `KnowledgeItemRecord` carries no extra-keys field (pydantic drops unknown keys at sync), so `export_single_item` can only preserve historical keys by re-reading an existing target file. Empirically, a sync → export-to-fresh-dir → re-sync round-trip preserved all 282 items and 188 edges but stripped keys from 225/282 items (`created`, `updated`, `summary`, `references`, `claims`, `source_commit`, `source_uri`, …). The plan's "preserve all non-standard keys" claim holds for the in-place migration only. Anyone seeding a new vault location from an export silently loses history.
- **The SQLite graph engine is test-only dead code.** `vault_sqlite_graph.py` implements the `ki_edges` table, a `WITH RECURSIVE` cycle-safe path query, and transitive dependents, all tested — but it has zero production callers (author spot-check confirmed: no references outside its own file). It is not wired into `sync_knowledge_vault` as the plan specified, and no CLI command or UI route calls it. It also lives in `vault_sqlite_graph.py`, not `src/harness/services/storage/sqlite.py` as specified.
- **Sync-backfill reads the wrong vault under a custom `--vault`.** `sync_knowledge_vault` calls `backfill_edges_mechanically([ki])` without passing `vault_dir` (`vault_operations.py:111`, author-confirmed), so references harvesting reads the default `.harness/knowledge` instead of the caller's vault. The single-item call also means `same_domain` can never come from sync-backfill (it needs pairs) — harmless now that disk has them, but misleading.
- **The default export is a starburst, not a mesh — and the plan's numbers describe a stale state.** The plan's verification note (299 nodes, 25 edges) predates the migration that wrote 184 of the 188 stored edges; it is not reproducible from any git-recoverable state. A current default export is 188 edges / 398 nodes (282 KI + 116 external), of which 134 are KI→external spokes and only 54 are KI→KI. On the KI-only subgraph that is 239 components, largest 6, 210 isolated KIs — not the Oct 29 census's giant component of 236, which counted similarity edges the exporter deliberately does not emit by default. The Gephi doc never mentions the mesh flags (`--include-single-tag-edges`, `--include-shared-source`) that produce a connected graph, and its Timeline step presumes `--dynamic` without saying so.
- **Gephi/Cytoscape/yEd were never actually opened.** The plan note admits the check was stdlib XML re-parsing with zero dangling edges. The item ("open a real export in Gephi") is struck through on weaker evidence than it claims.
- **No automatic lifecycle trigger.** No `evaluate_vault_lifecycle` call exists in `creator/reflection/` or the daemon worker. The plan marked the hook optional, so no promise is broken — but the maintenance loop still runs only when a human remembers, and on real data it has effectively never fired (all 282 `ACTIVE`, 15 with retrieval stats, zero `supersedes`/`contradicts` edges).
- **`--apply-contradictions` does not apply anything.** The flag only displays the contradiction queue (`reflection.py:592`: `if apply_contradictions or conflicts:`); resolution still requires a manual `knowledge resolve` per pair. The name overpromises.

### Medium

- **Shared-category edges were never implemented.** Track 0 lists them as a derivation rule and the Oct 29 census counted 459, but `shared_category` has zero matches in `src/` (author-confirmed). The exporter emits `same_domain` and flag-gated `shared_source`, but no pure shared-category edge type.
- **Summary block is not in every format.** Full summary in JSON and HTML cards; CLI stdout lacks edges-by-type and untagged/uncategorized counts; GEXF carries only a one-line counts description in `<meta>`; GraphML has no summary element at all; Cypher has only a header comment.
- **Golden test is half-built.** The CLI fixture-vault test asserts exit codes and file existence only, never node/edge counts; per-format counts are asserted only on a synthetic hand-built graph, never on a vault. The live-vault test bound (`total_edges >= 7`) passes at 7, 25, and 188 alike — too weak to catch an edge-drop recurrence.
- **Neo4j gate has no recorded outcome.** No commit message, doc, or comment states the gate passed, yet the Cypher exporter was built despite the plan's "If triggered" wording. The five justifying Cypher queries are documented nowhere (the how-to doc shows only the export command), and the exporter omits the plan-specified `IsnadClaim` nodes and 7-tuple temporal evidence properties — silent spec drift. No driver was added to `pyproject.toml`, correctly per the dependency guardrail. The plan's sole unticked item (line 183) stays open precisely because the gate was never demonstrably passed.
- **Paperwork gaps in Track 8.** The post-plan analysis RESOLVED markers contain zero commit hashes, though the plan item explicitly required them. `cli.md` omits pre-existing `reflect` and `lineage`, which the plan item named (the drift test passes anyway because its cli.md check covers only the core 9). Track 7's "record before/after hygiene telemetry in the plan progress notes" is ticked, but the plan file has no progress-notes section and no post-hygiene census numbers.
- **"Isolated" now has four incompatible definitions.** Capped-derived: 3. No-cap derived: 0 isolated (2 components, 278 + 4). Stored-KI→KI only: 210 without a stored edge to another KI. Shipped `orphans` definition (no edge in the derived graph, stored or derived): at least 2 confirmed. The CLI prints "Isolated KIs: 210" with no explanation of the definition, which will read as a regression against the old "33 isolated."
- **Silent per-item sync skips remain.** The per-item try/except in `sync_knowledge_vault` still skips a failed item with only a warning log; the sole signal is a lower sync count, and no command lists skipped items.
- **Cwd-relative vault paths.** The scaffold write-back uses cwd-relative `Path(".harness/knowledge")` (`scaffold.py:228`, failures swallowed at debug level), and sync-time backfill uses the wrapper default, so `references`-derived edges are silently skipped outside the repo root.
- **Timeline partials.** `knowledge stats` reports only an aggregate `date_coverage_count`, not the specified breakdown (274 from metadata/ID + 8 from git history); no date-source field exists in the summary model. `knowledge timeline` omits the mega-tag 15%-threshold crossing dates and retrieval velocity the plan specified.
- **Dynamic GEXF end-date quirk.** For `SUPERSEDED`/`ARCHIVED` nodes, `end` equals `start` (`vault_exporters.py:79-81`) — a zero-length span on Gephi's timeline, not a real end date. No supersession/end-date field exists in the model.

### Lower

- **Dead `file:///` links in `docs/domains/`** (2, pre-existing, Rule 47 violation, same class as the previously fixed skills links), last touched by `acc4b87`, outside the drift test's scope (it checks only the new how-to doc).
- **Stale README counts persist.** Skills README still says "50 Deep-Module Skills" vs 95 actual; plugins README says "134 Plugins" vs 135 canonical dirs (137 `plugin.json` files total, but 2 are nested `.claude-plugin` metadata, not harness plugins).
- **Nits.** Migration re-serialized all 302 vault files (cosmetic churn: `\u2014` escapes, no trailing newline); items with no source got `source_target: ""` rather than null; the 4-node DeepSelect fragment is disconnected from the giant component in the derived sense (genuinely separate cluster or under-linked?); the mega-tag decision is recorded in the plan and code default but not in a standalone taxonomy note; per-item human review of the 160 bulk `--apply` category assignments is unevidenced (bulk apply is consistent with review-then-apply but proves nothing per item); the React graph view is Mermaid-only while the interactive canvas lives in the standalone HTML view (acceptable per plan wording, but pip users get Mermaid + a link and React users need a build to see any of it).

## 3. The new plan

### Track 0 — Data integrity (do first)

- [ ] Carry extras through the record (`extra="allow"` or an `extras` dict on `KnowledgeItemRecord`) so fresh-directory export preserves all historical keys, or make export merge from a source dir; add a regression test asserting a sync → fresh-dir export → re-sync round-trip loses zero keys on the live vault shape.
- [ ] Until the above lands, warn loudly when exporting to a fresh location (stdout + summary) that historical keys are not carried.
- [ ] Fix sync-backfill `vault_dir` passthrough (`vault_operations.py:111`): pass the caller's vault dir so custom `--vault` runs harvest references from the right vault.
- [ ] Add a `--strict` mode (or a skipped-items report) to `knowledge sync` so a future validation failure fails loudly or is at least listed, instead of silently lowering the sync count.
- [ ] Resolve scaffold write-back and sync-time backfill against an explicit `vault_dir` / repo root instead of cwd-relative paths (`scaffold.py:228` and the backfill wrapper default).

### Track 1 — Wire or remove the SQLite engine (decision required)

- [ ] Decide: wire `sync_ki_edges` into `sync_knowledge_vault` (populated during sync, as the plan specified, in the specified module location or with the relocation recorded) — or explicitly delete/flag the engine as dead. Do not leave tested, plan-promised, unreachable code in place.
- [ ] If wired: add a production-path test (sync a fixture vault, assert `ki_edges` rows, run a recursive path query through a CLI command or route). If removed: delete the module and its tests, and record the decision in the plan notes.

### Track 2 — Honest exports

- [ ] Re-run the live export against the post-backfill vault (expect 188 edges / 398 nodes by default) and correct the plan's stale 25-edge/299-node annotation; never cite the stale numbers again.
- [ ] Actually open the GEXF in Gephi (and GraphML in Cytoscape or yEd) and record what was checked (attributes, layout, timeline with `--dynamic`); the XML re-parse does not count as verification.
- [ ] Document the mesh flags and the sparsity story in the Gephi doc: default export is a starburst (54 KI→KI edges); `--include-single-tag-edges --include-shared-source` produce the mesh; explain the KI-subgraph component metric so "210 isolated" is not misread; state that Timeline requires `--dynamic`.
- [ ] Decide shared-category: implement the edge type or strike it from Track 0 with a recorded reason (the 459-edge census figure is otherwise a dangling promise).
- [ ] Summary parity: add a summary to GraphML (e.g. `<desc>`/graph attributes) and Cypher header, and edges-by-type to CLI stdout and HTML cards — or explicitly narrow the plan requirement to JSON.
- [ ] Golden test: extend the CLI fixture-vault test to assert per-format node/edge counts, not just exit codes and file existence; strengthen the live-vault bound to assert `total_edges` ≥ stored-edge count on disk.
- [ ] Fix dynamic GEXF end dates: use a real supersession/end date when one exists, or omit `end` until it does; never emit `end == start`.

### Track 3 — A lifecycle loop that runs itself

- [ ] Add the `ReflectionDaemonWorker` hook (or a scheduled `knowledge lifecycle` run) so lifecycle evaluation and contradiction audit happen without a human remembering; record the trigger and cadence.
- [ ] Rename `--apply-contradictions` to `--show-contradictions`, or implement actual batch-apply with per-pair confirmation — the current name overpromises.
- [ ] Prove the loop end-to-end on real data: run a read-only lifecycle evaluation + contradiction audit against the live vault and record that the queue is non-empty (or that zero transitions is the expected current state, with the reason: only 15 items have retrieval stats, `min_retrievals=5`).
- [ ] Record the canonical "isolated" definition (recommend the shipped `orphans` definition) and its current count, in the plan notes and the stats output, so the four competing numbers stop confusing the next round.

### Track 4 — Neo4j decision record

- [ ] Record the gate decision explicitly (recommend: gate not passed; Cypher export retained as an offline artifact) and re-scope plan line 183 accordingly so the next round does not re-litigate it.
- [ ] Add `IsnadClaim` evidence nodes to the Cypher export, or amend the plan spec to drop that requirement — current state is silent drift.
- [ ] Document the five justifying Cypher queries (shortest path, contradiction chains, lineage, neighborhoods, orphans), or drop the requirement now that the gate is not passed — an undocumented export is a file, not a query story.
- [ ] Add cypher to the CLI export test's format coverage (currently json/gexf/graphml/html only; cypher coverage is exporter-level only).

### Track 5 — Paperwork completion

- [ ] Add commit hashes to the post-plan analysis RESOLVED markers (`0ef3a44`, and `77ceb2f` where relevant) as the Track 8 item required.
- [ ] Record post-hygiene telemetry in the plan progress notes (282 items, 0/0 uncategorized/untagged, 188 stored edges, orphan count per the canonical definition).
- [ ] Add `reflect` and `lineage` to `cli.md` (and consider widening the drift gate's cli.md check beyond the core 9).
- [ ] Add the date-source breakdown to `knowledge stats` (metadata/ID vs git-history counts) and mega-tag threshold-crossing dates + retrieval velocity to `knowledge timeline`, as Track 6 specified.
- [ ] Record the mega-tag decision in a standalone taxonomy note (not just the plan file and code default), and sample-audit 20 of the 160 bulk-applied category assignments rather than re-reviewing all.

### Track 6 — Docs hygiene

- [ ] Fix the two dead `file:///` links in `docs/domains/` (same fix class as the earlier skills links: relative paths per Rule 47).
- [ ] Fix the stale README counts (skills "50" → 95, plugins "134" → 135) and exclude nested `.claude-plugin` metadata from future plugin counts.
- [ ] Consider widening the drift test's link check beyond the how-to doc so the next dead-link class is caught by a gate, not by a sweep.

## Suggested order (the pick queue)

1. Track 0 (data integrity) — the fresh-dir key stripping is the only data-loss path; fix it before anyone seeds a vault from an export.
2. Track 1 (SQLite decision) — a one-decision item that removes the largest "looks done, does nothing" gap.
3. Track 2 (honest exports) — re-run, re-verify in real Gephi, and document the sparsity story; this is what the next Gephi user will actually hit.
4. Track 3 (lifecycle loop) — makes maintenance automatic instead of remembered.
5. Track 4 (Neo4j record) — five minutes of writing that closes the plan's only unticked item honestly.
6. Track 5 (paperwork) — small, all checkable, all currently ticked-but-incomplete.
7. Track 6 (docs hygiene) — same dead-link class as before, now with a gate to prevent recurrence.

## §11 Verification backlog (not verified during this analysis)

- [ ] Verify: built React bundle behavior (`vite build` + serve `frontend/dist`) for the knowledge mode — code reviewed, not runtime-verified in this pass.
- [ ] Verify: exact orphan count under the shipped `orphans` definition by running the command (this pass derived ≥2 from data + code reads; the full count needs a run).
- [ ] Verify: whether the 160 bulk-applied category assignments were individually reviewed (not establishable from the repo; the sampled audit in Track 5 is the remedy).
- [ ] Verify: Gephi/Cytoscape/yEd rendering of a real post-backfill export (Track 2) — the previous "verification" was XML re-parsing only.
- [ ] Verify: Neo4j availability (Docker/Testcontainers) if the gate is ever revisited — still the plan's only unticked item.
