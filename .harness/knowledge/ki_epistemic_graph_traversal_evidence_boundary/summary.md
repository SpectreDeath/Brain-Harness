# Epistemic Graph Traversal and the Relation-vs-Inference Boundary

**ID:** `ki_epistemic_graph_traversal_evidence_boundary`  
**Category:** `data_engineering`  
**Origin:** `D:\markdown from chrome\perplexity\KG` (Perplexity Epistemic Browsing Dialogue & Roni Das Neo4j Handbook)  
**Provenance Lineage:** `I was just thinking about knowledge graphs (fairly.md`, `How to Build a Knowledge Graph with Python and Neo4j [Full Handbook].md`

## Executive Summary

When constructing knowledge graphs for autonomous research agents, epistemic search, or scientific inquiry, the graph must not be treated as a static collection of flat assertions. Graph traversal mimics human epistemic investigation, moving from a query seed through foundational context, causal mechanisms, and active scientific controversy. 

To prevent autonomous agent hallucination and runaway bias loops, knowledge architectures must enforce a strict **Relation-vs-Inference Boundary** that segregates primary observed facts from secondary derived inferences, reifying contested edges into time-aware evidence tuples.

---

## 1. The Human-Scale Epistemic Traversal Path

Human researchers and autonomous browsing agents navigate knowledge through a structured 5-stage epistemic progression:

```
[Target Question / Anomaly]
          ↓
[Background Context & Foundations]
          ↓
[Causal Mechanism / Primary Actor]
          ↓
[Broader Context & Structural Network]
          ↓
[Controversy, Invalidation & Competing Claims]
```

1. **Question / Anomaly Seed**: The initial entry anchor (e.g., a specific paper, drug reaction, or unexplained system event).
2. **Background Context**: Expansion to foundational domain definitions, parent taxonomies, and recognized prerequisites.
3. **Causal Mechanism**: Direct 1-hop traversal across primary active edges (`INHIBITS`, `MUTATES`, `AUTHORED`).
4. **Broader Context**: Multi-hop structural network traversal (`AFFILIATED_WITH`, `FUNDED_BY`, `COLLABORATED_ON`).
5. **Controversy & Invalidation**: Bidirectional search for countervailing evidence (`REFUTES`, `CONTRADICTS`, `REPLICATED_WITH_FAILURE`).

---

## 2. Controlled Browsing Research Agent Architecture

Autonomous knowledge graph exploration requires four deterministic architectural constraints to prevent unbounded wandering:

| Component | Responsibility | Architectural Invariant |
| :--- | :--- | :--- |
| **Start Page / Anchor** | Explicit initial working node set. | Must resolve via unique index seek, not full scan. |
| **Selection Rule** | Heuristic ranking the next hop to expand. | Highest information gain or relevance to target competency question. |
| **Provenance Tree** | Graph path accumulator recording traversal steps. | Immutable directed acyclic graph tracking parent-child node hops. |
| **Decision Log** | Structured rationale for why each link was followed. | Persisted metadata recording selection score and alternative discarded links. |

---

## 3. The 7-Tuple Temporal Evidence Object

Static binary edges (`Subject -[:PREDICATE]-> Object`) fail in evolving, contested, or multi-agent domains. All dynamic or disputed relations must be modeled as a reified **7-tuple temporal evidence object**:

$$\mathcal{E} = \langle s, p, o, t, \sigma, c, \sigma_{status} angle$$

- **$s$ (Subject)**: Origin node identifier.
- **$p$ (Predicate)**: Semantic relationship verb.
- **$o$ (Object)**: Destination node identifier.
- **$t$ (Time)**: Temporal validity window (`valid_from`, `valid_to`, `observation_timestamp`).
- **$\sigma$ (Source)**: Provenance citation (DOI, URI, transcript timestamp, sensor ID).
- **$c$ (Confidence)**: Epistemic certainty score $\in [0.0, 1.0]$.
- **$\sigma_{status}$ (Status)**: Lifecycle state (`HYPOTHESIS`, `PEER_REVIEWED`, `CONTESTED`, `REFUTED`).

---

## 4. The 5-Layer Relation-vs-Inference Boundary Matrix

Knowledge graphs must never blend raw observations with derived algorithmic claims into indistinguishable edge types:

| Boundary Layer | Data Classification | Example Primitive | Storage & Labeling Rule |
| :--- | :--- | :--- | :--- |
| **1. Primary Facts** | Direct empirical observations from sources. | `(:Author)-[:AUTHORED]->(:Paper)` | Unmodified source data; immutable once ingested. |
| **2. Network Structure** | Direct topological relationships. | `(:Paper)-[:CITES]->(:Paper)` | Explicit, verified directed edges. |
| **3. Derived Hypotheses** | Model-generated or inferred edges. | `(:Drug)-[:POTENTIAL_TARGET]->(:Protein)` | Must include `inferred: true`, model ID, and confidence. |
| **4. Verification Data** | Replication attempts and audits. | `(:Study)-[:VALIDATES {method: "RCT"}]->(:Claim)` | Explicit evidence node or relationship with methodology. |
| **5. Actionable Conclusions** | High-confidence syntheses. | `(:Condition)-[:INDICATES_TREATMENT]->(:Drug)` | Derived view; requires multi-source convergence. |

---

## Architectural Invariants & Rules

1. **Inference Tagging Invariant**: Every graph relationship created by an agent or algorithmic pipeline must declare `inferred: true` and record the generator run ID.
2. **Temporal Window Assertion**: Relationships describing state changes or human affiliations must record valid-time properties rather than assuming perpetual truth.
3. **Epistemic Depth Boundary**: Autonomous exploration traversals must enforce a maximum depth ceiling ($\le 4$ hops) before returning evidence chains for synthesis.
