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

- [x] **0.1 Confirm Wave 4 Portfolio Scope:** Confirmed `2026-11-23` (**Option 2 — Core 4 + Opts A & B**, all **6** Wave 4 development & ingestion harnesses: `harness-repo-plugin-forge`, `harness-literature-media-forge`, `harness-kernel-plugin-dev`, `harness-self-evolution`, `harness-mind-artifact-miner`, and `harness-runtime-governor`; adds `23` newly covered skills -> `79` of `114` total workspace skills covered across `21` materialized harnesses).
- [x] **0.2 Confirm ICM Workspace Forms & External Storage Layout:** Confirmed `2026-11-23`: standalone dock-linked repositories under `D:\GitHub\harnesses\<name>\` registered in `D:\GitHub\harnesses\.spawns\registry.json` (`harness-repo-plugin-forge` = `pipeline`, `harness-literature-media-forge` = `knowledge_bundle`, `harness-kernel-plugin-dev` = `system_map`, `harness-self-evolution` = `pipeline`, `harness-mind-artifact-miner` = `record_library`, `harness-runtime-governor` = `context_map`).
- [x] **0.3 Confirm Track 3 Dock-Back Target (`Sandbox` vs `Live Vault`):** Confirmed `2026-11-23`: **Promote directly into the live Knowledge Vault** (`.harness/knowledge/` promoted from `382` -> **`388` KIs** with `0` skipped items under `harness knowledge sync --strict`, and synchronized in [README.md](README.md) and [USER_MANUAL.md](USER_MANUAL.md)).

---

## Track 1 — Catalog Registration, Default Limit Expansion & Pre-Materialization Format Gate

- [x] **1.1 Register Approved Wave 4 `CanonicalSpec` Entries & Expand Default `limit` (`16 -> 22`):** (`2026-11-23`)
  - Added all `6` Wave 4 `CanonicalSpec` entries to `CANONICAL_SPECS` in [src/harness/services/harness_spawner/_blueprint_catalog.py](src/harness/services/harness_spawner/_blueprint_catalog.py) (`21` total canonical specs).
  - Widened default `limit` from `16` to `22` across [src/harness/services/harness_spawner/blueprints.py](src/harness/services/harness_spawner/blueprints.py), [src/harness/commands/spawn.py](src/harness/commands/spawn.py), [plugins/agent_orchestration/harness_spawner/main.py](plugins/agent_orchestration/harness_spawner/main.py), [plugins/agent_orchestration/harness_spawner/service.py](plugins/agent_orchestration/harness_spawner/service.py), and [docs/reference/cli.md](docs/reference/cli.md).
- [x] **1.2 Export Wave 4 Blueprint Selection Artifact:** (`2026-11-23`)
  - Exported all `21` ranked blueprints to [docs/reports/spawn-wave4-blueprints-selection-2026-11-23.json](docs/reports/spawn-wave4-blueprints-selection-2026-11-23.json).
  - Verified all `6` Wave 4 blueprints satisfy `always_on_chars <= 2000` (`1,307–1,423`), `n_files <= 25` (`12–15`), `skills == 5 <= 6`, `len(seeded_kis) == 6`, and `len(excluded_unverified_kis) == 0`.
- [x] **1.3 Verify Standalone Execution of Bundled Wave 4 Skill Scripts:** (`2026-11-23`)
  - Verified all `17` bundled `.agents/skills/<skill>/scripts/*.py` runners (`run_audit.py`, `bridge_forge_driver.py`, `ki_scaffolder.py`, `multimedia_distiller.py`, `media_pipeline_cli.py`, `plugin_auditor.py`, `pre_commit_security_engine.py`, `agent_harness_architect.py`, `ai_native_harness.py`, `harness_compass_engine.py`, `r3_integrator.py`, `temp_artifact_miner.py`, `brain_artifact_miner.py`, `pi_harness_engine.py`, `shim_governor_engine.py`, `elephant_goldfish_engine.py`, `context_engineering_engine.py`) execute cleanly from `cwd=D:\GitHub\harnesses\<name>` (`rc=0`).
- [x] **1.4 Mandatory Pre-Materialization Format & Static Gate (Prevent Post-Spawn `tree_sha256` Drift):** (`2026-11-23`)
  - Executed `ruff check .` (`All checks passed!`) and `ruff format --check` on all modified spawner/command/test files (`6 files already formatted`) prior to materialization (`0` post-spawn skill script formatting edits).

---

## Track 2 — Materialization, Drift Inspection & Deterministic Reproducibility

- [x] **2.1 Materialize Approved Wave 4 Harnesses under `D:\GitHub\harnesses\`:** (`2026-11-23`)
  - Materialized all `6` Wave 4 harnesses under `D:\GitHub\harnesses\<name>\` and registered in `D:\GitHub\harnesses\.spawns\registry.json` (`21` total registered spawns across Waves 1–4):
    1. `harness-repo-plugin-forge` (`pipeline`): `spawn_id=spawn_harness-repo-plugin-forge_6e908a64`, `tree_sha256=facefd6840906874a025e4d0c54de45ffba1bbd226405cd57462156dd301a61a`, `docs_sha256=a77e588c69115a6abd62a95c9052d7dbbcb2e5df81909ce5d1c75054f9d86eb4` (`1,311 chars / 12 files / 5 skills`)
    2. `harness-literature-media-forge` (`knowledge_bundle`): `spawn_id=spawn_harness-literature-media-forge_ed7fffbd`, `tree_sha256=e9d334c1311c563c15239bd047be4eabdb1e2c68399b1b76442e693252719de9`, `docs_sha256=5c7951f08da9979f4aeaf7f315d0b3f5ea55063a59d2b56b9bd5a7ef8849aef7` (`1,373 chars / 15 files / 5 skills`)
    3. `harness-kernel-plugin-dev` (`system_map`): `spawn_id=spawn_harness-kernel-plugin-dev_20dd44ab`, `tree_sha256=c4cd586280e3d23428521d36aef2d815a0c37d61009fdc843c9c09b6a197addf`, `docs_sha256=c8635e03ca3904ae202eeecc9428a10c016373cbf8c4e257d1c0080af067bffd` (`1,423 chars / 13 files / 5 skills`)
    4. `harness-self-evolution` (`pipeline`): `spawn_id=spawn_harness-self-evolution_6fd5ddd6`, `tree_sha256=bbd6ac0c08f560bb5aa409783e60cbe74422e230d42fccc7e216154eb836138e`, `docs_sha256=12eeba2ed8b1b81eb61bba0691eb528d3150606fab4de8e3884181f173e3ecdd` (`1,344 chars / 14 files / 5 skills`)
    5. `harness-mind-artifact-miner` (`record_library`): `spawn_id=spawn_harness-mind-artifact-miner_46d8f64c`, `tree_sha256=98987ebe219cf89efbd7893fb1544d5a608be176d768ed7eeedad6694d6ecc1c`, `docs_sha256=8e1810e6cd1dd43e8c56090d239bf2667664b7e314709a791f1dd2f924b67046` (`1,307 chars / 12 files / 5 skills`)
    6. `harness-runtime-governor` (`context_map`): `spawn_id=spawn_harness-runtime-governor_50ed32ef`, `tree_sha256=87b4b9fd48e800c83b4bbfa6a29ebc73fb7876964710b7a092b4adb15f924bc8`, `docs_sha256=ecce1e22f7299b584a78cd89be392a728ca4eea4f605baea9f32a2cd2b239fe6` (`1,382 chars / 14 files / 5 skills`)
- [x] **2.2 Zero-Drift & Dock Inspection Gate across All Materialized Wave 4 Harnesses:** (`2026-11-23`)
  - Verified `check_materialized_drift()` returns `drifted: false` (`tree_drifted: false`, `docs_drifted: false`, `manifest_drifted: false`, `dock_status: "approved"`) and all 4 dock entrypoints (`validate`, `audit-docs`, `icm-audit`, `icm-links`) return `success: true` across all `6` Wave 4 harnesses.
- [x] **2.3 Deterministic Reproducibility Proof:** (`2026-11-23`)
  - Re-materialized every Wave 4 blueprint into an isolated temporary directory against the `388`-KI live vault and verified `repro_info["tree_sha256"] == mat_info["tree_sha256"]` and `repro_info["docs_sha256"] == mat_info["docs_sha256"]` across all `6` harnesses.

---

## Track 3 — 8-Point Cold-Walk Audit, Worked Development/Ingestion Runs & Dock-Back Proof

- [ ] **3.1 Execute 8-Point Cold-Walk Audit ([docs/reports/spawn-wave4-cold-walk-2026-11-23.md](docs/reports/spawn-wave4-cold-walk-2026-11-23.md)):**
  - **Automated + prechecks + agent cold reads complete (`2026-11-23`):** Recorded in [docs/reports/spawn-wave4-cold-walk-2026-11-23.md](docs/reports/spawn-wave4-cold-walk-2026-11-23.md) across all `6` Wave 4 harnesses (`#2,#3,#4,#6,#7` = `PASS`; `IcmAuditor` `10/10` invariants clean; `IcmVerifier` `0` broken links across `51`, `44`, `50`, `51`, `43`, and `53` links; `validate_harness_docs` clean; `check-drift` `drifted: false`; agent cold reader `Gemini 4 Neon` verified `AGENTS.md` `22L` + `CONTEXT.md`).
  - **Remaining for checkbox closure:** Explicit human reader sign-off on qualitative points `#1, #5, #8`.
- [x] **3.2 Execute Real Worked Development & Ingestion Use Cases + Direct Live Vault Promotion ([docs/reports/spawn-wave4-adoptions-2026-11-23.md](docs/reports/spawn-wave4-adoptions-2026-11-23.md)):** (`2026-11-23`)
  - Executed real development and ingestion workloads from `cwd=D:\GitHub\harnesses\<name>`, proposed `12` merge-back items (`6` adopted directly into Prime's live `.harness/knowledge/` vault + `6` rejected negative controls), ran `harness knowledge sync --strict` (`388` KIs synced, `0` skipped), and restored all `6` child harnesses to `drifted: false`:
    1. **`harness-repo-plugin-forge` (`pipeline`):** Standalone `run_audit.py --no-briefs` on `harness_spawner` (`files=5, axes=4, composite=0.268`) + `PluginValidator` (`valid=True`, `5` checks), stages `01–03` passed -> promoted `ki-repo-plugin-forge-4axis-and-sandbox-validator` into `.harness/knowledge/`.
    2. **`harness-literature-media-forge` (`knowledge_bundle`):** Standalone `ki_scaffolder.py` + `media_pipeline_cli.py fetch-transcript` & `distill-seams` + `IcmVerifier.verify_quotes` (`verified=1, valid=True`) -> promoted `ki-literature-media-dual-lens-isnad-distillation` into `.harness/knowledge/`.
    3. **`harness-kernel-plugin-dev` (`system_map`):** Standalone `plugin_auditor.py dag` (`cycles=0`) + `PreCommitSecurityService.scan_staged_files` (`passed=True, findings=0`), `objects` & `processes` indexed (`ICM 10/10`) -> promoted `ki-kernel-plugin-ioc-seam-and-shift-left-gate` into `.harness/knowledge/`.
    4. **`harness-self-evolution` (`pipeline`):** Standalone `agent_harness_architect.py audit --json` + `ai_native_harness.py --gates --json` + `harness_compass_engine.py` & `r3_integrator.py`, stages `01–03` passed -> promoted `ki-self-evolution-compass-r3-and-4gate-pipeline` into `.harness/knowledge/`.
    5. **`harness-mind-artifact-miner` (`record_library`):** Standalone `temp_artifact_miner.py --scan --json` + `brain_artifact_miner.py scan`, `records` indexed (`ICM 10/10`) -> promoted `ki-mind-artifact-temp-salvage-and-questio-gate` into `.harness/knowledge/`.
    6. **`harness-runtime-governor` (`context_map`):** Standalone `pi_harness_engine.py` + `shim_governor_engine.py` + `context_engineering_engine.py audit --json`, `teams` indexed (`ICM 10/10`) -> promoted `ki-runtime-governor-tiered-permissions-and-bifurcated-review` into `.harness/knowledge/`.
- [x] **3.3 Reconcile Spawner & Vault Unit/Integration Tests:** (`2026-11-23`)
  - Updated [tests/test_harness_spawner_blueprints.py](tests/test_harness_spawner_blueprints.py) (`len(CANONICAL_SPECS) == 21` + `test_wave4_blueprints_seed_verified_kis_and_pass_surface_and_guards`), updated [README.md](README.md) and [USER_MANUAL.md](USER_MANUAL.md) to `**388 Knowledge Items**`, and restamped the `3` historical `AGENTS.md` git-blob LF SHA-256 claim hashes (`9b0b702b5e1ab1d7bc32e27503bd536bda49f508629488292e6e99769736eb79`) in `.harness/knowledge/{ki_agent_skills_progressive_disclosure,ki_self_20260907_02,ki_self_20260907_03}/metadata.json`.

---

## Track 4 — Full Verification Gate & Independent Check

- [x] **4.1 Execute Full Verification Suite:** (`2026-11-23`)
  - Targeted 15-file pytest suite (`test_service_joint_query`, `test_service_dock`, `test_command_dock`, `test_layer_import_boundaries`, `test_icm_workspace_architect`, `test_harness_spawner_blueprints`, `test_harness_spawner_doc_bundle`, `test_harness_spawner_materialize`, `test_harness_spawner_e2e`, `test_harness_spawner_plugin_forwarding`, `test_plugin_integration_drift`, `test_cli_content_drift`, `test_gods_eye_view_service`, `test_service_storage_vault_integrity`, `test_track4_track5_vault_integrity`): **`104 passed`** (`0` skipped, `0` failed).
  - Full unit gate (`.\.venv\Scripts\python.exe -m pytest -m "unit" -q --timeout=60`): **`2358 passed, 885 deselected`** (`0` skipped, `0` failed; `.harness/config.json` restored via `git checkout`).
  - `.\.venv\Scripts\ruff.exe check .` (`All checks passed!`) and `.\.venv\Scripts\ruff.exe format --check` on all `6` touched spawner/command/test files (`6 files already formatted`).
  - `.\.venv\Scripts\mypy.exe src/harness/kernel --ignore-missing-imports` (`Success: no issues found in 27 source files`) and strict `mypy` on the `5` modified spawner/command modules (`Success: no issues found in 5 source files`).
  - `.\.venv\Scripts\harness.exe context lint` (`[PASS] Context files healthy across 3 checks at: .`) and `.\.venv\Scripts\harness.exe knowledge sync --strict` (`✓ Successfully synced 388 Knowledge Item(s) from '.harness/knowledge' into storage.`).
  - Verified `Wave 4 domain harness spawning plan-2026-11-23-EST.md` contains `0` workspace-absolute file URI matches (`Rule 47`).
  - Verified `D:\GitHub\harnesses\.spawns\registry.json` lists all **`21` materialized harnesses** across Waves 1–4 (`4` Wave 1 + `4` Wave 2 + `7` Wave 3 + `6` Wave 4) with `drifted: false` and live `.harness/knowledge/` promoted to **`388` KIs**.
- [ ] **4.2 Independent check** — A fresh session (or human reviewer) re-runs `harness spawn check-drift` across every Wave 4 harness under `D:\GitHub\harnesses\`, verifies `tree_sha256` digests against `D:\GitHub\harnesses\.spawns\registry.json`, and signs off on `3.1` cold-walk qualitative criteria `#1, #5, #8`. *(Must remain unticked `[ ]` in the authoring/execution session.)*
