# Cluster Pipeline Connectedness Fix Plan (2026-11-06-1950-EST)

## Goal

Resolve the two architectural defects in `src/harness/services/skill_clustering/` causing low or zero pipeline connectedness in `cluster_01` and `cluster_02_ask_matt`, guaranteeing that ordered cluster pipelines preserve continuous causal DAG execution chains in representative execution windows without violating the 200-line ceiling per Rule 11.

## Starting Facts & Architecture Seams

- **File 1**: `src/harness/services/skill_clustering/engine/pipeline.py` (107 lines).
  - Defect 1: `order_cluster_pipeline` seeds `queue = deque(connected_roots)` with all `in_degree == 0, out_degree > 0` nodes. In multi-root clusters (such as `cluster_01` with 5+ roots), standard FIFO BFS pops all roots sequentially before visiting downstream neighbors, resulting in `0/4` adjacent internal edges in `final_pipeline[:5]`.
- **File 2**: `src/harness/services/skill_clustering/engine/emergent.py` (167 lines).
  - Defect 2: Stripping `disable_model_invocation=True` skills (`ask-matt` router hub) prior to inducing intra-cluster edges leaves 9 autonomous skills with 0 mutual `dependencies`/`references` edges (`0/4` in `final_pipeline[:5]`).
- **Constraint**: Rule 11 strict 200-line ceiling on all modularized pipeline submodules.

---

## Track 1 — Multi-Root Component Chain Traversal (`pipeline.py`)

- [ ] **1.1** Failing test contract: Author unit test in `tests/test_skill_clustering_pipeline.py` verifying that a multi-root DAG with connected chains preserves path adjacency in `final_pipeline[:5]` rather than interleaving roots.
- [ ] **1.2** Depth-first / longest-chain traversal: Refactor `order_cluster_pipeline` in `pipeline.py` to traverse connected chains depth-first or longest-path-first per root component before consuming subsequent roots.
- [ ] **1.3** Representative window selection: Ensure that the `[:5]` representative window is extracted from the primary connected execution path rather than an arbitrary slice across disconnected components.
- [ ] **1.4** Rule 11 verification: Assert `pipeline.py` remains strictly $\le 200$ lines.

---

## Track 2 — Hub-Mediated Connectivity for Router Clusters (`emergent.py` & `pipeline.py`)

- [ ] **2.1** Failing test contract: Author unit test asserting that router-centered clusters like `cluster_02_ask_matt` maintain positive pipeline connectedness across autonomous members.
- [ ] **2.2** 2-Hop affinity edge induction: Update `emergent.py` / `pipeline.py` to preserve hub-mediated 2-hop co-routing affinity edges when inducing pipelines on clusters centered around non-invocable router skills.
- [ ] **2.3** Connectedness metrics exposition: Expose explicit `pipeline_connectedness` ratio (`connected_adjacent_pairs / (len(pipeline) - 1)`) on `EmergentCapability` and `SkillCluster` metadata.
- [ ] **2.4** Rule 11 verification: Assert `emergent.py` remains strictly $\le 200$ lines.

---

## Track 3 — Reporting & Cluster Pipeline Synchronization

- [ ] **3.1** Cluster report synchronization: Update CLI cluster pipeline export and markdown summary tables to report `pipeline_connectedness` percentages across all clusters.
- [ ] **3.2** Regression verification across all 19 clusters: Run pipeline ordering across all 19 existing clusters to verify zero regressions in component order or execution safety.

---

## Track 4 — Verification & Governance

- [ ] **4.1** Unit test suite pass: Execute `pytest tests/test_skill_clustering*.py` and verify 100% pass rate.
- [ ] **4.2** Full repository gate: Run `harness context lint` and ensure drift gate remains green.
- [ ] **4.3** Line count audit: Run submodule line count test across `src/harness/services/skill_clustering/` enforcing $\le 200$ lines on all files.
- [ ] **4.4** Independent check: Independent verification of all 13 prior checkboxes with primary test artifacts before sign-off.
