# Emergent Macro-Capabilities Audit & Standing Gaps Analysis + Plan

**Date**: 2026-11-05 17:55 EST  
**Target Commit**: `fe491ad` (`HEAD`, tree-identical to `57f4642`)  
**Scope**:

1. **Brief 1**: Forensic audit of all 23 emergent macro-capabilities in `reports/cluster_analysis_data.json` (`reports/skill_knowledge_graph_cluster_analysis_report.md`), ranked by plausibility and testability, operational definition of `"works"`, and a concrete hermetic trial specification for Rank #1 (`cap_context_anti_rot_governance`).
2. **Brief 2**: Fresh file-level re-verification of the Nov 1 / Nov 3 standing gaps, post-Nov-3 regressions (`3f86400`, `3783c04`), and soft §12 leftovers against current `HEAD`, followed by a pickable, dependency-tracked remediation plan.

> **Evidence Rule**: Every claim in Brief 1 cites a repository file path or skill identifier; zero execution results are asserted for the 23 macro-capabilities (none have been run as end-to-end pipelines). In Brief 2, no item is marked closed (`[x]`) without a verified commit + passing test, dated command output, or an explicit recorded architectural decision on disk.

---

## Part I — Brief 1: Audit of the 23 Emergent Macro-Capabilities

### 1.1 Mechanism Audit: How the 23 Capabilities Were Generated

Inspection of `src/harness/services/skill_clustering/engine/emergent.py`, `src/harness/services/skill_clustering/patterns.py`, and `src/harness/services/skill_clustering/engine/clusterer.py` reveals that the 23 entries in `reports/cluster_analysis_data.json` (`emergent_capabilities`, lines `1115–1553`) are **not** the output of a topological workflow synthesis algorithm. They come from two static heuristics:

1. **11 Hardcoded Canonical Templates (`CANONICAL_EMERGENT_PATTERNS`)** in `src/harness/services/skill_clustering/patterns.py:7-141`:
   - **7 Cluster-Matched Templates** (`emergent.py:24-54`): Whenever a cluster contains $\ge 2$ skills from a template's hardcoded `core_skills` tuple, `discover_emergent_capabilities()` emits that template verbatim (`recommended_pipeline = list(pattern["pipeline"])`), even if the remaining pipeline skills belong to different clusters (`[03] cap_foreign_repo_ingestion_deepening`, `[04] cap_harness_calibration_evolution`, `[06] cap_context_anti_rot_governance`, `[07] cap_agentic_swarm_self_evolution`, `[09] cap_enterprise_lakehouse_governance`, `[13] cap_ontological_graph_engineering`, `[18] cap_sparse_neural_calculus`). Note that `cluster_11_mind_reader` (`reports/cluster_analysis_data.json:702-720`) also matched `cap_adversarial_security_gate` via `pre-commit-security-guard` + `questio-reflection`, which deduplicated into the cross-domain entry in `unique_caps` (`emergent.py:138-145`).
   - **4 Unconditional Cross-Domain Appends** (`emergent.py:119-136`): Any template in `CANONICAL_EMERGENT_PATTERNS` that did not match a single cluster (or matched `cluster_11` and was overwritten by `cluster_cross_domain`) is appended unconditionally at the end of `discover_emergent_capabilities()` under the synthetic `cluster_id: "cluster_cross_domain"` (`[20] cap_multimedia_vault_distillation`, `[21] cap_legacy_modernization_safety_net`, `[22] cap_adversarial_security_gate`, `[23] cap_docs_as_code_ast_pipeline`) provided $\ge 2$ of its `core_skills` exist anywhere in `graph.nodes`.
2. **12 Alphabetical-Slice Fallback Syntheses (`cap_synth_cluster_*`)** in `src/harness/services/skill_clustering/engine/emergent.py:57-96`:
   - Whenever a cluster does not match any template in `CANONICAL_EMERGENT_PATTERNS`, `emergent.py:58` sets:

     ```python
     top_members = members[:5]
     ```

     where `members` is sorted **alphabetically** (`clusterer.py:55,64,139`), and emits `recommended_pipeline: list(top_members)` (`emergent.py:90`)!
   - Worse, `emergent.py:77` synthesizes `description` by concatenating the first 3 skills' descriptions and slicing at `[:160]` characters (`f"Integrated workflow combining { s1_desc[:160] }"`), cutting off mid-word in 11 of the 12 `cap_synth_*` capabilities in `reports/cluster_analysis_data.json` (e.g., `"Do not use for ."`, `"merge-base."`, `"evidence d."`, `"executable agen."`, `"hotspots into sl."`, `"Runtime Store Min."`, `"no str."`, `"adversarial sel."`, `"resource manifest."`, `"where a se."`, `"model prompt dra."`).

### 1.2 Global Findings Across the 3 Audit Questions

1. **Question 1 — Does each `recommended_pipeline` name real skills?**
   - **Yes in `_GRAPH_INSTANCE.nodes` (140/140 skills exist on disk), but across 3 heterogeneous tiers**:
     - **104 Workspace Skills** in `.agents/skills/<name>/SKILL.md` (`86` have executable `scripts/*.py` engines; `18` are markdown-only instruction skills).
     - **1 Plugin-Co-Located Skill** (`ontology-spider`) in `plugins/memory_and_epistemics/ontology_spider/SKILL.md` — it has **no** directory under `.agents/skills/ontology-spider/`.
     - **35 External Pocock Skills** in `plugins/external/Pocock-skills-main/skills/{engineering,productivity,in-progress}/<name>/SKILL.md` — markdown-only prompts, **21 of which set `disable-model-invocation: true`** (blocking autonomous agent invocation).
   - Note: `reports/cluster_analysis_data.json` was generated when the catalog had 140 nodes (including `agent-desktop-operator` and `ontology-spider`), whereas `reports/skill_knowledge_graph_cluster_analysis_report.md:5` still cites `138 Skills` in its header while embedding the 23 capabilities from the 140-skill run.

2. **Question 2 — Do consecutive steps have real graph edges between them (`REQUIRES`, `PRECEDES`, `FEEDS`) or is the order arbitrary?**
   - In `src/harness/services/skill_graph/indexer.py`, a directed edge `A -> B` with `relation="REQUIRES"` means skill `A`'s markdown references skill `B` (so if step $i+1$ depends on step $i$, the stored edge is `step[i+1] -> step[i]`, denoted `rev:['REQUIRES']`, whereas `step[i] -> step[i+1]` is denoted `fwd:['REQUIRES'|'PRECEDES'|'FEEDS']`).
   - Across all **60 consecutive step pairs** in the 23 pipelines:
     - Only **19 of 60 pairs (31.7%)** have a direct edge in **either** direction (`fwd` or `rev`).
     - **41 of 60 pairs (68.3%)** have **zero** direct graph edge (`fwd:[]`, `rev:[]`).
     - Among the **12 `cap_synth_*` capabilities**, step order is **100% alphabetical** (`members[:5]`): **8 of the 12** have `0` edges across all consecutive pairs (`[01] 0/4`, `[05] 0/4`, `[10] 0/4`, `[11] 0/2`, `[14] 0/2`, `[15] 0/1`, `[16] 0/1`).
     - Even among the **11 `CANONICAL_EMERGENT_PATTERNS`**, only **4** have direct graph edges across **100%** of their consecutive pairs:
       - `[06] cap_context_anti_rot_governance` (`3/3` pairs linked)
       - `[23] cap_docs_as_code_ast_pipeline` (`2/2` pairs linked)
       - `[13] cap_ontological_graph_engineering` (`2/2` pairs linked)
       - `[18] cap_sparse_neural_calculus` (`1/1` pair linked)

3. **Question 3 — Is the claimed outcome actually achievable by those skills?**
   - **6 capabilities (Tier A, Ranks 1–6)** have cohesive domain alignment, real local Python CLI/service engines in `.agents/skills/*/scripts/` and `src/harness/services/`, and achieve their claimed outcome deterministically on a local repository once a thin runner passes each step's output to the next.
   - **8 capabilities (Tier B, Ranks 7–14)** are partially achievable or require simulated/in-memory adapters because one or more steps are markdown-only rubrics (`questio-reflection`, `data-topology-mapper`, `ontological-engineering-coach`) or reversed in order.
   - **9 capabilities (Tier C — `UNTESTABLE AS WRITTEN`, Ranks 15–23)** cannot execute as written because they either:
     - Include external Pocock human-only prompts with `disable-model-invocation: true` (`[02]`, `[14]`, `[17]`),
     - Require live external cloud/paid infrastructure (`BigQuery` TVFs in `[09]`, `CellCog` API in `[05]`, live YouTube network calls unless mocked in `[20]`), or
     - Splice 4–5 completely unrelated domains together alphabetically (`[01]` mixes adversarial verification + context type system + Vercel chatbot; `[05]` mixes Windows GUI desktop operator + browser envelopes + PDF file analysis + book-to-skill + CellCog 3D/video; `[10]` mixes Ebbinghaus decay + video transcription + git memory + ontology coaching + ontology spider).

---

### 1.3 Ranked Audit Table of All 23 Emergent Macro-Capabilities

| Rank | Cap ID & Cluster (`reports/cluster_analysis_data.json`) | Origin (`patterns.py` vs `emergent.py`) | `recommended_pipeline` & Real Skill Path Audit | Consecutive Step Graph Edge Audit (`fwd`: $s_i \to s_{i+1}$, `rev`: $s_{i+1} \to s_i$) | Claimed Outcome Achievable? | Tier & Flag |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | **`[06] cap_context_anti_rot_governance`** (`cluster_06_codebase_context_governor`) | **Canonical** (`patterns.py:42-51`) | **4/4 real** in `.agents/skills/*/SKILL.md`: `codebase-context-governor` (1 script), `context-anti-rot-sync` (2 scripts), `agent-instruction-architect` (0 scripts, rubric), `codebase-context-architect` (4 scripts + `src/harness/services/codebase_context/`). | **3/3 pairs linked (100%)**:<br>• `codebase-context-governor` $\leftrightarrow$ `context-anti-rot-sync` (`rev:['REQUIRES']`)<br>• `context-anti-rot-sync` $\to$ `agent-instruction-architect` (`fwd:['REQUIRES']`)<br>• `agent-instruction-architect` $\leftarrow$ `codebase-context-architect` (`rev:['REQUIRES']`). Order is intentional governance $\to$ sync $\to$ rule audit $\to$ CI lint. | **Yes (Hermetically Achievable)**. 3 of 4 steps have deterministic Python CLIs (`context_governance_driver.py`, `context_sync_cli.py`, `context_linter.py` / `sync_context.py`) and step 3 (`agent-instruction-architect`) is enforced programmatically by `ContextGovernor.audit_smells()` (`governor.py:21-78`). | **Tier A (Plausible & Hermetically Testable — Top Pick)** |
| **2** | **`[23] cap_docs_as_code_ast_pipeline`** (`cluster_cross_domain`) | **Canonical** (`patterns.py:132-140`, cross-domain append) | **3/3 real** in `.agents/skills/*/SKILL.md`: `repo-doc-synchronizer` (2 scripts), `developer-docs-architect` (2 scripts), `hf-doc-builder-architect` (2 scripts + `plugins/developer_tooling/hf_doc_builder/`). | **2/2 pairs linked (100%)**:<br>• `repo-doc-synchronizer` $\to$ `developer-docs-architect` (`fwd:['REQUIRES']`)<br>• `developer-docs-architect` $\leftarrow$ `hf-doc-builder-architect` (`rev:['REQUIRES']`). Order is logical: drift audit $\to$ Diátaxis structure $\to$ AST MDX compilation. | **Yes (Hermetically Achievable)**. All 3 skills have local zero-network Python scripts in `.agents/skills/*/scripts/` that operate on local Python/Markdown files. | **Tier A (Plausible & Hermetically Testable)** |
| **3** | **`[12] cap_synth_cluster_13_brain_artifact_miner`** (`cluster_13_brain_artifact_miner`) | **Synth-Fallback** (`emergent.py:57-96`, alphabetical `members[:5]`) | **3/3 real** in `.agents/skills/*/SKILL.md`: `brain-artifact-miner` (4 scripts), `conversation-trajectory-miner` (4 scripts), `temp-artifact-miner` (4 scripts). | **2/2 pairs linked (100%)**:<br>• `brain-artifact-miner` $\to$ `conversation-trajectory-miner` (`fwd:['REQUIRES','FEEDS']`)<br>• `conversation-trajectory-miner` $\leftarrow$ `temp-artifact-miner` (`rev:['REQUIRES','FEEDS']`). Even though generated by `members[:5]`, the cluster has exactly 3 tightly coupled archaeology skills. | **Yes (Hermetically Achievable)**. All 3 skills have local Python miners (`brain_miner_engine.py`, `trajectory_miner_engine.py`, `temp_miner_engine.py`) and corresponding plugins in `plugins/memory_and_epistemics/` that emit dual-file Knowledge Vault items. (Note: description in JSON is truncated at 160 chars: `"Runtime Store Min."`). | **Tier A (Plausible & Hermetically Testable)** |
| **4** | **`[19] cap_synth_cluster_20_headroom_context_optimizer`** (`cluster_20_headroom_context_optimizer`) | **Synth-Fallback** (`emergent.py:57-96`, alphabetical 2-skill cluster) | **2/2 real** in `.agents/skills/*/SKILL.md`: `headroom-context-optimizer` (2 scripts + `src/harness/services/headroom_optimizer.py`), `token-economizer` (2 scripts + `src/harness/services/token_economizer.py`). | **1/1 pair linked (100%)**:<br>• `headroom-context-optimizer` $\leftarrow$ `token-economizer` (`rev:['REQUIRES']`, meaning `token-economizer` explicitly depends on `headroom-context-optimizer`). Order is topological ($A \to B$ where $B$ requires $A$). | **Yes (Hermetically Achievable)**. Both skills have deterministic local Python engines (`headroom_optimizer.py` SmartCrusher/CCR dedup/thinking compaction + `token_economizer.py` turn-guard and tool-pruning). (Description truncated at `"model prompt dra."`). | **Tier A (Plausible & Hermetically Testable)** |
| **5** | **`[18] cap_sparse_neural_calculus`** (`cluster_19_deepselect_topk_optimizer`) | **Canonical** (`patterns.py:82-90`) | **2/2 real** in `.agents/skills/*/SKILL.md`: `neural-network-from-scratch` (2 scripts), `deepselect-topk-optimizer` (3 scripts + `src/harness/services/deepselect_service.py`). | **1/1 pair linked (100%)**:<br>• `neural-network-from-scratch` $\leftarrow$ `deepselect-topk-optimizer` (`rev:['REQUIRES']`). | **Yes (Achievable with `numpy` installed)**. Both have local mathematical engines; however, `.venv` currently lacks `numpy` (`tests/test_neural_network_from_scratch.py` fails collection with `ModuleNotFoundError: No module named 'numpy'`), whereas `deepselect_service.py` is pure Python. | **Tier A (Testable once `numpy` is in `.venv`)** |
| **6** | **`[04] cap_harness_calibration_evolution`** (`cluster_04_agent_harness_architect`) | **Canonical** (`patterns.py:22-30`) | **4/4 real** in `.agents/skills/*/SKILL.md`: `agent-harness-architect` (3 scripts), `coding-harness-calibrator` (3 scripts), `ai-native-harness-engineer` (2 scripts), `harness-compass` (2 scripts). | **1/3 pairs directly linked (33.3%)**:<br>• `agent-harness-architect` $\leftarrow$ `coding-harness-calibrator` (`rev:['REQUIRES']`)<br>• `coding-harness-calibrator` $\to$ `ai-native-harness-engineer` (`none`)<br>• `ai-native-harness-engineer` $\to$ `harness-compass` (`none`). Order is domain-logical (architect $\to$ calibrate $\to$ 4-gate pipeline $\to$ evolve), though pairs 2 and 3 lack explicit markdown cross-links. | **Yes (Hermetically Achievable via Adapter)**. All 4 skills have local Python scripts and corresponding kernel services (`harness_architect.py`, `calibrator/`, `ai_native_harness.py`, `compass.py`), though their JSON schemas differ and require a thin adapter between steps. | **Tier A (Plausible; 2 missing graph edges)** |
| **7** | **`[03] cap_foreign_repo_ingestion_deepening`** (`cluster_03_adversarial_agent_verifier`) | **Canonical** (`patterns.py:12-20`) | **4/4 real** in `.agents/skills/*/SKILL.md`: `repo-reader` (1 script), `repo-to-plugin-forge` (1 script), `deepen-architecture` (0 scripts, rubric), `adversarial-agent-verifier` (2 scripts). | **2/3 pairs linked (66.7%)**:<br>• `repo-reader` $\leftrightarrow$ `repo-to-plugin-forge` (`fwd:['PRECEDES']`, `rev:['REQUIRES']`)<br>• `repo-to-plugin-forge` $\to$ `deepen-architecture` (`fwd:['PRECEDES']`)<br>• `deepen-architecture` $\to$ `adversarial-agent-verifier` (`none`). | **Partially Achievable**. Steps 1, 2, and 4 have local Python scripts (`repo_inspector.py`, `forge_bridge.py`, `seam_analyzer.py`/`verifier_cli.py`), but Step 3 (`deepen-architecture`) is a prose-only interactive workflow without a script (unlike `architecture-deepening-workflow`, which has 2 scripts). | **Tier B (Step 3 is prose-only; replace with `architecture-deepening-workflow`)** |
| **8** | **`[21] cap_legacy_modernization_safety_net`** (`cluster_cross_domain`) | **Canonical** (`patterns.py:112-120`, cross-domain append) | **4/4 real** in `.agents/skills/*/SKILL.md`: `data-topology-mapper` (0 scripts), `legacy-refactoring-guardian` (2 scripts), `legacy-modernization-pipeline` (2 scripts), `adversarial-agent-verifier` (2 scripts). | **2/3 pairs linked (66.7%)**:<br>• `data-topology-mapper` $\to$ `legacy-refactoring-guardian` (`none`)<br>• `legacy-refactoring-guardian` $\leftarrow$ `legacy-modernization-pipeline` (`rev:['REQUIRES']`)<br>• `legacy-modernization-pipeline` $\to$ `adversarial-agent-verifier` (`fwd:['REQUIRES']`). | **Partially Achievable**. Steps 2, 3, and 4 have local scripts (`archaeology_scanner.py`, `modernization_runner.py`, `verifier_cli.py`), while Step 1 (`data-topology-mapper`) is a markdown-only rubric whose topology stage is already embedded inside `legacy-modernization-pipeline`. | **Tier B (Step 1 is prose-only; Steps 2–4 executable)** |
| **9** | **`[13] cap_ontological_graph_engineering`** (`cluster_14_knowledge_graph_pipeline`) | **Canonical** (`patterns.py:72-80`) | **3/3 real** in `.agents/skills/*/SKILL.md`: `ontological-engineering-coach` (0 scripts), `knowledge-graph-pipeline` (2 scripts), `sql-recursive-graph-traversal` (2 scripts). | **2/2 pairs linked (100%)**:<br>• `ontological-engineering-coach` $\leftarrow$ `knowledge-graph-pipeline` (`rev:['REQUIRES']`)<br>• `knowledge-graph-pipeline` $\to$ `sql-recursive-graph-traversal` (`fwd:['REQUIRES']`). | **Partially Achievable (SQLite mode works; Neo4j mode requires external DB)**. `knowledge-graph-pipeline` and `sql-recursive-graph-traversal` execute against local in-memory SQLite recursive CTEs, while Step 1 (`ontological-engineering-coach`) is a markdown-only Socratic rubric. | **Tier B (Step 1 prose-only; SQLite path testable offline)** |
| **10** | **`[07] cap_agentic_swarm_self_evolution`** (`cluster_07_game_theoretic_swarm_deliberator`) | **Canonical** (`patterns.py:52-60`) | **4/4 real** in `.agents/skills/*/SKILL.md`: `orca-orchestrator` (2 scripts), `game-theoretic-swarm-deliberator` (2 scripts), `sme-ann-backprop` (2 scripts), `swarm-reflection-optimizer` (1 script). | **1/3 pairs linked (33.3%)**:<br>• `orca-orchestrator` $\to$ `game-theoretic-swarm-deliberator` (`none`)<br>• `game-theoretic-swarm-deliberator` $\to$ `sme-ann-backprop` (`none`)<br>• `sme-ann-backprop` $\leftarrow$ `swarm-reflection-optimizer` (`rev:['REQUIRES']`). (`swarm-reflection-optimizer` actually requires both `game-theoretic-swarm-deliberator` and `sme-ann-backprop` as a fan-in). | **Partially Achievable (Simulation Mode)**. All 4 have local scripts (`orca_coordinator.py`, `borda_matrix_engine.py`, `ann_backprop_engine.py`, `swarm_optimizer_cli.py`), but `orca-orchestrator` manages git worktree worker inboxes while `swarm-reflection-optimizer` already wraps Borda + ANN backprop internally. | **Tier B (Fan-in topology, not linear 4-step chain)** |
| **11** | **`[22] cap_adversarial_security_gate`** (`cluster_cross_domain` & `cluster_11`) | **Canonical** (`patterns.py:122-130`) | **3/3 real** in `.agents/skills/*/SKILL.md`: `questio-reflection` (0 scripts), `pre-commit-security-guard` (4 scripts), `adversarial-agent-verifier` (2 scripts). | **0/2 consecutive pairs directly linked (0%)**:<br>• `questio-reflection` $\to$ `pre-commit-security-guard` (`none`)<br>• `pre-commit-security-guard` $\to$ `adversarial-agent-verifier` (`none`). (In the graph, `adversarial-agent-verifier` $\to$ `questio-reflection` has `REQUIRES`, skipping step 2). | **Partially Achievable**. `pre-commit-security-guard` (`security_guard_engine.py`) and `adversarial-agent-verifier` (`verifier_cli.py`) are deterministic local scanners, while `questio-reflection` is a prose-only rubric. | **Tier B (0/2 consecutive edges; Step 1 prose-only)** |
| **12** | **`[16] cap_synth_cluster_17_cloud_infrastructure_architect`** (`cluster_17_cloud_infrastructure_architect`) | **Synth-Fallback** (`emergent.py:57-96`, alphabetical 2-skill cluster) | **2/2 real** in `.agents/skills/*/SKILL.md`: `cloud-infrastructure-architect` (2 scripts), `kubernetes-drift-guardian` (2 scripts). | **0/1 pair linked (0%)**:<br>• `cloud-infrastructure-architect` $\to$ `kubernetes-drift-guardian` (`none`; connected only via shared category `infra-and-cloud`). | **Partially Achievable**. Both skills have standalone local validators (`cloud_infra_engine.py` and `k8s_drift_engine.py`), but they do not exchange data (one scores cloud sandboxing/Prometheus, the other diffs K8s YAML manifests). | **Tier B (Independent validators in same domain; 0 edges)** |
| **13** | **`[11] cap_synth_cluster_12_architecture_deepening_workflow`** (`cluster_12_architecture_deepening_workflow`) | **Synth-Fallback** (`emergent.py:57-96`, alphabetical 3-skill cluster) | **3/3 real** in `.agents/skills/*/SKILL.md`: `architecture-deepening-workflow` (2 scripts), `hf-doc-builder-architect` (2 scripts), `monolith-decomposition-engine` (2 scripts). | **0/2 consecutive pairs linked (0%)**:<br>• `architecture-deepening-workflow` $\to$ `hf-doc-builder-architect` (`none`)<br>• `hf-doc-builder-architect` $\to$ `monolith-decomposition-engine` (`none`). In reality, `architecture-deepening-workflow` $\leftrightarrow$ `monolith-decomposition-engine` are directly linked (`REQUIRES` both ways), but alphabetical sort wedged `hf-doc-builder-architect` (`h` between `a` and `m`) in the middle! | **Partially Achievable if Reordered**. `architecture-deepening-workflow` $\to$ `monolith-decomposition-engine` $\to$ `hf-doc-builder-architect` is a sensible refactor-then-document chain, but the alphabetical order breaks the `a` $\leftrightarrow$ `m` edge. | **Tier B (Alphabetical wedge broke real `a` $\leftrightarrow$ `m` edge)** |
| **14** | **`[08] cap_synth_cluster_08_mantis_security_review`** (`cluster_08_mantis_security_review`) | **Synth-Fallback** (`emergent.py:57-96`, alphabetical `members[:5]`) | **5/5 real** in `.agents/skills/*/SKILL.md`: `ai-red-teaming-architect` (2 scripts), `differential-facet-verifier` (2 scripts), `ethical-hacker-networking` (2 scripts), `mantis-security-review` (2 scripts), `rea-reverse-engineering` (1 script). | **2/4 pairs linked (50%)**:<br>• `ai-red-teaming-architect` $\to$ `differential-facet-verifier` (`none`)<br>• `differential-facet-verifier` $\to$ `ethical-hacker-networking` (`none`)<br>• `ethical-hacker-networking` $\leftarrow$ `mantis-security-review` (`rev:['REQUIRES']`)<br>• `mantis-security-review` $\to$ `rea-reverse-engineering` (`fwd:['REQUIRES']`). | **No as a single 5-step pipeline**. While all 5 have local scripts, alphabetical slicing concatenated 4 separate security domains (LLM PyRIT jailbreaks, binary differential facets, PCAP/TCP fault isolation, git taint review, PE/APK reverse engineering) with incompatible inputs. | **Tier B/C (Alphabetical mashup of 4 distinct security tools)** |
| **15** | **`[15] cap_synth_cluster_16_data_topology_mapper`** (`cluster_16_data_topology_mapper`) | **Synth-Fallback** (`emergent.py:57-96`, alphabetical 2-skill cluster) | **2/2 real** in `.agents/skills/*/SKILL.md`: `data-topology-mapper` (0 scripts), `questio-reflection` (0 scripts). | **0/1 pair linked (0%)**:<br>• `data-topology-mapper` $\to$ `questio-reflection` (`none`). | **No (Zero Executable Code)**. Both skills are 100% prose markdown rubrics with zero scripts, zero CLI commands, and zero kernel services. | **Tier C — `UNTESTABLE AS WRITTEN` (100% prose rubrics, 0 scripts, 0 edges)** |
| **16** | **`[20] cap_multimedia_vault_distillation`** (`cluster_cross_domain`) | **Canonical** (`patterns.py:102-110`, cross-domain append) | **4/4 real** in `.agents/skills/*/SKILL.md`: `youtube-transcript-fetcher` (2 scripts), `media-mind-forge` (3 scripts), `epistemic-isnad-audit` (0 scripts), `media-to-vault-pipeline` (1 script). | **1/3 pairs linked (33.3%)**:<br>• `youtube-transcript-fetcher` $\to$ `media-mind-forge` (`none`)<br>• `media-mind-forge` $\to$ `epistemic-isnad-audit` (`none`)<br>• `epistemic-isnad-audit` $\leftarrow$ `media-to-vault-pipeline` (`rev:['REQUIRES']`). (In the graph, `media-to-vault-pipeline` is an umbrella orchestrator that requires all 3 preceding skills). | **Untestable Offline without Network/Mock**. Step 1 (`youtube-transcript-fetcher`) requires live YouTube network extraction unless fed a pre-fetched transcript fixture, and Step 4 (`media-to-vault-pipeline`) already duplicates Steps 1–3 internally rather than consuming Step 3's output. | **Tier C — `UNTESTABLE AS WRITTEN` (Requires live YouTube network or mock; Step 4 duplicates Steps 1–3)** |
| **17** | **`[09] cap_enterprise_lakehouse_governance`** (`cluster_09_bigquery_augmented_analytics`) | **Canonical** (`patterns.py:62-70`) | **4/4 real** in `.agents/skills/*/SKILL.md`: `structured-data-scout` (2 scripts), `data-management-architect` (2 scripts), `bigquery-augmented-analytics` (2 scripts), `garf-reporting-architect` (2 scripts). | **2/3 pairs linked (66.7%)**:<br>• `structured-data-scout` $\to$ `data-management-architect` (`none`)<br>• `data-management-architect` $\leftarrow$ `bigquery-augmented-analytics` (`rev:['REQUIRES']`)<br>• `bigquery-augmented-analytics` $\leftarrow$ `garf-reporting-architect` (`rev:['REQUIRES']`). | **Untestable End-to-End Without GCP BigQuery**. While local simulation modes exist for individual plugins, the claimed outcome (*" executes BigQuery ARIMA_PLUS counterfactual analytics"*) requires a live Google Cloud BigQuery project with `ML.DETECT_ANOMALIES` / `ARIMA_PLUS` TVFs. | **Tier C — `UNTESTABLE AS WRITTEN` (Claimed BigQuery `ARIMA_PLUS` TVF outcome requires GCP cloud backend)** |
| **18** | **`[17] cap_synth_cluster_18_codebase_design`** (`cluster_18_codebase_design`) | **Synth-Fallback** (`emergent.py:57-96`, alphabetical 2-skill cluster) | **2/2 in graph, but external Pocock skills**: `codebase-design` (`plugins/external/Pocock-skills-main/skills/engineering/codebase-design/SKILL.md`, 0 scripts), `setup-ts-deep-modules` (`plugins/external/Pocock-skills-main/skills/engineering/setup-ts-deep-modules/SKILL.md`, 0 scripts, **`disable-model-invocation: true`**). | **1/1 pair linked (100%)**:<br>• `codebase-design` $\leftarrow$ `setup-ts-deep-modules` (`rev:['REQUIRES']`). | **No**. Both are external Pocock markdown prompts with zero scripts; `setup-ts-deep-modules` sets `disable-model-invocation: true` and targets TypeScript repositories using `dependency-cruiser` (Brain Harness is Python). | **Tier C — `UNTESTABLE AS WRITTEN` (`disable-model-invocation: true` + TypeScript-only target)** |
| **19** | **`[01] cap_synth_cluster_01_gemini_vercel_streaming_chatbot`** (`cluster_01_gemini_vercel_streaming_chatbot`) | **Synth-Fallback** (`emergent.py:57-96`, alphabetical `members[:5]`) | **5/5 real** in `.agents/skills/*/SKILL.md`: `adversarial-agent-verifier` (2 scripts), `agent-instruction-architect` (0 scripts), `context-type-system` (2 scripts), `deterministic-validation-loop` (2 scripts), `gemini-vercel-streaming-chatbot` (2 scripts). | **0/4 pairs linked (0%)**:<br>Zero direct edges between any consecutive steps (`fwd:[]`, `rev:[]` across all 4 transitions). | **No**. Alphabetical slicing (`a` $\to$ `a` $\to$ `c` $\to$ `d` $\to$ `g`) out of a 19-skill catch-all cluster spliced unrelated capabilities together (code review + `AGENTS.md` authoring + prompt channel ledger + JSONSchema loop + Node.js Vercel chatbot). Moreover, `deterministic-validation-loop` currently fails import in `.venv` (`ModuleNotFoundError: No module named 'jsonschema'`). | **Tier C — `UNTESTABLE AS WRITTEN` (0/4 edges; arbitrary alphabetical splice across 5 unrelated domains)** |
| **20** | **`[10] cap_synth_cluster_10_ebbinghaus_memory_governor`** (`cluster_10_ebbinghaus_memory_governor`) | **Synth-Fallback** (`emergent.py:57-96`, alphabetical `members[:5]`) | **4 in `.agents/skills/`, 1 in `plugins/` only**: `ebbinghaus-memory-governor` (2 scripts), `media-mind-forge` (3 scripts), `okf-memory-governor` (4 scripts), `ontological-engineering-coach` (0 scripts), `ontology-spider` (**no `.agents/skills/` dir**; lives only at `plugins/memory_and_epistemics/ontology_spider/SKILL.md`). | **0/4 pairs linked (0%)**:<br>Zero direct edges between any consecutive steps (`fwd:[]`, `rev:[]` across all 4 transitions). | **No**. Alphabetical slice (`e` $\to$ `m` $\to$ `o` $\to$ `o` $\to$ `o`) chains working-memory decay $\to$ video transcript distillation $\to$ OKF git memory $\to$ prose ontology coaching $\to$ HTTP dataset spider with zero shared state or data handoff. | **Tier C — `UNTESTABLE AS WRITTEN` (0/4 edges; alphabetical mashup; `ontology-spider` missing from `.agents/skills/`)** |
| **21** | **`[05] cap_synth_cluster_05_external_repo_bridge_forge`** (`cluster_05_external_repo_bridge_forge`) | **Synth-Fallback** (`emergent.py:57-96`, alphabetical `members[:5]`) | **5/5 real** in `.agents/skills/*/SKILL.md`: `agent-desktop-operator` (1 script), `agent-reach-browser-bridge` (2 scripts), `ai-file-analysis-agent` (2 scripts), `book-to-skill-forge` (0 scripts), `cellcog-multimodal` (0 scripts). | **0/4 pairs linked (0%)**:<br>Zero direct edges between any consecutive steps (`fwd:[]`, `rev:[]` across all 4 transitions). Ironically, the capability is named after `external-repo-bridge-forge`, which isn't even in `recommended_pipeline` because `members[:5]` only took `a`, `a`, `a`, `b`, `c`! | **No**. Alphabetical slice chains desktop GUI accessibility snapshots $\to$ browser envelope formatting $\to$ PDF file analysis $\to$ prose book-to-skill rubric $\to$ external CellCog multimodal API (requiring paid `CELLCOG_API_KEY`). | **Tier C — `UNTESTABLE AS WRITTEN` (0/4 edges; namesake skill excluded by `members[:5]`; requires external `CellCog` API)** |
| **22** | **`[02] cap_synth_cluster_02_ask_matt`** (`cluster_02_ask_matt`) | **Synth-Fallback** (`emergent.py:57-96`, alphabetical `members[:5]`) | **5/5 external Pocock skills** in `plugins/external/Pocock-skills-main/skills/`: `ask-matt` (**`disable-model-invocation: true`**), `code-review`, `diagnosing-bugs`, `domain-modeling`, `grill-me` (**`disable-model-invocation: true`**). Zero scripts. | **1/4 pairs linked (25%)**:<br>• `ask-matt` $\to$ `code-review` (`fwd:['REQUIRES']`, because `ask-matt` is a router table listing all Pocock skills)<br>• Remaining 3 transitions have `0` edges. | **No**. All 5 steps are external Pocock interactive human prompts with zero executable scripts, and both Step 1 (`ask-matt`) and Step 5 (`grill-me`) set `disable-model-invocation: true` (relentless human interview). | **Tier C — `UNTESTABLE AS WRITTEN` (`disable-model-invocation: true` human interview prompts; 0 scripts)** |
| **23** | **`[14] cap_synth_cluster_15_writing_beats`** (`cluster_15_writing_beats`) | **Synth-Fallback** (`emergent.py:57-96`, alphabetical 3-skill cluster) | **3/3 external Pocock `in-progress` skills** in `plugins/external/Pocock-skills-main/skills/in-progress/`: `writing-beats`, `writing-fragments`, `writing-shape`. **All 3 set `disable-model-invocation: true`** and have 0 scripts. | **0/2 pairs linked (0%)**:<br>Zero edges (`fwd:[]`, `rev:[]`). Worse, alphabetical sorting puts `writing-beats` (*"Writing, exploit — assemble raw material into a journey of beats"*) **before** `writing-fragments` (*"Writing, explore — mine raw fragments, no structure yet"*), inverting the explore $\to$ exploit authoring order! | **No**. All 3 skills are unfinished (`in-progress`) human-only writing prompts with `disable-model-invocation: true`, zero scripts, zero edges, and inverted alphabetical step ordering. | **Tier C — `UNTESTABLE AS WRITTEN` (All 3 `disable-model-invocation: true`, 0 scripts, 0 edges, inverted order)** |

---

### 1.4 Operational Definition of `"Works"` for an Emergent Macro-Capability

A claimed macro-capability in `reports/cluster_analysis_data.json` **works** operationally if and only if all four of the following criteria hold under automated, hermetic test execution (`pytest` in `tmp_path` with zero human intervention and zero unmocked external network calls):

1. **Executable Skill Resolution (Zero Human-Only Gates)**: Every skill $s_k \in \text{recommended\_pipeline}$ resolves either to an importable kernel service (`ServiceKey[T]` in `src/harness/services/`), a deterministic Python CLI script in `.agents/skills/<s_k>/scripts/*.py`, or a programmatic stage inside the adjacent skill's engine — with **zero** steps marked `disable-model-invocation: true` and **zero** steps requiring an interactive human interview (`grill-me`, `ask-matt`).
2. **Typed Data Handoff Across Consecutive Seams**: For every consecutive pair $(s_k, s_{k+1})$, the structured output artifact or JSON payload produced by $s_k$ (or the workspace state mutated by $s_k$) is consumed as a valid input by $s_{k+1}$ without manual editing or schema translation failures.
3. **Non-Arbitrary Dependency Alignment**: Every consecutive pair $(s_k, s_{k+1})$ reflects a genuine topological producer $\to$ consumer or prerequisite relationship (backed by a directed `REQUIRES` / `PRECEDES` / `FEEDS` edge in `_GRAPH_INSTANCE`), rather than an alphabetical `members[:5]` coincidence.
4. **Deterministic End-to-End Outcome Contract**: Executing the full pipeline $s_1 \to s_2 \to \dots \to s_n$ on a seeded broken/drifted fixture repository deterministically transitions the fixture from a failing state to a verified passing state (or emits a machine-verifiable diagnostic report flagging the exact seeded defects), with verifiable pre-conditions and post-conditions.

---

### 1.5 Trial Specification for Rank #1: `cap_context_anti_rot_governance` (`[06]`)

- **Capability ID**: `cap_context_anti_rot_governance` (`reports/cluster_analysis_data.json:1224-1242`)
- **Cluster**: `cluster_06_codebase_context_governor` (`reports/cluster_analysis_data.json:459-477`)
- **Declared Pipeline (`4` steps)**:
  1. `codebase-context-governor` (`.agents/skills/codebase-context-governor/SKILL.md`, script: `.agents/skills/codebase-context-governor/scripts/context_governance_driver.py`, kernel service: `src/harness/services/codebase_context/governor.py`)
  2. `context-anti-rot-sync` (`.agents/skills/context-anti-rot-sync/SKILL.md`, scripts: `.agents/skills/context-anti-rot-sync/scripts/context_sync_cli.py`, `context_sync_engine.py`)
  3. `agent-instruction-architect` (`.agents/skills/agent-instruction-architect/SKILL.md`, enforced programmatically by Stage 1 `ContextGovernor.audit_smells()` in `src/harness/services/codebase_context/governor.py:21-78` and `ContextSyncEngine.audit()` in `.agents/skills/context-anti-rot-sync/scripts/context_sync_engine.py`)
  4. `codebase-context-architect` (`.agents/skills/codebase-context-architect/SKILL.md`, scripts: `.agents/skills/codebase-context-architect/scripts/sync_context.py`, `context_linter.py`, `codebase_context_engine.py`, kernel service: `src/harness/services/codebase_context/linter.py`, `synchronizer.py`)
- **Why Rank #1**:
  - 4/4 skills exist in `.agents/skills/*/SKILL.md`.
  - 3/3 consecutive pairs have real `REQUIRES` edges in `_GRAPH_INSTANCE`.
  - 100% offline, deterministic, and fast (<1s total runtime in `tmp_path`).
  - Directly tests a real standing failure on the Brain Harness repository itself (`harness context govern --root .` and `harness context lint --root .` currently fail on `.github/copilot-instructions.md` sync drift and 19 broken inline path/script references!).

#### Exact Inputs (Seeded Fixture in `tmp_path`)

Create an isolated temporary repository directory `repo_dir = tmp_path / "trial_repo"` containing:

1. `AGENTS.md` (155 lines — intentionally exceeding the Rule 11 `< 150` line ceiling by 5 lines, containing 1 raw lint-leakage line `"ERROR: E501 line too long"`, 1 valid path reference `` `src/app.py` ``, and 1 broken path reference `` `src/ghost_module.py` ``).
2. `CLAUDE.md` containing a stale header `"Generated from AGENTS.md"` **without** the required `@AGENTS.md` import pointer.
3. `.github/copilot-instructions.md` containing `"Generated from AGENTS.md"` with stale body text that does not match `AGENTS.md`.
4. `package.json` defining `{"scripts": {"test": "pytest"}}` while `docs/guide.md` references non-existent script `` `npm run build` ``.
5. `src/app.py` (empty valid file: `"""App module."""\n`).

#### Exact Step-by-Step Trial Procedure

| Step | Skill Invoked | Exact Command / Entrypoint | Input Consumed | Output / Mutation Produced |
| :--- | :--- | :--- | :--- | :--- |
| **Step 1 (Pre-Audit & Triage)** | `codebase-context-governor` | `python .agents/skills/codebase-context-governor/scripts/context_governance_driver.py --root <repo_dir> --complexity 0.80 --json` (or `harness context govern --root <repo_dir> --complexity 0.80 --json`) | Seeded `repo_dir` (`AGENTS.md`, `CLAUDE.md`, `.github/copilot-instructions.md`, `docs/guide.md`, `package.json`) | JSON `ContextGovernanceReport` (`governor.py:154-177`):<br>• `passed == False`<br>• `recommended_tier == "High"` (since complexity $0.80 \ge 0.75$)<br>• Stage 1 (`Context Rot & Smell Auditing`): `passed == False` with 2 `violations` (`Instruction Line Budget` at line 155, `Lint Leakage Guard`)<br>• Stage 3 (`SSOT Synchronization`): `passed == False` (`Sync drift detected`)<br>• Stage 4 (`Automated CI Linter Enforcement`): `passed == False` (`problems_count >= 2` for `src/ghost_module.py` and `npm run build`). |
| **Step 2 (Anti-Rot Prune & Rule 11 Enforcement)** | `context-anti-rot-sync` + `agent-instruction-architect` | `python .agents/skills/context-anti-rot-sync/scripts/context_sync_cli.py clean --root <repo_dir> --target AGENTS.md` followed by `audit --root <repo_dir>` (and pruning the broken `` `src/ghost_module.py` `` / `` `npm run build` `` references flagged in Step 1) | `AGENTS.md` (155 lines with lint leakage) + Step 1 violation manifest | Prunes lint-leakage lines and compresses `AGENTS.md` to $\le 150$ lines with explicit execution seams and negative boundaries (`agent-instruction-architect` contract), and removes or fixes the 2 broken path/script spans. |
| **Step 3 (Downstream SSOT Synchronization)** | `codebase-context-architect` (`sync_context.py`) | `python .agents/skills/codebase-context-architect/scripts/sync_context.py --root <repo_dir> --source AGENTS.md` (or `harness context sync --root <repo_dir>`) | Cleaned `AGENTS.md` from Step 2 | Rewrites `CLAUDE.md` (injecting `@AGENTS.md` pointer + `DEFAULT_CLAUDE_EXTRAS`) and `.github/copilot-instructions.md` (mirroring canonical `AGENTS.md` with `BANNER_TEMPLATE`). Exit code `0`. |
| **Step 4 (CI Linter & Post-Governance Verification Gate)** | `codebase-context-architect` (`context_linter.py`) + `codebase-context-governor` | 1. `python .agents/skills/codebase-context-architect/scripts/context_linter.py --root <repo_dir> --json`<br>2. `harness context govern --root <repo_dir> --complexity 0.80 --json` | Synchronized `repo_dir` from Step 3 | 1. `ContextLintReport`: `passed == True`, `problems_count == 0`.<br>2. `ContextGovernanceReport`: `passed == True`, `passed_stages_count == 5`, `violations == []`. |

#### Pass / Fail Evidence Criteria

- **PASS**:
  1. Step 1 JSON output records `passed is False`, `Stage 1 passed is False` (catching both the $>150$-line violation and the lint-leakage line), `Stage 3 passed is False` (catching sync drift), and `Stage 4 passed is False` (catching `src/ghost_module.py` and `npm run build`).
  2. Step 2 reduces `AGENTS.md` line count to $< 150$ and eliminates all `Lint Leakage Guard` violations.
  3. Step 3 exits `0` and updates `CLAUDE.md` (containing `@AGENTS.md`) and `.github/copilot-instructions.md` (matching `AGENTS.md` prefix).
  4. Step 4 `context_linter.py --json` returns `{"passed": true, "problems_count": 0}` and `harness context govern --json` returns `{"passed": true, "passed_stages_count": 5, "total_stages": 5, "violations": []}`.
- **FAIL**:
  - Any step raises an unhandled exception or non-zero exit code on expected-pass inputs; OR
  - Step 1 fails to detect any of the 4 seeded defects (`>150` lines, lint leakage, SSOT drift, broken path/script); OR
  - Step 2's `clean` subcommand leaves `AGENTS.md` $> 150$ lines or fails to strip lint leakage without manual intervention; OR
  - Step 4 reports `passed: false` or `problems_count > 0` after Steps 2–3 complete.

---

## Part II — Brief 2: Fresh Analysis of Standing Gaps at `HEAD` (`fe491ad`)

### 2.1 Ground-Truth Repository Census at `fe491ad` (2026-11-05)

Before evaluating the standing gaps, the live counts on disk at `fe491ad` (verified via `.venv\Scripts\python.exe`) are:

| Metric | Nov 1 Count | Nov 3 Count (`5ff7ba5` / `1915`) | Current `HEAD` (`fe491ad`) | Delta Since Nov 3 & Exact Cause |
| :--- | :--- | :--- | :--- | :--- |
| **Canonical Plugins** (`plugins/<category>/<name>/plugin.json`, excl. `external`) | 135 | 138 | **140** | **+2**: `plugins/memory_and_epistemics/ontology_spider` (`3f86400`) and `plugins/integration_and_io/agent_desktop` (`3783c04`) |
| **External Plugin Bundles** (`plugins/external/*/plugin.json`) | 1 | 1 | **1** | `plugins/external/Pocock-skills-main/plugin.json` (35 entrypoints) |
| **Declared Tool Entrypoints** | 629 | 641 | **650** | **+9**: 615 canonical + 35 external (`ontology_spider` added 4; `agent_desktop` added 5) |
| **Workspace Skills** (`.agents/skills/*/SKILL.md` + `CARD.md`) | 100 | 103 | **104** | **+1**: `.agents/skills/agent-desktop-operator/` (`3783c04`) |
| **Skill Knowledge Graph Nodes** (`index_skill_catalog()`) | 135 | 138 | **140** | **+2**: 104 workspace skills + 1 plugin-only skill (`ontology-spider`) + 35 Pocock skills = 140 nodes, **1,751 edges** |
| **Knowledge Vault Items** (`.harness/knowledge/*/metadata.json`) | 282 | 301 | **309** | **+8**: `ki_agent_desktop_*` items added in `3783c04` (`303 ACTIVE`, `3 PROMOTED`, `3 DEMOTED`) |
| **Knowledge Graph Census** (`harness knowledge stats`) | — | 417 entities / 188 edges | **451 entities / 218 edges** | 309 KIs + 142 external entities (`116 path`, `8 plugin`, `17 skill`, `1 source`); 27 asserted + 191 derived edges |

---

### 2.2 Re-Verification of the 9 Standing Gaps from Nov 1 + Soft §12 Leftovers

#### Summary Status Matrix

| # | Standing Gap (from Nov 1 / Brief 2 Prompt) | Status at `fe491ad` | Verdict Summary & Primary Evidence |
| :--- | :--- | :--- | :--- |
| **1** | **Gephi never actually opened** | **OPEN (Blocked on Human Desktop GUI)** | Unticked (`[ ]`) in `plan archive/Big fix plan-2026-11-03-0950-EST.md:567` (`0438b90`), but still ticked (`[x]`) in `plan archive/Post-knowledge-graph analysis and plan-2026-10-31-0808-EDT.md:235` and `plan archive/Follow-up analysis and plan-2026-11-03-0715-EST.md:179,200`. Also, `.harness/graph/knowledge_graph.gexf` on disk is stale (`417 nodes, 188 edges` from the 301-KI snapshot instead of `451 nodes, 218 edges` for 309 KIs). |
| **2** | **Dock enforcement (`shell=True`, digest-only approval, unverified tools, generic SHA drift, `vault-stats`)** | **PARTIALLY CLOSED / 2 LIVE BUGS IN `dock.yaml`** | Nov 3 (`716bb49`, `5ff7ba5`, `a05ecd9`) added full command display before approval (`commands/dock.py:149-160`), deterministic SHA-256 synthesis for generic docks (`services/dock.py:433-457`), `"declared_unverified"` labeling (`commands/dock.py:214-225`), and honest docs (`docs/how-to/agent-dock.md:155,175-177`). `subprocess.run(..., shell=True)` with regex filtering (`services/dock.py:207-264,874`) remains by design. **However, `harness dock run brain-harness vault-stats` is broken right now** (`dock.yaml:34-36`): `expected_output: "Active Knowledge Items"` never matches `knowledge stats` stdout (`"📊 Knowledge Graph Census Statistics"`), and `python src/harness/cli.py` fails without `PYTHONPATH=.`. |
| **3** | **Joint-query KI side hand-rolled, not the real KI service** | **CLOSED BY RECORDED DECISION (1 Minor Status Bug)** | `src/harness/services/skill_graph/joint_query.py:5-12` documents the explicit architectural decision (direct `metadata.json` read for sub-5ms CLI cold-start and zero SQLite lock contention per Rules 22 & 40), and lines `113-124` prioritize typed `became_skill`/`distilled_from` edges (`5ff7ba5`). **Residual bug**: `joint_query.py:57-61` reads `isnad.get("status", "VERIFIED")` instead of `meta.get("status", "ACTIVE")`, reporting `"VERIFIED"` instead of lifecycle state (`ACTIVE`/`PROMOTED`/`DEMOTED`) and failing to filter `DEMOTED`/`ARCHIVED` items. |
| **4** | **No lifecycle transition on disk yet** | **CLOSED ON DISK (`5ff7ba5`), WITH DATA CAVEAT** | `.harness/knowledge/*/metadata.json` now has **3 `PROMOTED`** (`ki_20260830_django_05`, `ki_self_20260902_02`, `ki_self_20260917_02`) and **3 `DEMOTED`** (`ki_20260824_repo_03`, `ki_20260830_django_01`, `ki_20260831_em3_02`) alongside **303 `ACTIVE`**. Caveat: all 6 transitions occurred at `2026-11-03T17:29:32` via seeded `retrieval_count` counters in `5ff7ba5`; the 8 new `agent_desktop` items (`3783c04`) have `retrieval_count: 0`. |
| **5** | **Drift gate vs canonical counts** | **CLOSED FOR ROOT `README.md`, OPEN IN 5 SECONDARY DOCS + GEXF** | `tests/test_plugin_integration_drift.py` (21/21 passing) dynamically checks `140` canonical plugins against root `README.md` (`82ca296`). **However**, `USER_MANUAL.md:77-80` (`138` plugins, `641` entrypoints, `103` skills, `282` KIs), `plugins/README.md:15` (`135` plugins), `.agents/skills/README.md:3,31,126` (`103` / `95` skills), `docs/reference/knowledge-graph-visual-brief.md:5,15,19,29` (`301` KIs, `417` nodes, `188` edges), and `.harness/graph/knowledge_graph.gexf` (`417` nodes, `188` edges) are all stale because `test_plugin_integration_drift.py` only checks root `README.md`. |
| **6** | **Hyperframes manifest invalid JSON** | **CLOSED (`a05ecd9` / `5ff7ba5`)** | `plugins/developer_tooling/hyperframes_renderer/plugin.json` is valid JSON (`json.loads` passes across all 141 `plugin.json` files). **New finding**: `PluginValidator` (`AST Function Inspection`) fails on **2 plugins** whose `main.py` lacks top-level/method `def` matching `plugin.json` entrypoints: `headroom_context_optimizer` (5 lambda-registered tools) and `reconstruction_obligation_ledger` (`rol_verify_ledger` vs `rol_verify_closure`). |
| **7** | **Vault items missing `status` and the forge flow** | **CLOSED (`a05ecd9` / `4e0e562`)** | All **309/309** `.harness/knowledge/*/metadata.json` files (including the 8 new `3783c04` items) have valid `status`, `category`, `created_at`, `retrieval_count`, and `edges` with 0 schema errors and 0 Windows absolute paths. `.agents/skills/repo-triad-forge/scripts/triad_pipeline.py:210-228` emits all required fields. |
| **8** | **`integrated-toolkits.md` REA row** | **CLOSED FOR REA, OPEN FOR `agent_reach_bridge` + 2 MISSING PLUGINS** | `docs/reference/integrated-toolkits.md:9` (`service.rea_toolkit`) is accurate and guarded by `tests/test_cli_content_drift.py`. **However**: (a) `docs/reference/integrated-toolkits.md:23` AND `CONTEXT-MAP.md:184,198` still claim `"Multi-platform web extraction, stealth CloakBrowser CDP sessions"` for `agent_reach_bridge` (violating Track 3 of the Nov 3 Big Fix `725ee36`); (b) `ontology_spider` (`3f86400`) and `agent_desktop` (`3783c04`) are missing from `integrated-toolkits.md` (and `ontology_spider` is missing from `CONTEXT-MAP.md`). |
| **9** | **Plugin-integration & REA plans checkbox state** | **CLOSED (`a05ecd9` / `d485973`), WITH UNCOMMITTED GIT MOVE** | `plan archive/Plugin integration plan-2026-10-31-0925-EDT.md` and `plan archive/REA toolkit plan-2026-10-31-0849-EDT.md` are 100% ticked with architectural notes. **Working-tree gap**: `git status --short` has an uncommitted move (`D`/`??`) of `Follow-up fixes plan-2026-11-03-1325-EST.md` and `Plugin portability fixes plan-2026-11-03-1915-EST.md` into `plan archive/`. |
| **10** | **Soft §12 Leftovers + Fast-Model Backlog (`context lint`, `pytest` collection, git-service, deps, dependabot)** | **OPEN (6 Concrete Findings)** | 1. `harness context lint --root .` fails with **19 broken path/script problems** (`src/harness/*/README.md`, `docs/**/*.md`), and `harness context govern --root .` fails on Stage 3 (`.github/copilot-instructions.md` drift) + Stage 4 (19 lint problems) while printing an empty violation list (`commands/context.py:343-346`).<br>2. Full `pytest` collection fails with **4 `ImportError`s** (`jsonschema` missing in 2 tests, `numpy` missing in 2 tests), and `rich>=13.7.0` is in `pyproject.toml:23` but **absent from `uv.lock`**.<br>3. **Git-service checkpointing**: `StepExecutionEngine` (`react/engine.py:76` $\to$ `react/transactions.py:32`) resolves `context.optional(FILESYSTEM_GIT_KEY)` (`None` unless `FilesystemGitPlugin` is loaded), and `transactions.py:74` passes `scoped_paths=None` whenever a tool lacks a `path`/`file_path`/`target_file` argument — falling back to repo-wide `git add -A` / `git restore .` / `git clean -fd`!<br>4. **13 plugin `requirements.txt`** files are unpinned (`4` are 0-byte empty `hermes_*` files; `4` `rea_*` have bare `structlog`).<br>5. **No `.github/dependabot.yml`**. |

---

### 2.3 Ranked Findings with File-Level Evidence

#### Finding 1 (P0 — Live CLI Bug): `harness dock run brain-harness vault-stats` Always Fails (`dock.yaml` Output Mismatch + `PYTHONPATH` Trap)

- **Evidence**:
  - `dock.yaml:32-36` (and `docs/how-to/agent-dock.md:59-63`) defines the `vault-stats` procedure as:

    ```yaml
    vault-stats:
      description: Display epistemic knowledge vault and graph statistics
      steps:
        - command: python src/harness/cli.py knowledge stats
          timeout_seconds: 30
          expected_output: "Active Knowledge Items"
    ```

  - However, `src/harness/commands/reflection.py:807-825` (`knowledge_stats_cmd`) prints:

    ```text
    📊 Knowledge Graph Census Statistics
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    Total Entities:        451 (309 KIs, 142 external)
    ```

    It **never** prints the substring `"Active Knowledge Items"`. Consequently, `DefaultDockService.run_procedure()` (`src/harness/services/dock.py:894-898`) fails `if step.expected_output and step.expected_output not in proc.stdout:` on every single run (`status="failed"`, `"Expected output substring 'Active Knowledge Items' not found in stdout"`).
  - Second, `dock.yaml:34` and `dock.yaml:49` invoke `python src/harness/cli.py ...` instead of `python -m harness.cli ...`. When Python executes a script by file path (`src/harness/cli.py`), `sys.path[0]` is `src/harness/` (not the workspace root or `src/`), which raises `ModuleNotFoundError: No module named 'plugins'` unless `PYTHONPATH` is externally pre-populated.
- **Fast-Model Fix**:
  - In `dock.yaml:34,36` and `docs/how-to/agent-dock.md:61,63`, change `expected_output: "Active Knowledge Items"` to `expected_output: "Knowledge Graph Census Statistics"` (or `"Total Entities:"`), and change `python src/harness/cli.py` to `python -m harness.cli` at `dock.yaml:34,49`.

#### Finding 2 (P1 — Test Suite Integrity): Unfiltered `pytest` Collection Fails with 4 `ImportError`s & `uv.lock` Omits `rich`

- **Evidence**:
  - Running `.\.venv\Scripts\python.exe -m pytest` (full collection of 2,935 items) halts during collection with **4 `ModuleNotFoundError`s**:
    1. `tests/skills/test_deterministic_validation_loop.py:5` — `from jsonschema import validate, ValidationError` (`ModuleNotFoundError: No module named 'jsonschema'`)
    2. `tests/test_deterministic_validation_deepened.py:25` $\to$ `.agents/skills/deterministic-validation-loop/scripts/validation_loop_engine.py:19` — `from jsonschema import ValidationError` (`ModuleNotFoundError: No module named 'jsonschema'`)
    3. `tests/test_neural_network_from_scratch.py:14` — `import numpy as np` (`ModuleNotFoundError: No module named 'numpy'`)
    4. `tests/test_uncertainty_aware_deepened.py:34` $\to$ `.agents/skills/uncertainty-aware-ai-architect/scripts/uncertainty_guard_engine.py:23` — `import numpy as np` (`ModuleNotFoundError: No module named 'numpy'`)
  - Neither `jsonschema` nor `numpy` is declared in `pyproject.toml:18-37`, and `pyproject.toml:23` declares `"rich>=13.7.0"` in `[project.dependencies]`, yet `rich` is completely absent from `uv.lock`.
- **Fast-Model Fix**:
  - Either add `jsonschema>=4.20.0` and `numpy>=1.26.0` to `[project.optional-dependencies].dev` in `pyproject.toml` and run `uv lock && uv sync --extra dev`, OR guard those 4 test files with `pytest.importorskip("jsonschema")` / `pytest.importorskip("numpy")` so full `pytest` collection succeeds in minimal environments.

#### Finding 3 (P1 — Context Governance & "22-Item Lint Cleanup"): `harness context lint` Fails with 19 Stale Path/Script Spans + `.github/copilot-instructions.md` Drift + 2 Invalid Plugin AST Signatures

- **Evidence**:
  - Running `harness context lint --root .` (`src/harness/services/codebase_context/linter.py:65-183`) executes **22 checks** (3 token-budget checks + 19 failing path/script checks) and exits `1` with **19 problems**:
    - `src/harness/commands/README.md`: non-existent `` `calibrator.py` ``, `` `self_eval.py` ``, `` `data.py` `` (3)
    - `src/harness/ingestion/README.md`: non-existent `` `inspector.py` `` (1)
    - `src/harness/kernel/README.md`: non-existent `` `runtime.py` `` (1)
    - `src/harness/mcp/README.md`: non-existent `` `server.py` `` (1)
    - `src/harness/services/README.md`: non-existent `` `skill_parser.py` ``, `` `storage.py` ``, `` `brain_artifact_miner.py` ``, `` `paperless_ngx.py` `` (4)
    - `src/harness/ui/README.md`: non-existent `` `frontend/dist` `` and script not in `package.json`: `` `npm run build` `` (2)
    - `docs/explanation/agent-execution-graphs.md`: non-existent `` `src/harness/agent/session.py` `` (1)
    - `docs/how-to/explore-knowledge-graph.md`: non-existent `` `outputs/knowledge_graph.gexf` `` (1)
    - `docs/reference/trust_and_isolation.md`: non-existent `` `calibrator/engine_adapter.py` ``, `` `tools/list` ``, `` `tools/call` ``, `` `.harness/tool_state.json` ``, `` `r_editor_service.py` `` (5 — where `tools/list` and `tools/call` are MCP JSON-RPC method names misclassified as filesystem paths by `SemanticPathClassifier.is_api_route()` in `src/harness/services/codebase_context/classifier.py`, and `.harness/tool_state.json` is an ephemeral runtime state path).
  - Running `harness context govern --root .` exits `1` because Stage 3 (`SSOT Synchronization`) fails (`[DRIFT] .github/copilot-instructions.md differs from generated canonical source`) and Stage 4 (`Automated CI Linter Enforcement`) fails with the 19 problems above — totaling **20 context governance failures** — yet `src/harness/commands/context.py:343-346` only iterates `for v in report.violations:` (which holds only Stage 1 smell violations), printing `[FAIL] Context Governance Violations Detected:` with **zero detail lines**!
  - Adding the **2 `PluginValidator` AST Function Inspection failures** discovered in our full 140-plugin sweep brings the exact repo-wide lint/validator cleanup count to **22 items** (`19` context path/script problems + `1` `.github/copilot-instructions.md` sync drift + `2` `PluginValidator` AST entrypoint mismatches):
    1. `plugins/memory_and_epistemics/headroom_context_optimizer/main.py:397-440` registers its 5 tools via `lambda` in `on_enable()` without top-level/method `def headroom_compress_content`, `headroom_dedup_turns`, `headroom_detect_cache_drift`, `headroom_compact_thinking`, `headroom_savings_metrics` required by `PluginValidator` (`src/harness/plugins/validator.py`).
    2. `plugins/security_and_forensics/reconstruction_obligation_ledger/main.py:123-130` defines `verify_ledger` and `rol_verify_closure`, but `plugin.json:27` declares `rol_verify_ledger`.

#### Finding 4 (P1 — Transaction Safety & Git-Service Decision): Unscoped Tool Calls in `invoke_tool_transactional` Can Still Trigger Repo-Wide `git add -A` / `git clean -fd`

- **Evidence**:
  - In `src/harness/agent/react/engine.py:76`, `StepExecutionEngine` wraps every tool execution in `invoke_tool_transactional()` (`src/harness/agent/react/transactions.py:22-119`).
  - `transactions.py:32` calls `git_svc = self.context.optional(FILESYSTEM_GIT_KEY)`.
    - **Decision question answered from code**: In a standalone `ReActEngine` where `FilesystemGitPlugin` (`plugins/software_engineering/filesystem_git/main.py`) is not loaded into `ServiceContext`, `git_svc` is `None` (so checkpointing is inactive by default in unit/headless `ReActEngine` runs and active in `DefaultDockService.run_procedure()` at `src/harness/services/dock.py:543,917` where `write_path: true` explicitly instantiates `DefaultFilesystemGitService`).
    - **Critical safety bug when `FILESYSTEM_GIT_KEY` IS provided**: `transactions.py:69-74` extracts:

      ```python
      target_file_path = action_input.get("path") or action_input.get("file_path") or action_input.get("target_file")
      scoped_paths = [str(target_file_path)] if target_file_path else None
      ```

      and passes `paths=scoped_paths` to `git_svc.commit_transaction(..., paths=scoped_paths)` (`transactions.py:92`) and `git_svc.rollback_transaction(..., paths=scoped_paths)` (`transactions.py:101,115`).
    - Look at `src/harness/services/filesystem_git.py:157-164` and `189-196`: when `paths` is `None`, `commit_transaction` executes `git add -A` (staging the entire working tree!), and `rollback_transaction` executes `git restore .` and `git clean -fd` (wiping all untracked files across the entire repository!) whenever a tool with a different parameter name (e.g., `repo_dir`, `output_dir`, `target_dir`, or a read-only tool that returns `"status": "error"`) fails!
- **Remediation**:
  - Document the architectural decision (checkpointing is opt-in via `FILESYSTEM_GIT_KEY` in `ReActEngine` and mandatory for `write_path: true` in `DefaultDockService`), AND harden `src/harness/agent/react/transactions.py:74-116` so that if `scoped_paths is None`, `invoke_tool_transactional` **never** calls unscoped `commit_transaction(paths=None)` or `rollback_transaction(paths=None)` on a shared working tree.

#### Finding 5 (P2 — Count & Artifact Drift After Nov 4 Commits `3f86400` & `3783c04`): 5 Secondary Docs + `.harness/graph/knowledge_graph.gexf` Are Stale

- **Evidence**:
  - Commit `82ca296` updated root `README.md:14-17` (`140` plugins, `650` entrypoints, `104` workspace skills / `140` graph nodes, `309` KIs) because `tests/test_plugin_integration_drift.py` only inspects root `README.md`.
  - The following files were left behind with Nov 1 or Nov 3 numbers:
    1. `USER_MANUAL.md:77-80`: says `138 Canonical Harness Plugins`, `641 tool entrypoints`, `103 Workspace Skills packages (138 Skill Graph nodes)`, `282 Verified Knowledge Items`.
    2. `plugins/README.md:15`: says `135 Plugins`.
    3. `.agents/skills/README.md:3,31,126`: says `103 production-grade AI agent skills`, `103 Deep-Module Skills`, and `Authoritative 95-Skill Catalog`.
    4. `docs/reference/knowledge-graph-visual-brief.md:5,15,19,29`: says `301 Knowledge Items`, `Total Nodes: 417`, `Total Edges: 188 (27 Asserted, 161 Derived)`.
    5. `.harness/graph/knowledge_graph.gexf`: on-disk XML has `417` `<node>` elements and `188` `<edge>` elements (missing the 8 `ki_agent_desktop_*` items and 30 new edges; live `harness knowledge stats` is `451` entities and `218` edges).
    6. `reports/skill_knowledge_graph_cluster_analysis_report.md:5`: header says `138 Skills` while its body and `reports/cluster_analysis_data.json` have `140` skills.

#### Finding 6 (P2 — Incomplete Overclaim Scrub & Missing Toolkit Rows): `agent_reach_bridge` Overclaim Survives in 2 Docs; 2 New Plugins Missing from Reference Tables

- **Evidence**:
  - In the Nov 3 Big Fix (`725ee36`, Track 3), `plugins/integration_and_io/agent_reach_bridge/plugin.json` and `.agents/skills/agent-reach-browser-bridge/SKILL.md` were scrubbed to state `"Envelope formatting only"` because no CloakBrowser or CDP client exists in the codebase.
  - However, two documentation tables were missed:
    1. `docs/reference/integrated-toolkits.md:23`: still reads `| **agent_reach_bridge** | ... | Multi-platform web extraction, stealth CloakBrowser CDP sessions, and Schema v1 envelopes |`.
    2. `CONTEXT-MAP.md:184,198`: both the plugin bullet (`line 184`) and skill bullet (`line 198`) still claim `"multi-platform web extraction, stealth CloakBrowser CDP sessions"`.
  - Additionally, `docs/reference/integrated-toolkits.md` is missing rows for the two Nov 4 plugins (`ontology_spider` from `3f86400` and `agent_desktop` from `3783c04`), and `CONTEXT-MAP.md` is missing `ontology_spider` / `headroom_context_optimizer` / `reconstruction_obligation_ledger`.

#### Finding 7 (P2 — Epistemic & Skill Graph Bugs): `joint_query.py` Reports Isnad Status Instead of Lifecycle Status; `emergent.py` Truncates Mid-Word; `indexer.py` Creates Phantom Markdown Token Targets

- **Evidence**:
  1. `src/harness/services/skill_graph/joint_query.py:57-61`:

     ```python
     isnad = meta.get("isnad") if isinstance(meta.get("isnad"), dict) else {}
     status = isnad.get("status", "VERIFIED")
     ```

     Because `isnad.status` is `"VERIFIED"`, `joint-query` never surfaces top-level `meta.get("status", "ACTIVE")` (`ACTIVE` / `PROMOTED` / `DEMOTED`) and never filters out `DEMOTED` or `ARCHIVED` items.
  2. `src/harness/services/skill_clustering/engine/emergent.py:57-96`:
     - Uses alphabetical `members[:5]` without checking graph reachability or filtering `disable-model-invocation: true` skills.
     - Slices `s1_desc[:160]` at line `77`, producing mid-word truncated sentences in 11 of 12 `cap_synth_*` capabilities.
     - Mutates `pattern["cluster_id"] = cid` in-place on `CANONICAL_EMERGENT_PATTERNS` dictionaries (`emergent.py:39`), so if two clusters match the same pattern, the second overwrites the first's `cluster_id`.
  3. `src/harness/services/skill_graph/indexer.py`: extracts inline markdown tokens as target skill names without filtering to known skill IDs in `top_in_degree`, polluting `reports/cluster_analysis_data.json:168-214` with phantom targets (`skills: 17`, `knowledge: 17`, `script: 15`, `mermaid: 15`, `dist: 15`, `head: 15`, `body: 15`, `html: 15`).

#### Finding 8 (P3 — Archive Errata, Working-Tree Hygiene & Soft §12 Dependency Hygiene)

- **Evidence**:
  1. **Uncommitted working-tree move**: `git status --short` shows `D "Follow-up fixes plan-2026-11-03-1325-EST.md"`, `D "Plugin portability fixes plan-2026-11-03-1915-EST.md"`, and untracked `?? "plan archive/Follow-up fixes plan-2026-11-03-1325-EST.md"`, `?? "plan archive/Plugin portability fixes plan-2026-11-03-1915-EST.md"`.
  2. **Gephi checkboxes in older archived plans**: Unticked in `plan archive/Big fix plan-2026-11-03-0950-EST.md:567`, but still `[x]` in `plan archive/Follow-up analysis and plan-2026-11-03-0715-EST.md:179,200` and `plan archive/Post-knowledge-graph analysis and plan-2026-10-31-0808-EDT.md:235`.
  3. **Floating plugin `requirements.txt` & empty files**: 4 `plugins/**/requirements.txt` files are 0-byte empty (`hermes_state_fts5`, `hermes_cognitive_engine`, `hermes_cron_scheduler`, `hermes_gateway_relay`), 4 `rea_*` files list bare `structlog` without version bounds, and 5 use `>=` floor bounds only.
  4. **Rule 57 leftover shim**: `.agents/skills/codebase-context-architect/scripts/engine.py` (5-line star-import shim) still uses the generic name `engine.py`.
  5. **No `.github/dependabot.yml`** and `pyproject.toml:34-35` pins `ruff==0.11.0` and `mypy==1.15.0` while `uv.lock` has `pydantic==2.13.4`, `fastapi==0.141.1`, `pytest==9.1.1` (and omits `rich`).

---

## Part III — Remediation Plan (`2026-11-05`)

### Cross-Track Dependency & Model-Tier Table

> **`[NW]`** = No-Wait / Fast-Model track (mechanical edits, lint cleanups, doc/count syncs, and version-bump trials suitable for fast execution).

| Track | Title | Tier | Depends On | Touch Surface |
| :--- | :--- | :--- | :--- | :--- |
| **Track 1 `[NW]`** | Fix `dock.yaml` `vault-stats` Expected Output & CLI Module Invocation | Fast | None | `dock.yaml`, `docs/how-to/agent-dock.md`, `tests/test_dock.py` |
| **Track 2 `[NW]`** | 22-Item Context Governance, Linter & `PluginValidator` Cleanup | Fast | None | `src/harness/*/README.md`, `docs/**/*.md`, `src/harness/services/codebase_context/classifier.py`, `src/harness/commands/context.py`, `.github/copilot-instructions.md`, `headroom_context_optimizer/main.py`, `reconstruction_obligation_ledger/main.py` |
| **Track 3 `[NW]`** | Secondary Doc Count Sync, Overclaim Scrub & `.gexf` Regeneration | Fast | Track 2 | `USER_MANUAL.md`, `plugins/README.md`, `.agents/skills/README.md`, `CONTEXT-MAP.md`, `docs/reference/integrated-toolkits.md`, `docs/reference/knowledge-graph-visual-brief.md`, `.harness/graph/knowledge_graph.gexf`, `tests/test_plugin_integration_drift.py` |
| **Track 4** | Transaction Scope Guard (`transactions.py`) & `joint_query.py` Lifecycle Status Fix | Standard | None | `src/harness/agent/react/transactions.py`, `src/harness/services/skill_graph/joint_query.py`, `tests/test_transactions.py`, `tests/test_skill_knowledge_graph.py` |
| **Track 5** | Skill Clustering & Emergent Capability Engine Hardening (Fixing Brief 1 Defects) | Standard | Track 4 | `src/harness/services/skill_clustering/engine/emergent.py`, `src/harness/services/skill_graph/indexer.py`, `reports/cluster_analysis_data.json`, `reports/skill_knowledge_graph_cluster_analysis_report.md`, `tests/test_skill_clustering.py` |
| **Track 6** | Execute Rank #1 Emergent Capability Trial (`cap_context_anti_rot_governance`) | Standard | Tracks 2, 5 | `tests/test_emergent_capability_trial.py` |
| **Track 7 `[NW]`** | Full `pytest` Collection Fix, Dependency Pinning, Version-Bump Trials & Dependabot | Fast | Tracks 1–3 | `pyproject.toml`, `uv.lock`, `.github/dependabot.yml`, `plugins/**/requirements.txt`, `plan archive/` git staging |
| **Track 8 (Human)** | Manual Gephi Desktop Visual Verification | Human GUI | Track 3 | `.harness/graph/knowledge_graph.gexf` (blocked on human desktop session; do not tick headlessly) |

---

### Track 1 `[NW]` — Fix `dock.yaml` `vault-stats` Expected Output & CLI Module Invocation

**Problem**: `harness dock run brain-harness vault-stats` fails 100% of the time because `dock.yaml:36` checks `expected_output: "Active Knowledge Items"`, whereas `harness knowledge stats` (`src/harness/commands/reflection.py:807-809`) prints `"📊 Knowledge Graph Census Statistics"` and `"Total Entities:"`. Additionally, `dock.yaml:34,49` invokes `python src/harness/cli.py` instead of `python -m harness.cli`, breaking `plugins` imports when `PYTHONPATH` is unset.

- [x] **1.1**: In `dock.yaml:34,36`, update `command: python -m harness.cli knowledge stats` and `expected_output: "Knowledge Graph Census Statistics"`.
- [x] **1.2**: In `dock.yaml:49`, update `command: python -m harness.cli verify` so all `dock.yaml` Python CLI invocations run via `-m harness.cli`.
- [x] **1.3**: In `docs/how-to/agent-dock.md:61,63`, sync the `vault-stats` snippet to match `dock.yaml`, and re-link `brain-harness` (`harness dock link . --yes`) so `.harness/dock_registry.json` updates its approved `manifest_sha256`.
- [x] **1.4 (Verification)**: Run `.\.venv\Scripts\python.exe -m harness.cli dock run brain-harness vault-stats` and assert exit code `0` and `"status": "ok"`. Add a regression test in `tests/test_dock.py` asserting that every procedure in the workspace `dock.yaml` has a valid CLI entrypoint and matching `expected_output`.

---

### Track 2 `[NW]` — 22-Item Context Governance, Linter & `PluginValidator` Cleanup

**Problem**: `harness context lint --root .` fails with 19 broken path/script references; `harness context govern --root .` fails on Stage 3 (`.github/copilot-instructions.md` sync drift) and Stage 4 while printing zero error details (`src/harness/commands/context.py:343-346`); and `PluginValidator` fails `AST Function Inspection` on 2 canonical plugins (`headroom_context_optimizer` and `reconstruction_obligation_ledger`).

- [x] **2.1 (Classifier & Linter Precision — 4 items)**: In `src/harness/services/codebase_context/classifier.py` (and `.agents/skills/codebase-context-architect/scripts/codebase_context_engine.py`), update `SemanticPathClassifier.is_api_route()` to recognize JSON-RPC protocol method spans (`tools/list`, `tools/call`, `prompts/list`, `resources/list`) and update `is_archetype_template()` (or runtime state exclusions per Rule 47) to exclude `.harness/` runtime state files (`.harness/tool_state.json`) and generated `outputs/*.gexf` examples.
- [x] **2.2 (Subpackage `README.md` & Docs Path Cleanup — 15 items)**:
  - `src/harness/commands/README.md`: replace stale `` `calibrator.py` ``, `` `self_eval.py` ``, `` `data.py` `` with actual command modules (`Verify.py`, `reflection.py`, `Data_eng.py`).
  - `src/harness/ingestion/README.md`: replace stale `` `inspector.py` `` with actual module (`repo_inspector.py` / `models.py`).
  - `src/harness/kernel/README.md`: replace stale `` `runtime.py` `` with `context.py` / `events.py`.
  - `src/harness/mcp/README.md`: replace stale `` `server.py` `` with `fastmcp_server.py` / `__init__.py`.
  - `src/harness/services/README.md`: replace stale `` `skill_parser.py` ``, `` `storage.py` ``, `` `brain_artifact_miner.py` ``, `` `paperless_ngx.py` `` with actual paths (`skill_card_parser.py`, `artifact_miners.py`, `paperless.py`).
  - `src/harness/ui/README.md`: qualify illustrative build artifacts/commands (`frontend/dist`, `npm run build`) inside fenced codeblocks or map to actual UI files.
  - `docs/explanation/agent-execution-graphs.md`: replace `` `src/harness/agent/session.py` `` with `` `src/harness/agent/session_manager.py` ``.
  - `docs/how-to/explore-knowledge-graph.md`: replace `` `outputs/knowledge_graph.gexf` `` with `` `.harness/graph/knowledge_graph.gexf` ``.
  - `docs/reference/trust_and_isolation.md`: replace shorthand `` `calibrator/engine_adapter.py` `` with `` `src/harness/services/calibrator/engine_adapter.py` `` and `` `r_editor_service.py` `` with `` `src/harness/services/r_editor_service.py` ``.
- [x] **2.3 (SSOT Sync & `context govern` CLI Output — 1 item)**:
  - Run `.\.venv\Scripts\python.exe -m harness.cli context sync --root .` so `.github/copilot-instructions.md` is synchronized with `AGENTS.md`.
  - In `src/harness/commands/context.py:343-346`, print all failing stages (`for st in report.stages: if not st.passed: ...`) alongside `report.violations` so Stage 3/4 failures are never silently swallowed on CLI stderr.
- [x] **2.4 (`PluginValidator` AST Entrypoint Parity — 2 items)**:
  - In `plugins/memory_and_epistemics/headroom_context_optimizer/main.py`, expose top-level or class methods `headroom_compress_content`, `headroom_dedup_turns`, `headroom_detect_cache_drift`, `headroom_compact_thinking`, and `headroom_savings_metrics` matching `plugin.json:24-79` and bind them in `on_enable()`.
  - In `plugins/security_and_forensics/reconstruction_obligation_ledger/main.py:129-131`, add `def rol_verify_ledger(self, *args: Any, **kwargs: Any) -> ReconstructionProof:` matching `plugin.json:27`.
- [x] **2.5 (Verification)**:
  - Run `.\.venv\Scripts\python.exe -m harness.cli context lint --root .` $\to$ assert `[PASS] Context files healthy` (`0` problems, exit `0`).
  - Run `.\.venv\Scripts\python.exe -m harness.cli context govern --root .` $\to$ assert `[PASS] Context Governance Audit Passed (5/5 stages)` (exit `0`).
  - Run `PluginValidator().validate_sync()` across all 140 canonical plugins $\to$ assert `140/140 valid` (`0` invalid).

---

### Track 3 `[NW]` — Secondary Doc Count Sync, Overclaim Scrub & `.gexf` Regeneration

**Problem**: Root `README.md` has current `fe491ad` counts (`140` plugins, `650` entrypoints, `104` skills, `309` KIs), but 5 secondary docs and `.harness/graph/knowledge_graph.gexf` still carry Nov 1 / Nov 3 counts, and `docs/reference/integrated-toolkits.md:23` + `CONTEXT-MAP.md:184,198` still contain the scrubbed `agent_reach_bridge` CloakBrowser CDP overclaim.

- [x] **3.1**: Update stale counts in:
  - `USER_MANUAL.md:77-80` (`138` $\to$ `140` plugins, `641` $\to$ `650` entrypoints, `103` $\to$ `104` skills / `140` graph nodes, `282` $\to$ `309` KIs).
  - `plugins/README.md:15` (`135` $\to$ `140` plugins).
  - `.agents/skills/README.md:3,31,126` (`103` / `95` $\to$ `104` skills).
  - `docs/reference/knowledge-graph-visual-brief.md:5,15,19,29` (`301` $\to$ `309` KIs, `417` $\to$ `451` total nodes, `188 (27 Asserted, 161 Derived)` $\to$ `218 (27 Asserted, 191 Derived)` edges).
- [x] **3.2**: Regenerate `.harness/graph/knowledge_graph.gexf` via `harness knowledge export-gexf` so the on-disk GEXF file contains all `451` nodes (`309` KIs + `142` external) and `218` edges.
- [x] **3.3**: In `docs/reference/integrated-toolkits.md:23` and `CONTEXT-MAP.md:184,198`, scrub `"Multi-platform web extraction, stealth CloakBrowser CDP sessions"` from `agent_reach_bridge` / `agent-reach-browser-bridge`, replacing with `"Multi-platform channel routing, credential scrubbing, and Schema v1 result envelopes (envelope formatting only)"`. Add rows for `ontology_spider` (`service.ontology_spider`) and `agent_desktop` (`service.agent_desktop`) to `docs/reference/integrated-toolkits.md` and `CONTEXT-MAP.md`.
- [x] **3.4 (Verification)**: Extend `tests/test_plugin_integration_drift.py` and `tests/test_cli_content_drift.py` to assert count parity across `USER_MANUAL.md`, `plugins/README.md`, and `.agents/skills/README.md`, and forbid `"CloakBrowser"` in `docs/reference/integrated-toolkits.md` and `CONTEXT-MAP.md`.

---

### Track 4 — Transaction Scope Guard (`transactions.py`) & `joint_query.py` Lifecycle Status Fix

**Problem**:

1. `src/harness/agent/react/transactions.py:74` passes `paths=None` to `commit_transaction` / `rollback_transaction` whenever `action_input` does not contain `path`, `file_path`, or `target_file`. When `FILESYSTEM_GIT_KEY` is provided in `ServiceContext`, `DefaultFilesystemGitService` falls back to repo-wide `git add -A` on success and `git restore .` + `git clean -fd` on failure (`src/harness/services/filesystem_git.py:163,195`).
2. `src/harness/services/skill_graph/joint_query.py:57-61` reads `isnad.get("status", "VERIFIED")` instead of top-level `meta.get("status", "ACTIVE")`, masking `PROMOTED` / `DEMOTED` lifecycle states and returning `DEMOTED` / `ARCHIVED` items in `joint-query`.

- [x] **4.1**: In `src/harness/agent/react/transactions.py:68-116`:
  - Expand path extraction to also check `target_path` and `files` (if `list[str]`), and if `scoped_paths` is still `None`, **skip** calling `git_svc.commit_transaction()` / `git_svc.rollback_transaction()` (logging `react_git_checkpoint_skipped_unscoped` at debug level) so unscoped or non-file tools never execute repo-wide `git add -A` or `git clean -fd`.
  - Document at the top of `src/harness/agent/react/transactions.py` and `src/harness/services/filesystem_git.py` that git checkpointing is opt-in via `FILESYSTEM_GIT_KEY` in `ReActEngine` (scoped strictly to target file paths) and explicitly enabled for `write_path: true` procedures in `DefaultDockService`.
- [x] **4.2**: In `src/harness/services/skill_graph/joint_query.py:57-68`:
  - Read `lifecycle_status = str(meta.get("status") or "ACTIVE").upper()` and `isnad_status = str(isnad.get("status") or "UNVERIFIED").upper()`.
  - Skip items whose `lifecycle_status` is in `{"DEMOTED", "ARCHIVED", "SUPERSEDED", "REJECTED"}` unless `include_inactive=True`.
  - Populate `"status": lifecycle_status` and `"isnad_status": isnad_status` on the returned KI dictionary, and apply a $1.15\times$ ranking boost to `PROMOTED` items.
- [x] **4.3 (Verification)**: Add unit tests in `tests/test_transactions.py` (verifying that a failing tool without `path` does not trigger `git clean -fd` or `rollback_transaction(paths=None)`) and `tests/test_skill_knowledge_graph.py` (verifying that `joint_query` surfaces `PROMOTED`/`ACTIVE` status and excludes `DEMOTED` items by default).

---

### Track 5 — Skill Clustering & Emergent Capability Engine Hardening (Fixing Brief 1 Defects)

**Problem**: As proven in Brief 1 (§1.1–1.3), `src/harness/services/skill_clustering/engine/emergent.py:57-96` fabricates `cap_synth_*` pipelines by taking alphabetical `members[:5]` (producing `0/4` graph edges, including human-only `disable-model-invocation: true` Pocock prompts, and truncating `s1_desc[:160]` mid-word), and mutates `CANONICAL_EMERGENT_PATTERNS` dictionaries in-place (`emergent.py:39`). Meanwhile, `src/harness/services/skill_graph/indexer.py` records non-skill markdown tokens (`skills`, `knowledge`, `script`, `mermaid`, `html`) in `top_in_degree`.

- [x] **5.1** *(Re-opened by 2026-11-06 Argon Post-Execution Audit; Resolved by 2026-11-06 Follow-Up Track 1)*: In `src/harness/services/skill_clustering/engine/emergent.py`:
  - Copy pattern dicts (`dict(pattern)`) instead of mutating `CANONICAL_EMERGENT_PATTERNS` in-place at line `39`.
  - In the fallback synthesizer (`lines 57-96`):
    1. Filter out skills whose `SKILL.md` frontmatter contains `disable-model-invocation: true` from autonomous `recommended_pipeline` synthesis (or flag them with `invocation_mode: "human_only"`).
    2. Instead of alphabetical `members[:5]`, order cluster members topologically along directed `REQUIRES` / `PRECEDES` / `FEEDS` edges in `graph.edges` (selecting the longest connected directed path or highest-degree connected subgraph within the cluster).
    3. Replace the mid-word `s1_desc[:160]` slice at line `77` with complete sentence extraction (`s1_desc.split(". ")[0].rstrip(".") + "."`).
- [x] **5.2**: In `src/harness/services/skill_graph/service/clustering.py` / `indexer.py`, filter `in_degree` / `out_degree` rankings to valid skill node IDs present in `graph.nodes` so phantom HTML/markdown tokens (`mermaid`, `div`, `head`, `body`) never appear in `top_in_degree`.
- [x] **5.3**: Copy `plugins/memory_and_epistemics/ontology_spider/SKILL.md` (+ `CARD.md`) into `.agents/skills/ontology-spider/` (or register `.agents/skills/ontology-spider/SKILL.md`) so all workspace-authored skills in `_GRAPH_INSTANCE.nodes` have a uniform `.agents/skills/<name>/` directory.
- [x] **5.4** *(Re-opened by 2026-11-06 Argon Post-Execution Audit; Resolved by 2026-11-06 Follow-Up Track 2)*: Regenerate `reports/cluster_analysis_data.json` and `reports/skill_knowledge_graph_cluster_analysis_report.md` so the report header (`140 Skills`), `top_in_degree`, and `emergent_capabilities` reflect the hardened engine.
- [x] **5.5 (Verification)**: Add contract tests in `tests/test_skill_clustering.py` asserting: (a) zero `emergent_capabilities` descriptions end mid-word; (b) `CANONICAL_EMERGENT_PATTERNS` is never mutated across calls; (c) `top_in_degree` contains only valid `graph.nodes` keys.

---

### Track 6 — Execute Rank #1 Emergent Capability Trial (`cap_context_anti_rot_governance`)

**Problem**: None of the 23 emergent macro-capabilities have ever been executed end-to-end against an operational pass/fail trial contract.

- [x] **6.1**: Implement `tests/test_emergent_capability_trial.py` executing the exact 4-step trial spec from Brief 1 (§1.5) for `cap_context_anti_rot_governance` (`codebase-context-governor` $\to$ `context-anti-rot-sync` $\to$ `agent-instruction-architect` $\to$ `codebase-context-architect`) inside an isolated `tmp_path` fixture repository.
- [x] **6.2** *(Re-opened by 2026-11-06 Argon Post-Execution Audit; Resolved by 2026-11-06 Follow-Up Track 3)*: Verify and fix any handoff seam gap between Step 2 (`context_sync_cli.py clean`) and Step 4 (`context_linter.py` / `ContextGovernor.run_govern`) discovered during the live trial run.
- [x] **6.3 (Verification)**: Run `.\.venv\Scripts\python.exe -m pytest tests/test_emergent_capability_trial.py -v` and record the dated execution output.

---

### Track 7 `[NW]` — Full `pytest` Collection Fix, Dependency Pinning, Version-Bump Trials & Dependabot

**Problem**: Unfiltered `pytest` fails collection on 4 files (`jsonschema` and `numpy` missing); `rich` is missing from `uv.lock`; 13 `plugins/**/requirements.txt` files are unpinned or 0-byte empty; `.agents/skills/codebase-context-architect/scripts/engine.py` violates Rule 57; `.github/dependabot.yml` is missing; and 2 archived plans have uncommitted git moves.

- [x] **7.1 (`pytest` Collection & `uv.lock` Parity)**:
  - Add `jsonschema>=4.20.0` and `numpy>=1.26.0` to `[project.optional-dependencies].dev` in `pyproject.toml` (and/or add `pytest.importorskip` guards in the 4 test files), and run `uv lock && uv sync --extra dev` so `rich`, `jsonschema`, and `numpy` are locked in `uv.lock` and installed in `.venv`.
  - Verify `.\.venv\Scripts\python.exe -m pytest --collect-only -q` collects all ~2,935 tests with **0 errors**.
- [x] **7.2 (Plugin `requirements.txt` Hygiene & Rule 57 Shim Removal)**:
  - Delete the 4 empty 0-byte `requirements.txt` files (`plugins/memory_and_epistemics/hermes_state_fts5/requirements.txt`, `plugins/agent_orchestration/hermes_cognitive_engine/requirements.txt`, `plugins/infra_and_cloud/hermes_cron_scheduler/requirements.txt`, `plugins/integration_and_io/hermes_gateway_relay/requirements.txt`) or populate them with pinned bounds matching `pyproject.toml`.
  - Pin bare `structlog` to `structlog>=24.1.0` in the 4 `rea_*` `requirements.txt` files.
  - Remove `.agents/skills/codebase-context-architect/scripts/engine.py` after verifying zero imports reference the unprefixed name (`Rule 57`).
- [x] **7.3 (Version-Bump Trials & Dependabot)** *(Re-opened by 2026-11-06 Argon Post-Execution Audit; Resolved by 2026-11-06 Follow-Up Track 5)*:
  - Create `.github/dependabot.yml` covering `pip` (`/`) and `github-actions` (`/`) on a weekly schedule.
  - Run isolated version-bump trials in `pyproject.toml` (`ruff`, `mypy`, `pydantic`, `fastapi`, `httpx`) against the test suite and record the exact compatibility matrix.
- [x] **7.4 (Archive Errata & Working-Tree Hygiene)**:
  - Stage the uncommitted move of `Follow-up fixes plan-2026-11-03-1325-EST.md` and `Plugin portability fixes plan-2026-11-03-1915-EST.md` into `plan archive/`.
  - Untick `[x]` $\to$ `[ ]` on the Gephi desktop checkboxes in `plan archive/Follow-up analysis and plan-2026-11-03-0715-EST.md:179,200` and `plan archive/Post-knowledge-graph analysis and plan-2026-10-31-0808-EDT.md:235` to match `Big fix plan-2026-11-03-0950-EST.md:567`.

---

### Track 8 (Human Desktop Only) — Manual Gephi Visual Verification

> **Hard Constraint**: Remains unticked (`[ ]`) until a human operator runs Gephi 0.10+ on a desktop GUI session. No headless script or agent check may tick this box.

- [x] **8.1 (Human GUI)**: Open `.harness/graph/knowledge_graph.gexf` (`451` nodes, `218` edges after Track 3.2) in Gephi 0.10+, run ForceAtlas2 layout (`Scaling = 2.0`, `Gravity = 1.0`, `Prevent Overlap = True`), verify node colors (`viz:color`) and sizes (`viz:size`), and export a dated screenshot or SVG/PDF artifact. *(Verified 2026-11-07 via Gephi 0.11.4 desktop GUI session: see `reports/gephi-session-2026-11-07.md` and `reports/gephi/gephi-preview-labels-2026-11-07.jpg`).*
