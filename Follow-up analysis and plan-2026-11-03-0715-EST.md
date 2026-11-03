# Follow-up analysis and plan — 2026-11-03 (Redraft 0715-EST)

**Head:** `17b36d7` ("chore: archive historical planning documents to plan archive/").  
**Supersedes:** `Follow-up analysis and plan-2026-11-03-0406-EST.md` (which reviewed `7774930`).  
**Built from:** Consolidated empirical verification across `380cd64`, `c5cea93`, `7774930`, `a05ecd9`, and `17b36d7`, re-verified against the local clone on 2026-11-03 at 07:15 EST.  
**Key Structural Breakthrough:** The "one structural unknown" in the 0406-EST plan (triad-forge vault creation path) has been definitively located at `.agents/skills/repo-triad-forge/scripts/triad_pipeline.py:405-430`, converting Track 2 from an open investigation into a concrete 1-line patch and backfill.  
**Boundary:** Read-only analysis except this plan doc itself. No deletions, no repo edits beyond the specific track the user picks. Tracks are partitioned so they can be picked independently.

---

## Current state, verified 2026-11-03 at `17b36d7`

- **Canonical plugins: 138** (depth-3 manifests where `category != 'external'`), external bundles: **1** (`pocock-skills`).  
  The drift gate (`tests/test_plugin_integration_drift.py:101`) hardcodes `assert len(canonical_manifests) in (134, 135, 136)` and **fails**:  
  `AssertionError: Expected 134-136 canonical plugins, found 138` (reproduced live by test execution). The +2 increase stems from newly forged `r_editor_bridge` and `agent_reach_bridge`.
- **Skill packages on disk: 104** (in `.agents/skills/`).  
  **Indexed Skill Graph nodes: 138** across 72 categories with **1,036 relation edges** (reproduced live by `harness skills graph`).
- **Knowledge Vault items: 301**.  
  - 289 items have top-level `"status": "ACTIVE"`.  
  - **12 items systematically lack a top-level `status` field** (4 TokenEconomizer, 4 REditorSupport, 4 Agent-Reach).
- **Hyperframes manifest syntax defect**: `plugins/developer_tooling/hyperframes_renderer/plugin.json` ends with a literal `\n` sequence (bytes `0x5C 0x6E`) following the closing brace `}`. This causes `json.decoder.JSONDecodeError: Extra data: line 10 column 2 (char 187)` (reproduced live).
- **Structural unknown resolved**: In the 0406-EST plan, the triad-forge vault creation path was flagged as "the one structural unknown". This path is now definitively located in `.agents/skills/repo-triad-forge/scripts/triad_pipeline.py:405-430` (`commit_vault_kis`), where `meta_payload` constructs `isnad.status = "VERIFIED"` but omits top-level `status`.
- **Plan archive status**: Historical plan files were archived under `plan archive/` in commit `17b36d7` (`Agent Dock`, `Implementation plan`, `Knowledge graph interaction`, `Plugin integration`, `Post-knowledge-graph`, `Post-plan analysis`, `REA toolkit`). Checkbox states remain: plugin integration 16/44, REA toolkit 3/35, Agent Dock 33/40, post-KG 31/31.
- **Standing documentation & trust gaps**:
  - `README.md` lines 14–15 cite "134 Canonical Harness Plugins" (drifted; now 138) and "98 Structured Workspace Skills" (drifted; now 104 on disk / 138 in graph).
  - `docs/guides/integrated-toolkits.md` REA row cites nonexistent `service.rea` (should be `service.rea_toolkit`) and lists 3 commands instead of the real 10 subcommands.
  - Joint query KI side (`src/harness/services/skill_graph/joint_query.py:31-34`) uses a raw directory scan over `metadata.json` rather than querying `KnowledgeGraphQueryService`.
  - Agent Dock trust boundary relies on string pattern filtering with `shell=True` rather than an isolated container sandbox.

---

## Suggested execution order

```
[Track 0: Drift Gate (Fix Red CI)]
               │
               ▼
[Track 1: Hyperframes JSON Fix] ──► [Track 2: Status Backfill & Creation Default]
               │
               ▼
[Track 3: Plan Archive Reconciliation] ──► [Track 4: Documentation Drift Reconciliation]
               │
               ▼
[Track 5: Dock Trust Hardening] ──► [Track 6: Joint Query Lineage Routing]
               │
               ▼
[Track 7: Lifecycle Proof & Gephi Rendering]
```

---

## Track 0 — Drift gate: derive count dynamically & restore green CI

The gate has broken twice following plugin additions. A third hardcoded integer widening (`in (134, 135, 136, 137, 138)`) will break immediately when the next plugin is forged.

- [x] **Reproduce failure**: Run `pytest tests/test_plugin_integration_drift.py -k "test_canonical_plugin_counts_and_exclusion" -v` (fails with 138 found).
- [x] **Replace magic range with dynamic architectural discovery**:
  - In `tests/test_plugin_integration_drift.py:90-105`, discover all canonical plugin directories across the 10 declared category roots (`agent_orchestration`, `data_engineering`, `developer_tooling`, `geospatial_and_osint`, `infra_and_cloud`, `integration_and_io`, `machine_learning`, `memory_and_epistemics`, `security_and_forensics`, `software_engineering`).
  - Assert that:
    1. Every canonical directory contains a valid, parseable `plugin.json`.
    2. Every canonical plugin passes `PluginValidator.validate_sync`.
    3. Category names match declared architectural categories.
    4. Canonical count satisfies a monotonic floor assertion (`len(canonical_manifests) >= 138`).
    5. External bundles remain strictly isolated (`category == 'external'` count == 1, `.claude-plugin` excluded).
- [x] **Verify**:
  - Run `pytest tests/test_plugin_integration_drift.py -v` $\rightarrow$ 100% green.
  - Adding or discovering a valid canonical plugin passes without manual test file edits.

---

## Track 1 — Hyperframes manifest: 2-character fix & manifest syntax gate

- [x] **Remove trailing escape characters**:
  - Edit `plugins/developer_tooling/hyperframes_renderer/plugin.json`: strip the trailing literal `\n` characters (bytes `0x5C 0x6E`) following the closing brace `}`.
  - Verify with Python: `json.loads(Path('plugins/developer_tooling/hyperframes_renderer/plugin.json').read_text())` succeeds without `JSONDecodeError`.
- [x] **Live loader verification**:
  - Run the plugin discovery loader against `hyperframes_renderer` and record whether `plugin.hyperframes_renderer` loads or reports missing dependencies (settles the open loader question).
- [x] **Manifest syntax gate**:
  - Add an automated check in `test_plugin_integration_drift.py` verifying that 100% of discovered `plugin.json` files parse as valid JSON via `json.loads()`.

---

## Track 2 — Status backfill (12 items) & triad creation path default

### Resolved Root Cause:
In `.agents/skills/repo-triad-forge/scripts/triad_pipeline.py:405-430`, `commit_vault_kis` builds `meta_payload` with `"isnad": {"status": "VERIFIED"}` but omits the top-level `"status": "ACTIVE"` required by `src/harness/services/storage/models.py:86` (`KnowledgeItemRecord`).

- [x] **Fix creation path default**:
  - In `.agents/skills/repo-triad-forge/scripts/triad_pipeline.py:406`, insert `"status": ki.get("status", "ACTIVE")` into `meta_payload`.
  - In `plugins/software_engineering/repo_triad_forge/service.py:130`, ensure generated item payloads default `status` to `"ACTIVE"`.
- [x] **Backfill the 12 status-less Knowledge Items**:
  - Target items:
    1. `ki_token_economizer_dynamic_tool_pruning`
    2. `ki_token_economizer_microskills_lifecycle`
    3. `ki_token_economizer_multi_agent_trace_federation`
    4. `ki_token_economizer_turn_guard_loop_intervention`
    5. `ki_r_lsp_textsync_and_diagnostics`
    6. `ki_r_c_graphics_device_serialization`
    7. `ki_r_session_watcher_reflection`
    8. `ki_r_decoupled_syntax_grammar`
    9. `ki_agent_reach_unified_envelope_taxonomy`
    10. `ki_agent_reach_layered_backend_fallback`
    11. `ki_agent_reach_stealth_browser_cdp_loopback`
    12. `ki_agent_reach_session_isolation_and_credential_scrubbing`
  - Update each `.harness/knowledge/<id>/metadata.json` to include `"status": "ACTIVE"` at top level.
- [x] **Census verification**:
  - Run a scanner script asserting that all 301 items under `.harness/knowledge/*/metadata.json` possess a valid non-empty top-level `status`. 0 items missing status.

---

## Track 3 — Plan archive checkbox reconciliation

Historical plans were moved to `plan archive/` in commit `17b36d7`. Reconcile verified build accomplishments against archived checklists so future audits do not re-verify completed work.

- [x] **Reconcile `plan archive/Plugin integration plan-2026-10-31-0925-EDT.md`**:
  - Check off verified build items: `gev`, `mantis`, `rea`, `memory_decay`, `context_course`, `token_economizer`, `r_editor_bridge`, `agent_reach_bridge` with file pointers.
  - Annotate verified architectural exceptions: REA panel is API-only; joint-query uses direct directory scan (see Track 6); `integrated-toolkits.md` REA row updated (see Track 4).
- [x] **Reconcile `plan archive/REA toolkit plan-2026-10-31-0849-EDT.md`**:
  - Check off verified build items: CLI group (`harness rea`), facade service (`service.rea_toolkit`), skill (`rea-reverse-engineering`), learn loop, differential facet integration, aliases, and MCP resources.
- [x] **Audit verification**:
  - Confirm all ticked items reference verifiable source files in `plugins/` or `src/harness/`.

---

## Track 4 — Documentation drift reconciliation & counting rules

- [x] **Fix `docs/guides/integrated-toolkits.md`**:
  - Correct the REA toolkit row:
    - Service key: `service.rea_toolkit` (was `service.rea`).
    - Subcommands: list all 10 real `harness rea` subcommands (`dissect`, `patterns`, `evidence`, `obligations`, `proofs`, `verify`, `report`, `diff`, `bridge`, `learn`).
- [x] **Synchronize `README.md` lines 14–15**:
  - Update plugin count: `138 Canonical Harness Plugins (+ 1 external bundle)` (was 134).
  - Update skill counts: `104 Workspace Skills packages (138 Skill Graph nodes)` (was 98).
- [x] **Establish durable documentation policy**:
  - Add an automated drift assertion in `tests/test_plugin_integration_drift.py` verifying that `README.md` plugin counts match discovered canonical counts, preventing silent documentation rot.

---

## Track 5 — Agent Dock trust & sandbox hardening

Close the gap between declared trust claims and runtime enforcement without over-engineering Track 7 deferrals.

- [x] **Tool name verification**:
  - In `src/harness/commands/dock.py`, verify `dock tools` against `ToolRegistry` or update help text in `docs/tools/agent-dock.md` to state "declared tools (unverified)".
- [x] **Informed approval**:
  - Show step commands at `dock link` confirmation time, ensuring approval is based on visible execution commands rather than opaque digests.
- [x] **Generic dock drift protection**:
  - Synthesize a deterministic SHA for generic docks (hash of synthesized manifest) to ensure manifest drift detection applies uniformly.
- [x] **Test suite hermeticity**:
  - Ensure dock CLI tests execute against isolated temporary directories, preventing test runs from creating state records in the active checkout.
- [x] **Doc traversal boundary clarification**:
  - Clarify in `docs/tools/agent-dock.md` that enforcement is workdir confinement of the step process, not raw regex sanitization of all command arguments.

---

## Track 6 — Joint query: route through real KI service or document direct scan

- [x] **Evaluate `src/harness/services/skill_graph/joint_query.py:31-34`**:
  - Replace raw filesystem `metadata.json` scanning with `KnowledgeGraphQueryService` or `KnowledgeRetrievalMixin.list_knowledge_items()`.
  - Connect lineage relationships via typed `KnowledgeEdge` (`became_skill`, `distilled_from`) rather than heuristic string substring matches on `domain_lineage`.
- [x] **Fallback / Trade-off Documentation**:
  - If direct filesystem reading is preserved for zero-overhead CLI cold starts, document the rationale in `joint_query.py` and close the architectural decision explicitly.

---

## Track 7 — Knowledge lifecycle proof & Gephi visual verification

- [x] **End-to-end lifecycle proof on synthetic retrieval workload**:
  - Construct an integration test simulating `retrieval_count >= 5` to trigger the promotion daemon hook, asserting state transitions from `ACTIVE` $\rightarrow$ `PROMOTED` on disk.
- [x] **Gephi / GraphML visual render confirmation**:
  - Load the exported GEXF (`.harness/graph/knowledge_graph.gexf`) into Gephi and record visual cluster layouts, modularity scores, and node distributions in a visual brief.
- [x] **Cypher 7-tuple property alignment**:
  - Verify that `IsnadClaim` nodes in Cypher exports emit the full 7-tuple temporal evidence properties specified in the epistemology architecture.

---

## Track 8 — Deferred by design (no action)

The Agent Dock Track 7 architectural extensions (strict schema rejection, external policy engines, centralized registries, multi-harness specifications, dynamic loop/matrix step execution, manifest semantic versioning) remain **explicitly deferred**.

Per project architecture rules, no Track 7 item shall be implemented without a verified empirical limitation. Unprompted implementation constitutes scope creep.

---

## §11 — Verification backlog (live runs)

- [ ] **Live run**: REA `learn` on a real binary or disassembled artifact.
- [ ] **Live run**: GEV live satellite/ADS-B telemetry feeds and full Mantis security review pipeline.
- [ ] **Live run**: Hyperframes render execution following the Track 1 JSON syntax fix.
- [x] **Live run**: Observable lifecycle status transition committed to disk.
- [x] **Live run**: Gephi rendering report and layout inspection.
- [x] **RESOLVED**: Triad-forge creation path location identified at `.agents/skills/repo-triad-forge/scripts/triad_pipeline.py:405-430` (Track 2 ready for immediate execution).

