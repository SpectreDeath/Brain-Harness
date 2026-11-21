# Graph-driven domain harness spawning plan — 2026-11-21 EST

Use Brain Harness's live skill knowledge graph (`19` clusters, `55` cross-cluster bridges) and Knowledge Vault (`382` KIs) to design, document, and spawn a prioritized set of lean, high-value domain harnesses — each backed by an explicit documentation contract and ICM workspace layout so no spawned harness is a nebulous collection of files.

## Verified starting state (BH `f337079`, 2026-11-21)

What exists and is verified live:

- **Spawning & plugin seam:** `HarnessSpawnerEngine` + `HarnessSpawnerPlugin` (`plugins/agent_orchestration/harness_spawner/`) + `harness spawn` CLI (`run`, `review`, `list`, `retire`, `propose`, `adopt`, `reject`, `check-drift`), all routed through `get_spawner_service` (`5718fa6`). All six spawn defaults (`Q2–Q7`) are confirmed (`f337079`, `"keep all six as-is"`).
- **Skill knowledge graph & vault discovery:**
  - `harness skills clusters` discovers `19` functional skill clusters with central hubs, cohesion percentages, and emergent capabilities (ranging from tight `2–5` skill clusters at `17–50%` cohesion up to `8–23` skill mixed hubs at `10–12%` cohesion).
  - `harness skills bridges --json` discovers `55` cross-cluster macro edges.
  - `harness skills joint-query <TOPIC> --json` queries both the Skill Graph and `.harness/knowledge/` (`382` KIs), returning `knowledge_items` (with `isnad_status`), `skills`, `linked_pairs`, `unbridged_kis`, and `ungrounded_skills`.
- **ICM workspace architecture:** `icm-workspace-architect` skill and `harness icm` CLI (`scaffold`, `audit`, `links`, `quotes`, `index`) in `src/harness/commands/icm.py` and `src/harness/services/icm_architect/`.
- **Doc tooling:** `harness doc` (`audit`, `drift`, `scaffold`, `wiki-compile`, `wiki-lint`) and `dock.yaml` materialization (`src/harness/services/harness_spawner/materialize.py`).

Verified gaps to close as part of this plan:

1. **`IcmScaffolder.scaffold_form()` (`src/harness/services/icm_architect/scaffolder.py:56-116`) only scaffolds `pipeline` and `record_library`.** The other 3 canonical ICM forms (`knowledge_bundle`, `context_map`, `system_map`) do not yet generate their form-specific `CONTEXT.md` and directories.
2. **Materialized harnesses currently lack a documentation bundle.** `materialize_spawn_as_dock()` (`materialize.py:76`) writes only the `BRAIN_SURFACE` tree (`AGENTS.md`, `.agents/skills/*/SKILL.md`, scripts), `dock.yaml`, and `.harness/spawn_tree_digest.json`. There is no required `README.md`, `CONTEXT.md`, `docs/USE_CASES.md`, `docs/PROVENANCE.md`, `docs/RUNBOOK.md`, or companion `CARD.md` verification.
3. **No graph-to-blueprint ranking seam.** Selecting which clusters/bridges make the highest-value harnesses and assembling their skill + KI + ICM-form blueprints is currently manual.
4. **No worktree/branch materialization mode.** Today `--materialize <dir>` writes a standalone dock-linked directory; optional `git worktree` branch mode (`harness/<name>`) is not wired yet.

## Evidence rule

Tick a box only with a commit + a passing test, a dated command output, or a written decision recorded verbatim from the user in chat. Never record a user pick that did not happen in visible conversation. Never tick the independent-check box (`5.2`) yourself.

## Scope limits

- No new third-party dependencies without the user's explicit approval.
- Do not change the confirmed spawn defaults (`Q2–Q7` in `Harness spawning research-2026-11-13-EST.md`) or weaken the merge-back policy (zero silent auto-adoption; never raw-`git merge` a trimmed domain branch back into `main`).
- Do not delete or move `.agents/skills/` directories on `main` (`tests/test_plugin_integration_drift.py` asserts live skill and plugin counts on `main`).
- Do not touch any unticked box in any other plan (`Spawn provenance 3.3`, `Spawn capability completion 5.2`, `Spawn completion follow-up 3.1`, etc.) and do not re-open any ticked box.

---

## Mandatory Documentation Inclusion Specification (Every Spawned Harness)

Every durable domain harness spawned under this plan **must** include the following 7-part documentation and contract bundle so it is immediately intelligible to both humans and cold agents:

| # | Path | Audience | Purpose & Required Sections | Verification Gate |
|---|---|---|---|---|
| 1 | `README.md` | Human | **Identity & Quick Start:** Domain mission, concrete use cases, explicit **"Out of Scope / Do NOT Use For"** boundary, lineage header (`Prime` commit SHA, cluster/bridge ID, spawn ID, date), quick-start CLI commands, skill inventory table, and seeded KI table. | Non-empty, required headings present, zero broken relative links (`harness icm links .`). |
| 2 | `AGENTS.md` (+ `CLAUDE.md` / `GEMINI.md` pointers) | Agent (L0) | **Small Routing Entry (`< 60` lines / `<= 500` tokens):** 2-line identity, routing table to `README.md`, `CONTEXT.md`, `docs/`, `_shared/`, and `.agents/skills/*/SKILL.md`, domain invariants, and explicit merge-back rule (stage via `propose`, never auto-adopt). | `SurfaceSpec` `validate()` + `harness icm audit .` (`AGENTS.md < 60` lines). |
| 3 | `CONTEXT.md` + stage/shelf `CONTEXT.md` | Agent (L1/L2) | **Operational Contracts:** ICM form map (`pipeline` / `record_library` / `knowledge_bundle` / `context_map` / `system_map`), numbered stages or shelf schema, exact backticked `Inputs`, explicit `Do NOT load:` deflections, `Outputs`, and `Check` (`check.md` gate). | `harness icm audit .` (`< 8,000` tokens/step) + `harness icm links .`. |
| 4 | `docs/USE_CASES.md` | Human + Agent | **Worked Scenarios:** 2–3 concrete end-to-end walkthroughs (trigger/input -> stage or command sequence -> expected artifact -> pass/fail check criterion) demonstrating real usage. | Required sections present; relative links resolve. |
| 5 | `docs/PROVENANCE.md` | Auditor | **Graph & Knowledge Lineage:** Exact `skills clusters` / `skills bridges` / `skills joint-query` inputs used to choose this harness, skill-count and estimated token savings vs Prime (`114` skills -> `3–5` skills), and table of every seeded KI with its `isnad_status` (`VERIFIED` required for ground-truth claims; `UNVERIFIED` excluded or explicitly flagged). | Deterministic JSON/Markdown check; zero `UNVERIFIED` KIs promoted as verified. |
| 6 | `docs/RUNBOOK.md` | Operator | **Lifecycle & Merge-Back Guide:** Commands to inspect (`dock inspect`), validate (`dock run <name> validate`), check drift (`spawn check-drift`), re-materialize when Prime updates, propose learnings (`spawn propose`), and adopt/reject (`spawn adopt` / `reject`). Includes explicit warning against raw `git merge` into `main` if branch/worktree-backed. | Commands match live CLI (`docs/reference/cli.md` parity). |
| 7 | `.agents/skills/<skill>/SKILL.md` + `CARD.md` + `dock.yaml` | Agent + Runtime | **Executable Surface & Manifest:** Only the `3–5` selected skills (plus `icm-workspace-architect`), each retaining its companion `CARD.md` (Rule 37) and passing Rule 44 description bounds (`100–350` chars with negative boundary); `dock.yaml` declares permissions (`write: false`, `push: false` by default), boundaries, `tools`, `validate`, and `audit-docs` entrypoints. | `SurfaceSpec.validate()` + `SkillCardRule` + `dock run <name> validate` (`DOCK_HARNESS_OK`). |

---

## Prioritized Harness Portfolio (Derived from Live Graph Data)

Selection rubric for ranking candidates from `harness skills clusters` (`19` clusters) + `harness skills bridges` (`55` bridges) + `harness skills joint-query`:
1. **Repeatability & Frequency:** Solves a recurring engineering or research workflow run weekly.
2. **Token Savings:** Replaces `114` Prime workspace skills (`~10,226` est. tokens) with `3–5` domain skills (`~350–600` est. tokens — **~94–96% workspace skill reduction**).
3. **Graph Cohesion & Grounding:** Draws from a tight cluster (`>= 17%` cohesion) or high-value bridge, backed by `VERIFIED` KIs in `.harness/knowledge/`.
4. **Clear ICM Form Fit:** Maps cleanly to a deterministic ICM form with disk-verifiable `check.md` or `_index.md` outputs.

### Tier 1 — Highest Value (Spawn First, Wave 1)

| Priority | Harness Name | Graph Source (Live) | Included Skills (`4–5`) | ICM Form | Core Use Cases |
|---:|---|---|---|---|---|
| **1** | `harness-repo-distiller` | Bridge `cluster_12_brain_artifact_miner` (`50%` cohesion) -> `cluster_06_mind_reader` + `cluster_04_external_repo_bridge_forge` | `icm-workspace-architect`, `repo-triad-forge`, `epistemic-isnad-audit`, `brain-artifact-miner`, `conversation-trajectory-miner` | `knowledge_bundle` + `pipeline` | 1) Ingest an external GitHub repo in isolation and stage dual-file KIs with verbatim quote checks (`harness icm quotes`). 2) Mine session transcripts/artifacts into reusable skills without bloating Prime. |
| **2** | `harness-security-forensics` | `mantis-security-review` cluster (`5` skills, `20%` cohesion) + bridge to `plugin-seam-and-mirror-auditor` + `ki_20260908_mantis_01` | `icm-workspace-architect`, `mantis-security-review`, `rea-reverse-engineering`, `differential-facet-verifier`, `ethical-hacker-networking` | `record_library` + `pipeline` | 1) Commit-history security triage and finding deduplication tracked as frontmatter records (`findings/_index.md`). 2) Binary/bundle reverse-engineering and multi-provider claim verification with auditable evidence dossiers. |
| **3** | `harness-arch-modernizer` | `architecture-deepening-workflow` cluster (`3` skills, `17%` cohesion) + bridges to `data-topology-mapper` & `codebase-context-governor` | `icm-workspace-architect`, `architecture-deepening-workflow`, `monolith-decomposition-engine`, `data-topology-mapper`, `legacy-modernization-pipeline` | `system_map` + `pipeline` | 1) Map DAG seams and blast radius before touching legacy modules. 2) Decompose monolithic files to `<= 200` lines behind characterization test safety nets with `< 8,000` token stage contracts. |
| **4** | `harness-context-economizer` | `headroom-context-optimizer` cluster (`2` skills, `50%` cohesion) + bridges to `agent-harness-architect` & `codebase-context-governor` | `icm-workspace-architect`, `headroom-context-optimizer`, `token-economizer`, `codebase-context-governor`, `repo-doc-synchronizer` | `context_map` + `pipeline` | 1) Audit `AGENTS.md`, skills, and docs for Rule 11/44/47 bloat and link drift. 2) Profile and trim prompt/catalog token waste across repos before spawning or shipping changes. |

### Tier 2 — Specialized On-Demand Harnesses (Wave 2, Spawn When Needed)

| Priority | Harness Name | Graph Source (Live) | Included Skills (`3–5`) | ICM Form | Core Use Cases |
|---:|---|---|---|---|---|
| **5** | `harness-knowledge-graph` | `knowledge-graph-pipeline` cluster (`3` skills, `50%` cohesion) + bridge to `ebbinghaus-memory-governor` | `icm-workspace-architect`, `knowledge-graph-pipeline`, `neo4j-knowledge-graph-architect`, `sql-recursive-graph-traversal`, `ontological-engineering-coach` | `knowledge_bundle` + `pipeline` | Ingest tabular/domain corpora into Neo4j or recursive SQL CTE hierarchies with ontological/Gruber audits. |
| **6** | `harness-skill-factory` | `deep-skill-forge` subset + `skill-eval-assurance-runner` | `icm-workspace-architect`, `crafting-skills`, `agent-skill-sdlc`, `skill-eval-assurance-runner` | `pipeline` + `record_library` | Design, scaffold (`SKILL.md` + `CARD.md`), and statistically evaluate (`pass^k` / Wilson CI) new skills before admission to Prime (`runs/_index.md`). |
| **7** | `harness-data-lakehouse` | `bigquery-augmented-analytics` cluster (`4` skills, `25%` cohesion) | `icm-workspace-architect`, `bigquery-augmented-analytics`, `data-management-architect`, `garf-reporting-architect`, `paperless-document-pipeline` | `pipeline` + `record_library` | Govern ODCS/Medallion data contracts, SQL reporting DAGs, and hybrid document-pipeline queries. |
| **8** | `harness-cloud-k8s` | `cloud-infrastructure-architect` cluster (`2` skills, `10%` cohesion) | `icm-workspace-architect`, `cloud-infrastructure-architect`, `kubernetes-drift-guardian` | `record_library` + `pipeline` | Audit K8s manifest/RBAC drift, container sandboxing policies, and Prometheus exposition. |

---

## Track 0 — User Decision Gate (Confirm Before Building)

- [x] **0.1 Confirm storage layout for durable spawned harnesses.** Choose one:
  - **(a) Standalone dock-linked directories** under a dedicated root (e.g. `D:\GitHub\harnesses\<name>\` via `--materialize`, zero git branch management on `Brain Harness`), or
  - **(b) Git worktree branches** off `Brain Harness` (`harness/<name>` in e.g. `D:\GitHub\harnesses\<name>\` via `git worktree add`, sharing `src/` and `.venv` with trimmed `.agents/skills/` and scoped merge-back only).
  **Recorded user choice (2026-11-21):** `"0.1 Storage layout: (a) standalone dock-linked directories"`
- [x] **0.2 Confirm Wave 1 scope.** Confirm which Tier 1 harnesses to spawn first (all 4 in Tier 1, a subset of 1–2 as a tracer bullet first, or swaps from Tier 2).
  **Recorded user choice (2026-11-21):** `"0.2 tracer bullet -- repo distiller first, then security-forensics"`
- [x] **0.3 Confirm documentation strictness.** Confirm the 7-part Documentation Inclusion Specification above (specifically whether `docs/USE_CASES.md`, `docs/PROVENANCE.md`, and `docs/RUNBOOK.md` should be included in the canonical drift digest alongside `AGENTS.md` + skills, so editing docs without re-approving flags drift in `harness spawn check-drift`).
  **Recorded user choice (2026-11-21):** `".3 yes, include all three docs in the check drift digest"`

## Track 1 — Close ICM Scaffolder & Graph-Selection Gaps

- [x] **1.1 Complete the 3 missing ICM scaffold forms.** (`49b2d0a`, 2026-11-21) Extended `IcmScaffolder.scaffold_form()` (`src/harness/services/icm_architect/scaffolder.py`) to scaffold `knowledge_bundle` (`sources/raw/.gitkeep`, `_meta/keep-out.txt`, `concepts/_index.md`, `_templates/concept-template.md`, `CONTEXT.md`), `context_map` (`teams/_index.md`, `teams/core-domain.md`, `CONTEXT.md` with `consumes:` / `produces:`), and `system_map` (`objects/_index.md`, `processes/_index.md`, `_templates/object-template.md`, `CONTEXT.md`), and added `.agents`/`.harness` to `SKIP_DIRS` in `auditor.py`. All 5 `IcmFormType` skeletons pass `IcmAuditor` (10/10 invariants), `IcmVerifier().verify_links()`, and `verify_quotes()` via `@pytest.mark.unit` tests in `tests/test_icm_workspace_architect.py`.
- [x] **1.2 Build a deterministic graph-to-blueprint recommender.** (`49b2d0a`, 2026-11-21) Added `src/harness/services/harness_spawner/_blueprint_catalog.py` & `blueprints.py` (`HarnessBlueprint`, `SeededKI`, `recommend_harness_blueprints`, `build_blueprint_tree`), reading service-layer `get_default_skill_registry` (`cluster_skills` & `get_cross_cluster_bridges`, layer-boundary clean) and `query_knowledge_and_skills`; forwarded through `DefaultHarnessSpawnerService` & `HarnessSpawnerPlugin`; added `harness spawn blueprints` and `--blueprint` on `review`/`run` in `src/harness/commands/spawn.py`; documented in `docs/reference/cli.md`.
- [x] **1.3 Unit tests for blueprint scoring & KI grounding filter.** (`49b2d0a`, 2026-11-21) Added `@pytest.mark.unit` tests in `tests/test_harness_spawner_blueprints.py` verifying deterministic ranking, `UNVERIFIED`/`UNKNOWN` KI exclusion into `excluded_unverified_kis`, Rule 43 frozen immutability, skill-count cap `<= 6`, `BRAIN_SURFACE` validation, and `harness spawn blueprints --json` / `review --blueprint` parity.

## Track 2 — Documentation Bundle & Materialization Contract

- [x] **2.1 Implement the 7-part Documentation Bundle generator & validator.** (`49b2d0a`, 2026-11-21) Added `src/harness/services/harness_spawner/_doc_templates.py` & `doc_bundle.py` (`build_harness_docs`, `compute_docs_sha256`, `validate_harness_docs`, `HarnessDocContext`, `TRACKED_DOC_PATHS`, standalone `_tools/audit_docs.py`) emitting `README.md`, `<60`-line `AGENTS.md` + pointers, ICM `CONTEXT.md`, `docs/USE_CASES.md`, `docs/PROVENANCE.md`, `docs/RUNBOOK.md`, and companion `CARD.md` files for all bundled skills.
- [x] **2.2 Wire documentation generation & `audit-docs` entrypoint into `materialize_spawn_as_dock`.** (`49b2d0a`, 2026-11-21) Per decision `0.1(a)` (standalone dock-linked directories; no `--worktree` implemented), extended `materialize_spawn_as_dock()` & `build_spawn_dock_yaml()` (`src/harness/services/harness_spawner/materialize.py`) and `HarnessSpawnerPlugin` forwarding to emit the 7-part docs bundle, add portable `audit-docs` (`DOCS_AUDIT_OK`) alongside `validate` (`DOCK_HARNESS_OK`), use `DefaultDockService()` so CLI materializations register in Prime's `.harness/docks.json`, and track `docs_sha256` across the 5 canonical docs in `.harness/spawn_tree_digest.json` & `check_materialized_drift()` per decision `0.3`.
- [x] **2.3 Contract & portability tests.** (`49b2d0a`, 2026-11-21) Added `@pytest.mark.unit` tests in `tests/test_harness_spawner_doc_bundle.py` verifying (a) `validate_harness_docs()` fails when any required doc artifact or `CARD.md` is deleted; (b) `dock run <name> validate` and `dock run <name> audit-docs` pass with bare `python` stripped from `PATH`; (c) `IcmAuditor` (10/10) and `IcmVerifier` (0 broken links) pass cleanly; (d) tampering `README.md`, `CONTEXT.md`, `docs/USE_CASES.md`, `docs/PROVENANCE.md`, or `docs/RUNBOOK.md` triggers `check-drift` exit 1 (`docs_drifted: true`) and restoring returns exit 0.

## Track 3 — Spawn Wave 1 Harnesses (End-to-End Real Runs)

- [x] **3.1 Run graph blueprint discovery and save dated selection report.** (2026-11-21) Ran `harness spawn blueprints --json` live against `Brain Harness` (`19` clusters, `55` bridges, `382` KIs, `114` skills):
  - `harness-repo-distiller`: score `59.0610`, form `knowledge_bundle`, `cluster_12_brain_artifact_miner` (`cohesion=0.50`, `bridges=7`), `5/114` skills (`95.61%` skill-count reduction), `6` `VERIFIED` KIs, `0` excluded.
  - `harness-security-forensics`: score `45.5610`, form `record_library`, `cluster_09_mantis_security_review` (`cohesion=0.20`, `bridges=4`), `5/114` skills (`95.61%` skill-count reduction), `6` `VERIFIED` KIs, `0` excluded.
- [x] **3.2 Review and spawn each selected Wave 1 harness.** (2026-11-21) Spawned both tracer-bullet harnesses in user-chosen order into standalone dock-linked directories (`--save-dir D:\GitHub\harnesses\.spawns`):
  1. `harness-repo-distiller` (`spawn_harness-repo-distiller_ba7f71b5` -> `D:\GitHub\harnesses\harness-repo-distiller`): reviewed digest `fc0353cfca8c5005ee02879d8274a45eeea0f5488d5914f82da0b187243dd264`; `docs_sha256=ff6f679549a758e7b89489098d9af59685d32f4876299166fab279247a145711`; `dock run validate` -> `DOCK_HARNESS_OK`; `dock run audit-docs` -> `DOCS_AUDIT_OK`; `icm audit` -> `10/10` (`knowledge_bundle`); `icm links` -> `45/45` (`0` broken); `check-drift` -> `drifted: false`; tamper `docs/RUNBOOK.md` -> exit `1` (`docs_drifted: true`) -> restore -> exit `0`; `5` skills (`~372` est. catalog tokens vs Prime's `114` skills / `~8,392` est. catalog tokens).
  2. `harness-security-forensics` (`spawn_harness-security-forensics_6af6d2c7` -> `D:\GitHub\harnesses\harness-security-forensics`): reviewed digest `ad69a698a924b7dc729a55525e6301e3a54328cf6aebaa7bd0035cfba90f3603`; `docs_sha256=c232eda6d3f9846dd9e4f75bb6b597d00bc77ecb2b3e28f3f1e7752702e06afa`; `dock run validate` -> `DOCK_HARNESS_OK`; `dock run audit-docs` -> `DOCS_AUDIT_OK`; `icm audit` -> `10/10` (`record_library`); `icm links` -> `45/45` (`0` broken); `check-drift` -> `drifted: false`; tamper `docs/RUNBOOK.md` -> exit `1` (`docs_drifted: true`) -> restore -> exit `0`; `5` skills (`~432` est. catalog tokens vs Prime's `114` skills / `~8,392` est. catalog tokens).
  3. `harness-arch-modernizer` (follow-up Wave 1 expansion, `spawn_harness-arch-modernizer_8ce8b20e` -> `D:\GitHub\harnesses\harness-arch-modernizer`): reviewed digest `19c78f42140739fa58f281abdd809421b7973334d72278c57cfdec437cc764b2`; `dock run validate` -> `DOCK_HARNESS_OK`; `dock run audit-docs` -> `DOCS_AUDIT_OK`; `icm audit` -> `10/10` (`system_map`); `icm links` -> `47/47` (`0` broken); `check-drift` -> `drifted: false`; tamper `docs/RUNBOOK.md` -> exit `1` (`docs_drifted: true`) -> restore -> exit `0`; `5` skills (`~366` est. catalog tokens vs Prime's `114` skills / `~8,392` est. catalog tokens).
  4. `harness-context-economizer` (follow-up Wave 1 expansion, `spawn_harness-context-economizer_2ab8fab4` -> `D:\GitHub\harnesses\harness-context-economizer`): reviewed digest `88b61b6a0564615537ccda3c3e2308f8d753d1fa84af0da9225fdb5d91c11339`; `docs_sha256=ce32136226496a6ac4d8d96cf7be1a4b1b1912f43db6cfaabaefc4fccfa8e15f`; `dock run validate` -> `DOCK_HARNESS_OK`; `dock run audit-docs` -> `DOCS_AUDIT_OK`; `icm audit` -> `10/10` (`context_map`); `icm links` -> `50/50` (`0` broken); `check-drift` -> `drifted: false`; tamper `docs/RUNBOOK.md` -> exit `1` (`docs_drifted: true`) -> restore -> exit `0`; `5` skills (`~371` est. catalog tokens vs Prime's `114` skills / `~8,392` est. catalog tokens).

## Track 4 — Cold-Agent Walk Test & Use-Case Proof

- [x] **4.1 Run the 8-Point ICM Cold Walk Test on every spawned Wave 1 harness.** (2026-11-21) Verified all `9/9` automated cold-walk invariants across all 4 Tier-1 harnesses (`AGENTS.md` = `22` lines / `~330–347` est. tok; `CONTEXT.md` = `~188–209` est. tok `< 8,000`; `<= 2` reads cover mission, out-of-scope, inputs, outputs, and checks; `IcmAuditor` 10/10; `IcmVerifier` `0` broken links; `validate_harness_docs()` clean; `94.85%–95.64%` frontmatter token reduction vs Prime; `check-drift` clean).
- [x] **4.2 Execute one real use case per spawned Wave 1 harness and exercise reviewed merge-back.** (2026-11-21)
  - `harness-repo-distiller`: inspected `D:\GitHub\cloned\andrej-karpathy-skills` (`9` files, `Medium` tier) via `RepoTriadForgeServiceImpl`, wrote raw excerpt `sources/raw/karpathy_claude.txt` + `concepts/karpathy-behavioral-rules.md`, indexed `concepts/_index.md` (`1` note), `harness icm quotes` passed `2/2` verified (`0` broken), staged 2 proposals via `spawn propose` -> adopted `ki-distill-karpathy-minimalism` (`prop_distill-karpathy-1_214b16a9`) into isolated sandbox parent store & rejected negative control (`prop_distill-karpathy-2_a9f2e525`); `check-drift` remained `drifted: false`.
  - `harness-security-forensics`: ran `harness mantis audit src/harness/services/dock/safety.py --json` (`0` AST findings), recorded `records/finding-001.md`, rebuilt `records/_index.md` (`1` note) via `harness icm index`, verified `icm audit` & `icm links`, staged 2 proposals -> adopted `ki-sec-dock-safety-baseline` into isolated sandbox parent store & rejected negative control (`prop_mantis-safety-audit-2_34321887`); `check-drift` remained `drifted: false`.
  - `harness-arch-modernizer`: inventoried all `10` modules under `src/harness/services/harness_spawner/`, wrote `objects/spawner-blueprints.md` + `processes/spawn-materialize-flow.md`, indexed `objects` & `processes` (`2` notes), verified `icm audit` & `icm links`, staged 2 proposals -> adopted `ki-arch-service-layer-graph-seam` into isolated sandbox parent store & rejected negative control (`prop_arch-map-spawner-2_d0e36648`); `check-drift` remained `drifted: false`.
  - `harness-context-economizer`: ran `harness context lint` (`[PASS]`) + measured `AGENTS.md`/catalog budgets, wrote `teams/spawner-context-boundary.md`, indexed `teams/_index.md` (`2` notes), verified `icm audit` & `icm links`, staged 2 proposals -> adopted `ki-econ-trimmed-domain-catalog` into isolated sandbox parent store & rejected negative control (`prop_econ-audit-2_e8cb41d2`); `check-drift` remained `drifted: false`.

## Track 5 — Verification

- [x] **5.1 Re-run all gates with dated outputs.** (`49b2d0a`, 2026-11-21 EST, Windows 11 local `.venv` timings):
  - Combined targeted + layer boundary + drift suites (`tests/test_layer_import_boundaries.py`, `test_icm_workspace_architect.py`, `test_harness_spawner_blueprints.py`, `test_harness_spawner_doc_bundle.py`, `test_harness_spawner_materialize.py`, `test_harness_spawner_e2e.py`, `test_harness_spawner_plugin_forwarding.py`, `test_plugin_integration_drift.py`, `test_cli_content_drift.py`): **`57 passed` in `48.41s`**
  - Full unit gate (`pytest -m "unit" -q --timeout=60`): **`2348 passed`, `885 deselected`, `2 warnings` in `301.63s` (`0:05:01`)** (restored `.harness/config.json` mutated by pre-existing test)
  - `ruff check .`: **All checks passed!**
  - CI-scoped `ruff format --check`: **`77 files already formatted`**
  - Touched-file `ruff format --check` (`17` files): **`17 files already formatted`**
  - `mypy src/harness/kernel --ignore-missing-imports`: **Success: no issues found in 27 source files**
  - `mypy` (without `--ignore-missing-imports`) on 10 new/modified service/plugin/command modules: **Success: no issues found in 10 source files**
  - `harness context lint`: **`[PASS]` Context files healthy across 3 checks**
  - `harness knowledge sync --strict`: **`382 Knowledge Item(s)` synced cleanly**
  - `uv lock --check`: **Resolved 98 packages in 1ms (exit 0)**
- [ ] **5.2 Independent check.** Left unticked until a genuinely separate check lands. The executor must not tick it.
