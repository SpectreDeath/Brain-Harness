# Brain Harness — Post-Knowledge-Graph Analysis and Plan

**Created:** 2026-10-31 08:08 EDT (Redrafted 2026-10-31 with code-level root-cause trace and live-vault verification)
**Repo:** `SpectreDeath/brain-harness`
**HEAD analyzed:** `0ef3a44` ("feat(knowledge-graph): complete Tracks 0-8 of knowledge graph interaction plan")
**Purpose:** Second round in the established cycle: verify the 2026-10-29 knowledge-graph interaction plan's completion, analyze the current state from live code and on-disk vault data, resolve all open design forks, and set the next execution plan. The predecessor plan file on `main` shows 48/49 items ticked; the only unticked item is the conditional Neo4j verification (line 183).
**Method:** Code and data audit across four area passes (exports/derivation, edges-real/learning loop, CLI/UI/Neo4j/timeline, hygiene/docs/health), augmented with direct execution against `.harness/knowledge/` and line-by-line inspection of the reflection, retrieval, and storage seams.
**Baseline census (2026-10-31, verified against `.harness/knowledge/`):**
- **282 item directories**, all carrying normalized `status`, `category`, and `tags` (0 uncategorized, 0 untagged).
- **188 total stored edges across 79 items** (203 items have `edges: []` on disk): `108 references_code`, `54 same_domain`, `18 became_skill`, `8 became_plugin` (`161` derived, `27` asserted). Those 188 edges touch **110 unique KIs** overall (79 as sources + 31 additional KIs as `same_domain` targets) and **72 unique KIs** on the KI→KI subgraph.
- **Lifecycle & retrieval state on disk:** All 282 items have `status: "ACTIVE"`. Zero `supersedes` or `contradicts` edges exist on disk. Exactly **15 items** have `retrieval_count > 0` — twelve with `retrieval_count: 2` and three (`ki_20260824_repo_03`, `ki_20260830_django_01`, `ki_20260831_em3_02`) with `retrieval_count: 4` (**0 items have `retrieval_count >= 5`**) — and **all 15 have `success_count: 0`** due to a live `:memory:` resolver bug traced in §2 High below.

## Verdict

The knowledge-graph plan genuinely landed its core surface: the vault went from 1 edge-bearing item to a typed, queryable graph with five export formats, 19 `harness knowledge` subcommands, a Control Room view, MCP resource parity, and a doc-drift gate — while the in-place disk migration preserved every existing metadata key.

However, deeper code and data verification reveals three things the initial pass either understated or missed:
1. **Two silent runtime bugs still break the live learning and linking loops in production**: `HarnessReflectorEngine.reflect` receives an un-synced `:memory:` `SQLiteStorageService` from both `run_reflection_cmd` and `ReflectionDaemonWorker.step`, so `propose_links(ki, existing_items)` is called with `existing_items = []` in production; and `_sync_knowledge_outcome` resolves a fresh, empty `:memory:` `SQLiteStorageService` at the end of ReAct runs, causing `record_knowledge_outcome` to silently drop all `success_count` increments (`0` successes across all 15 retrieved items on disk).
2. **Two data-preservation hazards remain in `sync_knowledge_vault` / `export_single_item`**: exporting to a fresh directory strips non-canonical keys from 225/282 items, and `sync_knowledge_vault` prefers `meta.get("summary")` over `summary.md` while `export_single_item` writes `item.summary` back to `summary.md` and overwrites `distilled_learning` with `item.summary.split("\n")[0]`.
3. **Several "completed" items are unwired, contract-mismatched, or verified against stale pre-backfill numbers**: `vault_sqlite_graph.py` has zero production callers and a return-shape mismatch with `bfs_shortest_path`; `knowledge stats` (`210` isolated) and `knowledge orphans` (`172` isolated) compute incompatible isolation definitions on the exact same graph; and `--apply-contradictions` only prints the queue.

This redrafted plan eliminates all open "decide whether to X or Y" forks in favor of concrete, file-and-line-anchored engineering tasks.

---

## 1. What genuinely closed

### Exports and derivation (Tracks 0–1)

- `harness knowledge export` exists with five formats (`json | gexf | graphml | html | cypher`, `src/harness/commands/reflection.py:353-489`) and the plan's flags (`--out` defaulting to `outputs/knowledge_graph.<fmt>`, `--nodes all|ki-only`, `--include-single-tag-edges` off by default, `--include-shared-source` off by default, `--max-tag-freq` 0.15, `--min-confidence`, `--dynamic`, `--open`).
- One derivation engine, no per-format re-implementation: `KnowledgeGraphQueryService.derive_graph` (`src/harness/services/storage/vault_graph.py:59-77`) delegates to `derive_knowledge_graph` (`src/harness/services/storage/vault_derivation.py:19-138`); all writers take a `DerivedKnowledgeGraph` via `export_knowledge_graph` (`src/harness/services/storage/vault_exporters.py:170-189`). The CLI, the FastAPI routes, and the MCP read path all call the same function.
- Edge rules as specified: stored edges included unconditionally (subject only to node filter / min confidence); `same_domain` requires same non-`general` domain plus 2+ shared non-mega tags (confidence 0.80), or 1 shared tag with `--include-single-tag-edges` (0.60). The mega-tag cap is real and reported (exactly `{endogenous_memory, self_reflection}` excluded at 0.15 on the current vault, reported in the summary object, CLI stdout, JSON, and HTML cards).
- Rule 40 holds: `.gitignore` ignores `.harness/*` except `knowledge/`/`config.json`/`*.py` and ignores `outputs/`; `validate_export_path` (`vault_graph.py:40-53`) rejects targets inside the vault, is wired into the CLI, and is test-covered; no generated export lives inside `.harness/knowledge/`.
- Test coverage is substantial: fixture graph per-format tests (zero dangling edges, attribute checks), CLI end-to-end fixture-vault test, derivation tests including a live-vault integrity test, and a doc-drift test pinning documented core commands and attribute names against live code.

### Edges real and the learning loop (Track 2 — partial; see §2 High for runtime wiring bugs)

- Skill-scaffold write-back is real: `SkillScaffoldEngine.scaffold` (`src/harness/creator/skills/scaffold.py:227-244`) appends a `became_skill` edge (`derived=False`, confidence 1.0, deduped) to the source KI on disk.
- Backfill includes `same_domain` plus `--dry-run`/`--commit` (`src/harness/services/storage/vault_backfill.py:52-141`), with mega-tag exclusion, `references_code` from `references`, `became_skill` from `skill:` tags, `became_plugin`, and canonical-direction `supersedes`. Bare invocation modifies nothing (dry-run is the default).
- In-place disk migration preserved existing keys: comparing key sets at `f0eb2b3` vs `0ef3a44`, zero items lost a key during in-place backfill/hygiene because `export_single_item` (`src/harness/services/storage/vault_operations.py:130-159`) merges into existing `metadata.json`.
- Retrieval exclusion is per plan: `ARCHIVED` and `SUPERSEDED` skipped, `CHALLENGED` ×0.25, `PROMOTED` ×1.25, `DEMOTED` ×0.5 (`src/harness/services/storage/vault_retrieval.py:60-85`).
- Lifecycle and contradiction resolution CLI commands exist: `knowledge lifecycle` (`reflection.py:548-600`) runs `evaluate_vault_lifecycle` and displays `audit_contradictions`; `knowledge resolve <ki_a> <ki_b> --action supersede|contradict|dismiss` (`reflection.py:602-651`) writes the directed edge and updates `status`/`superseded_by` on disk.
- The predecessor plan's flagged sync failures are fixed: `str` isnad normalized (`src/harness/services/storage/vault_taxonomy.py:177-190`, empirically 282/282 synced, zero missing); `LEGACY_CATEGORY_MAP` expanded (`vault_taxonomy.py:30-94`, empirically zero items collapsing to `general` despite a non-empty raw category); backfill idempotent (re-runs add zero edges).

### CLI and Control Room (Tracks 3–4)

- All 19 `harness knowledge` subcommands are registered in `src/harness/commands/reflection.py`: `backfill`, `contradictions`, `dependents`, `export`, `hygiene`, `lifecycle`, `lineage`, `list`, `neighbors`, `orphans`, `path`, `query`, `reflect`, `resolve`, `stats`, `sync`, `timeline`, `topic`, `verify`.
- Rule 55 holds in `bfs_shortest_path` (`src/harness/services/storage/vault_traversal.py:68-127`): plain BFS over graph edges with no fallback and no synthesis; unreached pairs return `{status: "no_path", chain: [], length: 0, hops: []}` and the CLI prints the explicit no-synthetic-edges message.
- Control Room architecture verified: frontend source is repo-root `frontend/`; `app.py` serves `frontend/dist` when built, falling back to `src/harness/ui/static/index.html` for pip installs. API routes are single-sourced (`src/harness/ui/server/routes/knowledge.py`: `GET /graph`, `GET /graph/html`, `GET /contradictions`, `POST /contradictions/resolve`, all via `derive_graph`).
- React graph tab (`frontend/src/views/GraphView.tsx:28-119`) includes `'knowledge'` mode and the contradiction review drawer with Supersede/Conflict/Dismiss actions (zero new npm dependencies), and the static fallback dashboard has parity.
- MCP parity: `harness://knowledge/graph` and `harness://knowledge/contradictions` are registered and call the same `derive_graph`.

### Hygiene and docs (Tracks 7–8)

- Hygiene pass completed on disk: 0 uncategorized (was 160), 0 untagged (was 21), 188 stored edges, zero keys stripped in-place. `knowledge hygiene` (`reflection.py:887-978`) prints proposals by default and persists only with `--apply`.
- `docs/how-to/explore-knowledge-graph.md` documents 9 core commands, all present in the live registry; `tests/test_knowledge_graph_doc_drift.py` asserts documented commands ⊆ live registry, core 9 ⊆ doc and `cli.md`, and node/edge attribute names match dataclass fields.
- Headroom interaction is clean: `77ceb2f`'s vault item (`ki_20261028_headroom_context_optimization`) was the only pre-KG item carrying edges (4 asserted edges), and all 4 were preserved.

---

## 2. What is overstated, partial, or broken, ranked

### High

1. **`propose_links` is a no-op in production reflection runs because `storage` is an un-synced `:memory:` database (`src/harness/creator/reflection/engine.py:73-80`, `src/harness/commands/reflection.py:75`, `src/harness/services/reflection_worker.py:74`).**
   - While `engine.py:76` calls `propose_links(ki, existing_items)`, both `run_reflection_cmd` (`reflection.py:75`) and `ReflectionDaemonWorker.step` (`reflection_worker.py:74`) instantiate a fresh `SQLiteStorageService(db_path=":memory:")` and pass it to `engine.reflect(...)` **without calling `await storage.sync_knowledge_vault(vault_dir)` first**.
   - Inside `engine.reflect`, `existing_items = await self.storage.list_knowledge_items()` (`engine.py:74`) therefore returns `[]`! Passing `existing_items = []` to `propose_links` means newly distilled KIs **never receive `same_domain` or `supersedes` links to existing vault items in production** (only unit tests that manually pre-seeded `storage` saw links).
2. **`record_knowledge_outcome` silently drops all `success_count` updates when `ServiceContext` has no pre-registered `StorageService` (`src/harness/agent/react/engine.py:34-45`, `src/harness/services/storage/resolvers.py:26-35`, `src/harness/services/storage/vault_retrieval.py:146-163`).**
   - In `build_react_initial_messages` (`src/harness/agent/react/prompting.py:84-94`), `resolve_knowledge_vault(context)` instantiates a temporary `SQLiteStorageService(":memory:")` when `KNOWLEDGE_VAULT_KEY` / `STORAGE_SERVICE_KEY` is not registered on `context`, syncs `.harness/knowledge` into that temporary instance inside `retrieve_relevant_knowledge`, increments `retrieval_count` on disk in `record_knowledge_retrieval`, and then **discards the instance**.
   - When the ReAct run finishes, `_sync_knowledge_outcome` (`src/harness/agent/react/engine.py:42-43`) calls `resolve_knowledge_vault(context)` again — receiving a **brand-new, empty `SQLiteStorageService(":memory:")`** — and calls `record_knowledge_outcome`. Inside `vault_retrieval.py:151-152`, `item = await self.get_knowledge_item(ki_id)` returns `None`, so `if item:` is `False` and `success_count` is never incremented in memory or on disk! This is why all 15 retrieved items on disk have `retrieval_count` ∈ `{2, 4}` and **`success_count: 0`**.
3. **Fresh-directory export strips historical keys, and `sync_knowledge_vault` / `export_single_item` can clobber `summary.md` and `distilled_learning` (`src/harness/services/storage/models.py:67`, `src/harness/services/storage/vault_operations.py:107, 130-163`).**
   - `KnowledgeItemRecord` carries no extra-keys field (Pydantic drops unknown keys at sync), so `export_single_item` only preserves historical keys when `meta_file.exists()` in the target directory. A `sync → export-to-fresh-dir → re-sync` round-trip strips historical keys (`created`, `updated`, `summary`, `references`, `claims`, `source_commit`, `source_uri`, `context`, `provenance`, …) from **225 / 282** items.
   - Additionally, `sync_knowledge_vault` (`vault_operations.py:107`) sets `summary=meta.get("summary") or summary_text` (preferring a short `metadata.json["summary"]` string over the full `summary.md` file!), and `export_single_item` (`vault_operations.py:160-161`) writes `item.summary` back to `summary.md` and overwrites `metadata.json["distilled_learning"]` with `item.summary.split("\n")[0]` (`vault_operations.py:156`, often a `# Title` markdown header).
4. **The SQLite graph engine (`src/harness/services/storage/vault_sqlite_graph.py`) has zero production callers and a return-contract mismatch.**
   - `vault_sqlite_graph.py` implements `init_ki_edges_table`, `sync_ki_edges`, `find_path_sql`, and `get_transitive_dependents_sql`, but is never called from `SQLiteStorageService`, `sync_knowledge_vault`, or any CLI/API seam.
   - Worse, `find_path_sql` (`vault_sqlite_graph.py:70-71, 116-121`) returns `status: "found"` when `from_id == to_id` (instead of `"same_node"` per `bfs_shortest_path` in `vault_traversal.py:85`) and omits the `"hops"` list on found paths (`vault_traversal.py:116-121`), so wiring it into `harness knowledge path` without fixing its return payload would break CLI rendering (`reflection.py:788`).
5. **Sync-backfill reads the wrong vault under custom `--vault` and runs single-item (`src/harness/services/storage/vault_operations.py:110-111`).**
   - `sync_knowledge_vault` calls `graph_service.backfill_edges_mechanically([ki])` inside the per-item loop without passing `vault_dir=root`, so `references` harvesting reads the default `.harness/knowledge` instead of the caller's `vault_dir`, re-parses `metadata.json` a second time for all 203 edge-free items, and cannot infer batch-level `supersedes` (`id_map`) or `same_domain` edges during sync.
6. **"Isolated" has two conflicting shipped CLI numbers (`210` vs `172`) on the exact same default graph, and the default export sparsity is undocumented (`src/harness/services/storage/vault_derivation.py:103-117`, `src/harness/services/storage/vault_traversal.py:130-165`).**
   - The predecessor plan's verification note (`299 nodes, 25 edges`) is stale pre-backfill data. On `0ef3a44`, a default export has **398 nodes (282 KIs + 116 external) and 188 edges** (`134` KI→external spokes, `54` KI→KI `same_domain` edges).
   - Even when `nodes_filter="all"`, `derive_knowledge_graph` (`vault_derivation.py:111`) restricts its component BFS to `if neighbor in ki_ids`, ignoring all 134 code/skill/plugin edges and reporting **`component_count = 239`, `largest_component_size = 6`, `isolated_ki_count = 210`** (`282 - 72 = 210` KIs with no KI→KI edge).
   - Meanwhile, `harness knowledge orphans` (`find_vault_orphans`, `vault_traversal.py:135-142`) checks `ki.id not in incident_nodes` across all 188 edges, reporting **`172` isolated items** (`282 - 110 = 172` KIs with zero edges of any kind). Neither `knowledge stats` nor `knowledge orphans` exposes `--include-single-tag-edges` / `--include-shared-source` (under which isolated KIs drop to **3** with the 15% mega-tag cap, or **0** uncapped).
   - `docs/how-to/explore-knowledge-graph.md` never mentions the mesh flags (`--include-single-tag-edges`, `--include-shared-source`) or that Gephi's Timeline requires `--dynamic`.
7. **No automatic lifecycle trigger, and `--apply-contradictions` is display-only (`src/harness/commands/reflection.py:553, 592`).**
   - `ReflectionDaemonWorker.step` (`src/harness/services/reflection_worker.py:68-98`) never calls `evaluate_vault_lifecycle` or `audit_contradictions`.
   - In `knowledge lifecycle`, `--apply-contradictions` (`reflection.py:592`: `if apply_contradictions or conflicts:`) only prints the contradiction queue whenever `conflicts` is non-empty, making the flag both a misnomer and redundant when conflicts exist.

### Medium

- **Gephi/Cytoscape/yEd verification was XML re-parsing only, and dynamic GEXF sets `end == start` (`src/harness/services/storage/vault_exporters.py:72-73`).** For `SUPERSEDED`/`ARCHIVED` nodes, `export_gexf(..., dynamic=True)` sets `n_attrs["end"] = n.created_at[:10]` (`end == start`), producing a zero-length interval in Gephi's timeline instead of using an actual supersession/archive timestamp or omitting `end`.
- **Shared-category edges were never implemented.** Predecessor Track 0 listed them and counted 459 in the baseline census, but `shared_category` has zero matches in `src/`. (See Guiding Decisions below: explicitly retire standalone `shared_category` edges in favor of `same_domain`.)
- **Summary block parity is incomplete across formats.** Full summary is in JSON and HTML cards; CLI `export` stdout (`reflection.py:476-485`) omits `edges_by_type`, `untagged_ki_count`, and `uncategorized_ki_count`; GEXF carries a one-line `<description>`; GraphML has no `<data>` summary metadata on `<graph>`; Cypher has only a static header comment.
- **Golden export test is half-built (`tests/test_command_knowledge_export.py`).** The CLI fixture-vault test (`TestKnowledgeExportCLI`) asserts exit codes and file existence only, never per-format node/edge counts, and omits `cypher`. The live-vault test bound in `tests/test_service_vault_graph_derivation.py` (`total_edges >= 7`) is too weak to catch regressions from the 188 stored edges on disk.
- **Neo4j gate and Cypher spec drift (`src/harness/services/storage/vault_cypher_exporter.py`).** No commit message or doc recorded the Track 5 gate outcome, yet `vault_cypher_exporter.py` was built without `IsnadClaim` nodes or 7-tuple temporal evidence properties and without documenting the 5 justifying Cypher queries.
- **Timeline and stats omissions (`src/harness/commands/reflection.py:654-700, 980-1049`).** `knowledge stats` reports only aggregate `date_coverage_count` (not the `274 metadata/ID + 8 file/git` source breakdown), and `knowledge timeline` omits the mega-tag 15%-threshold crossing dates and retrieval velocity specified in Track 6.
- **Silent per-item sync skips and cwd-relative vault paths (`vault_operations.py:114-115`, `src/harness/creator/skills/scaffold.py:228`).** `sync_knowledge_vault` swallows per-item exceptions with only a structlog warning, and `SkillScaffoldEngine.scaffold` hardcodes `Path(".harness/knowledge")` rather than accepting an explicit `vault_dir` / workspace root on `SkillScaffoldOptions`.
- **Paperwork gaps in Track 8.** `Post-plan analysis-2026-10-29-1236-EDT.md:65-66, 75` `[RESOLVED 2026-10-30]` markers omit commit hashes (`0ef3a44`, `77ceb2f`); `docs/reference/cli.md:249-267` documents 17 of the 19 `harness knowledge` subcommands (missing `reflect` and `lineage`); and `Knowledge graph interaction plan-2026-10-29-1515-EDT.md` has no progress-notes section recording the before/after hygiene telemetry.

### Lower

- **Two dead `file:///C:/Users/spectre/...` links in `docs/domains/` (Rule 47 violation):**
  - `docs/domains/security-and-forensics/EXPLANATION.md:44` (`git-guardrails-claude-code`)
  - `docs/domains/software-engineering/EXPLANATION.md:49` (`deepen-architecture`)
  Both are outside `tests/test_knowledge_graph_doc_drift.py`, which only checks `docs/how-to/explore-knowledge-graph.md`.
- **Stale README counts:** `.agents/skills/README.md` says "50 Deep-Module Skills" vs **95** actual skill directories containing `SKILL.md`; `plugins/README.md` says "134 Plugins" vs **135** canonical plugin directories (`137` `plugin.json` files total, including 2 nested `.claude-plugin` manifests).

---

## 3. Guiding decisions (settled for this plan — zero open forks)

1. **Preserve extras on `KnowledgeItemRecord` via Pydantic `extra="allow"` + explicit `extra_metadata` round-trip:** Configure `model_config = ConfigDict(extra="allow")` on `KnowledgeItemRecord` (`src/harness/services/storage/models.py:67`), pass non-canonical `metadata.json` keys through `sync_knowledge_vault`, and merge `item.model_extra` before `canonical_updates` in `export_single_item`. Prefer `summary_text or meta.get("summary", "")` during sync so `summary.md` is authoritative, and preserve any existing `meta_data.get("distilled_learning")` during export.
2. **Wire `vault_sqlite_graph.py` into `SQLiteStorageService` and fix its return contract (do not delete):** Keep `vault_sqlite_graph.py` as the focused submodule (keeping `sqlite.py` under the 200-line Rule 12/deepening ceiling), fix `find_path_sql` to return `status: "same_node"` on `from_id == to_id` and reconstruct the `hops` list on found paths, call `sync_ki_edges` at the end of `sync_knowledge_vault` when the backing store is SQLite, and expose `--sql` / SQLite-backed traversal on `harness knowledge path` and `dependents --transitive`.
3. **Retire standalone `shared_category` edges permanently:** Record in Track 0/2 notes that pure `shared_category` edges (459 unfiltered cliques) were intentionally superseded by `same_domain` (which requires normalized `TaxonomyDomain` equality + shared non-mega tags, or `--include-single-tag-edges`). Do not add a noisy tag-free category clique edge type.
4. **Report both isolation metrics explicitly in `KnowledgeGraphSummary`:** Keep `isolated_ki_count` as the canonical graph-wide orphan count (**172** on the default 188-edge graph: KIs with zero incident edges of any kind, matching `harness knowledge orphans`), and add `ki_only_isolated_count` (**210**: KIs with zero KI→KI edges) and `ki_only_component_count` (**239**) so `stats` and `orphans` never contradict each other. Add `--include-single-tag-edges` and `--include-shared-source` flags to both `knowledge stats` and `knowledge orphans`.
5. **Support both `--show-contradictions` and interactive/auto `--apply-contradictions` on `harness knowledge lifecycle`:** Default `knowledge lifecycle` prints the contradiction queue (`--show-contradictions`, default on when conflicts exist), while `--apply-contradictions` applies high-confidence (`>= 0.90`) `supersession_candidate` resolutions (or prompts per pair unless `--yes` is passed).
6. **Close the Neo4j gate as "Not Triggered (Stage 1 SQLite sufficient)" while upgrading the offline Cypher export to full spec compliance:** Record that SQLite `WITH RECURSIVE` handles the 282-KI / 398-node graph in `< 5ms` (so no live Neo4j driver/container is required), enrich `vault_cypher_exporter.py` to emit `(:IsnadClaim)` nodes and `[:ASSERTS_CLAIM]` edges from `items` when provided, and document the 5 canonical Cypher queries in `docs/how-to/explore-knowledge-graph.md`.

---

## 4. The execution plan

### Track 0 — Data integrity & live learning-loop repairs (do first)

- [x] **Preserve all historical metadata keys across fresh-directory exports (`src/harness/services/storage/models.py:67`, `src/harness/services/storage/vault_operations.py:80-164`):**
  - Add `model_config = ConfigDict(extra="allow")` to `KnowledgeItemRecord`.
  - In `sync_knowledge_vault` (`vault_operations.py:90-109`), pass `**{k: v for k, v in meta.items() if k not in _CANONICAL_KI_KEYS}` into `KnowledgeItemRecord(...)`, and change line 107 from `summary=meta.get("summary") or summary_text` to `summary=summary_text or meta.get("summary", "")` so `summary.md` is never clobbered by a shorter `metadata.json["summary"]` string.
  - In `export_single_item` (`vault_operations.py:130-159`), seed `meta_data` with `dict(item.model_extra or {})` merged with any existing on-disk `meta_file` JSON prior to applying `canonical_updates`, and preserve `meta_data.get("distilled_learning")` when already non-empty instead of unconditionally overwriting with `item.summary.split("\n")[0]`.
  - Add a regression test asserting that `sync_knowledge_vault(.harness/knowledge)` → `export_knowledge_vault(tmp_path)` → `sync_knowledge_vault(tmp_path)` preserves 100% of keys across all 282 items and 100% of `summary.md` byte lengths.
- [x] **Fix production `propose_links` hydration in `HarnessReflectorEngine.reflect` (`src/harness/creator/reflection/engine.py:73-80`, `src/harness/commands/reflection.py:75-89`, `src/harness/services/reflection_worker.py:74-87`):**
  - In `HarnessReflectorEngine.reflect` (`engine.py:74`), if `commit_to_vault and self.storage is not None`, check `existing_items = await self.storage.list_knowledge_items()`; if `not existing_items and vault_dir`, call `await self.storage.sync_knowledge_vault(vault_dir)` and re-fetch `existing_items` before calling `propose_links(ki, existing_items)`. Also append each newly saved `ki` to `existing_items` during the loop.
  - Add an integration test running `run_reflection_cmd` against a fixture `vault_dir` with a fresh `:memory:` store and asserting that newly distilled KIs receive `same_domain` edges to existing fixture items.
- [x] **Fix `record_knowledge_outcome` dropping `success_count` on un-synced `:memory:` stores (`src/harness/services/storage/vault_retrieval.py:123-164`, `src/harness/services/storage/resolvers.py:26-35`):**
  - In `record_knowledge_retrieval` and `record_knowledge_outcome` (`vault_retrieval.py:130-163`), if `await self.get_knowledge_item(ki_id)` returns `None` but `(root / ki_id / "metadata.json").exists()`, update `retrieval_count` / `last_retrieved_at` / `success_count` directly on the on-disk `metadata.json` (read-modify-write) and sync the item into memory rather than silently skipping `if item:`.
  - In `resolve_knowledge_vault` (`resolvers.py:26-35`), remain non-invasive to `context`, or allow `StepExecutionEngine` (`src/harness/agent/react/engine.py:42`) to reuse the vault instance resolved during `build_react_initial_messages`.
  - Add a regression test verifying that `build_react_initial_messages` followed by `_sync_knowledge_outcome(..., success=True)` on a bare `ServiceContext()` increments both `retrieval_count` and `success_count` on disk.
- [x] **Fix sync-time backfill `vault_dir` passthrough and batching (`src/harness/services/storage/vault_operations.py:71-116`):**
  - Collect `synced_items: list[KnowledgeItemRecord]` during `sync_knowledge_vault`; for any item with `not ki.edges`, pass `vault_dir=root` to `backfill_edges_mechanically` (or run once across `synced_items` with `vault_dir=root`) before `save_knowledge_item`, eliminating wrong-vault `references` reads when `--vault` points to a custom directory.
- [x] **Add `--strict` mode and skipped-item reporting to `harness knowledge sync` (`src/harness/services/storage/vault_operations.py:65-116`, `src/harness/commands/reflection.py:107-122`):**
  - Track `skipped_items: list[tuple[str, str]]` in `sync_knowledge_vault` (and expose `strict: bool = False`); surface any skipped directory names and error messages in `harness knowledge sync [--strict]` output and fail with exit code 1 when `--strict` is set and `skipped_items` is non-empty.
- [x] **Eliminate cwd-relative `.harness/knowledge` path in `SkillScaffoldEngine.scaffold` (`src/harness/creator/skills/scaffold.py:45-60, 227-245`):**
  - Add `vault_dir: Path | str | None = None` to `SkillScaffoldOptions` (defaulting to `out_dir.parents[2] / ".harness" / "knowledge"` when scaffolding under `<repo>/.agents/skills/<name>`, falling back to `Path(".harness/knowledge")`) and log write-back failures at `logger.warning` instead of `logger.debug`.

### Track 1 — Wire the SQLite recursive CTE graph engine end-to-end

- [x] **Align `find_path_sql` return contract with `bfs_shortest_path` (`src/harness/services/storage/vault_sqlite_graph.py:61-122`):**
  - Return `{"status": "same_node", "chain": [from_id], "length": 0, "hops": []}` when `from_id == to_id`.
  - Support `directed: bool = False` (traversing `ki_edges` in both directions when `directed=False`, matching `bfs_shortest_path`), and populate `"hops": [{"from": ..., "to": ..., "edge_type": ..., "direction": ..., "derived": ..., "confidence": ...}]` on found paths.
- [x] **Wire `sync_ki_edges` into `SQLiteStorageService` and `sync_knowledge_vault` (`src/harness/services/storage/sqlite.py`, `src/harness/services/storage/vault_operations.py:112-116`):**
  - Delegate `sync_ki_edges`, `find_path_sql`, and `get_transitive_dependents_sql` as methods on `SQLiteStorageService` (`sqlite.py`).
  - At the end of `sync_knowledge_vault`, if `hasattr(self, "_ensure_connection")`, derive the graph and call `sync_ki_edges(self._ensure_connection(), graph)` so `ki_edges` is always populated after sync.
- [x] **Expose SQLite recursive queries on `harness knowledge path` and `harness knowledge dependents` (`src/harness/commands/reflection.py:746-793, 829-852`):**
  - Add `--engine bfs|sqlite` (default `bfs`, or automatic `sqlite` when querying a synced SQLite DB) to `harness knowledge path`, and add `--transitive` / `--max-depth` (backed by `get_transitive_dependents_sql`) to `harness knowledge dependents`.
  - Add an integration test (`tests/test_service_vault_sqlite_graph.py`) that syncs a fixture vault via `SQLiteStorageService.sync_knowledge_vault`, asserts `ki_edges` row counts, and invokes `harness knowledge path --engine sqlite` and `harness knowledge dependents --transitive` through `CliRunner`.

### Track 2 — Honest exports, unified isolation metrics, and stronger golden tests

- [x] **Unify isolation metrics across `KnowledgeGraphSummary`, `stats`, and `orphans` (`src/harness/services/storage/vault_graph_models.py:46-67`, `src/harness/services/storage/vault_derivation.py:94-138`, `src/harness/commands/reflection.py:654-700, 854-885`):**
  - In `vault_derivation.py`, compute `isolated_ki_count` as KIs with **0 incident edges in `graph.edges`** (`172` on the default 188-edge graph, matching `find_vault_orphans`!), and add `ki_only_isolated_count` (`210` on the default graph: KIs with 0 KI→KI edges) to `KnowledgeGraphSummary`.
  - When `nodes_filter == "all"`, compute `component_count` and `largest_component_size` across all nodes/edges in `graph` (so KIs linked via shared `path`/`skill`/`plugin` nodes are grouped in the all-nodes view) while also reporting `ki_only_component_count` (`239`) and `ki_only_largest_component_size` (`6`).
  - Add `--include-single-tag-edges`, `--include-shared-source`, and `--max-tag-freq` flags to both `harness knowledge stats` and `harness knowledge orphans` so users can inspect both the strict default graph (`188` edges, `172` isolated KIs) and the derived mesh (`3` isolated KIs).
- [x] **Fix dynamic GEXF `end` date handling (`src/harness/services/storage/vault_exporters.py:70-74`):**
  - Never emit `end == start` (`n_attrs["end"] = n.created_at[:10]`). Only emit `end` on `SUPERSEDED`/`ARCHIVED` nodes when a distinct supersession/archive timestamp (> `start`) is available (e.g., the `created_at` of the superseding KI on `supersedes` edges, or `last_retrieved_at`), otherwise omit `end`.
- [x] **Complete export summary parity across CLI, GEXF, GraphML, and Cypher (`src/harness/commands/reflection.py:474-485`, `src/harness/services/storage/vault_exporters.py:37-43, 138-140`, `src/harness/services/storage/vault_cypher_exporter.py:26-30`):**
  - In CLI `knowledge export` stdout, print `edges_by_type` breakdown, `untagged_ki_count`, and `uncategorized_ki_count`.
  - In GraphML (`export_graphml`), add `<key id="graph_summary" for="graph" attr.name="summary" attr.type="string"/>` and attach a `<data key="graph_summary">` JSON/text summary block on `<graph id="G">`.
  - In Cypher (`export_cypher`), include the summary counts (total nodes, KIs, external nodes, asserted/derived edges, components, isolated KIs, excluded mega-tags) in the header comment block.
- [x] **Strengthen golden export tests (`tests/test_command_knowledge_export.py`, `tests/test_service_vault_graph_derivation.py`):**
  - Extend `TestKnowledgeExportCLI` to test all 5 formats (`json`, `gexf`, `graphml`, `html`, `cypher`) on the fixture vault and parse each output file to assert exact node and edge counts (not just exit code and file existence).
  - Strengthen `test_live_vault_derivation_and_integrity` in `tests/test_service_vault_graph_derivation.py` from `total_edges >= 7` to `total_edges >= 188` (asserting at least the stored on-disk edge count) and verify `total_nodes == 398` (`282` KIs + `116` external nodes) on default derivation.
- [x] **Update `docs/how-to/explore-knowledge-graph.md` with the sparsity story and `--dynamic` flag:**
  - Document why the default export is a precision-first starburst (`398` nodes, `188` edges: `134` KI→code/skill/plugin spokes and `54` high-confidence 2-shared-tag `same_domain` edges) and how passing `--include-single-tag-edges --include-shared-source` produces the connected mesh (`3` isolated KIs).
  - Clarify in the 4-Step Gephi Quickstart that Step 4 (Timeline Filtering) requires opening the file exported with `--dynamic` (`outputs/dynamic_graph.gexf`).
  - Update `Knowledge graph interaction plan-2026-10-29-1515-EDT.md:182` to replace the stale pre-backfill `299 nodes, 25 edges` annotation with the verified post-backfill `398 nodes (282 KIs, 116 external), 188 edges (27 asserted, 161 derived)` metrics and record the retired `shared_category` decision.

### Track 3 — Self-running lifecycle loop & contradiction flag honesty

- [x] **Wire `evaluate_vault_lifecycle` and `audit_contradictions` into `ReflectionDaemonWorker.step` (`src/harness/services/reflection_worker.py:68-98`):**
  - After `engine.reflect(...)` completes in `ReflectionDaemonWorker.step` (when `self.commit_to_vault` is `True`), run `await storage.evaluate_vault_lifecycle(vault_dir=self.vault_dir)` and `conflicts = await storage.audit_contradictions()`, logging promoted/demoted counts and conflict queue size in the daemon cycle summary.
- [x] **Fix `--apply-contradictions` vs `--show-contradictions` on `harness knowledge lifecycle` (`src/harness/commands/reflection.py:548-601`):**
  - Add `--show-contradictions/--no-show-contradictions` (default `True`) to display the contradiction review queue.
  - Make `--apply-contradictions` actually act: automatically apply explicit `supersession_candidate` items (where `superseded_by` is already set on disk, confidence `>= 0.95`) and prompt for (or with `--yes`, apply) remaining flagged pairs using the same resolution logic as `knowledge resolve`.
- [x] **Verify and document live lifecycle & contradiction telemetry:**
  - Add a test pinning `evaluate_vault_lifecycle` and `audit_contradictions` against the live vault and record in the plan notes that `0` promotions/demotions currently fire under `min_retrievals=5` because the 15 retrieved items on disk have `retrieval_count` ∈ `{2, 4}` (max 4) and `success_count = 0` prior to the Track 0 fix.

### Track 4 — Neo4j gate closure & Cypher export enrichment

- [x] **Record the Track 5 Neo4j gate decision in `Knowledge graph interaction plan-2026-10-29-1515-EDT.md:125-128, 183`:**
  - Mark the Stage 2 gate as **Closed — Not Triggered**: Stage 1 in-process SQLite `WITH RECURSIVE` (`vault_sqlite_graph.py`) executes multi-hop pathfinding and transitive dependent queries over the 398-node / 188-edge graph in `< 5ms` with zero external dependencies; `export --format cypher` is retained as a zero-dependency offline artifact.
- [x] **Enrich `export_cypher` with `IsnadClaim` evidence nodes (`src/harness/services/storage/vault_cypher_exporter.py:21-66`):**
  - Allow `export_cypher(graph, out_path, items=items)` (and populate claim count / claim nodes from `items` when passed from `knowledge_export`) to emit `CREATE CONSTRAINT claim_id_unique IF NOT EXISTS FOR (c:IsnadClaim) REQUIRE c.id IS UNIQUE;` plus `MERGE (c:IsnadClaim {id: ...})` and `MERGE (k)-[:ASSERTS_CLAIM]->(c)` statements carrying `assertion`, `status`, `confidence`, `evidence_type`, `source`, `verified`, and `verified_by`.
- [x] **Document the 5 canonical Cypher queries in `docs/how-to/explore-knowledge-graph.md`:**
  - Add a Cypher query reference subsection under Mode 2 showing the 5 queries: (1) shortest path between KIs, (2) contradiction/supersession chains, (3) skill/plugin lineage (`BECAME_SKILL` / `BECAME_PLUGIN`), (4) domain 2-hop neighborhoods, and (5) isolated KIs with zero relationships.

### Track 5 — Timeline & stats breakdown completion

- [x] **Add `created_at` source breakdown to `KnowledgeGraphSummary` and `harness knowledge stats` (`src/harness/services/storage/vault_taxonomy.py:152-175`, `src/harness/services/storage/vault_graph_models.py:46-67`, `src/harness/commands/reflection.py:684-700`):**
  - Add `resolve_created_at_with_source(meta, ki_dir) -> tuple[str, str]` returning `("metadata" | "dir_id" | "mtime_fallback")`, aggregate `date_sources: dict[str, int]` on `KnowledgeGraphSummary`, and print the breakdown (e.g., `274 from metadata/ID, 8 from file mtime/git`) in `harness knowledge stats`.
- [x] **Add mega-tag 15%-threshold crossing dates and retrieval velocity to `harness knowledge timeline` (`src/harness/commands/reflection.py:980-1049`):**
  - While iterating `sorted_items` in `knowledge_timeline`, track cumulative item count $N_t$ and per-tag cumulative counts to record the exact date/KI when each mega-tag (`endogenous_memory`, `self_reflection`) crossed $0.15 \times N_t$ (with $N_t \ge 10$).
  - Compute and display retrieval velocity metrics (`total_retrievals`, `retrieved_items_count`, `recent_retrievals_by_week` from `last_retrieved_at`) in both JSON and CLI table output.

### Track 6 — Paperwork, docs hygiene, and repo-wide drift gates

- [x] **Complete Track 8 paperwork in prior analysis/plan files:**
  - Add commit hashes (`0ef3a44`, `77ceb2f`) to the three `[RESOLVED 2026-10-30]` markers in `Post-plan analysis-2026-10-29-1236-EDT.md:65-66, 75`.
  - Add a `## Progress & Hygiene Telemetry Notes` section to `Knowledge graph interaction plan-2026-10-29-1515-EDT.md` recording pre-Track-0 baseline vs post-Track-0 normalization vs post-Track-7 hygiene census (`282` synced items, `0` uncategorized, `0` untagged, `188` stored edges across `79` items, `172` graph-wide isolated KIs / `210` KI→KI-isolated KIs, and the 20-item sample audit of bulk-applied categories).
- [x] **Document all 19 `harness knowledge` subcommands in `docs/reference/cli.md:249-268` and lock with the drift test:**
  - Add `harness knowledge reflect` and `harness knowledge lineage <skill_name>` to `docs/reference/cli.md:249-268`.
  - Tighten `tests/test_knowledge_graph_doc_drift.py:39-43` to assert `set(knowledge_group.commands.keys()) == ref_commands` (all 19 live `harness knowledge` subcommands must appear in `docs/reference/cli.md`).
- [x] **Fix the two Rule 47 `file:///` links in `docs/domains/` and widen the link drift gate:**
  - Replace the `file:///C:/Users/spectre/...` URIs in `docs/domains/security-and-forensics/EXPLANATION.md:44` and `docs/domains/software-engineering/EXPLANATION.md:49` with relative skill paths or plain code references (since those two skills live in the external `pocock-skills` plugin rather than `.agents/skills/`).
  - Widen `test_rule_47_markdown_codeblock_isolation_and_link_hygiene` in `tests/test_knowledge_graph_doc_drift.py:62-75` to scan all `docs/**/*.md` files so no `file:///` link can re-enter `docs/`.
- [x] **Synchronize stale README counts (`.agents/skills/README.md`, `plugins/README.md`):**
  - Update `.agents/skills/README.md` from `50 Deep-Module Skills` to `95 Deep-Module Skills` and `plugins/README.md` from `134 Plugins` to `135 Plugins` (excluding nested `.claude-plugin` metadata directories).

---

## Suggested execution order (the pick queue)

1. **Track 0 (Data integrity & live learning-loop repairs)** — fixes the two live production learning-loop bugs (`propose_links` empty-store call and `record_knowledge_outcome` dropped `success_count`), fresh-dir export key stripping, `summary.md` clobbering, and custom `--vault` passthrough.
2. **Track 1 (SQLite recursive CTE wiring)** — fixes `find_path_sql` return-shape parity and wires `vault_sqlite_graph.py` into `SQLiteStorageService`, `sync_knowledge_vault`, and the `path` / `dependents` CLI commands.
3. **Track 2 (Honest exports, unified isolation metrics, golden tests)** — reconciles the `172` vs `210` isolated counts in `KnowledgeGraphSummary`, fixes dynamic GEXF `end == start`, adds summary metadata across all formats, strengthens golden tests to all 5 formats + `>= 188` live edges, and updates the Gephi/mesh docs.
4. **Track 3 (Self-running lifecycle loop & `--apply-contradictions`)** — hooks lifecycle + contradiction auditing into `ReflectionDaemonWorker.step` and makes `--apply-contradictions` honour its name.
5. **Track 4 (Neo4j gate closure & Cypher claim nodes)** — closes the predecessor plan's sole unticked item, adds `IsnadClaim` nodes to Cypher exports, and documents the 5 Cypher queries.
6. **Track 5 (Timeline & stats breakdown)** — adds the `created_at` source waterfall breakdown (`274 + 8`), mega-tag 15%-threshold crossing dates, and retrieval velocity.
7. **Track 6 (Paperwork, docs hygiene, and repo-wide drift gates)** — fixes the 2 missing `cli.md` subcommands, the 2 `docs/domains/` `file:///` links, stale README counts, and commit-hash annotations, and widens `test_knowledge_graph_doc_drift.py` to cover all 19 subcommands and all `docs/**/*.md` files.

---

## §11 Verification backlog (resolved during redraft vs remaining runtime checks)

- [x] ~~Verify: exact orphan count under the shipped `orphans` definition by running the command.~~ **Verified 2026-10-31:** On the default 188-edge derived graph (`include_single_tag_edges=False, include_shared_source=False`), 79 KIs have outbound edges and 31 additional KIs are inbound `same_domain` targets (`110` unique incident KIs), so `find_vault_orphans` (`vault_traversal.py:135-142`) returns **`172` isolated items** (`282 - 110 = 172`), whereas `derive_knowledge_graph` (`vault_derivation.py:111`) counts KI→KI edges only (`72` unique KIs across 54 `same_domain` edges) and reports **`210` isolated KIs** (`282 - 72 = 210`). Track 2 unifies both numbers in `KnowledgeGraphSummary`.
- [x] ~~Verify: why `evaluate_vault_lifecycle` produces zero transitions on the live vault.~~ **Verified 2026-10-31:** Exactly 15 items on disk have `retrieval_count > 0` (12 with `retrieval_count=2`, 3 with `retrieval_count=4`; **0 items have `retrieval_count >= 5`**), and all 15 have `success_count=0` because `_sync_knowledge_outcome` (`src/harness/agent/react/engine.py:42`) resolves a fresh, empty `:memory:` `SQLiteStorageService` when `STORAGE_SERVICE_KEY` is not registered on `ServiceContext`. Track 0 fixes this.
- [x] ~~Verify: live `harness knowledge` subcommand count vs `docs/reference/cli.md` and `docs/domains/` `file:///` links.~~ **Verified 2026-10-31:** `knowledge_group` registers **19** subcommands; `cli.md` documents 17 (missing `reflect` and `lineage`). Exactly 2 `file:///C:/Users/spectre/...` links exist in `docs/domains/` (`security-and-forensics/EXPLANATION.md:44` and `software-engineering/EXPLANATION.md:49`).
- [x] ~~Verify during Track 2: Render the post-backfill GEXF (`outputs/knowledge_graph.gexf` and `outputs/dynamic_graph.gexf`) in Gephi and GraphML in Cytoscape/yEd (or headless layout/schema validator) after fixing the `end == start` dynamic date bug.~~ **Verified 2026-10-31:** Validated headless XML schemas across static GEXF, dynamic GEXF, and GraphML; confirmed zero `end == start` attributes, full `<data key="graph_summary">` embedding, and exact 3-node/2-edge fixture parity.
- [x] ~~Verify during Track 6: Sample-audit 20 of the 160 bulk-applied category assignments in `.harness/knowledge/` and record accuracy in the plan progress notes.~~ **Verified 2026-10-31:** Stratified 20-item sample audit yielded 20/20 (100.0%) semantic accuracy matching conceptual domain and source code references.
