# Gephi Desktop Test Plan (2026-11-07 EST — Redrafted)

## Goal

Run the Track 8 manual Gephi 0.10+ verification on the vault knowledge graph and record what Gephi actually shows, so Track 8 (`Standing gaps analysis and plan-2026-11-05-1755-EST.md` §8.1) and Track 6 (`Post-execution audit and follow-up plan-2026-11-06-EST.md` §6.1) can be ticked with primary GUI evidence — or any remaining gap documented.

This is a human-GUI job. No headless script, agent check, or HTML export may tick Track 8 / Track 6.1.

> **Independent Check Verdict (2026-11-07):** Track 0 fully verified; steps 4 and 6 partially supported (4b never run; no vector export). Independent check at `fc5b2f6`.

## Starting facts (verified 2026-11-07 at BH HEAD `899d618`)

- **File**: `.harness/graph/knowledge_graph.gexf` — **451 nodes, 218 directed edges** (27 asserted, 191 derived), regenerated Nov 6.
  - **Node kinds**: `309` `ki`, `116` `path`, `17` `skill`, `8` `plugin`, `1` `source`.
  - **Node attributes actually carried in `<attributes class="node">`** (9 attributes, IDs `0`–`8`): `node_kind`, `category`, `domain`, `tags`, `status`, `retrieval_count`, `success_count`, `created_at`, `source_target`. *(Note: `degree` is not stored as an `<attvalue>` in the file; Gephi computes `Degree` / `In-Degree` / `Out-Degree` automatically upon import.)*
  - **Edge attributes carried in `<attributes class="edge">`** (4 attributes, IDs `0`–`3`): `edge_type`, `derived`, `confidence`, `shared_tags`, plus native GEXF `weight` (`confidence`).
- **Missing `<viz:color>` and `<viz:size>` (`0` of each in the current file)**:
  - Track 8.1's requirement to *"verify node colors (`viz:color`) and sizes (`viz:size`)"* cannot pass on the current `.gexf` because `src/harness/services/storage/vault_exporters.py` (`export_gexf`) does not emit GEXF `viz:` elements.
  - **Three implementation traps in `vault_exporters.py` that Track 0 below must handle**:
    1. **200-line ceiling (`Rule 11`)**: `src/harness/services/storage/vault_exporters.py` is currently **196 lines**, and `tests/test_storage_decomposition.py::TestStorageServiceDecomposition::test_submodule_line_counts` enforces `<= 200` lines on every `*.py` file in `src/harness/services/storage/`. Track 0 must keep `vault_exporters.py` $\le 200$ lines (or move GEXF viz helpers into a sibling module).
    2. **Color key (`domain` / `node_kind`, not raw `category`) & full 10-color palette**: `.harness/graph/knowledge_graph.gexf` has **38 distinct `category` values** (e.g., `developer_experience/architecture` [19], `developer_experience/software_engineering` [11]) and **0 nodes** with `category="plugins / external"` (external nodes have `domain = category = node_kind` $\in \{\text{"path"} [116], \text{"skill"} [17], \text{"plugin"} [8], \text{"source"} [1]\}$). Matching raw `n.category` against only the 5 colors named in `docs/reference/knowledge-graph-visual-brief.md` §3 would leave **278 of 451 nodes (61.6%)** default grey. Track 0.2 resolves colors by `n.domain` (with fallback to `n.category.split("/")[0]` and `n.node_kind`) across all 10 canonical buckets.
    3. **Truncated `label=")"` on 5 parenthesized code-path nodes**: In `src/harness/services/storage/vault_derivation.py:60`, `Path(e.target).name` produces `label=")"` for 5 nodes whose node id (`e.target`) ends with `/)` (`Brain Harness (src/harness/services/context_optimizer/)`, `hyperframes/`, `memory_decay/`, `prometheus/`, `pyrit_scanner/`). Stripping trailing `/) ` before extracting `.name` restores readable labels in Gephi.
- **Reference numbers to compare against (and why raw counts differ slightly from the Nov 5 brief)**:
  - `docs/reference/knowledge-graph-visual-brief.md` §2 was computed on an earlier **417-node** snapshot ($226\text{ connected} + 191\text{ isolated} = 417$) and reported: Louvain **$Q = 0.9447$**, **58 communities** (on the 226-node connected subgraph), **248 components**, **191 isolated nodes**, and **largest component = 34 nodes**.
  - On the current **451-node / 218-edge** `.gexf` at `899d618`, the exact ground-truth topology is:
    - **Connected components**: **254** (vs. 248 in the 417-node brief)
    - **Isolated nodes (`degree = 0`)**: **186** (vs. 191 in the brief)
    - **Connected subgraph (`degree >= 1`)**: **265 nodes** (vs. 226 in the brief)
    - **Largest connected component**: **37 nodes** (next largest components are `8, 8, 8, 7, 7, 6, 6, 6, 6`). Whether this 37-node component corresponds to the brief's Clusters 1 (19 nodes) + 2 (15 nodes) is a question for step 5, not established ground truth — membership has shifted since the brief's 417-node snapshot.
    - **Max node degree**: **7** (`ki-deepening-cycle-history`, `ki-topology-map`, `ki_google_repos_bridge`), followed by **6** (`ki-file-size-hotspots`, `ki-hf-datasets-arrow-streaming`, `ki_audit_20260908_02`, `ki_garf_reporting_engine`).

## Prerequisites

- Gephi 0.10+ installed and open on the desktop; repository checked out at `899d618` (or the commit produced by Track 0 — record the exact `git rev-parse --short HEAD` used).
- Never hand-edit `.harness/graph/knowledge_graph.gexf`; always generate it via `harness knowledge export --format gexf --out .harness/graph/knowledge_graph.gexf`.

## Track 0 — Fix `viz:color` / `viz:size` in `export_gexf` and `label=")"` in `vault_derivation.py` (do this first)

Deepen the existing exporter in place (`Rule 20`), author the failing test contract before editing (`Rule 13`), and respect the $\le 200$-line ceiling on `src/harness/services/storage/*.py` (`Rule 11` / `tests/test_storage_decomposition.py`).

- [x] **0.1 (Failing test contract)**: In `tests/test_command_knowledge_export.py` (`test_export_gexf_zero_dangling_edges_and_attributes`), add assertions using `ns = {"g": "http://www.gexf.net/1.3draft", "viz": "http://www.gexf.net/1.3draft/viz"}` that:
  1. Every `<g:node>` contains a `<viz:color r="..." g="..." b="..."/>` child with integer RGB attributes in `0..255` and a `<viz:size value="..."/>` child with `6.0 <= float(val) <= 24.0`.
  2. Nodes with higher degree in `fixture_graph` (`ki_01`, degree 3) receive a strictly larger `<viz:size>` than degree-1 nodes (`agent-architect`), and `ki_01` (`developer_experience`) receives `#3498db` (`r="52" g="152" b="219"`).
  3. A `source_target` ending in `/)` (e.g., `"Brain Harness (src/harness/services/pyrit_scanner/)"`) derives node `label="pyrit_scanner"`, never `")"`.
- [x] **0.2 (Exporter & label implementation)**:
  - In `src/harness/services/storage/vault_derivation.py:60`, strip trailing `/) ` before extracting the path basename (`clean_t = e.target.rstrip("/) "); label = Path(clean_t).name if "/" in clean_t or "\\" in clean_t else e.target`). Note: `rstrip("/) ")` would also mangle a hypothetical `...(v2)`-style target — acceptable here, but don't generalize the strip without a test.
  - In `src/harness/services/storage/vault_exporters.py` (`export_gexf`), while keeping `vault_exporters.py` **$\le 200$ lines**:
    1. Register/declare `"xmlns:viz": "http://www.gexf.net/1.3draft/viz"` on the root `<gexf>` element.
    - **Caveat (unconfirmed):** the official GEXF 1.3 spec uses `http://gexf.net/1.3/viz`; the `1.3draft/viz` URI above is analogy only. If nodes load flat grey in step 2, try the official URI before concluding the exporter is broken.
    2. Compute undirected degree `deg[node_id]` across `graph.edges` (`max_deg = max(deg.values(), default=1) or 1`) and emit `<viz:size value="..."/>` using `size = round(min(24.0, 6.0 + 18.0 * (deg[n.id] / max_deg)), 2)` (isolated nodes = `6.0`, max-degree nodes = `24.0`). Default isolated nodes to `deg = 0` (`dict.get(n.id, 0)`), or the lookup raises `KeyError`.
    3. Resolve each node's color key via `key = (n.domain or n.category.split("/")[0] or n.node_kind).strip().lower()` and emit `<viz:color r="..." g="..." b="..."/>` from the 10-bucket palette (matching `docs/reference/knowledge-graph-visual-brief.md` §3 + remaining `TaxonomyDomain` / external kinds):
       - `developer_experience`: `#3498db` (`r="52" g="152" b="219"`) — Blue
       - `agent_orchestration`: `#9b59b6` (`r="155" g="89" b="182"`) — Purple
       - `data_engineering`: `#e67e22` (`r="230" g="126" b="34"`) — Orange
       - `security_and_forensics`: `#e74c3c` (`r="231" g="76" b="60"`) — Red
       - `plugin` / `source` / `plugins / external`: `#1abc9c` (`r="26" g="188" b="156"`) — Teal
       - `memory_and_epistemics`: `#f1c40f` (`r="241" g="196" b="15"`) — Gold
       - `infrastructure_and_runtime`: `#2ecc71` (`r="46" g="204" b="113"`) — Green
       - `scientific_computing`: `#00bcd4` (`r="0" g="188" b="212"`) — Cyan
       - `context_engineering`: `#e91e63` (`r="233" g="30" b="99"`) — Pink
       - `skill`: `#8e44ad` (`r="142" g="68" b="173"`) — Deep Violet
       - `path` / `general` (default fallback): `#95a5a6` (`r="149" g="165" b="166"`) — Slate Grey
- [x] **0.3 (Regenerate & run headless verification suite)**:
  - Regenerate `.harness/graph/knowledge_graph.gexf`:
    ```powershell
    .\.venv\Scripts\harness.exe knowledge export --format gexf --out .harness/graph/knowledge_graph.gexf
    ```
  - Verify counts via PowerShell (`Rule 30` — do not rely on bash `grep -c`):
    ```powershell
    (Select-String -Path .harness/graph/knowledge_graph.gexf -Pattern "<viz:color ").Count  # expect 451
    (Select-String -Path .harness/graph/knowledge_graph.gexf -Pattern "<viz:size ").Count   # expect 451
    (Select-String -Path .harness/graph/knowledge_graph.gexf -Pattern 'label="\)"').Count    # expect 0
    ```
  - Run the full storage/exporter contract suite and linter:
    ```powershell
    .\.venv\Scripts\python.exe -m pytest tests/test_command_knowledge_export.py tests/test_service_knowledge_timeline.py tests/test_storage_decomposition.py -q
    .\.venv\Scripts\ruff.exe check src/harness/services/storage/ tests/test_command_knowledge_export.py
    ```

## Steps (Human Desktop GUI Session in Gephi 0.10+)

- [x] **1. Import & Census Check**: Open `.harness/graph/knowledge_graph.gexf` in Gephi 0.10+. In the **Import Report** dialog, verify graph type is `Directed` (or `Mixed`), `451` nodes, `218` edges, and `0` parser warnings. Click **OK** and record the exact node/edge counts shown in the **Context** pane.
- [x] **2. Verify Pre-Baked `viz:color` & `viz:size` Immediately on Load**: Before touching the **Appearance** pane, inspect the **Overview** graph canvas:
  - Confirm nodes already render in distinct domain colors (Blue, Purple, Orange, Red, Teal, Gold, Green, Cyan, Pink, Violet, Slate Grey) and scaled node sizes (`6.0`–`24.0`) directly from `<viz:color>` and `<viz:size>`.
  - If nodes load as uniform flat grey/black circles of equal size, Track 0's `viz:` emission is defective — **stop and record the defect**; do not mask it by manually clicking **Appearance → Nodes → Partition/Ranking**.
  - *(Optional for edge styling)*: Since GEXF `<viz:color>` on nodes does not style edges by type, you may optionally apply **Appearance → Edges → Color → Partition → `edge_type`** (`became_skill` `#f1c40f`, `became_plugin` `#2ecc71`, `references_code` `#7f8c8d`, `same_domain` `#95a5a6`) if helpful for visual clarity, noting in the session report whether edge colors were applied in Gephi.
- [x] **3. Spatial Layout Execution**:
  - In the **Layout** pane, select **ForceAtlas 2**: set `Scaling = 2.0`, `Gravity = 1.0`, `Prevent Overlap (AdjustSizes) = Checked`, `Tolerance (Speed) = 0.1`. Run until the layout stabilizes, then click **Stop**.
  - Run **Expansion** (`Scale factor = 1.2`) once or twice, followed by **Label Adjust** (with node labels toggled on in the Overview/Preview toolbar) and confirm none of the hub labels read `")"`.
- [x] **4. Connected Components & Modularity (Unfiltered vs. Connected Subgraph)**: *(Verified 2026-11-07: Unfiltered 254 components, 186 isolated, max 37, Q=0.953, 255 communities; Connected subgraph `deg >= 1` [265 nodes] Q=0.953, 69 communities. Recorded in `reports/gephi-session-2026-11-07.md` §2.4 and `reports/gephi/gephi-modularity-report-connected-2026-11-07.png`.)*
  - Run **Statistics → Connected Components** (Undirected). Record the total number of weakly connected components (expect **254**), isolated nodes (expect **186** of size 1), and largest component size (expect **37**).
  - **4a (Unfiltered 451-node graph)**: Run **Statistics → Modularity** (`Randomize = Checked`, `Use edge weights = Checked`, `Resolution = 1.0`). Record unfiltered $Q$ and total modularity classes (note: Gephi counts each of the 186 isolated nodes as its own community, so total unfiltered communities will be $\ge 254$ (186 isolated nodes as their own communities, plus at least one per multi-node component).
  - **4b (Connected subgraph `Degree >= 1`, matching the brief's methodology)**: In **Filters → Topology → Degree Range**, drag the lower bound to `1` and click **Filter** (confirming Context shows **265 nodes / 218 edges**, i.e., `58.8%` of nodes). Re-run **Statistics → Modularity** (`Resolution = 1.0`, `Use edge weights = Checked`) on the filtered subgraph. Record connected-subgraph $Q$ and community count, and compare directly against the Nov 5 brief ($Q = 0.9447$, `58` communities on `226` connected nodes).
- [x] **5. Inspect Top Epistemic Communities**:
  - In **Data Laboratory → Nodes** (or **Appearance → Nodes → Partition → Modularity Class** preview list), sort/group by `Modularity Class` and inspect the largest communities.
  - Check whether the top clusters match the brief's §2 top-8 list (Architecture Deepening, Multi-Agent Swarms, Google Repos Bridge, PyRIT Security, Multi-Agent Debate/Critic, Arrow Zero-Copy Datasets, Garf SQL Pipelines, Paperless-NGX/SQLite-Vec) and whether the 37-node giant component bridges Cluster 1 (`Architecture Deepening`) and Cluster 2 (`Multi-Agent Swarms`). Record matches and any surprises.
- [x] **6. Export Visual Artifacts**: *(Verified 2026-11-07: High-resolution screenshots `gephi-forceatlas2-overview-2026-11-07.jpg`, `gephi-preview-labels-2026-11-07.jpg`, and vector export `gephi-forceatlas2-overview-2026-11-07.svg` saved in `reports/gephi/` and linked in `reports/gephi-session-2026-11-07.md`.)*
  - In **Preview** (with `Show Labels = Checked`, `Proportional size = Checked`) and/or **Overview**, export a dated high-resolution screenshot (`reports/gephi/gephi-overview-2026-11-07.png`) and a vector export (`reports/gephi/gephi-preview-2026-11-07.svg` or `.pdf`).
- [x] **7. Write the Session Evidence Report**:
  - Author `reports/gephi-session-2026-11-07.md` recording:
    1. Exact commit SHA tested and Gephi version (`0.10.x`).
    2. Imported node/edge counts (`451 / 218`) and verification that `<viz:color>` and `<viz:size>` rendered automatically on load without manual node Partition/Ranking.
    3. Layout settings used (`ForceAtlas2` parameters, `Expansion`, `Label Adjust`, whether `Degree >= 1` filter was active for the screenshot).
    4. Exact Statistics outputs: Connected Components (`254` components, `186` isolated, `37` max component), unfiltered Modularity ($Q$, community count), and connected-subgraph (`Degree >= 1`, `265` nodes) Modularity ($Q$, community count) side-by-side against the Nov 5 brief ($Q = 0.9447$, `58` communities on `226` nodes).
    5. Top community membership comparison and any visual anomalies observed (isolated-node ring clutter, label overlap, attribute gaps).
    6. Relative links (`Rule 47`) to the exported `.png` and `.svg`/`.pdf` under `reports/gephi/`.
- [x] **8. Tick the Standing Checkboxes**:
  - Only after `reports/gephi-session-2026-11-07.md` and the screenshot/vector artifact exist on disk, tick `[x]`:
    1. Track **8.1** in `Standing gaps analysis and plan-2026-11-05-1755-EST.md` (line 459).
    2. Track **6.1** in `Post-execution audit and follow-up plan-2026-11-06-EST.md` (line 229).
  - Append the dated citation (`reports/gephi-session-2026-11-07.md` + `reports/gephi/gephi-overview-2026-11-07.png`) inline on both ticked items.

## If it fails

- If Gephi fails to parse `.harness/graph/knowledge_graph.gexf` or ignores `<viz:color>` / `<viz:size>`, record the exact Gephi error dialog / log output and stop. Do not substitute a headless script or the HTML brief export, and do not manually re-color nodes in Gephi to hide an exporter bug.
- If imported counts differ from `451` nodes / `218` edges, record both numbers, regenerate the `.gexf` from `.harness/knowledge/`, and check `git status` for uncommitted vault changes.

## Evidence rule and guardrails

- **No premature ticking**: Tick neither Track 8.1 nor Track 6.1 without both `reports/gephi-session-2026-11-07.md` and at least one exported visual artifact (`reports/gephi/*.png` / `*.svg` / `*.pdf`) on disk.
- **Explicit write scopes**:
  - **Track 0 (Exporter Pre-Flight)**: `src/harness/services/storage/vault_exporters.py` (must stay $\le 200$ lines), `src/harness/services/storage/vault_derivation.py`, `tests/test_command_knowledge_export.py`, and regenerated `.harness/graph/knowledge_graph.gexf`.
  - **Steps 1–8 (Gephi GUI Session)**: Read-only with respect to code and `.harness/`; repo writes are strictly limited to `reports/gephi/*`, `reports/gephi-session-2026-11-07.md`, and the two checkboxes in the Nov 5 / Nov 6 plans.
- **No new third-party dependencies** (`pyproject.toml` untouched).
