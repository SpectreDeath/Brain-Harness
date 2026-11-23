# Wave 4 Domain Harness Spawning Plan — Harness Development & Repo/Literature/Media Ingestion (2026-11-23 EST)

## Purpose

Design and materialize **Wave 4** of specialized, ICM-compliant domain harnesses under `D:\GitHub\harnesses\`, purpose-built so the developer can open a **lightweight spawned harness as their active IDE project** (~`314–341` workspace skill tokens + ~`278–350` rule tokens instead of Prime's `114`-skill frontmatter overhead) whenever working on:
1. **Ingesting foreign GitHub repositories** and forging/validating sandboxed `HarnessPlugin` packages (`harness-repo-plugin-forge`),
2. **Ingesting books, papers, technical articles, and video/multimedia transcripts** into deep-module skills (`SKILL.md` + `CARD.md`) and isnad-verified Knowledge Vault items (`harness-literature-media-forge`),
3. **Developing and verifying Brain Harness kernel, IoC service seams, slotted domain models, and shift-left pre-commit security gates** (`harness-kernel-plugin-dev`), and
4. **Improving and evolving Brain Harness itself** via 5-part harness architecture diagnostics, 4-gate behavioral pipelines, HarnessCompass evolutionary loops, and endogenous reflection (`harness-self-evolution`), plus two optional Wave 4b introspection/runtime harnesses (`harness-mind-artifact-miner` and `harness-runtime-governor`).

---

## Starting State (Verified Live on `2026-11-23`)

- **Part A Root Context Slimming Completed Locally (`2026-11-23`):**
  - [AGENTS.md](AGENTS.md) was compacted from `109` lines / `27,646` bytes (`6,873` tokens) to `33` lines / `3,394` bytes (`847` tokens — an **87.7% reduction** in always-on rule overhead), with the full 59-rule catalog preserved on demand in [docs/reference/agent-invariants.md](docs/reference/agent-invariants.md) and synchronized to [.github/copilot-instructions.md](.github/copilot-instructions.md) (`871` tokens) and [CLAUDE.md](CLAUDE.md) (`95` tokens).
  - Why Wave 4 is still essential when opening projects in the IDE: Antigravity IDE automatically loads the YAML frontmatter (`name` + `description`) of every `.agents/skills/*/SKILL.md` in the open workspace (`114` workspace skills = `33,662` chars / ~`8,416` tokens, plus global plugin skills). Opening a Wave 4 development harness under `D:\GitHub\harnesses\<name>\` loads only **`5` workspace skills** (~`1,256–1,364` total L0+L1 chars / ~`314–341` tokens — a **95.9%–96.3% reduction** in workspace skill frontmatter cost) while retaining full CLI/Python access to Prime's engine (`d:\GitHub\projects\Brain Harness`).
- **Existing Materialized Portfolio (`15` Harnesses across Waves 1–3 in `D:\GitHub\harnesses\.spawns\registry.json`):**
  - **Wave 1 (`4`):** `harness-repo-distiller` (`pipeline`), `harness-security-forensics` (`pipeline`), `harness-arch-modernizer` (`system_map`), `harness-context-economizer` (`context_map`)
  - **Wave 2 (`4`):** `harness-reverse-engineering` (`pipeline`), `harness-ontology-spider` (`system_map`), `harness-knowledge-graph` (`knowledge_bundle`), `harness-memory-graph` (`context_map`)
  - **Wave 3 (`7`):** `harness-data-lakehouse` (`pipeline`), `harness-agent-reliability` (`pipeline`), `harness-swarm-orchestrator` (`context_map`), `harness-docs-architect` (`system_map`), `harness-cloud-k8s` (`record_library`), `harness-geospatial-gis` (`system_map`), `harness-skill-factory` (`pipeline`)
- **Live Skill Graph & Knowledge Vault Topology:**
  - `.\.venv\Scripts\harness.exe skill-graph cluster --min-size 2 --json` -> **`19` functional clusters**, **`55` cross-cluster bridges**, **`22` emergent capabilities**, **`382` Knowledge Vault items** (`.harness/knowledge/`).
  - Of Prime's `114` workspace skills, **`56` unique skills** (`49.1%`) are bundled across Waves 1–3 (`15` materialized harnesses + `1` reserve spec `harness-ux-streaming`).
  - Crucially, the core **Harness Development & Repo/Book/Media Ingestion** skills (`external-repo-bridge-forge`, `repo-to-plugin-forge`, `deep-repo-auditor`, `repo-reader`, `book-to-skill-forge`, `deep-skill-forge`, `multimedia-intelligence-forge`, `media-to-vault-pipeline`, `plugin-seam-and-mirror-auditor`, `adversarial-agent-verifier`, `python-dataclass-architect`, `pre-commit-security-guard`, `agent-harness-architect`, `ai-native-harness-engineer`, `harness-compass`, `harness-reflector`, `mind-reader`, `temp-artifact-miner`, `questio-reflection`, `pi-coding-harness`, `shim-harness-governor`, `elephant-goldfish-governor`, `context-engineering-architect`) are **not yet materialized** in dedicated development harnesses.
- **Empirical `BRAIN_SURFACE` & `EvidenceLeakError` Pre-Verification (`2026-11-23`):**
  - Every one of the **6 Wave 4 candidates** (`4` Core + `2` Optional Wave 4b) was tested against `build_blueprint_tree()`, `guards.assert_tree_clean(tree)`, `surface_ops.validate(BRAIN_SURFACE, tree)`, and `_collect_kis()` against the live `.harness/knowledge/` vault:
    - **`0` `EvidenceLeakError` tripwire markers** across all 6 candidates.
    - **`6` verified `SeededKI`s (`isnad_status == "VERIFIED"`) and `0` unverified KIs** per candidate.
    - **`always_on_chars` between `1,256` and `1,364`** (well below the `2,000`-char `BRAIN_SURFACE` ceiling), **`n_files` between `12` and `15`** (`<= 25`), and **`skills == 5`** (`<= 6`).
    - **`0` direct `plugins.*` imports** in any bundled `.agents/skills/*/scripts/*.py` file across all 6 candidates.

---

## Evidence Rule

A checkbox `[x]` may be ticked **only** when the command or test output, file path, `spawn_id`, and `tree_sha256` digest are cited inline under that step. Any step requiring human sign-off (`3.1` qualitative cold-walk points `#1, #5, #8`) or an independent session (`4.2 Independent check`) **must remain `[ ]`** until that actor completes it.

---

## Scope Limits (Out of Scope for Wave 4)

- Do **not** modify or re-materialize any of the `15` existing Wave 1–3 harnesses under `D:\GitHub\harnesses\` unless a shared catalog test requires updating expected blueprint counts.
- Do **not** mutate or pollute Prime's live `.harness/knowledge/` vault (`382` KIs) during Track 3 dock-back verification unless the user explicitly selects live promotion in Decision `0.3`.
- Do **not** weaken `BRAIN_SURFACE` bounds (`max_always_on_chars=2000`, `max_files=25`, `max_skills=6`, `max_sub_agents=0`, `max_scripts=0`) or `GRADER_VERDICT_MARKERS` in [src/harness/services/recursive_harnessing/guards.py](src/harness/services/recursive_harnessing/guards.py).
- Do **not** run `git push` unless explicitly instructed by the user.

---

## Mandatory 7-Part Per-Harness Documentation & Cold-Walk Contract

Every materialized Wave 4 harness under `D:\GitHub\harnesses\<name>\` must satisfy the 7-part documentation & cold-walk contract enforced by `build_blueprint_tree()` in [src/harness/services/harness_spawner/blueprints.py](src/harness/services/harness_spawner/blueprints.py):
1. **`AGENTS.md` (L0 Routing Contract, `<= 22` lines):** Mission, exact ICM form, stage routing table (`01_drop` -> `04_output` for `pipeline`; `INDEX.md` -> `synthesis/` -> `output/` for `knowledge_bundle`; `INDEX.md` -> `subsystems/` -> `diagrams/` -> `audits/` for `system_map`; `INDEX.md` -> `records/` -> `extractions/` for `record_library`; `MAP.md` -> `layers/` -> `budgets/` -> `output/` for `context_map`), skill triggers, and explicit out-of-scope guardrails.
2. **`CONTEXT.md` (L1 Purpose, Stage Input/Output Contracts & Worked Example):** Concrete invocation recipe showing how the spawned harness operates against a target repository, book/video transcript, or Brain Harness subsystem.
3. **`README.md` (Operator Quickstart & Dock-Back Guide):** Exact CLI commands (`harness spawn check-drift .`, `harness dock inspect . --json`, `harness dock adopt . --parent-root ...`).
4. **`.harness/spawn_manifest.json`:** Deterministic metadata including `spawn_id`, `tree_sha256`, `icm_form`, `skills`, `seeded_kis`, `cohesion_score`, `bridge_count`, and `census`.
5. **`.harness/knowledge/SEEDED_KIS.md`:** 6 `VERIFIED` Knowledge Items with isnad lineage and domain tags (`0` unverified KIs).
6. **`.agents/skills/<skill>/` (`5` skills per harness):** Always anchored by `icm-workspace-architect` plus 4 domain skills (with `SKILL.md`, `CARD.md`, and `scripts/*.py` where present, formatted with `ruff format --check` **prior** to materialization per Gate `1.4`).
7. **Worked Use-Case Execution (`task-001` or domain equivalent) + Non-Destructive Dock-Back Proof:** Real CLI/service execution generating verifiable artifacts and docking back into an isolated sandbox parent copy (`scratch/sandbox_parent_wave4`) so `check-drift` returns `drift_detected: false` after workspace cleanup.

---

## Wave 4 Candidate Portfolio (Empirically Verified Against Live Graph & Vault)

| Rank | Blueprint Name | Tier | ICM Form | Primary Graph Cluster & Emergent Capability | Bundled Skills (`5`, all `<= 6`) | Verified Seeded KIs (`isnad=VERIFIED`) | Live `BRAIN_SURFACE` Census (`chars / files / skills`) | How It Assists With Harness Development & Ingestion |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Core 1** | `harness-repo-plugin-forge` | Core Wave 4 | `pipeline` | `cluster_04_external_repo_bridge_forge` + `cluster_06_mind_reader` (**Cap #6**: *Zero-Shot Foreign Repo Ingestion & IoC Packaging*) | `icm-workspace-architect`, `external-repo-bridge-forge`, `repo-to-plugin-forge`, `deep-repo-auditor`, `repo-reader` | `6` (`ki_google_repos_bridge`, `ki-omarchy-quattro-bridge`, `ki_self_20261114_04_brainbridge_external_plugin_pruning`, `ki_20260831_cellcog_04`, `ki_self_20260901_03`, `ki_20260823_02`) | `1,261 / 12 / 5` | **Ingesting external GitHub repos into Brain Harness**: runs 4-axis repo audits (`run_audit.py`), extracts commit/architecture trajectories (`repo-reader`), and scaffolds/validates sandboxed `HarnessPlugin` packages (`bridge_forge_driver.py`, `harness creator`, `harness bridge`). |
| **Core 2** | `harness-literature-media-forge` | Core Wave 4 | `knowledge_bundle` | `cluster_04_external_repo_bridge_forge` + `cluster_05_deep_skill_forge` (**Cap #5**: *Cryptographically Grounded Multimedia Literature-to-Vault Distillation*) | `icm-workspace-architect`, `book-to-skill-forge`, `deep-skill-forge`, `multimedia-intelligence-forge`, `media-to-vault-pipeline` | `6` (`ki_self_20260905_04`, `ki_self_20260905_03`, `ki_20260821_05`, `ki_self_20260903_02`, `ki_self_20260922_03`, `ki-shim-bounded-session-and-layered-skill-loader`) | `1,322 / 15 / 5` | **Ingesting books, papers, articles & video/multimedia lectures**: distills chapters, papers, and media transcripts into deep-module skills (`SKILL.md` + `CARD.md`) and isnad-verified Knowledge Vault items (`ki_scaffolder.py`, `multimedia_distiller.py`, `media_pipeline_cli.py`). |
| **Core 3** | `harness-kernel-plugin-dev` | Core Wave 4 | `system_map` | `cluster_01_plugin_seam_and_mirror_auditor` (**Central Hub, Size 23**; **Cap #21**: *Shift-Left Vulnerability Interception & Adversarial Seam Verification*) | `icm-workspace-architect`, `plugin-seam-and-mirror-auditor`, `adversarial-agent-verifier`, `python-dataclass-architect`, `pre-commit-security-guard` | `6` (`ki_self_20260914_01`, `ki_audit_20260915_01`, `ki_self_20260909_03`, `ki_self_20260924_02`, `ki_self_20260828_03`, `ki_self_20260909_01`) | `1,364 / 13 / 5` | **Daily Brain Harness kernel, plugin & service development**: audits `ServiceKey[T]` IoC DAG seams and AST doc mirrors (`plugin_auditor.py`), enforces `@dataclass(slots=True, frozen=True)` models (`Rule 12`), runs adversarial verification contracts, and executes shift-left DevSkim/Gitleaks gates (`pre_commit_security_engine.py`). |
| **Core 4** | `harness-self-evolution` | Core Wave 4 | `pipeline` | `cluster_03_agent_harness_architect` (**Central Hub, Size 22**; **Cap #4**: *Self-Calibrating Multi-Tier Autonomous Agent Harness Architecture*) | `icm-workspace-architect`, `agent-harness-architect`, `ai-native-harness-engineer`, `harness-compass`, `harness-reflector` | `6` (`ki-harnesscompass-evolution`, `ki_techwithrj_harness_engineering`, `ki_koos_typescript_harness_from_scratch`, `ki-empirical-harness-calibration`, `ki-harness2-recursive-harnessing`, `ki_20260831_sme_01`) | `1,277 / 14 / 5` | **Improving and evolving Brain Harness itself**: evaluates 5-part harness architecture (`agent_harness_architect.py`), runs 4-gate behavioral pipelines (`ai_native_harness.py`), executes HarnessCompass + R3 evolutionary loops (`harness_compass_engine.py`, `r3_integrator.py`), and reflects over Harness reports/trajectories (`harness reflect`). |
| **Opt A** | `harness-mind-artifact-miner` | Wave 4b Optional | `record_library` | `cluster_06_mind_reader` + `cluster_12_brain_artifact_miner` + `cluster_15_data_topology_mapper` | `icm-workspace-architect`, `mind-reader`, `temp-artifact-miner`, `brain-artifact-miner`, `questio-reflection` | `6` (`ki_brain_20261003_01`, `ki_20260824_repo_01`, `ki-getzep-graphiti-bitemporal-edge-normalization`, `ki_20260913_memgraph_rag_05`, `ki_20260821_05`, `ki_conversations_20261003_01`) | `1,256 / 12 / 5` | **Mining external IDE brains, `%TEMP%` sandboxes & pre-refactor dialectical reflection**: extracts learnings from foreign IDE histories (`mind-reader`, `brain_artifact_miner.py`), harvests `%TEMP%` visual briefs/pytest diagnostics (`temp_artifact_miner.py`), and runs Aquinas-style `questio-reflection` before structural edits. |
| **Opt B** | `harness-runtime-governor` | Wave 4b Optional | `context_map` | `cluster_03_agent_harness_architect` (`pi-coding-harness` + `shim-harness-governor` + `elephant-goldfish-governor`) | `icm-workspace-architect`, `pi-coding-harness`, `shim-harness-governor`, `elephant-goldfish-governor`, `context-engineering-architect` | `6` (`ki-shim-bounded-session-and-layered-skill-loader`, `ki-shim-tiered-permission-and-symlink-sandbox`, `ki-empirical-harness-calibration`, `ki_koos_typescript_harness_from_scratch`, `ki_self_20260917_01`, `ki_20260922_tau_pi_agent_architecture`) | `1,320 / 14 / 5` | **Engineering CLI agent loops, permission sandboxes & spec-review gates**: governs 3-tier terminal coding loops (`pi_harness_engine.py`), 4-tier tool permissions and symlink sandboxes (`shim_governor_engine.py`), Elephant-Goldfish 5-stage antagonistic review gates (`elephant_goldfish_engine.py`), and 6-layer context stacks (`context_engineering_engine.py`). |

### How `harness-repo-plugin-forge` (Wave 4) Complements `harness-repo-distiller` (Wave 1)

| Dimension | `harness-repo-distiller` (Wave 1 — Epistemic Trajectory & KI Miner) | `harness-repo-plugin-forge` (Wave 4 — Foreign Repo Ingestion & Plugin Builder) |
| :--- | :--- | :--- |
| **Primary Goal** | Mine IDE conversation trajectories, brain artifacts, and triad quotes into isnad-audited Knowledge Items | Ingest an external GitHub repository, run 4-axis codebase introspection, and scaffold/validate a sandboxed `HarnessPlugin` under `plugins/<category>/<name>/` |
| **Bundled Skills** | `icm-workspace-architect`, `repo-triad-forge`, `epistemic-isnad-audit`, `brain-artifact-miner`, `conversation-trajectory-miner` | `icm-workspace-architect`, `external-repo-bridge-forge`, `repo-to-plugin-forge`, `deep-repo-auditor`, `repo-reader` |
| **Bundled Runners** | `brain_artifact_miner.py`, `trajectory_miner.py` | `bridge_forge_driver.py`, `run_audit.py` + `harness creator` & `harness bridge` |

---

## Track 0 — User Decision Gate (Blocking Before Track 1–4 Execution)

- [ ] **0.1 Confirm Wave 4 Portfolio Scope:**
  - **Option 1 (Core 4 Development & Ingestion Harnesses):** Materialize `harness-repo-plugin-forge`, `harness-literature-media-forge`, `harness-kernel-plugin-dev`, and `harness-self-evolution` (`4` harnesses; adds `16` newly covered skills -> `72 / 114` total workspace skills covered across `19` materialized harnesses).
  - **Option 2 (Core 4 + Optional Wave 4b Add-Ons — Recommended):** Materialize all **6** Wave 4 development & ingestion harnesses (`Core 1–4` + **Opt A** `harness-mind-artifact-miner` + **Opt B** `harness-runtime-governor`; adds `23` newly covered skills -> `79 / 114` total workspace skills covered across `21` materialized harnesses).
- [ ] **0.2 Confirm ICM Workspace Forms & External Storage Layout:**
  - Confirm the ICM form assignment for each selected Wave 4 harness (`pipeline` for `harness-repo-plugin-forge` and `harness-self-evolution`; `knowledge_bundle` for `harness-literature-media-forge`; `system_map` for `harness-kernel-plugin-dev`; `record_library` for `harness-mind-artifact-miner`; `context_map` for `harness-runtime-governor`) and confirm materialization under `D:\GitHub\harnesses\<name>\` registered in `D:\GitHub\harnesses\.spawns\registry.json`.
- [ ] **0.3 Confirm Track 3 Dock-Back Target (`Sandbox` vs `Live Vault`):**
  - Confirm whether Track 3 (`3.2`) dock-back adoption should target an isolated sandbox copy (`scratch/sandbox_parent_wave4`, keeping Prime's live `.harness/knowledge/` untouched at `382` KIs — **recommended**) or promote synthesized KIs directly into Prime's live `.harness/knowledge/` vault.

---

## Track 1 — Catalog Registration, Default Limit Expansion & Pre-Materialization Format Gate

- [ ] **1.1 Register Approved Wave 4 `CanonicalSpec` Entries & Expand Default `limit` (`16 -> 22`):**
  - Add the approved Wave 4 `CanonicalSpec` entries to `CANONICAL_SPECS` in [src/harness/services/harness_spawner/_blueprint_catalog.py](src/harness/services/harness_spawner/_blueprint_catalog.py).
  - Widen the default `limit` parameter from `16` to `22` in:
    - `recommend_harness_blueprints(..., limit: int = 22)` in [src/harness/services/harness_spawner/blueprints.py](src/harness/services/harness_spawner/blueprints.py),
    - `DefaultHarnessSpawnerService.recommend_blueprints(..., limit: int = 22)` in [src/harness/services/harness_spawner/service.py](src/harness/services/harness_spawner/service.py), and
    - `harness spawn blueprints --limit 22` in [src/harness/commands/spawn.py](src/harness/commands/spawn.py)
    so every canonical blueprint across Waves 1–4 is returned by default without truncating lower-scoring specs.
- [ ] **1.2 Export Wave 4 Blueprint Selection Artifact:**
  - Run `.\.venv\Scripts\harness.exe spawn blueprints --json` and save the full selection report to `docs/reports/spawn-wave4-blueprints-selection-2026-11-23.json`.
  - Verify every approved Wave 4 blueprint satisfies `always_on_chars <= 2000`, `n_files <= 25`, `skills <= 6`, `len(seeded_kis) == 6`, and `len(excluded_unverified_kis) == 0`.
- [ ] **1.3 Verify Standalone Execution of Bundled Wave 4 Skill Scripts:**
  - Verify each bundled `.agents/skills/<skill>/scripts/*.py` runner (`bridge_forge_driver.py`, `run_audit.py`, `ki_scaffolder.py`, `pipeline_runner.py`, `multimedia_distiller.py`, `media_pipeline_cli.py`, `plugin_auditor.py`, `pre_commit_security_engine.py`, `agent_harness_architect.py`, `ai_native_harness.py`, `harness_compass_engine.py`, `r3_integrator.py`, plus `temp_artifact_miner.py`, `brain_artifact_miner.py`, `pi_harness_engine.py`, `shim_governor_engine.py`, `elephant_goldfish_engine.py`, `context_engineering_engine.py` if Option 2 is selected) can execute cleanly from a materialized child harness directory `D:\GitHub\harnesses\<name>\` using Prime's `.venv\Scripts\python.exe` without `ModuleNotFoundError`.
  - If any script relies solely on `Path(__file__).resolve().parents[4]` to locate Prime's `src/` directory (which in a materialized child points to `D:\GitHub\harnesses\<name>\` rather than Prime when invoked without `harness.exe` or editable install), verify that `.\.venv\Scripts\python.exe` (which has `harness` editable-installed in `.venv`) imports `harness.*` cleanly from `D:\GitHub\harnesses\<name>\`.
- [ ] **1.4 Mandatory Pre-Materialization Format & Static Gate (Prevent Post-Spawn `tree_sha256` Drift):**
  - Run `.\.venv\Scripts\ruff.exe check .` and `.\.venv\Scripts\ruff.exe format --check src/ tests/ .agents/skills/` **before** Track 2 materialization so zero post-materialization formatting edits can alter any bundled skill script's byte length or `tree_sha256` digest.

---

## Track 2 — Materialization, Drift Inspection & Deterministic Reproducibility

- [ ] **2.1 Materialize Approved Wave 4 Harnesses under `D:\GitHub\harnesses\`:**
  - Materialize each approved Wave 4 blueprint into `D:\GitHub\harnesses\<name>\` with `--force` and register it in `D:\GitHub\harnesses\.spawns\registry.json`.
  - Record each harness's `spawn_id`, `tree_sha256`, `always_on_chars`, `n_files`, and `skills` count inline.
- [ ] **2.2 Zero-Drift & Dock Inspection Gate across All Materialized Wave 4 Harnesses:**
  - Run `.\.venv\Scripts\harness.exe spawn check-drift "D:\GitHub\harnesses\<name>"` (`drift_detected: false`, `modified_files: []`, `missing_files: []`, `extra_files: []`) and `.\.venv\Scripts\harness.exe dock inspect "D:\GitHub\harnesses\<name>" --json` (`ready_to_adopt: true`) on every Wave 4 harness.
- [ ] **2.3 Deterministic Reproducibility Proof:**
  - Re-materialize every approved Wave 4 blueprint into a temporary directory and verify that `actual_tree_sha256 == expected_tree_sha256` matches both `D:\GitHub\harnesses\<name>\.harness\spawn_manifest.json` and `D:\GitHub\harnesses\.spawns\registry.json`.

---

## Track 3 — 8-Point Cold-Walk Audit, Worked Development/Ingestion Runs & Dock-Back Proof

- [ ] **3.1 Execute 8-Point Cold-Walk Audit (`docs/reports/spawn-wave4-cold-walk-2026-11-23.md`):**
  - Evaluate every materialized Wave 4 harness against the 8-Point Cold-Walk Checklist (`#1` 30-second mission clarity, `#2` ICM form truthfulness, `#3` stage input/output contract completeness, `#4` skill trigger precision, `#5` worked example followability, `#6` seeded KI relevance & isnad verification, `#7` out-of-scope boundary enforcement, `#8` dock-back readiness).
  - *Note:* Per the Evidence Rule, `3.1` remains `[ ]` until the human reader confirms qualitative points `#1, #5, #8`.
- [ ] **3.2 Execute Real Worked Development & Ingestion Use Cases (`task-001`) + Non-Destructive Dock-Back Proof (`docs/reports/spawn-wave4-adoptions-2026-11-23.md`):**
  - Run a real development or ingestion task inside each materialized Wave 4 harness:
    1. **`harness-repo-plugin-forge`:** Run `deep-repo-auditor` (`run_audit.py --no-briefs`) and `external-repo-bridge-forge` (`bridge_forge_driver.py` / `DefaultPluginCreatorService`) on a target package to produce a 4-axis audit and validated plugin bridge summary in `04_output/task-001-repo-plugin-forge-report.md`.
    2. **`harness-literature-media-forge`:** Run `book-to-skill-forge` / `deep-skill-forge` (`ki_scaffolder.py`) and `multimedia-intelligence-forge` (`multimedia_distiller.py`) on a sample technical chapter/transcript in `sources/` to produce a distilled skill card and isnad-verified synthesis in `output/task-001-literature-media-distillation.md`.
    3. **`harness-kernel-plugin-dev`:** Run `plugin-seam-and-mirror-auditor` (`plugin_auditor.py`) and `pre-commit-security-guard` (`pre_commit_security_engine.py`) against a target plugin/service directory to produce an IoC DAG seam + shift-left SAST audit in `audits/task-001-kernel-plugin-dev-audit.md`.
    4. **`harness-self-evolution`:** Run `agent-harness-architect` (`agent_harness_architect.py`), `ai-native-harness-engineer` (`ai_native_harness.py`), and `harness-compass` (`harness_compass_engine.py`) to produce a 5-part harness architecture & evolutionary scorecard in `04_output/task-001-harness-self-evolution-report.md`.
    5. **`harness-mind-artifact-miner` (if Option 2 selected):** Run `temp-artifact-miner` (`temp_artifact_miner.py`) and `brain-artifact-miner` (`brain_artifact_miner.py`) to catalog ephemeral diagnostics and brain trajectory artifacts into `extractions/task-001-mind-artifact-mining-report.md`.
    6. **`harness-runtime-governor` (if Option 2 selected):** Run `pi-coding-harness` (`pi_harness_engine.py`), `shim-harness-governor` (`shim_governor_engine.py`), and `elephant-goldfish-governor` (`elephant_goldfish_engine.py`) to produce a 3-tier session DAG, 4-tier permission matrix, and 5-stage antagonistic spec review report in `output/task-001-runtime-governance-audit.md`.
  - Dock each harness's synthesized output back into `scratch/sandbox_parent_wave4` (or live vault per `0.3`) via `DefaultHarnessDockService.adopt()`, restore each child harness under `D:\GitHub\harnesses\<name>\` to its clean post-spawn state (`drift_detected: false`), and record all adoption manifests in `docs/reports/spawn-wave4-adoptions-2026-11-23.md`.
- [ ] **3.3 Reconcile Spawner & Dock Unit/Integration Tests:**
  - Update [tests/test_harness_spawner.py](tests/test_harness_spawner.py) and [tests/test_harness_dock.py](tests/test_harness_dock.py) to assert the Wave 4 canonical blueprint catalog, default `limit=22`, `BRAIN_SURFACE` compliance, and clean tree invariants across all canonical blueprints.

---

## Track 4 — Full Verification Gate & Independent Check

- [ ] **4.1 Execute Full Verification Suite:**
  - `.\.venv\Scripts\python.exe -m pytest -q tests/test_harness_spawner.py tests/test_harness_dock.py tests/test_recursive_harnessing.py tests/test_skill_graph.py tests/test_icm_workspace.py tests/test_plugin_integration_drift.py`
  - `.\.venv\Scripts\python.exe -m pytest -m "unit" -q --timeout=60`
  - `.\.venv\Scripts\ruff.exe check .` and `.\.venv\Scripts\ruff.exe format --check src/harness/services/harness_spawner/ src/harness/commands/spawn.py tests/test_harness_spawner.py`
  - `.\.venv\Scripts\harness.exe context lint`
  - Verify `Wave 4 domain harness spawning plan-2026-11-23-EST.md` contains `0` workspace-absolute file URI matches (`Rule 47`).
  - Verify `.\.venv\Scripts\harness.exe spawn list --spawn-root "D:\GitHub\harnesses" --json` shows all Wave 1–4 harnesses (`19` or `21` total) with `drift_detected: false` and live `.harness/knowledge/` untouched at `382` KIs.
- [ ] **4.2 Independent check** — A fresh session (or human reviewer) re-runs `harness spawn check-drift` across every Wave 4 harness under `D:\GitHub\harnesses\`, verifies `tree_sha256` digests against `D:\GitHub\harnesses\.spawns\registry.json`, and signs off on `3.1` cold-walk qualitative criteria `#1, #5, #8`. *(Must remain unticked `[ ]` in the authoring/execution session.)*
