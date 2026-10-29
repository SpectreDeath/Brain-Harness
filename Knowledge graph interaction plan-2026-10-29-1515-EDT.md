# Brain Harness — Knowledge Graph Interaction Plan

**Created:** 2026-10-29 15:15 EDT
**Repo:** `SpectreDeath/brain-harness`
**HEAD at planning time:** `f6672a6` (main)
**Purpose:** Turn `.harness/knowledge/` from a folder of notes into a knowledge graph the user can actually interact with — in multiple ways, not one. This plan follows the same pattern as the 2026-10-25 implementation plan: small, checkable items the user picks through one at a time, with evidence cited per item.
**Baseline (measured 2026-10-29, local clone):** 281 items, each a dual-file directory (`metadata.json` + `summary.md`, per repo Rule 40). Schema is uneven: tags on 260 items, category on 121, `source_target` on 132, retrieval stats on 15, `anchors` on 9. Zero items carry `edges` or a non-default `status` on disk. Derived-edge census: 1,144 shared-tag edges, 459 shared-category, 218 shared-source, 1,703 union; one giant component of 236 nodes, 37 small fragments, 33 isolated nodes. Top tags: `endogenous_memory` (78), `self_reflection` (66), `architecture` (29).
**Existing machinery to build on:** `KnowledgeGraphQueryService` (`src/harness/services/storage/vault_graph.py`) with `propose_links`, `backfill_edges_mechanically`, `get_skill_lineage`, `get_dependents`, `get_contradictions`, `get_topic_neighborhood`; `harness knowledge` CLI group (`src/harness/commands/reflection.py`: `sync`, `list`, `query`, `verify`, `reflect`, `contradictions`, `lineage`); skill-graph HTML brief precedent (`registry.export_html_brief` via `export_skill_graph_visual_cmd`); swarm Mermaid DAG generator (`src/harness/ui/server/swarm_graph.py`) as a control-room rendering precedent.
**What this plan is not:** It does not change the vault's dual-file format, does not rewrite item content, and does not add new third-party dependencies without explicit user approval (repo dependency guardrail). Generated exports never default into `.harness/knowledge/` itself (Rule 40 forbids flat files there; exports live at an explicit `--out` path).

## Guiding decisions (settle before or during Track 0)

- **Derived vs asserted edges must stay distinguishable.** Every edge carries `derived: true/false` and a `confidence`, matching the existing `KnowledgeEdge` model. Visualizations label derived edges as such; nothing derived is ever presented as a fact the vault asserts.
- **Edge threshold policy.** The repo's own `propose_links` rule (2+ shared tags AND same taxonomy domain → `same_domain`, confidence 0.80) is the default for stored edges. Single-shared-tag edges are export-only context, off by default, because 945 of them trace to the two mega-tags and produce a hairball.
- **Mega-tag treatment.** `endogenous_memory` and `self_reflection` are too broad to be edges by themselves. Either exclude tags above a frequency cap from edge derivation, or weight edges by tag rarity. Decide in Track 0; do not silently drop data either way — the cap and the excluded tags are reported by the export.
- **One derivation engine, many outputs.** GEXF, GraphML, HTML, Cypher, and CLI queries all read the same derived-graph function. No per-format re-implementation of edge rules; a format that disagrees with the others is a bug.

## Track 0 — Foundations

- [ ] Define the derived-graph function: inputs (disk items via existing sync), edge rules (stored edges + `same_domain` + `references_code` + `became_skill` + shared-category + shared-source), threshold/cap policy from the guiding decisions, and output schema (node attributes: id, title, category, domain, tags, retrieval_count, created; edge attributes: type, derived, confidence, shared_tags).
- [ ] Add a unit test that pins the derivation on a small fixture vault (nodes, edges, thresholds, mega-tag cap) so later tracks cannot silently change the graph.
- [ ] Decide and record the default export location policy: explicit `--out` required, never inside `.harness/knowledge/`; generated exports git-ignored or kept out of the repo by default.
- [ ] Normalize-or-tolerate decision for schema unevenness: export tolerates missing tags/category (21 untagged, 160 uncategorized) without crashing, and reports coverage counts in every export summary.
- [ ] Add an export summary block (node count, edge count by type, component count, isolated count, excluded-tag report) to every output format, so a picture is never divorced from its provenance.

## Track 1 — One export engine, three formats (the first build)

- [ ] Implement `harness knowledge export` with `--format gexf|graphml|html|json` and `--out`, reusing the Track 0 derivation function; `--include-single-tag-edges` flag off by default.
- [ ] GEXF writer: nodes with category/domain/tags/retrieval attributes, edges with type/derived/confidence; verify the file opens in Gephi with attributes intact (node colors by category, size by retrieval count).
- [ ] GraphML writer: same graph, same attributes; verify it opens in Cytoscape and yEd.
- [ ] Standalone HTML writer: self-contained page (D3 or vis.js vendored or CDN with a local fallback note), click node → title + summary excerpt, filter by category/tag, search by title, toggle derived edges on/off. Reuse the `export_html_brief` pattern from the skill graph rather than inventing a new renderer contract.
- [ ] JSON writer: the raw derived graph (nodes + edges + summary) as the machine-readable seam other tools and future tracks consume.
- [ ] Write a short Gephi workflow note (open GEXF → ForceAtlas2 → Louvain communities → filter by degree) as `docs/how-to/explore-knowledge-graph-gephi.md` or a section in the graph docs page; keep it to the steps that were actually verified.
- [ ] Golden-file test: export a fixture vault to all four formats and assert node/edge counts and one known edge per format.

## Track 2 — Make edges real (stored, not re-derived)

- [ ] Wire `propose_links` into the reflection save path so new items get candidate edges at creation, with candidates marked derived and reviewable rather than silently asserted.
- [ ] Extend `backfill_edges_mechanically` to include `same_domain` edges under the Track 0 threshold rule (it currently backfills only `references_code`/`became_skill`/`supersedes`), and add a `--dry-run` report of what would be added.
- [ ] Add a disk migration that writes `edges` and `status` into existing `metadata.json` files from the backfill, preserving the dual-file format and every existing field; run it once over the 281 items and report per-item edge counts.
- [ ] Add a `knowledge export` round-trip test: sync from disk → export → re-import comparison, proving stored edges survive sync and are not duplicated on re-backfill (idempotency test).
- [ ] Wire the lifecycle trigger the post-plan analysis flagged as missing: a `knowledge lifecycle` command (or a step in the reflection daemon cycle) that runs `evaluate_vault_lifecycle`, prints `audit_contradictions`, and lets a review decision set `status`/`superseded_by`.
- [ ] Add a contradiction-apply step: convert a reviewed `supersession_candidate` into a `supersedes` edge + status change, closing the detection-without-resolution gap.
- [ ] Exclude SUPERSEDED from retrieval scoring (down-weight CHALLENGED) in `retrieve_relevant_knowledge`, so the graph's own maintenance feeds back into what the agent injects into prompts.

## Track 3 — CLI graph queries (headless seam, repo Rule 10)

- [ ] `harness knowledge neighbors <ki_id> [--depth N] [--edge-type TYPE]`: list adjacent items with edge types and confidences.
- [ ] `harness knowledge path <from> <to>`: shortest path through stored + derived edges, or an explicit `no_path` result (repo Rule 55: never synthesize fake direct edges).
- [ ] `harness knowledge topic <topic>`: promote the existing `get_topic_neighborhood` service to a CLI command (matched KIs, skills, code paths).
- [ ] `harness knowledge dependents <ki_id>`: surface the existing `get_dependents` service as a command.
- [ ] `harness knowledge orphans`: list isolated and low-degree nodes (the 33 isolated + small fragments) with their missing-field profile, as triage input for Track 7.
- [ ] `harness knowledge stats`: node/edge/component/tag-coverage report on stdout, reusing the Track 0 summary block, for scripting and CI-friendly checks.

## Track 4 — Control-room graph view

- [ ] Confirm the frontend source location and `dist` resolution before building (repo-root `frontend/` vs `src/harness/ui/frontend/`; the static fallback is what pip installs actually serve) and record the finding.
- [ ] Add a `GET /api/knowledge/graph` endpoint returning the Track 0 JSON graph (same derivation function, no second implementation).
- [ ] Add a graph tab to the control room: interactive canvas (reuse the Track 1 HTML approach or the existing frontend's graph library if one is already vendored — check before adding a dependency), node click → detail drawer showing title, summary, tags, category, retrieval stats, and edge list.
- [ ] Add a contradictions-review affordance to the same view (queue from `audit_contradictions`, approve → applies the Track 2 apply step), or explicitly defer it with a reason.
- [ ] Add a frontend build/test step to CI only if Track 4 ships a React change (otherwise the static fallback story stays as-is and the graph view ships as the standalone HTML from Track 1).

## Track 5 — Neo4j (optional, gated)

- [ ] Decision gate first: only pursue if a CLI/web query need appears that Track 3/4 cannot answer (multi-hop path queries at scale, persistent cross-session graph queries). If not, skip the whole track and say so.
- [ ] Cypher import writer (from the Track 0 JSON): `(:KI)` nodes with the same attributes, typed relationships matching edge types, `derived`/`confidence` properties on every relationship.
- [ ] Document the five queries that justify the track: shortest path, contradiction chains, topic neighborhoods, skill lineage expansion, orphan detection — each verified against the imported 281-node graph.
- [ ] Note the existing Neo4j architect skill as prior art; reuse its patterns before writing new ones, and do not add a Neo4j driver dependency without explicit approval.

## Track 6 — Timeline layer

- [ ] Add `created` as a first-class node attribute in all exports (it already exists on most items; report coverage for the items missing it).
- [ ] Dynamic GEXF export: nodes/edges with start dates so Gephi's timeline slider animates the graph's growth (memory/reflection core forming, source clusters arriving).
- [ ] Time slider on the standalone HTML view (filter nodes by creation date range), reusing the Track 1 page.
- [ ] A short "how the graph grew" note generated from the data (first items, largest growth months, when the mega-tags took over) — derived from dates, not narrated from memory.

## Track 7 — Vault hygiene the graph exposes

- [ ] Triage the 33 isolated nodes: genuinely standalone vs under-tagged; retag or link where the content supports it, leave and annotate where it does not.
- [ ] Category backfill pass for the 160 uncategorized items, using the existing 9-domain taxonomy (mechanical suggestion + human confirm, not silent assignment).
- [ ] Tag pass for the 21 untagged items, same confirm-before-write rule.
- [ ] Mega-tag review: decide whether `endogenous_memory`/`self_reflection` split into narrower tags or stay as broad markers excluded from edge derivation; record the decision in the taxonomy notes.
- [ ] Re-run the Track 0 census after hygiene and record the before/after (component count, isolated count, edge count) in the plan's progress notes.

## Track 8 — Docs and gates

- [ ] Docs page `docs/how-to/explore-knowledge-graph.md`: what the graph is, the four interaction modes (Gephi, web, CLI, Neo4j-if-built), derived-vs-asserted labeling, and the export commands.
- [ ] Update `docs/reference/cli.md` with the new `knowledge` subcommands (or generate it from the command catalog if that Track 3B follow-up lands first).
- [ ] Drift gate: a test asserting the export schema (node/edge attribute names) matches what the docs promise, so docs and exporter cannot silently diverge.
- [ ] Update the post-plan analysis notes: mark the graph-interaction items done with commit references as tracks land.

## Suggested order (the pick queue)

1. Track 0 + Track 1 (one derivation engine, GEXF/GraphML/HTML/JSON) — unlocks Gephi, Cytoscape, yEd, and the browser in a single build. This is the recommended first pick.
2. Track 2 (edges real + lifecycle trigger + contradiction apply) — the graph stops being re-derived and starts being maintained.
3. Track 3 (CLI queries) — cheap, scriptable, agent-usable.
4. Track 4 (control-room view) — only after confirming the frontend/dist story.
5. Track 7 (hygiene) — in parallel with 2–4, since the graph itself points at what needs cleaning.
6. Track 6 (timeline) — small once Track 1 exists.
7. Track 5 (Neo4j) — only if the decision gate passes.

## §11 Verification backlog (not verified during planning)

- [ ] Verify: exact `export_html_brief` implementation and whether its HTML template is reusable for the knowledge graph or skill-specific.
- [ ] Verify: whether the React frontend already vendors a graph library (if so, Track 4 reuses it; if not, the standalone HTML from Track 1 is the view and no new dependency is added without approval).
- [ ] Verify: Gephi's current GEXF attribute handling for the exact attribute set in Track 0 (open a real export in Gephi before calling Track 1 done).
- [ ] Verify: whether `.harness/` is fully git-tracked and whether generated exports belong in the repo at all (default: out of repo, explicit `--out`).
- [ ] Verify: Neo4j availability and driver compatibility before Track 5 leaves the decision gate.
- [ ] Verify: the 33-isolated / 37-fragment census against the post-hygiene vault, since tagging changes move nodes between components.
