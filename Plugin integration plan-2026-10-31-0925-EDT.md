# Brain Harness — Plugin Integration Plan

**Created:** 2026-10-31 09:25 EDT (Redrafted 2026-10-31 with live-code verification, resolved §11 backlog findings, exact file/line seams, and `AGENTS.md` architectural invariants)
**Repo:** `SpectreDeath/brain-harness`
**HEAD at planning time:** `c1ec34e` / `8ba3f55` (main)
**Purpose:** One unified, code-verified plan for the plugin-integration program: take the capable-but-buried plugins found in the 2026-10-31 survey and give them the same treatment as REA and Agent Dock — examined against live code, surfaced cleanly through thin facades, connected to the learning core, and locked with drift gates — instead of fixing them one ad-hoc plan at a time.

---

## Baseline (Measured & Code-Verified 2026-10-31 Against Local Clone)

### 1. Exact Repository Counts (Resolving the Survey Count Wobble)
- **Plugin manifests on disk:** **137** `plugin.json` files total under `plugins/`, partitioned into:
  - **134 canonical Harness plugins** at depth 3 (`plugins/<category>/<name>/plugin.json`, across 10 domain categories where `category != "external"`).
  - **1 external skill-bundle manifest** at `plugins/external/Pocock-skills-main/plugin.json` (`name: "mattpocock-skills"`, 35 entrypoints, `isolation: "subprocess"`, `trusted: false`).
  - **2 nested upstream `.claude-plugin/plugin.json` files** inside the vendored Pocock tree (`plugins/external/Pocock-skills-main/.claude-plugin/plugin.json` and `.../skills-main/.claude-plugin/plugin.json`) that inflated naive `rglob("plugin.json")` counts.
- **Total declared plugin tool entrypoints:** **625** (`590` across the 134 canonical Harness plugins + `35` in `mattpocock-skills`).
- **Workspace agent skills (`.agents/skills/*/SKILL.md`):** **96** skills (each paired with `CARD.md` per `Rule 37`).
- **Canonical CLI command groups (`src/harness/cli.py:_CANONICAL_GROUPS`):** **42** groups + **10** standalone commands + **35** declared aliases in `src/harness/commands/aliases.py`.

### 2. What Has Already Landed Since Initial Survey (Do Not Rebuild — `Rule 20`)
Live code inspection confirms several items assumed missing in the initial 09:25 draft **already exist** in the codebase:
- **REA Toolkit + Differential Facet Verifier + Reconstruction Obligation Ledger (`REA toolkit plan-2026-10-31-0849-EDT.md`):**
  - `src/harness/services/rea_toolkit.py` (`REA_TOOLKIT_KEY`), `src/harness/commands/rea.py` (`harness rea inspect|list|providers|decompile|callgraph|signatures|devices|diff|learn|learned`), and `.agents/skills/rea-reverse-engineering/` (`SKILL.md` + `CARD.md`) are **already implemented and registered** in `src/harness/cli.py:139`.
  - `src/harness/services/differential_facet.py` (`harness facet compare|claim-absence|verify|export`, `.agents/skills/differential-facet-verifier/`) and `src/harness/services/reconstruction_obligation.py` (`harness rol ingest|obligation|verify|export`, `.agents/skills/reconstruction-obligation-ledger/`) are **already integrated** behind `harness rea diff` and `harness rea learn`.
- **Agent Dock (`Agent Dock plan-2026-10-31-0909-EDT.md`):**
  - `src/harness/services/dock.py` (`DOCK_SERVICE_KEY`) and `src/harness/commands/dock.py` (`harness dock`) are **already registered** in `src/harness/cli.py:124`.
- **Skill Knowledge Graph CLI (`src/harness/commands/skills/`):**
  - Contrary to the initial draft's assumption that `skill_knowledge_graph` had no CLI surface, `harness skills` (`src/harness/cli.py:144`) **already exposes 15 subcommands**: `capabilities`, `chain`, `check-chain`, `clusters`, `create`, `graph`, `guidance`, `info`, `intercept`, `list`, `prereqs`, `route`, `run`, `select`, and `validate`.
  - Only **2 of the 9** `plugin.skill_knowledge_graph` entrypoints (`get_cross_cluster_bridges` and `index_skill_catalog`) lack subcommands on `harness skills`, and the **cross-graph joint query** (`SkillIntelligenceService` ↔ Knowledge Vault `SQLiteStorageService`) remains unbuilt.
- **Existing Skills & Partial Surfaces on Target Plugins:**
  - `memory_decay_engine` already has `src/harness/services/memory_decay.py` (`MEMORY_DECAY_SERVICE_KEY`), `config.default.yaml`, and `.agents/skills/ebbinghaus-memory-governor/SKILL.md` (`CARD.md`), lacking only a CLI surface and `"provides": ["service.memory_decay"]` in `plugin.json`.
  - `okf_memory` already has `src/harness/services/okf_memory.py` (`OKF_MEMORY_SERVICE_KEY`), `src/harness/commands/okf.py` (`harness okf scope|search|show|validate`), and `.agents/skills/okf-memory-governor/SKILL.md`.
  - `paperless_ngx` already has `src/harness/services/paperless_ngx.py` (`PAPERLESS_NGX_SERVICE_KEY`), `config.default.yaml`, and `.agents/skills/paperless-document-pipeline/SKILL.md` (`CARD.md`).

### 3. Cross-Cutting Architectural Trap Caught During Verification (`Rule 58` + Manifest `provides` Drift)
- **Trap 1 — Null `provides` in `plugin.json` despite `ctx.provide()` in `main.py`:**
  Six target plugins (`gods_eye_view`, `context_type_system`, `memory_decay_engine`, `memgraphrag`, `graphiti_memory`, `wiki_compiler`) declare `"provides": null` (or omit `provides`) in `plugin.json` even though their `main.py` subclasses `HarnessPlugin` and calls `ctx.provide(KEY, self)` (`Rule 3`, `Rule 45`). When loaded via `PluginLoader`, the topological dependency sorter and `SandboxedPlugin.on_load` rely on `manifest.provides` to register service keys into `ServiceContext`!
- **Trap 2 — Missing `config.default.yaml` (`Rule 44` Zero-Fork Config):**
  Seven target plugins (`mantis_security_review`, `skill_knowledge_graph`, `context_type_system`, `okf_memory`, `memgraphrag`, `graphiti_memory`, `wiki_compiler`) are missing co-located `config.default.yaml` files in `plugins/<category>/<name>/`.
- **Trap 3 — `SandboxedPlugin` vs In-Process Service Resolution (`Rule 58`):**
  Plugins with `"isolation": "subprocess"` (`gods_eye_view`, `memory_decay_engine`, `memgraphrag`, `paperless_ngx`, `wiki_compiler`) are wrapped in `SandboxedPlugin` (`src/harness/plugins/sandboxed.py:69`) when loaded from manifests. Every new service resolver (`resolve_gods_eye_view`, `resolve_mantis_security_review`, etc.) must implement a `Rule 58` adapter supporting `SandboxedPlugin.invoke_typed()`, in-process `HarnessPlugin` / domain engines, and `MagicMock(spec=...)` test doubles without `AttributeError`.

---

## Guiding Principles

1. **Integrate before building new (`Rule 20`).** Wire existing services, skills, and CLI groups before writing new code. Never duplicate a command group (`Rule 6`) or fork a second copy of an existing skill.
2. **Facade, not rewrite (`Rule 49`, `Rule 58`).** Each toolkit gets a thin CLI/service front door delegating to its existing slotted domain engine, wrapped in a `Rule 58` adapter that handles `SandboxedPlugin`, in-process instances, and test mocks.
3. **Complete surface triad + manifest hygiene (`Rules 3, 10, 37, 44, 45`).** A plugin counts as integrated when it has:
   - Accurate `plugin.json` (`provides` matching its `ServiceKey[T]`) + co-located `config.default.yaml` (`Rule 44`),
   - A headless Click CLI surface (`Rule 6`, `Rule 10`, `Rule 23` UTF-8 stream reconfiguration, `--json`),
   - A compliant skill in `.agents/skills/<name>/` (`SKILL.md` + single-pipe `CARD.md` per `Rule 37`, 100–350 char description per `Rule 44`, relative links per `Rule 47`), and
   - Diátaxis documentation + automated CLI/manifest drift gate coverage.
4. **Avoid top-level CLI sprawl.** Prefer adding subcommands to existing canonical groups (`harness skills`, `harness context`, `harness doc`) where the domain matches, and create new top-level groups only for major standalone toolkits (`harness gev`, `harness mantis`).
5. **Untrusted stays untrusted (`Rule 5`, `Rule 7`).** External/vendored bundles (`plugins/external/`) remain `trusted: false` with lazy subprocess isolation and never auto-upgrade trust.

---

## Track 0 — Close the REA Record & Fix Manifest/Config Drift Baseline

- [x] **REA Plan Track 5 & Verification Record (`REA toolkit plan-2026-10-31-0849-EDT.md`):**
  - *Already completed in `901996e` / `src/harness/services/rea_toolkit.py`:* `REA toolkit plan-2026-10-31-0849-EDT.md` integrates `DifferentialFacetService` (`src/harness/services/differential_facet.py`) and `ReconstructionObligationService` (`src/harness/services/reconstruction_obligation.py`) behind `harness rea diff` and `harness rea learn`.
- [ ] **Verify & Lock `differential_facet_verifier` + `reconstruction_obligation_ledger` Plugin Seams:**
  - Add missing `README.md` front-door files to `plugins/security_and_forensics/differential_facet_verifier/` and `plugins/security_and_forensics/reconstruction_obligation_ledger/`, plus `config.default.yaml` to `reconstruction_obligation_ledger/` (`Rule 44`), linking both to `docs/how-to/use-rea-toolkit.md` via relative paths (`Rule 47`).
- [ ] **Reconcile `plugin.json` `"provides"` Declarations Across Target Plugins (`Rule 3`, `Rule 45`):**
  - Update `plugin.json` `"provides"` so manifest-loaded instances register their typed `ServiceKey` in `ServiceContext`:
    - `plugins/geospatial_and_osint/gods_eye_view/plugin.json` → `"provides": ["service.gods_eye_view"]`
    - `plugins/memory_and_epistemics/context_type_system/plugin.json` → `"provides": ["service.context_type_system"]`
    - `plugins/memory_and_epistemics/memory_decay_engine/plugin.json` → `"provides": ["service.memory_decay"]`
    - `plugins/memory_and_epistemics/memgraphrag/plugin.json` → `"provides": ["service.memgraphrag"]`
    - `plugins/memory_and_epistemics/graphiti_memory/plugin.json` → `"provides": ["service.graphiti_memory"]`
    - `plugins/data_engineering/wiki_compiler/plugin.json` → `"provides": ["service.wiki_compiler"]`

---

## Track 1 — `gods_eye_view` Planetary & OSINT Toolkit (24 Tools → 5 Domain Subgroups)

### Settled Architecture & Network Profile (Verified from `plugins/geospatial_and_osint/gods_eye_view/`)
All 24 entrypoints in `plugins/geospatial_and_osint/gods_eye_view/tool_groups/` partition into **5 domain subgroups** and **3 runtime network/provider tiers**:

| Subgroup | Tools (24) | Network & Provider Profile |
| :--- | :--- | :--- |
| **1. Analyst & Briefs** (`analyst_tools.py`) | `gev_analyst_query`, `gev_situation_brief` | **Hybrid (Offline-capable):** Queries local spatial index + cached/mock feeds when `enable_offline_mock_fallback: true` (`config.default.yaml:28`). |
| **2. Aviation & Maritime** (`aviation_maritime_tools.py`) | `gev_fetch_live_flights`, `gev_find_aircraft`, `gev_get_aircraft_track`, `gev_fetch_ais_vessels`, `gev_find_vessel`, `gev_get_vessel_track` | **Live HTTP Telemetry + Offline Simulation Fallback:** Fetches ADS-B / AIS feeds (`cache_ttl`: 15s flights, 30s vessels); falls back deterministically to `engine/mock_data.py` & `engine/simulation.py` when air-gapped (`HARNESS_NO_NETWORK=1`). |
| **3. Environmental & Disasters** (`environmental_tools.py`) | `gev_fetch_earthquakes`, `gev_fetch_firms_hotspots`, `gev_get_weather`, `gev_get_weather_map`, `gev_get_cyclones`, `gev_get_active_fires` | **Live HTTP Telemetry + Offline Simulation Fallback:** USGS / NASA FIRMS / Open-Meteo (`cache_ttl`: 60s earthquakes, 300s FIRMS) with deterministic offline fallback. |
| **4. Tactical, Space & Infrastructure** (`tactical_tools.py`) | `gev_query_infrastructure`, `gev_calculate_satellite_passes`, `gev_query_military_awareness`, `gev_find_cctv_cameras`, `gev_get_cctv_snapshot` | **Split:** `gev_query_infrastructure` (`builtin_infrastructure.py` + `spatial_index.py`) and `gev_calculate_satellite_passes` (SGP4 orbital math) run **100% offline in pure Python**; military/CCTV tools use live MCP/HTTP with simulation fallback. |
| **5. Geospatial & 3D Rendering** (`geo_terrain_tools.py`, `cli_bridge.py`) | `gev_render_sat_ortho`, `gev_capture_streetview_headings`, `gev_render_globe_snapshot`, `gev_get_terrain_height`, `gev_get_recent_imagery` | **External Node.js Bridge + Tile Network:** Invokes `sat-ortho.mjs`, `streetview-headings.mjs`, `cesium-render.mjs` via `NodeCliBridge` (`cli_bridge.py:28`); returns structured simulated `ImageryRenderResult` when `node` or upstream scripts are absent. |

### Deliverable Items
- [ ] **Service Adapter & Provenance Envelope (`src/harness/services/gods_eye_view.py`):**
  - Add `resolve_gods_eye_view(ctx: ServiceContext | None = None) -> GodsEyeViewService` with a `Rule 58` adapter handling `SandboxedPlugin`, in-process `GodsEyeViewPlugin`, and test mocks.
  - Ensure every response includes explicit provenance metadata: `source_mode: Literal["live", "cached", "simulated_fallback"]`, `fetched_at_utc`, `ttl_seconds`, and `fallback_reason` so callers never mistake simulated or stale snapshots for live telemetry.
- [ ] **`harness gev` CLI Group (`src/harness/commands/gev.py`, `Rule 6`, `Rule 10`, `Rule 23`):**
  - Register `("gev", gev_group)` in `src/harness/cli.py:_CANONICAL_GROUPS` and aliases `"gods-eye": "gev"`, `"osint": "gev"` in `src/harness/commands/aliases.py`.
  - Organize into domain subcommands (not a flat 24-command dump):
    - `harness gev status [--json]` — probe `node` runtime, `GEV_TOOLS_DIR`, offline fallback config, and cache TTLs.
    - `harness gev brief --lat LAT --lon LON [--radius-km R] [--query TEXT] [--json]` — run `gev_situation_brief` / `gev_analyst_query`.
    - `harness gev flights --lat LAT --lon LON [--radius-km R] [--callsign CS] [--json]` — aviation queries (`fetch_live_flights`, `find_aircraft`, `get_aircraft_track`).
    - `harness gev vessels --lat LAT --lon LON [--radius-km R] [--name NAME] [--json]` — maritime AIS queries (`fetch_ais_vessels`, `find_vessel`, `get_vessel_track`).
    - `harness gev hazards --lat LAT --lon LON [--radius-km R] [--kind all|earthquakes|fires|cyclones|weather] [--json]` — environmental & disaster feeds.
    - `harness gev spatial --lat LAT --lon LON [--radius-km R] [--kind infra|sat-passes|military|cctv] [--json]` — infrastructure, SGP4 satellite pass predictor, military awareness, and CCTV discovery.
    - `harness gev render --lat LAT --lon LON [--mode globe|ortho|streetview|terrain|imagery] [--output PATH] [--json]` — rendering and elevation tools.
- [ ] **Skill `.agents/skills/gods-eye-view/` (`SKILL.md` + `CARD.md`, `Rule 37`, `Rule 44`, `Rule 47`):**
  - Document the 5 subgroups, the 3 network/provider tiers, freshness/TTL rules (a flight or vessel position is a timestamped observation, never real-time truth; `source_mode == "simulated_fallback"` must be disclosed to the user), and `## Anti-Patterns` (treating simulated fallback as live OSINT, omitting `source_mode` / timestamp caveats, unbounded radius queries).
  - Cross-link to `../open-source-gis-architect/SKILL.md` and `../geospatial-disaster-simulation/SKILL.md` via relative links (`Rule 47`).
- [ ] **Recorded Control-Room View Decision:**
  - **Decision:** Keep 3D globe and orthomosaic outputs as file artifacts (PNG/HTML exported via `harness gev render`) rather than embedding CesiumJS into `src/harness/ui/static/`. Reason: `AGENTS.md` Negative Boundary prohibits modifying `src/harness/ui/static/` generated bundles and adding heavy third-party frontend dependencies.
- [ ] **Documentation (`docs/how-to/use-gods-eye-view.md`):**
  - Document the command tree, one worked example per subgroup, the network vs offline simulation matrix, and rate-limit/freshness rules.

---

## Track 2 — `mantis_security_review` & Security/Forensics Cluster Unification

### Settled Architecture (Verified from `plugins/security_and_forensics/mantis_security_review/`)
`MantisSecurityReviewPlugin` (`plugins/security_and_forensics/mantis_security_review/main.py`) wraps `MantisReviewEngine` (`engine/core.py`) across a 10-stage pipeline with SQLite OKF finding persistence (`init_okf_db`).

### Deliverable Items
- [ ] **Micro-Kernel Service Seam & Zero-Fork Config (`Rule 44`, `Rule 49`, `Rule 57`, `Rule 58`):**
  - Create `src/harness/services/mantis_security_review.py` re-exporting `MANTIS_SECURITY_REVIEW_KEY`, `MantisSecurityReviewService`, `MantisFinding`, `ExploitChain`, `ExploitStep`, and `resolve_mantis_security_review(ctx)` (with `Rule 58` adapter).
  - Add `plugins/security_and_forensics/mantis_security_review/config.default.yaml` defining operational budgets (`max_commits: 100`, `confidence_threshold: 0.7`, `gate_fail_on_severity: "HIGH"`, `max_exploit_chain_depth: 5`, `timeout_seconds: 60.0`).
- [ ] **`harness mantis` Stepwise CLI Group (`src/harness/commands/mantis.py`, `Rule 6`, `Rule 10`, `Rule 23`):**
  - Follow the exact CLI structure of `src/harness/commands/network_forensics.py` (`Rule 23` UTF-8 header, service resolver, `--json` flag, colored human summary).
  - Register `("mantis", mantis_group)` in `src/harness/cli.py:_CANONICAL_GROUPS` and alias `"security-review": "mantis"` in `src/harness/commands/aliases.py`.
  - Expose each stage as an independently runnable subcommand (because review gates are human/agent decision boundaries, not just batch steps) plus a composable pipeline runner:
    1. `harness mantis history-scan <repo_path> [--max-commits 100] [--pattern REGEX] [--json]`
    2. `harness mantis dir-summary <dir_path> [--no-recursive] [--json]`
    3. `harness mantis plan-review --target <path>... [--cwe CWE-79,...] [--json]`
    4. `harness mantis audit <target_file> [--cwe CWE-89] [--json]`
    5. `harness mantis dedupe <findings_json> [--json]`
    6. `harness mantis critic-filter <findings_json> [--min-confidence 0.7] [--json]`
    7. `harness mantis gate <findings_json> [--fail-on HIGH|CRITICAL] [--json]` (exits non-zero when gate fails for CI integration)
    8. `harness mantis chain-exploits <findings_json> [--json]`
    9. `harness mantis calibrate-risk <findings_json> [--exposure public|internal] [--json]`
    10. `harness mantis report <findings_json> [--output PATH] [--json]`
- [ ] **Skill `.agents/skills/mantis-security-review/` (`SKILL.md` + `CARD.md`, `Rule 37`, `Rule 44`, `Rule 47`):**
  - Cover the 10-stage Mantis workflow, what `mantis_review_gate` guarantees (threshold gating on discovered findings, *not* a formal proof of absence of vulnerabilities), and `## Anti-Patterns` (skipping `history_scan` before `plan_review`, bypassing `dedupe_ladder` + `critic_filter` before `chain_exploits`, calibrating risk without exposure context).
  - Cross-link via relative paths (`Rule 47`) to `../rea-reverse-engineering/SKILL.md`, `../differential-facet-verifier/SKILL.md`, `../reconstruction-obligation-ledger/SKILL.md`, `../ethical-hacker-networking/SKILL.md`, and `../pre-commit-security-guard/SKILL.md`.
- [ ] **Unified Security & Forensics Composition Guide (`docs/how-to/security-forensics-workflow.md`):**
  - Document how the 6 security/forensics surfaces compose into one end-to-end pipeline:
    1. **Shift-Left Gate:** `harness pre-commit-security` (`pre-commit-security-guard`)
    2. **Source & History Review:** `harness mantis` (`mantis-security-review`)
    3. **Binary & Artifact Dissection:** `harness rea` (`rea-reverse-engineering`)
    4. **Multi-Provider Differential Verification:** `harness facet` / `harness rea diff` (`differential-facet-verifier`)
    5. **Cryptographic Evidence Closure:** `harness rol` / `harness rea learn` (`reconstruction-obligation-ledger`)
    6. **Network & Packet Fault Isolation:** `harness network-forensics` (`ethical-hacker-networking`)

---

## Track 3 — Skill Knowledge Graph Completion & Cross-Graph Joint Query

### Settled Baseline (Verified from `src/harness/commands/skills/` and `src/harness/commands/reflection.py`)
`harness skills` (`src/harness/commands/skills/`) already implements 15 subcommands (`list`, `info`, `validate`, `create`, `run`, `select`, `route`, `chain`, `check-chain`, `clusters`, `capabilities`, `prereqs`, `guidance`, `intercept`, `graph`). What remains is exposing the 2 un-surfaced `skill_knowledge_graph` tools, adding `config.default.yaml`, and building the **joint query** across the Knowledge Vault graph and Skill graph.

### Deliverable Items
- [ ] **Complete `harness skills` Subcommand Coverage (`src/harness/commands/skills/graph_cmds.py`):**
  - Add `harness skills bridges [--json]` wrapping `get_cross_cluster_bridges()` (`plugins/memory_and_epistemics/skill_knowledge_graph/main.py:130`).
  - Add `harness skills index [--skills-dir .agents/skills] [--json]` wrapping `index_skill_catalog()` (`Rule 35`).
  - Add `plugins/memory_and_epistemics/skill_knowledge_graph/config.default.yaml` (`Rule 44`).
- [ ] **Joint Query Across Knowledge Graph & Skill Graph (`src/harness/services/skill_graph/` + `src/harness/commands/reflection.py`):**
  - **Design (recorded & locked):** A joint query `query_knowledge_and_skills(topic: str, *, ctx: ServiceContext | None = None, limit: int = 5)` queries:
    1. **Knowledge Vault (`SQLiteStorageService` / `.harness/knowledge/`):** matching Knowledge Items (`ki_id`, `title`, `domain`, `epistemic_state`, `tags`, `isnad`).
    2. **Skill Graph (`SkillIntelligenceService` / `BuiltinSkillRegistryService`):** matching skills (`skill_name`, `confidence`, `cluster`, `recommended_chain` obeying `Rule 35` `'skill_name'` key and `Rule 55` zero-synthetic routing).
    3. **Explicit Lineage Join (`became_skill` / `derived_from` / tag & domain overlap):** links each Knowledge Item to the skills distilled from it (via `became_skill` edges in `vault_operations.py` or `source_ki_id` / shared domain tags) and reports `unbridged_kis` (verified KIs with no procedural skill yet) and `ungrounded_skills` (skills with no backing Vault KI).
  - Expose via CLI as `harness knowledge joint-query <topic> [--limit 5] [--json]` (and alias `harness skills joint-query <topic>`), reusing `SQLiteStorageService` and `SkillIntelligenceService` with zero third graph store.
- [ ] **Unified Two-Graph Documentation (`docs/explanation/knowledge-and-skill-graphs.md`):**
  - Explain the epistemic/procedural split (`Rule 41` Dual-Lens Cognitive Distillation): the **Knowledge Graph** (`harness knowledge`, `.harness/knowledge/`) stores *what the harness knows* (claims, Isnad lineage, contradictions, lifecycle states), while the **Skill Graph** (`harness skills`, `.agents/skills/`) stores *how the harness acts* (procedural `SKILL.md` + `CARD.md`, prerequisites, chains). Include a query decision table mapping user questions to exact CLI commands.

---

## Track 4 — Learning-Core Surface (`context_type_system` + `memory_decay_engine`)

### Settled Verification Findings (Resolved from §11 Backlog)
1. **Verified Empirical Behavior of `memory_decay_engine` (`plugins/memory_and_epistemics/memory_decay_engine/decay_core.py:116-147`):**
   - Forgetting is **soft eviction (demotion from active working set), NOT deletion**:
     - `step_turn()` increments `current_turn` and evaluates $R(t) = \exp(-\Delta t / (S / m_{\text{channel}}))$ for each non-evicted item.
     - Items with `is_foundational=True` are **exempt from eviction** (`decay_core.py:136`).
     - Channel multipliers (`DEFAULT_CHANNEL_MULTIPLIERS`, `decay_core.py:11-17`) scale decay speed: `instruction` ($0.25\times$), `foundational` ($0.35\times$), `evidence` ($0.70\times$), `memory` ($1.0\times$), `tool_output` ($1.75\times$).
     - When $R(t) < \text{eviction\_threshold}$ (default `0.20`), `item.evicted` is set to `True`. The item **remains stored in `engine.items`** (and is preserved in `export_memory_session` snapshots and inspectable via `memory_query_working_set(include_evicted=True)`), but is excluded from `working_set()`, `query_ranked_working_set()`, and `recall()`.
     - Recalling an active item reinforces stability non-linearly: $S_{\text{new}} = S_{\text{old}} \cdot (1 + \ln(1 + n_{\text{realls}}))$ (`decay_core.py:123-128`).
2. **Verified Channel Alignment Between `context_type_system` and `memory_decay_engine`:**
   - Both plugins use the exact same 4 core semantic channels (`instruction`, `memory`, `evidence`, `tool_output` in `plugins/memory_and_epistemics/context_type_system/engine.py` and `decay_core.py:11-17`)!

### Deliverable Items
- [ ] **Extend `harness context` CLI with Provenance & Decay Subcommands (`src/harness/commands/context.py`, `Rule 6`):**
  - Rather than creating two extra top-level CLI groups that fragment the context/memory story, add two subcommand namespaces (or direct subcommands) under the existing `harness context` group (`src/harness/commands/context.py`) AND provide a dedicated `harness memory` group (`src/harness/commands/memory.py`) for working-memory decay & federation:
    - Under `harness context` (`context_type_system` — 8 tools):
      - `harness context add --session SESSION --type instruction|memory|evidence|tool_output --content TEXT [--source SRC] [--priority N] [--json]`
      - `harness context transform --session SESSION --id REQ_ID --to-type TYPE [--source SRC] [--json]`
      - `harness context validate-tool --session SESSION --tool-name NAME --output-json JSON [--json]`
      - `harness context assemble --session SESSION [--budget-tokens 4000] [--json]`
      - `harness context ledger --session SESSION [--id REQ_ID] [--json]` (combines `context_inspect_ledger` and `context_get_lineage`)
      - `harness context snapshot --session SESSION [--export PATH | --import PATH] [--json]`
    - Under `harness memory` (`memory_decay_engine` — 8 tools, aliased as `memory-decay` / `ebbinghaus` in `CLI_ALIASES`):
      - `harness memory register --key KEY --content TEXT [--session SESSION] [--channel memory|instruction|evidence|tool_output|foundational] [--stability 5.0] [--foundational] [--json]`
      - `harness memory recall <key> [--session SESSION] [--json]`
      - `harness memory step [--turns 1] [--session SESSION] [--json]`
      - `harness memory working-set [--session SESSION] [--include-evicted] [--ranked] [--limit N] [--json]`
      - `harness memory benchmark [--turns 30] [--items 25] [--seed 42] [--json]` (runs `simulate_session_benchmark` comparing Ebbinghaus vs FIFO/LRU)
      - `harness memory snapshot [--session SESSION] [--export PATH | --import PATH] [--json]`
- [ ] **Skill `.agents/skills/context-type-system/` (`SKILL.md` + `CARD.md`, `Rule 37`, `Rule 44`, `Rule 47`):**
  - Author the companion skill for `context_type_system` (note: `.agents/skills/ebbinghaus-memory-governor/` **already exists** for `memory_decay_engine` — update its `SKILL.md` to cross-link `../context-type-system/SKILL.md` and document the verified `item.evicted = True` soft-demotion semantics).
  - Add `plugins/memory_and_epistemics/context_type_system/config.default.yaml` (`Rule 44`).
- [ ] **End-to-End Learning-Core Lifecycle Narrative (`docs/explanation/learning-core-lifecycle.md`):**
  - Document the 4-stage endogenous loop with a Mermaid `flowchart LR` diagram and CLI sequence:
    1. **Channel Provenance & Trust Gate (`context_type_system`):** Raw `tool_output` is isolated from `instruction` and promoted to `evidence` only via `context_validate_tool_output` with an immutable origin ledger.
    2. **Working-Memory Retention & Decay (`memory_decay_engine`):** Channel-weighted Ebbinghaus decay ($R(t) = e^{-\Delta t / (S/m)}$) ranks active items and soft-evicts stale `tool_output` ($1.75\times$ decay) while protecting `instruction` ($0.25\times$) and `is_foundational=True` items.
    3. **Epistemic Vault Persistence (`SQLiteStorageService` / `harness knowledge`):** High-stability evidence promotes into dual-file Knowledge Vault items (`.harness/knowledge/<ki_id>/metadata.json` + `summary.md`, `Rule 40`) with Isnad chains.
    4. **Lifecycle Governance (`harness knowledge lifecycle`):** Tracks the 8-state epistemic promotion/deprecation lifecycle (`epistemic-memory-lifecycle`).

---

## Track 5 — Architectural Consolidations (Decisions Settled via Live Code Inspection)

### 1. Memory Cluster Decision: `okf_memory` vs `memgraphrag` vs `graphiti_memory`
- [x] **Decision (Verified Against Live Implementations — Keep Partitioned Behind a Query Router):**
  Live code inspection proves these three plugins are **not duplicate implementations of the same store**; they operate on three orthogonal data models and time horizons:
  1. **`okf_memory` (`src/harness/services/okf_memory.py`, `harness okf`, `.agents/skills/okf-memory-governor/`):** **Git-native normative file bundle (OKF v0.2)** — manages human-reviewed Markdown concept files (`knowledge/`) with path-based pre-edit governance scoping (`okf scope <file_path>`), BM25 lexical search, and actor trust ordering.
  2. **`memgraphrag` (`src/harness/services/memgraphrag.py`, `plugins/memory_and_epistemics/memgraphrag/`):** **Unstructured passage GraphRAG & conflict detector** — extracts entity-relation triples from raw text passages (`memgraphrag_add_passage`, `memgraphrag_index`) and detects factual contradictions across retrieved subgraphs (`memgraphrag_detect_conflicts`).
  3. **`graphiti_memory` (`src/harness/services/graphiti_memory.py`, `plugins/memory_and_epistemics/graphiti_memory/`):** **Bi-temporal episodic interaction graph** — ingests timestamped conversational episodes (`graphiti_add_episode`), performs tri-brid search (vector + BM25 + BFS reranking), and invalidates superseded temporal facts (`graphiti_invalidate_fact`) without deleting historical episodes.
- [ ] **Action Items for Memory Cluster:**
  - Add `config.default.yaml` to `okf_memory`, `memgraphrag`, and `graphiti_memory` (`Rule 44`).
  - Add `harness memory status [--json]` and `harness memory route <question> [--json]` inside `src/harness/commands/memory.py` that routes a developer/agent memory question to the authoritative store:
    - *"What rules/concepts govern editing `src/harness/kernel/`?"* → `okf_memory` (`harness okf scope`)
    - *"What changed over time in user/session episodes, and which facts were superseded?"* → `graphiti_memory`
    - *"Index these raw passages and check for entity-relation conflicts"* → `memgraphrag`
    - *"Which working-memory items are still active vs soft-evicted this turn?"* → `memory_decay_engine`
    - *"What verified Knowledge Items and Isnad chains exist in the vault?"* → `SQLiteStorageService` (`harness knowledge`)
  - Record the 5-store memory partition table in `docs/explanation/memory-architecture.md`.

### 2. DAG Trio Decision: `AgentExecutionGraphService` vs `SwarmDAG` vs `AgentSessionManager`
- [x] **Decision (Verified Against `src/harness/services/agent_graph.py`, `src/harness/agent/swarm/models.py`, and `src/harness/commands/session.py` — Intentional 3-Phase Lifecycle Layering):**
  Live code inspection (`Rule 17`, `Rule 36`) confirms the three models represent **three distinct phases of multi-agent execution**, already linked by composite key `f"{run_id}_{node_id}"` (`Rule 36`):
  1. **Compile-Time Plan (`SwarmDAG` in `src/harness/agent/swarm/models.py:92`):** Slotted/frozen static work plan that validates DAG acyclicity via `DependencyGraph`, computes topological execution waves (`get_execution_waves()`), and budgets tokens (`allocated_tokens`).
  2. **In-Flight Runtime Topology (`AgentExecutionGraphService` in `src/harness/services/agent_graph.py:130`, `AGENT_GRAPH_STORE_KEY`):** Live directional thread-spawn state machine (`ThreadSpawnStatus.OPEN` → `COMPLETED` / `FAILED` / `CLOSED`) with recursive parent-child token rollups (`Rule 17`).
  3. **Persistent Trajectory Store & CLI Exporter (`AgentSessionManager` in `src/harness/agent/session.py` + `src/harness/commands/session.py`):** Durable SQLite session records (`task`, `final_answer`, `error_message` per `Rule 36`) and headless CLI introspection (`harness session list|get|tree|export`, `Rule 10`).
- [ ] **Action Items for DAG Trio:**
  - Add a deterministic bridge helper `register_swarm_dag_in_graph(dag: SwarmDAG, graph_svc: AgentExecutionGraphService, run_id: str, root_thread_id: str = "root") -> list[str]` in `src/harness/agent/swarm/models.py` so any static `SwarmDAG` projects its nodes and dependency edges into `AgentExecutionGraphService` using canonical `f"{run_id}_{node.id}"` keys (`Rule 36`) without manual boilerplate.
  - Document the 3-phase DAG architecture (Plan → Live Spawn Graph → Persistent Session Tree) in `docs/explanation/agent-execution-graphs.md`.

---

## Track 6 — External Bundle (`mattpocock-skills`): Trust Review & Counting Rule

### Settled Trust Review & Counting Audit (Verified from `plugins/external/Pocock-skills-main/`)
- [x] **Code-Verified Trust Review of `mattpocock-skills` (`plugins/external/Pocock-skills-main/`):**
  - **Manifest (`plugin.json`):** Declares `name: "mattpocock-skills"`, `isolation: "subprocess"`, `trusted: false`, `sandbox_Tier: "restricted-venv"`, and 35 tool entrypoints (`ask_matt`, `code_review`, `codebase_design`, `crafting_skills`, `deepen_architecture`, `diagnosing_bugs`, `domain_modeling`, `git_guardrails_claude_code`, `grill_me`, `grill_with_docs`, `grilling`, `handoff`, `improve_codebase_architecture`, `migrate_to_shoehorn`, `obsidian_vault`, `prototype`, `pr_Creation`, `refactor_plan`, `research`, `resolve_conflicts_with_git_mergetool`, `resolving_merge_conflicts`, `scaffold_exercises`, `setup_matt_pocock_skills`, `setup_pre_commit`, `tdd`, `teach`, `to_questionnaire`, `to_spec`, `to_tickets`, `triage`, `verify_feature`, `wait_what`, `wayfinder`, `wizard`, `writing_for_agents`).
  - **Runtime Behavior (`skills_entrypoint.py:1-38`):** Every entrypoint dispatches via module `__getattr__` to `_get_skill(skill_name, task, context)`, which performs **pure read-only `Path.glob("skills/**/SKILL.md")` lookups inside `plugins/external/Pocock-skills-main/`** and returns a static JSON dictionary `{"status": "ok", "skill": clean_name, "instructions": <markdown>, "task": task, "context": context}`.
  - **Security Verdict:** Safe under existing `isolation: "subprocess"`, `trusted: false`, and `Rule 7` lazy staging. `skills_entrypoint.py` imports only `pathlib.Path` and `typing.Any` — it executes **zero subprocesses, zero network calls, and zero filesystem writes**. (Note: individual upstream `SKILL.md` files contain prose instructions for interactive human/Claude workflows like `gh` CLI issue creation or `git` hooks; returning their Markdown text is passive, and any subsequent tool execution by the agent remains governed by the harness's own `ToolRegistry` and `CodexExecPolicyService`).
- [x] **Canonical Counting Rule (Settled & Locked):**
  1. **Canonical Harness Plugins (134):** Count only `plugins/<category>/<name>/plugin.json` at depth 3 where `category != "external"`.
  2. **External Skill Bundles (1 bundle / 35 entrypoints):** Count `plugins/external/<bundle>/plugin.json` separately as *"1 external skill bundle (35 skill-prompt entrypoints)"*.
  3. **Excluded Nested Metadata (2 files):** Explicitly exclude any path containing `.claude-plugin` (`".claude-plugin" not in path.parts`) from all plugin scanners, validators, and test counters.
  4. **Workspace Agent Skills (96):** Count `.agents/skills/*/SKILL.md` directories.
- [x] **`ask-matt` Routing Decision (Settled):**
  - Keep `mattpocock-skills` as an **opt-in external reference bundle (`isolation: "subprocess"`, `trusted: false`)**, NOT merged into `BuiltinSkillRegistryService` (`harness skills route`).
  - **Reason:** 12 of the 35 Pocock skills (`crafting-skills`, `deepen-architecture`, `codebase-design`, `tdd`, `diagnosing-bugs`, `domain-modeling`, etc.) already have Harness-native, `Rule 37`/`Rule 44`-compliant counterparts or global IDE skills, and the remaining Pocock flows (`grill-me`, `to-tickets`, `wayfinder`) are interactive human-interview prompts (`disable-model-invocation: true`) rather than autonomous slotted domain engines (`Rule 49`).
- [ ] **Deliverable Items for Track 6:**
  - Update `plugins/external/README.md` with the recorded trust review, the `skills_entrypoint.py` read-only mechanics, and the `ask_matt` opt-in invocation example (`harness tool info plugin.mattpocock-skills.ask_matt`).
  - Update any plugin-manifest scanner helper in `src/harness/plugins/loader.py` / test helpers to ignore `.claude-plugin` directories so `rglob("plugin.json")` never trips over nested upstream metadata.

---

## Track 7 — Second-Tier Plugins (Code-Verified Surveys & Targeted Actions)

All four second-tier plugins (plus `evaluator_critic`) have been surveyed against live code (`plugins/` and `src/harness/services/`):

### 1. `filesystem_git` (`plugins/software_engineering/filesystem_git/`, 7 tools) — **Survey Outcome: Leave As-Is & Document Dual Seam**
- [x] **Code-Verified Finding (§11 Resolved):**
  - `FilesystemGitPlugin` (`plugins/software_engineering/filesystem_git/main.py`) **is the authoritative implementation** of `FILESYSTEM_GIT_KEY` (`src/harness/services/filesystem_git.py`) used by the ReAct kernel's transactional checkpointing (`Rule 8`)!
  - It is intentionally split into two seams on the same class:
    1. **Agent-facing `ToolRegistry` entrypoints (7 tools in `plugin.json`):** `fs_read_file`, `fs_write_file`, `fs_list_dir`, `fs_search_text`, `git_status`, `git_diff`, `git_log`.
    2. **Kernel-only transaction methods (on `FilesystemGitService`, omitted from `plugin.json`):** `commit_transaction()` and `rollback_transaction()`, invoked automatically by `async with context.transaction()` (`Rule 8`) so an LLM cannot manually spoof or roll back transaction boundaries.
- [ ] **Action:** Record this dual-seam architecture in `plugins/software_engineering/filesystem_git/README.md`; **do not** add a redundant `harness fs-git` CLI group (humans already have native `git` and `harness dock`).

### 2. `critic_loop` (7 tools) vs `evaluator_critic` (3 tools) vs `mantis_critic_filter` — **Survey Outcome: Already Consolidated at Engine Seam; Document & Leave CLI As-Is**
- [x] **Code-Verified Finding (§11 Resolved):**
  - `plugins/agent_orchestration/evaluator_critic/main.py:1-30` is **already a 90-line thin backward-compatibility adapter** that imports `CRITIC_EVALUATION_SERVICE_KEY` and `_EVAL_INSTANCE` directly from `plugins.agent_orchestration.critic_loop.main`! Its 3 tools (`critic_check_safety`, `critic_evaluate_code`, `critic_review_plan`) are exact aliases of `critic_loop`'s first 3 tools.
  - `mantis_critic_filter` (`plugins/security_and_forensics/mantis_security_review/engine/`) is a specialized security-finding deduplication/false-positive filter inside the Mantis 10-stage pipeline (surfaced in Track 2 under `harness mantis critic-filter`).
- [ ] **Action:** Update `plugins/agent_orchestration/evaluator_critic/README.md` and `critic_loop/README.md` to document that `critic_loop` is the primary plugin providing `CRITIC_EVALUATION_SERVICE_KEY` + `CRITIC_LOOP_KEY` while `evaluator_critic` is retained strictly as a legacy compatibility adapter. No separate `harness critic` top-level CLI group is needed (`harness eval` and `harness gate` already cover evaluation and gating).

### 3. `paperless_ngx` (`plugins/data_engineering/paperless_ngx/`, 7 tools) — **Survey Outcome: Service & Skill Exist; Leave CLI As-Is**
- [x] **Code-Verified Finding:**
  - Already has `src/harness/services/paperless_ngx.py` (`PAPERLESS_NGX_SERVICE_KEY`), `config.default.yaml`, and a complete skill at `.agents/skills/paperless-document-pipeline/` (`SKILL.md` + `CARD.md`).
  - Because `paperless_ngx` is an external REST client bridge requiring a running Paperless-NGX server (`PAPERLESS_URL` + `PAPERLESS_TOKEN`), it has no standalone offline local repo consumer warranting a top-level `harness paperless` CLI group.
- [ ] **Action:** Verify `plugins/data_engineering/paperless_ngx/README.md` links to `../../.agents/skills/paperless-document-pipeline/SKILL.md` (`Rule 47`) and mark complete.

### 4. `wiki_compiler` (`plugins/data_engineering/wiki_compiler/`, 8 tools) — **Survey Outcome: Surface Under `harness doc` + Add `config.default.yaml`**
- [x] **Code-Verified Finding:**
  - `plugins/data_engineering/wiki_compiler/compiler_core.py` is a self-contained, pure-Python compiler that transforms a directory of raw `.md`/`.txt` notes into a cross-referenced Markdown wiki with entity extraction, backlinks, and link/orphan linting (`compile_wiki`, `compile_pages_incremental`, `WikiGraphQuery`, `lint`).
  - Real consumer: compiling `.harness/knowledge/` summaries or raw project notes into a browsable Markdown wiki and linting cross-references (`harness doc`).
- [ ] **Action:**
  - Add `plugins/data_engineering/wiki_compiler/config.default.yaml` (`Rule 44`) and `"provides": ["service.wiki_compiler"]` in `plugin.json`.
  - Add `harness doc wiki-compile <raw_dir> <output_dir> [--incremental] [--no-lint] [--json]` and `harness doc wiki-lint <wiki_dir> [--json]` inside `src/harness/commands/doc.py` (reusing the existing `harness doc` group rather than adding a new top-level CLI group).

---

## Track 8 — Docs Index, Stale Count Remediation, and Automated Drift Gates

- [ ] **Integrated Toolkits Master Index (`docs/reference/integrated-toolkits.md`):**
  - One authoritative reference table listing every integrated toolkit (`rea`, `dock`, `gev`, `mantis`, `network-forensics`, `skills` + `knowledge` joint graph, `context` + `memory` learning core, `okf`, `doc wiki-*`), its `ServiceKey`, its `harness <group>` CLI commands, its `.agents/skills/<name>/` skill link, and its isolation mode.
- [ ] **CLI Reference Update (`docs/reference/cli.md`):**
  - Document `harness gev`, `harness mantis`, `harness memory`, the new `harness context` provenance subcommands, `harness skills bridges|index`, `harness knowledge joint-query`, and `harness doc wiki-compile|wiki-lint`.
- [ ] **Remediate Stale Counts in `README.md` and `USER_MANUAL.md`:**
  - Update `README.md` and `USER_MANUAL.md` using the locked Track 6 counting rule:
    - **134 canonical Harness plugins** + **1 external skill bundle (`mattpocock-skills`, 35 entrypoints)** (**625 total tool entrypoints**),
    - **96 workspace skills** in `.agents/skills/` (+ 3 created in this plan → **98 workspace skills** once `gods-eye-view`, `mantis-security-review`, and `context-type-system` land),
    - **45 canonical CLI command groups** (once `gev`, `mantis`, and `memory` are registered in `src/harness/cli.py:_CANONICAL_GROUPS`).
- [ ] **Automated Plugin Integration Drift Gate (`tests/test_plugin_integration_drift.py`):**
  - Assert that:
    1. Every CLI group and subcommand documented in `docs/reference/integrated-toolkits.md` and `docs/reference/cli.md` exists in `src/harness/cli.py:main`.
    2. All target plugins in this plan have non-empty `"provides"` in `plugin.json` matching their `ServiceKey` and a valid co-located `config.default.yaml` (`Rule 44`).
    3. Every new skill (`gods-eye-view`, `mantis-security-review`, `context-type-system`) passes `SkillValidator.validate()` (`report.valid is True` per `Rule 34`, `Rule 37`, `Rule 44`).
    4. All markdown links across new skills and docs use portable relative paths and pass static link linting (`Rule 47`).
    5. Naive `plugin.json` discovery excludes `.claude-plugin` directories, locking the canonical count separation.

---

## Suggested Execution Order (The Pick Queue)

1. **Track 0 (Manifest & Config Baseline):** Add missing `"provides"` to the 6 `plugin.json` files and `config.default.yaml` to the 7 plugins missing them (`Rules 3, 44, 45`).
2. **Track 1 (`gods_eye_view` — `harness gev` + skill + docs):** Surface the largest un-integrated 24-tool plugin with 5 domain subcommands, explicit `source_mode` provenance (`live` vs `cached` vs `simulated_fallback`), and `.agents/skills/gods-eye-view/`.
3. **Track 2 (`mantis_security_review` — `harness mantis` + skill + workflow doc):** Elevate `MANTIS_SECURITY_REVIEW_KEY` to `src/harness/services/mantis_security_review.py`, build the 10-stage `harness mantis` CLI, scaffold `.agents/skills/mantis-security-review/`, and author `docs/how-to/security-forensics-workflow.md`.
4. **Track 3 (Skill + Knowledge Graph Unification):** Add `harness skills bridges|index`, implement `harness knowledge joint-query <topic>` joining Vault KIs and Skills via `became_skill` lineage, and author `docs/explanation/knowledge-and-skill-graphs.md`.
5. **Track 4 (Learning Core — `context_type_system` & `memory_decay_engine`):** Add provenance subcommands to `harness context`, create `harness memory` for Ebbinghaus working-set & benchmark commands, scaffold `.agents/skills/context-type-system/`, and author `docs/explanation/learning-core-lifecycle.md`.
6. **Track 5 (Consolidation Seams — Memory Router & `SwarmDAG` Bridge):** Add `harness memory status|route`, `register_swarm_dag_in_graph()`, and the two architecture explanation docs (`memory-architecture.md` and `agent-execution-graphs.md`).
7. **Track 6 & Track 7 (External Bundle Guard + `harness doc wiki-compile|wiki-lint`):** Exclude `.claude-plugin` in manifest scanners, document the `mattpocock-skills` trust review & `filesystem_git`/`critic_loop` seams, and add `wiki-compile`/`wiki-lint` to `harness doc`.
8. **Track 8 (Master Index, README Counts, and Drift Gate):** Author `docs/reference/integrated-toolkits.md`, update `README.md` / `docs/reference/cli.md`, and lock everything with `tests/test_plugin_integration_drift.py`.

---

## §11 Verification Ledger (Resolved via Live Code Inspection 2026-10-31)

- [x] **Verified (Code Read 2026-10-31): `differential_facet_verifier`'s actual three-valued behavior and REA Track 5 status.**
  - `src/harness/services/differential_facet.py` implements `FacetAvailability(available, reason)` (`L70-L80`), `CoverageDeclaration.absence_claimable` (`L86-L107`), `DimensionOutcome` (`L109-L139`, 3-valued `unchanged` / `changed` / `unknown`), and `DifferentialReport` (`rep:<sha256>`). `REA toolkit plan-2026-10-31-0849-EDT.md` and `src/harness/commands/rea.py` (`harness rea diff`, `harness rea learn`) already integrate `DifferentialFacetService` and `ReconstructionObligationService`.
- [x] **Verified (Code Read 2026-10-31): `memory_decay_engine`'s forgetting semantics (demote vs archive vs delete).**
  - `plugins/memory_and_epistemics/memory_decay_engine/decay_core.py:131-147` (`EbbinghausMemoryEngine.step_turn`) performs **soft eviction (demotion), NOT deletion**: when retention falls below `eviction_threshold` (`0.20`), `item.evicted` is set to `True` (items with `is_foundational=True` never evict). Evicted items remain in `engine.items`, are preserved in session exports, and can be inspected via `memory_query_working_set(include_evicted=True)`, while being excluded from `working_set()` and `recall()`.
- [x] **Verified (Code Read 2026-10-31): `gods_eye_view`'s per-tool network vs offline profile.**
  - Across the 24 tools in `plugins/geospatial_and_osint/gods_eye_view/tool_groups/`: 4 tools (`gev_query_infrastructure`, `gev_calculate_satellite_passes`, `gev_analyst_query`, `gev_situation_brief`) run offline against local Python spatial/orbital engines; 15 telemetry tools (`flights`, `vessels`, `earthquakes`, `firms`, `weather`, `cyclones`, `fires`, `military`, `cctv`) fetch live HTTP/MCP feeds and automatically fall back to deterministic simulation (`engine/mock_data.py`, `engine/simulation.py`) when offline; 5 rendering tools (`sat_ortho`, `streetview_headings`, `globe_snapshot`, `terrain_height`, `recent_imagery`) invoke Node.js scripts via `NodeCliBridge` (`cli_bridge.py:28`) with simulated fallback when `node` or tile network is unavailable.
- [x] **Verified (Code Read 2026-10-31): Does `filesystem_git` duplicate or complement the harness's git transaction machinery?**
  - They are the **exact same service class**: `FilesystemGitPlugin` (`plugins/software_engineering/filesystem_git/main.py`) provides `FILESYSTEM_GIT_KEY` (`src/harness/services/filesystem_git.py`). Its 7 `plugin.json` entrypoints are the agent-facing read/write/git-query tools, while `commit_transaction()` and `rollback_transaction()` are kernel-only methods on the same service used by `async with context.transaction()` (`Rule 8`).
- [x] **Verified (Code Read 2026-10-31): Critic overlap (`critic_loop` vs `evaluator_critic` vs `mantis_critic_filter`).**
  - `plugins/agent_orchestration/evaluator_critic/main.py:26-48` is already a thin backward-compatibility wrapper delegating directly to `critic_loop._EVAL_INSTANCE` (`CRITIC_EVALUATION_SERVICE_KEY`). `mantis_critic_filter` is a domain-specific SAST/security-finding false-positive filter inside the 10-stage `mantis_security_review` pipeline.
- [x] **Verified (Code Read 2026-10-31): `mattpocock-skills` runtime behavior under subprocess isolation.**
  - `plugins/external/Pocock-skills-main/skills_entrypoint.py:9-38` is a 38-line pure-Python file reader that globs `skills/**/SKILL.md` inside its own bundle directory and returns the Markdown text in a dict. It executes zero shell commands, zero network requests, and zero file writes.
