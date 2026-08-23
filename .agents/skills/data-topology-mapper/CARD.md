# Skill Summary Card: `data-topology-mapper`

```
┌────────────────────────────────────────────────────────┐
│               SKILL SUMMARY CARD                       │
├────────────────────────────────────────────────────────┤
│ Name:        data-topology-mapper                      │
│ Category:    architecture / topology-mapping           │
│ Invocation:  /data-topology-mapper                     │
│ Trigger:     "map dependencies", "design architecture",│
│              "refactor database", "trace execution",   │
│              "data topology", "blast radius",          │
│              "hybrid topology", "cycle detection"      │
│ Version:     2.1.0                                     │
│ Requires:    "deepen-architecture"                     │
│ Provides:    "topology_mapping"                        │
├────────────────────────────────────────────────────────┤
│ Target:      Map complex architectures, DAG lineages,  │
│              execution queues, and hybrid topologies   │
│              into visual models before modifying code. │
└────────────────────────────────────────────────────────┘
```

---

## The 4-Stage Topology Mapping Loop

| Stage | Objective | Primary Artifact / Output | Completion Gate |
|---|---|---|---|
| **1. Domain Analysis** | Classify problem into 4 base analogies or hybrid composition | Categorization statement | Core topology and mental model declared |
| **2. Visual Brief** | Render interactive HTML Before/After topology & blast radius | `%TEMP%\data-topology-review-*.html` | Dark-mode HTML delivered with clickable URI |
| **3. Triage Checkpoint** | Priority queue interrupt with structured schema block | `implementation_plan.md` | `RequestFeedback: true` approved by user |
| **4. Execution** | Implement modifications and run algorithmic invariant checks | Modified source code | Invariants verified and test suite green |

---

## 4-Lens & Hybrid Analogies Matrix

```
┌─────────────────────────────────────────────────────────────────┐
│                    COGNITIVE TOPOLOGY LENSES                    │
├────────────────────────────────┬────────────────────────────────┤
│ Lens 1: Graph Topology         │ Vertices (modules) & edges     │
│ (Interconnected Networks)      │ (bridges/APIs). Directed DAG   │
│                                │ blast radius mapping.          │
├────────────────────────────────┼────────────────────────────────┤
│ Lens 2: Tree Topology          │ Inverted family tree. Root and │
│ (Hierarchical Lineage)         │ parent-child paths. Strictly   │
│                                │ acyclic (no circular loops).   │
├────────────────────────────────┼────────────────────────────────┤
│ Lens 3: Direct Access & Sets   │ Hash Map: O(1) drawer pointer. │
│ (Key-Value & VIP Lists)        │ Set: VIP guest list rejecting  │
│                                │ duplicates (deduplication).    │
├────────────────────────────────┼────────────────────────────────┤
│ Lens 4: Execution Order        │ Stack (LIFO undo/backtrack),   │
│ (Stacks, Queues, Heaps)        │ Queue (FIFO background pool),  │
│                                │ Max-Heap (ER triage interrupt).│
├────────────────────────────────┼────────────────────────────────┤
│ Hybrid Compositions            │ Graph of Trees, Hash-Indexed   │
│                                │ Queues, or Tree of DAGs.       │
└────────────────────────────────┴────────────────────────────────┘
```

---

## Anti-Patterns Cheat Sheet

- **Speculative Abstraction**: Applying complex design patterns before categorizing the base data structure analogy.
- **Blind Execution**: Modifying code without generating the Visual Brief and mapping systemic blast radius.
- **Horizontal Slicing**: Modifying horizontal layers instead of tracing vertical DAG execution paths.
- **Topology Confusion**: Permitting cyclic dependency loops in a designated Tree structure.

---

## Invariants & Guardrails

- [ ] **Declare Data Analogy**: Always explicitly state the chosen base data structure lens or hybrid composition before proposing changes.
- [ ] **Acyclic Invariant on Trees & DAGs**: Execute algorithmic cycle detection (DFS / Kahn's algorithm) to guarantee zero circular dependency loops.
- [ ] **Visual Brief Delivery**: Always emit an interactive `%TEMP%` HTML report with Mermaid Before/After diagrams and a Blast Radius table.
- [ ] **Structured Schema Block**: Always embed a formal JSON Topology Specification block in `implementation_plan.md`.
- [ ] **Triage Interrupt Gate**: Always pause execution on `implementation_plan.md` with `RequestFeedback: true` before modifying code.
- [ ] **Confine Blast Radius**: Confine code changes strictly to the vertices and edges mapped in the approved Visual Brief.
