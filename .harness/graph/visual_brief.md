# Knowledge Graph Visual Brief & Topology Analysis

**Export Format**: GEXF (`.harness/graph/knowledge_graph.gexf`) & Cypher (`.harness/graph/knowledge_graph.cypher`)  
**Generated Date**: 2026-11-03  
**Source Knowledge Vault**: `.harness/knowledge/` (301 Knowledge Items)  

---

## 1. Graph Census & Entity Inventory

The derived knowledge graph models the complete epistemic and architectural memory of the Brain Harness micro-kernel, connecting atomic Knowledge Items (KIs) with executable agent skills, external sandboxed plugins, and primary source code paths.

| Entity Kind | Count | Description |
|:---|:---:|:---|
| **Knowledge Items (`ki`)** | 301 | Primary empirical and architectural heuristics in `.harness/knowledge/` |
| **Code Paths (`path`)** | 86 | Upstream and workspace files referenced by `source_target` |
| **Agent Skills (`skill`)** | 22 | Scaffolding targets linked via `became_skill` |
| **Plugins (`plugin`)** | 8 | Ecosystem extensions linked via `became_plugin` |
| **Total Nodes** | **417** | Combined network entities |

### Edge Type Distribution

| Edge Type | Count | Inference Mode | Description |
|:---|:---:|:---:|:---|
| `references_code` | 108 | Derived | Directional provenance edge to source file/directory |
| `same_domain` | 54 | Derived | Semantic affinity edge sharing $\ge 2$ high-signal domain tags |
| `became_skill` | 18 | Asserted | Epistemic-to-procedural promotion edge into `.agents/skills/` |
| `became_plugin` | 8 | Asserted | Epistemic-to-kernel promotion edge into `plugins/` |
| **Total Edges** | **188** | 27 Asserted, 161 Derived | Multi-relational typed DAG edges |

---

## 2. Structural Modularity & Community Detection

Graph community detection was executed across the connected subgraph (226 non-isolated nodes) using the Louvain modularity optimization algorithm (resolution $\gamma = 1.0$, weighted edges).

- **Global Modularity ($Q$)**: **$0.9447$** (exceptional community segregation; values $> 0.70$ indicate strong natural clustering)
- **Detected Communities**: **58 modular clusters**
- **Connected Components**: 248 total components (Largest component: 34 nodes)
- **Isolated Nodes**: 191 leaf Knowledge Items awaiting outward distillation or specialized domain links

### Top Epistemic Clusters

```
                     ┌────────────────────────────────────────────────────────┐
                     │          Top 8 Louvain Communities (Q = 0.9447)        │
                     └────────────────────────────────────────────────────────┘

  Cluster 1 [19 nodes]  ━━━ Architecture Deepening & Context Refactoring (developer_experience)
  Cluster 2 [15 nodes]  ━━━ Multi-Agent Swarms & Topology Orchestration (agent_orchestration)
  Cluster 3 [ 8 nodes]  ━━━ Google Repos Bridge & ADK Plugin Suite (plugins/external)
  Cluster 4 [ 8 nodes]  ━━━ PyRIT Security & Adversarial Red-Teaming (security_and_forensics)
  Cluster 5 [ 8 nodes]  ━━━ Multi-Agent Debate & Critic Evaluation Loops (agent_orchestration)
  Cluster 6 [ 7 nodes]  ━━━ Arrow Zero-Copy Streaming Datasets (data_engineering)
  Cluster 7 [ 7 nodes]  ━━━ Google Garf Declarative SQL Pipelines (data_engineering)
  Cluster 8 [ 6 nodes]  ━━━ Paperless-NGX Document Lifecycle & SQLite-Vec (data_engineering)
```

---

## 3. Gephi Layout & Visual Styling Guide

When rendering `.harness/graph/knowledge_graph.gexf` in Gephi:

1. **Spatial Layout Engine**:
   - Primary: **ForceAtlas2**
   - Settings: `Scaling = 2.0`, `Gravity = 1.0`, `Prevent Overlap = Checked`, `Tolerance = 0.1`
   - Secondary: Run **Expansion** ($\times 1.2$) followed by **Label Adjust** to prevent overlapping node tags.
2. **Node Ranking & Partitioning**:
   - **Size**: Ranked by `Degree` (Min: 6, Max: 24) or `retrieval_count`
   - **Color**: Partitioned by `category` (10 canonical colors):
     - `developer_experience`: `#3498db` (Blue)
     - `agent_orchestration`: `#9b59b6` (Purple)
     - `data_engineering`: `#e67e22` (Orange)
     - `security_and_forensics`: `#e74c3c` (Red)
     - `plugins / external`: `#1abc9c` (Teal)
3. **Edge Styling**:
   - Partitioned by `edge_type`:
     - `became_skill`: Bold solid line (Weight: 2.5, Color: `#f1c40f` Gold)
     - `became_plugin`: Bold solid line (Weight: 2.5, Color: `#2ecc71` Green)
     - `references_code`: Thin dashed line (Weight: 1.0, Color: `#7f8c8d` Grey)
     - `same_domain`: Semi-transparent curve (Weight: 0.8, Color: `#95a5a6`)

---

## 4. Neo4j & Cypher Ingestion Verification

The companion Cypher export `.harness/graph/knowledge_graph.cypher` provides complete idempotent database recreation:

1. **Constraint Governance**:
   - `CREATE CONSTRAINT ki_id_unique IF NOT EXISTS FOR (k:KnowledgeItem) REQUIRE k.id IS UNIQUE;`
   - `CREATE CONSTRAINT skill_id_unique IF NOT EXISTS FOR (s:Skill) REQUIRE s.id IS UNIQUE;`
   - `CREATE CONSTRAINT plugin_id_unique IF NOT EXISTS FOR (p:Plugin) REQUIRE p.id IS UNIQUE;`
   - `CREATE CONSTRAINT path_id_unique IF NOT EXISTS FOR (f:CodePath) REQUIRE f.id IS UNIQUE;`
   - `CREATE CONSTRAINT claim_id_unique IF NOT EXISTS FOR (c:IsnadClaim) REQUIRE c.id IS UNIQUE;`
2. **7-Tuple Temporal Evidence Materialization**:
   - Every `IsnadClaim` node sets all 7 epistemic properties: `assertion`, `status`, `confidence`, `evidence_type`, `source`, `verified`, and `verified_by`.
   - Connected via directed `[:ASSERTS_CLAIM]` relationships from source Knowledge Items.

