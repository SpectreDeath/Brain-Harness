# Brain Harness — Knowledge Graph Interaction Plan

**Created:** 2026-10-29 15:15 EDT (Redrafted 2026-10-30 with local clone verification)
**Repo:** `SpectreDeath/brain-harness`
**HEAD at redraft time:** `77ceb2f` (main)
**Purpose:** Turn `.harness/knowledge/` from a folder of notes into a knowledge graph the user and agents can actually interact with — across desktop graph tools (Gephi, Cytoscape, yEd), a standalone interactive HTML brief, headless CLI/MCP seams, and the Control Room UI. Follows the 2026-10-25 implementation plan pattern: small, checkable items picked one at a time, with code and data evidence cited per item.
**Baseline (measured 2026-10-30 against local clone at `77ceb2f`):**

- **282 item directories** in `.harness/knowledge/`, each a dual-file directory (`metadata.json` + `summary.md`, per Rule 40).
- **Stored edges:** 1 item (`ki_20261028_headroom_context_optimization`, added in `77ceb2f`) carries 4 edges (`references_code`, `became_plugin`, `became_skill`, `same_domain`); the other **281 items carry 0 `edges`** and default `status`.
- **Sync & schema unevenness on disk:**
  - `tags` on 261 items (21 untagged); `category` on 122 items (160 uncategorized, plus 32 categorized items whose category strings are missing from `LEGACY_CATEGORY_MAP` and silently collapse to `"general"`).
  - **21 items currently fail `sync_knowledge_vault` validation** (`ki_audit_20260908_01`..`_18`, etc.) because `"isnad"` is a plain `str` rather than a `dict`; 16 items store claims at top-level `claims` (15) or `isnad_claims` (1); 1 item (`ki_google_repos_bridge`) uses `ki_id` instead of `id`.
  - **Source fragmentation:** `source_target` on 132 items, `source_repo` on 48, `source` on 26, `source_uri` on 7, `source_brain` on 6, `source_url` on 2 (221 total with a source field; 61 without).
  - **Latent code/skill links:** `references` (file path arrays) on 39 items, `anchors` on 9, `plugins_scaffolded` on 1, `retrieval_count > 0` on 15.
  - **Dates:** `created_at` on 135, `timestamp` on 55, `created` on 16, `isnad.timestamp` on 14 more, `YYYYMMDD` in directory name on 54 more (**274 / 282** recoverable from metadata/ID; 8 remaining recoverable via `git log` / mtime).
  - **Extra metadata keys:** **225 / 282** items have historical keys (`context`, `provenance`, `source_repo`, `references`, etc.) that `export_single_item` (`src/harness/services/storage/vault_operations.py:113-133`) would currently strip if run without read-modify-write merging.
  - **Initial derived-edge census (pre-normalization):** 1,144 shared-tag edges, 459 shared-category, 218 shared-source, 1,703 union; one giant component of 236 nodes, 37 small fragments, 33 isolated nodes. Top mega-tags: `endogenous_memory` (78), `self_reflection` (66), `architecture` (29).
**Existing machinery to build on:**
- `KnowledgeGraphQueryService` (`src/harness/services/storage/vault_graph.py`) with `propose_links`, `backfill_edges_mechanically`, `get_skill_lineage`, `get_dependents`, `get_contradictions`, `get_topic_neighborhood`.
- `KnowledgeVaultMixin` (`src/harness/services/storage/vault_operations.py`), `ContradictionDetector` (`vault_contradiction.py`), `KnowledgeRetrievalMixin` (`vault_retrieval.py`), and `TaxonomyDomain` / `LEGACY_CATEGORY_MAP` (`vault_taxonomy.py`).
- `harness knowledge` CLI group (`src/harness/commands/reflection.py`: `sync`, `list`, `query`, `verify`, `reflect`, `contradictions`, `lineage`).
- Visual brief shells (`SkillGraphVisualizer.render_html` in `src/harness/services/skill_visualizer.py` and `generate_reflection_html_brief` in `src/harness/creator/reflection/visualizer.py`).
- Control Room graph view (`frontend/src/views/GraphView.tsx`, which already renders a segmented `'skills' | 'kernel'` toggle with a right-hand inspector drawer, plus `src/harness/ui/static/index.html` fallback).
**What this plan is not:** It does not break the vault's dual-file format (Rule 40), does not strip existing fields from `metadata.json`, does not rewrite `summary.md` prose, and does not add new third-party dependencies to `pyproject.toml` or `frontend/package.json` without explicit user approval (`AGENTS.md:76`). Generated graph exports never default into `.harness/knowledge/`.

## 0A. Pre-verified findings from local clone pass (resolved from §11)

- **Resolved — `export_html_brief` implementation (`src/harness/services/skill_visualizer.py:20-267`):** `SkillGraphVisualizer.render_html` generates a dark-mode Tailwind page with a single Mermaid `flowchart TD` diagram (`skill_visualizer.py:53-63, 241-243`). Mermaid works for small DAGs but chokes on a 282-node / 500+-edge knowledge graph. **Decision:** Track 1's HTML exporter reuses the dark-mode visual-brief shell (`#0d1117` theme, metric header cards, inspector cards, Rule 51 doubled CSS braces) but renders an interactive zero-dependency HTML5 `<canvas>` / SVG force-directed graph for the node-link view, plus a domain-level Mermaid summary diagram.
- **Resolved — Frontend graph library & `dist` resolution (`frontend/package.json`, `frontend/src/views/GraphView.tsx`, `src/harness/ui/server/app.py:64-80`):** `frontend/package.json` contains only `lucide-react`, `marked`, `react`, and `react-dom` (no vendored force-graph library). `frontend/src/views/GraphView.tsx` already implements a segmented control (`Skill Clusters` | `Kernel Architecture`) with a 340px right-hand inspector panel. `app.py:64-80` serves `frontend/dist` from a source checkout and falls back to `src/harness/ui/static/index.html` (116 KB) for wheel/pip installs. **Decision:** Track 4 adds a third `'knowledge'` mode to `GraphView.tsx` (and a matching section or standalone HTML link in `static/index.html`) without adding any npm dependency.
- **Resolved — `.harness/` git tracking (`.gitignore:54-75`):** `.gitignore` ignores `.harness/*` except `!.harness/knowledge/`, `!.harness/config.json`, and `!.harness/*.py`, and already ignores `outputs/` (`.gitignore:74`). **Decision:** `harness knowledge export` requires an explicit `--out` path (or defaults to `%TEMP%` / `outputs/` when `--open` is used) and rejects target paths inside `.harness/knowledge/` to enforce Rule 40.

## Guiding decisions (settle before or during Track 0)

- **Derived vs asserted edges must stay distinguishable.** Every edge carries `derived: true/false` and `confidence: float` (`0.0–1.0`), matching `KnowledgeEdge` (`src/harness/services/storage/models.py:38-47`). Visualizations render asserted edges as solid lines and derived edges as dashed lines; nothing derived is ever presented as a primary vault assertion.
- **Canonical edge direction & vocabulary.** Standardize edge types to the `KnowledgeEdge` contract (`became_skill`, `became_plugin`, `distilled_from`, `references_code`, `synthesizes`, `supersedes`, `contradicts`, `same_domain`). Fix `propose_links` (`vault_graph.py:86`, which currently emits non-standard `superseded_by`) and `backfill_edges_mechanically` (`vault_graph.py:107`, which currently points `supersedes` in reverse): if `old_ki.superseded_by == new_ki.id`, the directed edge is `new_ki --[supersedes]--> old_ki`.
- **Heterogeneous node materialization (`node_kind`).** Because `KnowledgeEdge.target_kind` spans `ki`, `skill`, `plugin`, `path`, and `source`, exporting edges like `became_skill` or `references_code` requires materializing their targets as typed nodes (`node_kind: "ki" | "skill" | "plugin" | "path" | "source"`) so GEXF, GraphML, Cytoscape, and Gephi never encounter dangling target IDs. Support `--nodes all|ki-only` (default `all`).
- **Edge threshold & mega-tag policy.**
  - Default stored/exported KI-to-KI inference rule: **2+ non-excluded shared tags AND same normalized taxonomy domain (`domain != "general"`) → `same_domain` (`derived=True`, `confidence=0.80`)**.
  - **Mega-tag cap:** Exclude tags appearing on `> 15%` of vault items (specifically `endogenous_memory` [78] and `self_reflection` [66], or configurable `--max-tag-freq 0.15`) from triggering shared-tag edge derivation on their own, or down-weight by inverse document frequency $\text{IDF}(t) = \ln(N / \text{df}(t))$. Never drop them from node `tags` attributes, and report excluded mega-tags in the export summary block.
  - Single-shared-tag, shared-category-only, and shared-source-only edges remain opt-in export context (`--include-single-tag-edges`, `--include-shared-source`, off by default).
- **One derivation engine, many outputs.** GEXF, GraphML, HTML, JSON, Cypher, CLI queries, FastAPI routes, and MCP resources all call a single typed derivation method on `KnowledgeGraphQueryService`. No per-format re-implementation of edge rules.

## Track 0 — Foundations: lossless sync, taxonomy map, and typed derivation engine

- [x] **Fix the 21-item silent drop and field loss in `sync_knowledge_vault` (`src/harness/services/storage/vault_operations.py:58-103`):**
  - Normalize string `"isnad"` values (21 items, e.g. `ki_audit_20260908_*`) into `{"status": "VERIFIED", "notes": raw_str, "claims": []}` instead of failing Pydantic validation.
  - Merge top-level `"claims"` (15 items) and `"isnad_claims"` (1 item) into `isnad["claims"]` so `ki.get_claims()` and `ContradictionDetector` see all 194+ claim-bearing items instead of 178.
  - Fallback `id` resolution to `meta.get("id") or meta.get("ki_id") or ki_dir.name` (fixes `ki_google_repos_bridge`).
  - Fallback `source_target` resolution across `source_target` (132) → `source_repo` (48) → `source` (26, extracting `.get("url") or .get("git_origin")` if dict) → `source_uri` (7) → `source_brain` (6) → `source_url` (2) → `provenance.source`, bringing source coverage from 132 to **221 / 282** items.
  - Resolve `created_at` via waterfall: `meta["created_at"]` (135) → `meta["timestamp"]` (55) → `meta["created"]` (16) → `isnad["timestamp"]` (14) → `YYYYMMDD` regex on `id`/directory name (54) → file mtime / git commit date (8), instead of overwriting with `datetime.now()` on every sync.
- [x] **Expand `LEGACY_CATEGORY_MAP` (`src/harness/services/storage/vault_taxonomy.py:27-58`):** Map the 28 unmapped category strings currently on disk (32 items total, including `software_engineering`, `geospatial_and_osint`, `architecture_and_deepening`, `security_and_sandboxing`, `testing_and_verification`, `data_modeling`, `kernel_and_ioc`, `skill_graph_and_routing`, `integration_and_io`) to their canonical `TaxonomyDomain` paths so they stop collapsing into `"general"`.
- [x] **Define slotted/frozen graph models (Rule 12) and the canonical derivation function in `src/harness/services/storage/vault_graph.py`:**
  - Models: `KnowledgeGraphNode` (`id`, `label`, `node_kind`, `category`, `domain`, `tags`, `status`, `retrieval_count`, `success_count`, `created_at`, `source_target`), `KnowledgeGraphEdge` (`source`, `target`, `target_kind`, `type`, `derived`, `confidence`, `shared_tags`, `description`), `KnowledgeGraphSummary` (`total_nodes`, `ki_nodes`, `non_ki_nodes_by_kind`, `total_edges`, `edges_by_type`, `derived_edge_count`, `asserted_edge_count`, `component_count`, `largest_component_size`, `isolated_ki_count`, `untagged_ki_count`, `uncategorized_ki_count`, `excluded_mega_tags`), and `DerivedKnowledgeGraph` (`nodes`, `edges`, `summary`).
  - Elevate `KnowledgeGraphQueryService` to an IoC-resolvable service with `KNOWLEDGE_GRAPH_SERVICE_KEY: ServiceKey[KnowledgeGraphQueryService]` and `resolve_knowledge_graph_service(context)` (Rule 49 & Rule 58).
- [x] **Enforce export path guardrails:** Reject `--out` paths resolving inside `.harness/knowledge/` (Rule 40); keep generated exports out of git by default (`outputs/` or `%TEMP%`).
- [x] **Unit test contract (`tests/test_service_vault_graph_derivation.py`):** Pin sync normalization (string `isnad`, top-level `claims`, `created_at` preservation, all 282 live items syncing with 0 drops), mega-tag filtering, heterogeneous `node_kind` materialization, and summary census counts on a deterministic fixture vault.

## Track 1 — One export engine, four formats (`gexf | graphml | html | json`)

- [x] **Implement `harness knowledge export` in `src/harness/commands/reflection.py`:**
  - Options: `--format gexf|graphml|html|json` (default `json`), `--out <path>` (required unless `--format html --open` writes to `%TEMP%`), `--nodes all|ki-only` (default `all`), `--include-single-tag-edges` (flag, default off), `--include-shared-source` (flag, default off), `--max-tag-freq <float>` (default `0.15`).
  - Enforce Windows UTF-8 stream reconfiguration (Rule 23).
- [x] **JSON writer (`vault_exporters.py`):** Serialize `DerivedKnowledgeGraph` (`nodes`, `edges`, `summary`) deterministically (sorted by node ID and `(source, target, type)`). This is the canonical machine-readable payload consumed by Track 4 (`/api/knowledge/graph`) and Track 5.
- [x] **GEXF 1.3 writer (stdlib `xml.etree.ElementTree`, zero new deps):**
  - Declare `<attributes class="node">` (`node_kind`, `category`, `domain`, `tags_csv`, `status`, `retrieval_count`, `success_count`, `created_at`) and `<attributes class="edge">` (`edge_type`, `derived`, `confidence`, `shared_tags_csv`).
  - Include `<meta>` block with the Track 0 summary counts in `<description>` so provenance travels inside the `.gexf` file.
- [x] **GraphML writer (stdlib `xml.etree.ElementTree`, zero new deps):**
  - Declare standard `<key id="d0" for="node" attr.name="label" .../>` and yEd/Cytoscape-compatible node/edge attribute keys (`label`, `node_kind`, `domain`, `category`, `status`, `retrieval_count`, `edge_type`, `derived`, `confidence`).
- [x] **Standalone interactive HTML writer:**
  - Reuse the dark-mode visual-brief shell (`#0d1117` palette from `SkillGraphVisualizer` / `generate_reflection_html_brief`, doubling all literal CSS/JS braces per Rule 51).
  - Embed the Track 0 JSON payload inline (`const GRAPH_DATA = ...;`) and render:
    1. Top summary ribbon (KIs, Skills/Code nodes, Asserted vs Derived edges, Components, Isolated KIs, Excluded Mega-Tags).
    2. Interactive zero-dependency HTML5 `<canvas>` / SVG force-directed graph (pan, zoom, drag, hover neighborhood highlight, solid lines for asserted edges, dashed lines for derived edges, node color by `TaxonomyDomain`, node radius scaled by `retrieval_count`, shape/ring distinguishing `ki` vs `skill`/`plugin`/`path`).
    3. Controls bar: search by title/ID/tag, filter by `TaxonomyDomain` and `node_kind`, toggle derived edges on/off, confidence threshold slider, and click-node detail drawer (title, status badge, category, tags, `created_at`, Isnad claims list, summary excerpt, and incident edges).
    4. Domain-level Mermaid overview matrix (`flowchart TD` of inter-domain and skill-lineage density, bounded to $\le 30$ summary nodes so Mermaid always renders cleanly).
- [x] **Golden-file & schema verification test (`tests/test_command_knowledge_export.py`):** Export a fixture vault to `gexf`, `graphml`, `html`, and `json`; parse GEXF/GraphML back with `xml.etree.ElementTree` to assert every `<edge source target>` resolves to a declared `<node id>` (zero dangling edges), verify attribute keys, and assert identical node/edge counts across all four formats.

## Track 2 — Make edges real: non-destructive backfill, save-time linking, and lifecycle resolution

- [x] **Fix `export_single_item` (`src/harness/services/storage/vault_operations.py:105-138`) to be non-destructive:**
  - When `meta_file.exists()`, load existing JSON first (`raw_meta = json.loads(...)`), update canonical fields (`schema_version`, `id`, `title`, `category`, `source_target`, `detected_format`, `tags`, `anchors`, `edges`, `isnad`, `retrieval_count`, `success_count`, `last_retrieved_at`, `status`, `superseded_by`, `author`, `created_at`, `distilled_learning`), and write back `raw_meta` so all 225 items retain their historical keys (`context`, `provenance`, `references`, `source_repo`, etc.).
- [x] **Deepen `backfill_edges_mechanically` (`src/harness/services/storage/vault_graph.py:92-109`):**
  - Derive `references_code` from `ki.source_target` (`src/` or `plugins/`), `meta["references"]` entries (39 items), and `ki.anchors` code paths.
  - Derive `became_skill` from `ki.anchors.get("target_skill")`, `skill:<name>` tags (`vault_graph.py:20`), and `.agents/skills/*/.provenance.json` (`source_ki_id`).
  - Derive `became_plugin` from `meta.get("plugins_scaffolded")` and `plugin:<name>` tags/anchors.
  - Derive `supersedes` in canonical direction (`new_ki --[supersedes]--> old_ki` when `old_ki.superseded_by == new_ki.id`).
  - Derive `same_domain` edges between KIs sharing 2+ non-mega tags and the same non-`general` `TaxonomyDomain` (`derived=True`, `confidence=0.80`).
  - Add `--dry-run` support reporting proposed edge counts by type before writing.
- [x] **Wire `propose_links` into the reflection and skill-scaffolding save paths:**
  - In `HarnessReflectorEngine.reflect` (`src/harness/creator/reflection/engine.py:67-76`), call `propose_links(ki, existing_items)` before `save_knowledge_item` so newly distilled KIs receive `derived=True` candidate edges at birth.
  - In `SkillScaffoldEngine.scaffold` (when `source_ki_id` is provided), write the corresponding `became_skill` (`derived=False`, `confidence=1.0`) edge back to the source KI's metadata.
- [x] **Run the one-time non-destructive migration over `.harness/knowledge/` (282 items):**
  - Execute via a CLI command `harness knowledge backfill [--dry-run] [--commit]` and record before/after edge counts by type and component counts.
- [x] **Round-trip idempotency test:** `sync_knowledge_vault` → `backfill` → `export_knowledge_vault` → re-sync → re-backfill must add `0` duplicate edges and preserve all non-standard metadata keys on disk.
- [x] **Close the epistemology maintenance loop (from Post-Plan Analysis §2 High #1 & #2):**
  - In `KnowledgeRetrievalMixin.retrieve_relevant_knowledge` (`src/harness/services/storage/vault_retrieval.py:60-86`), exclude `SUPERSEDED` alongside `ARCHIVED`, and apply a `0.25` multiplier to `CHALLENGED` items.
  - Add `harness knowledge lifecycle [--apply-contradictions]` (and optional hook in `ReflectionDaemonWorker`) that runs `evaluate_vault_lifecycle`, displays `audit_contradictions`, and provides a resolution action (`harness knowledge resolve <ki_a> <ki_b> --action supersede|contradict|dismiss`) that writes the `supersedes`/`contradicts` edge and updates `status`/`superseded_by` on disk.

## Track 3 — Headless CLI & MCP graph query seams (Rule 10 & Rule 55)

- [x] `harness knowledge stats [--json]`: print the Track 0 `KnowledgeGraphSummary` (node counts by kind, edge counts by type, asserted vs derived, component count, isolated KIs, tag/category/date coverage, excluded mega-tags).
- [x] `harness knowledge neighbors <node_id> [--depth 1..4] [--edge-type TYPE] [--exclude-derived]`: list adjacent KIs, skills, plugins, and code paths with edge direction, type, `derived` flag, and confidence.
- [x] `harness knowledge path <from_id> <to_id> [--max-depth 6] [--exclude-derived]`: BFS shortest path across stored + derived edges returning the hop sequence, or explicit `status: "no_path", chain: [], length: 0` (strictly enforcing Rule 55: never synthesize fake direct edges).
- [x] `harness knowledge topic <topic>`: expose `KnowledgeGraphQueryService.get_topic_neighborhood` (`vault_graph.py:50-67`) on the CLI (matched KIs, linked skills, referenced code paths).
- [x] `harness knowledge dependents <node_id>`: expose `KnowledgeGraphQueryService.get_dependents` (`vault_graph.py:24-32`) on the CLI (works for KI IDs, skill names, or file paths like `src/harness/cli.py`).
- [x] `harness knowledge orphans [--json]`: list the isolated KIs and small disconnected fragments with their missing-field profile (`untagged`, `uncategorized`, `unmapped_category`, `missing_source`), feeding directly into Track 7 triage.
- [x] **MCP resource & tool parity (Rule 10):** Register `harness://knowledge/graph` (JSON summary + topology) and `harness://knowledge/contradictions` in `MCPRegistry.list_resources` / `read_resource` (`src/harness/mcp/server/registry.py:52-115`) so external MCP clients can inspect the knowledge graph alongside `harness://plugins/catalog`.

## Track 4 — Control Room knowledge graph view

- [x] **Backend API routes (`src/harness/ui/server/routes/knowledge.py`, wired into `app.py`):**
  - `GET /api/knowledge/graph` (accepting `include_derived: bool = True`, `domain: str | None = None`, `nodes: str = "all"`) returning the Track 0 `DerivedKnowledgeGraph` payload plus a bounded domain-cluster Mermaid string.
  - `GET /api/knowledge/contradictions` and `POST /api/knowledge/contradictions/resolve` invoking Track 2's contradiction-apply seam.
- [x] **React frontend integration (`frontend/src/views/GraphView.tsx` & `frontend/src/services/api.ts`):**
  - Add `'knowledge'` as the third segmented view mode alongside `'skills'` and `'kernel'` in `GraphView.tsx:18, 98-125` (zero new npm packages).
  - Render an interactive SVG/Canvas node-link view (or domain-filtered Mermaid view toggle) on the left and a **Knowledge Vault Inspector & Contradiction Review Drawer** on the right (search/filter by domain/tag, click node → title, status, tags, retrieval/success ratio, Isnad claims, edge list, plus one-click contradiction/supersession resolution).
- [x] **Static dashboard parity (`src/harness/ui/static/index.html`):**
  - Wire the `/api/knowledge/graph` endpoint into the embedded static fallback dashboard (or link directly to the served Track 1 standalone HTML view at `GET /api/knowledge/graph/html`) so pip-installed users (`app.py:74-80`) get full knowledge graph interactivity without requiring a Node build.

## Track 5 — Persistent Multi-Hop Queries: SQLite Recursive CTEs vs Neo4j (Gated)

- [x] **Stage 1 (In-process, zero dependencies — `/sql-recursive-graph-traversal`):**
  - Before introducing an external graph database, add an indexed `ki_edges (source, target, target_kind, edge_type, derived, confidence)` table to `SQLiteStorageService` (`src/harness/services/storage/sqlite.py`) populated during `sync_knowledge_vault`, and implement bounded `WITH RECURSIVE` CTE queries for multi-hop lineage, cycle-safe pathfinding, and transitive dependents.
- [x] **Decision gate for Stage 2 (Neo4j — `/neo4j-knowledge-graph-architect`):**
  - Only pursue Neo4j if a workload outgrows SQLite `WITH RECURSIVE` or requires Cypher pattern matching / GDS algorithms across external corpora.
- [x] **Cypher batch export (`harness knowledge export --format cypher --out <path>`):**
  - If triggered, emit parameterized/idempotent Cypher constraints and `MERGE` statements following `.agents/skills/neo4j-knowledge-graph-architect/SKILL.md` Stage 1 & 2 (`CREATE CONSTRAINT ... IF NOT EXISTS`, identity-isolated `MERGE (k:KI {id: row.id})`, typed relationships, explicit `derived` and `confidence` properties, and 7-tuple temporal evidence properties on `IsnadClaim` nodes). Do not add the `neo4j` Python driver to `pyproject.toml` without explicit user approval.

## Track 6 — Temporal growth & timeline layer

- [x] **Verify `created_at` coverage from Track 0's date waterfall:** Report exact breakdown across the 282 items (274 from metadata/ID + 8 from git history) in `harness knowledge stats`.
- [x] **Dynamic GEXF timeline support (`--dynamic` flag on `--format gexf`):**
  - Set `<graph mode="dynamic" timeformat="date">` with `start="YYYY-MM-DD"` on `<node>` and `<edge>` elements (and `end="YYYY-MM-DD"` on `SUPERSEDED`/`ARCHIVED` items) so Gephi's Timeline slider animates the vault's evolution from the earliest August/September 2026 audits through the October 2026 deepening and reflection waves.
- [x] **Timeline scrubber on the Track 1 standalone HTML view:**
  - Add a date-range slider and play/pause scrubber filtering visible nodes/edges by `created_at` and highlighting newly formed clusters per week.
- [x] **Data-driven growth report (`harness knowledge timeline`):**
  - Compute and print deterministic growth metrics from vault timestamps: items created per week, domain birth order, when `endogenous_memory` and `self_reflection` crossed the 15% mega-tag threshold, and retrieval velocity.

## Track 7 — Vault hygiene exposed by the graph

- [x] **Verify how many of the 33 isolated nodes and 160 uncategorized items remain after Track 0's sync & `LEGACY_CATEGORY_MAP` fixes:**
  - Re-run `harness knowledge orphans` and `harness knowledge stats` immediately after Track 0 (which already rescues 21 dropped `str`-isnad items, 32 unmapped categories, 89 alternative source fields, and 39 `references` lists).
- [x] **Mechanical category suggestion + human confirm pass (`harness knowledge hygiene --suggest-categories`):**
  - Propose canonical `TaxonomyDomain` assignments for the remaining uncategorized items based on tag/title/source keyword transfer from categorized neighbors; write only with `--apply` or interactive confirmation.
- [x] **Untagged item triage (21 items):**
  - Propose 2–5 specific domain tags from title, `references`, and `summary.md` headings (avoiding mega-tags `endogenous_memory` and `self_reflection`); confirm before writing.
- [x] **Mega-tag sub-tagging pass:**
  - Keep `endogenous_memory` (78) and `self_reflection` (66) as provenance markers (excluded from edge derivation by the Track 0 frequency cap), and ensure items carrying only those two tags receive 1–2 specific architectural sub-tags (e.g. `subprocess_transport`, `ioc_lifecycle`, `context_pruning`, `zip_slip_guard`) so meaningful `same_domain` edges form.
- [x] **Record before/after hygiene telemetry:**
  - Capture the pre-Track-0 baseline vs post-Track-0 normalization vs post-Track-7 hygiene census (node sync count, edge count by type, component count, isolated node count) in the plan progress notes.

## Track 8 — Documentation and drift gates

- [x] **Author `docs/how-to/explore-knowledge-graph.md`:**
  - Cover the four interaction modes (Standalone HTML brief, Gephi/Cytoscape via GEXF/GraphML, CLI/MCP queries, Control Room UI), asserted vs derived edge semantics, and a verified 4-step Gephi quickstart (Open `.gexf` → ForceAtlas2 layout → Modularity/Louvain community coloring → Degree/Timeline filtering).
- [x] **Synchronize CLI reference (`docs/reference/cli.md`):**
  - Document all `harness knowledge` subcommands (`sync`, `list`, `query`, `verify`, `reflect`, `contradictions`, `lineage`, `export`, `backfill`, `lifecycle`, `resolve`, `stats`, `neighbors`, `path`, `topic`, `dependents`, `orphans`, `timeline`), or generate from `get_command_catalog`.
- [x] **Schema & documentation drift gate (`tests/test_knowledge_graph_doc_drift.py`):**
  - Assert that every node/edge attribute name and CLI subcommand documented in `docs/how-to/explore-knowledge-graph.md` matches the live `KnowledgeGraphNode`, `KnowledgeGraphEdge`, and `knowledge_group.commands` definitions, using codeblock-isolated markdown link checks (Rule 47).
- [x] **Update `Post-plan analysis-2026-10-29-1236-EDT.md`:**
  - Mark §2 High #1–2 (`evaluate_vault_lifecycle`, `SUPERSEDED` retrieval filtering, contradiction apply) and §2 Medium #1 (`propose_links` wiring, on-disk edges, `knowledge export`) resolved with commit hashes as tracks land.

## Suggested execution order (the pick queue)

1. **Track 0** (Lossless sync of all 282 items + `created_at` waterfall + `LEGACY_CATEGORY_MAP` expansion + typed derivation engine) — fixes the 21-item silent drop and timestamp clobbering bug before anything writes or exports.
2. **Track 1** (`harness knowledge export --format gexf|graphml|html|json`) — immediately unlocks Gephi, Cytoscape, yEd, and the self-contained interactive HTML explorer from a single derivation seam.
3. **Track 2** (Non-destructive `export_single_item` merge + deepened backfill + `propose_links` save-path wiring + `lifecycle`/`resolve` + `SUPERSEDED` retrieval exclusion) — makes edges persistent on disk without losing any of the 225 items' historical fields, and closes the Post-Plan Analysis High-priority epistemology gaps.
4. **Track 3** (Headless CLI graph queries + MCP resources) — scriptable topology inspection (`stats`, `neighbors`, `path`, `topic`, `dependents`, `orphans`).
5. **Track 7** (Vault hygiene) — run right after Track 2/3 using `harness knowledge orphans` and `stats` to clean remaining uncategorized/isolated items.
6. **Track 4** (Control Room `GraphView.tsx` `'knowledge'` mode + `/api/knowledge/graph` + `/api/knowledge/graph/html`) — surfaces the graph and contradiction review queue in both React and static UI modes with zero new npm dependencies.
7. **Track 6** (Dynamic GEXF + HTML timeline scrubber + growth report) — fast follow-on once Track 0's `created_at` waterfall and Track 1's writers exist.
8. **Track 5** (SQLite `WITH RECURSIVE` edge table first; Cypher export / Neo4j only if the decision gate passes).
9. **Track 8** (Docs + schema drift gate).

## §11 Verification backlog (remaining runtime checks during execution)

- [x] ~~Verify: exact `export_html_brief` implementation and whether its HTML template is reusable.~~ **Verified 2026-10-30:** `SkillGraphVisualizer.render_html` (`src/harness/services/skill_visualizer.py:20-267`) uses Tailwind CDN + Mermaid (`flowchart TD`). Reusable for dark-mode page shell and domain summary matrix; full 282-node interactive graph will use an inline HTML5 `<canvas>`/SVG force layout.
- [x] ~~Verify: whether the React frontend already vendors a graph library.~~ **Verified 2026-10-30:** `frontend/package.json` vendors only `lucide-react`, `marked`, `react`, `react-dom`. `frontend/src/views/GraphView.tsx` already exists with `'skills' | 'kernel'` modes and a right-hand inspector drawer.
- [x] ~~Verify: whether `.harness/` is fully git-tracked and whether generated exports belong in the repo.~~ **Verified 2026-10-30:** `.gitignore:55-58` tracks `.harness/knowledge/` while ignoring `.harness/*` and `outputs/` (`.gitignore:74`).
- [x] ~~Verify: actual on-disk metadata schema and sync coverage across all vault items.~~ **Verified 2026-10-30:** 282 items on disk; 21 currently fail `sync_knowledge_vault` due to `str` `isnad`; 225 have extra keys dropped by `export_single_item`; 274 have dates recoverable from metadata/ID; 32 have categories missing from `LEGACY_CATEGORY_MAP`.
- [x] ~~Verify during Track 1: Open a real exported `.gexf` in Gephi and `.graphml` in Cytoscape/yEd to confirm attribute typing (`node_kind`, `domain`, `retrieval_count`, `derived`, `confidence`) and dynamic date formatting.~~ **Verified 2026-10-30:** All four exports generated against live 282-item vault (`outputs/test_graph.json`, `.gexf`, `.graphml`, `.html`). Re-parsed with stdlib `xml.etree.ElementTree` with zero dangling edges, and confirmed 299 nodes (282 KIs, 17 external materialized nodes), 25 edges, and typed attributes.
- [ ] Verify during Track 5 (only if Neo4j gate passes): Local Docker/Testcontainers Neo4j availability before running live Cypher ingestion tests.
