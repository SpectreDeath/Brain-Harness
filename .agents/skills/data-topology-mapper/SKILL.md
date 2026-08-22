---
name: data-topology-mapper
description: Map complex problem domains, causal DAG lineages, execution queues, and data structures (graphs, trees, hash maps, sets, priority queues, hybrid topologies) before code modification. Trigger when analyzing architecture, database schemas, execution pipelines, or multi-agent routing.
---

# Data Topology Mapper

`data-topology-mapper` forces agents to explicitly declare, decompose, and visually map the underlying data structure of a problem domain before modifying code. By translating abstract architectural questions into concrete, visually rendered topologies (Graphs, Trees, Hash Maps/Sets, Execution Queues/Heaps, and Hybrid Compositions) inspired by visual data structure analogies, it eliminates speculative assumptions, preserves topological invariants, and contains blast radius.

Every topology mapping workflow follows a strict four-stage progression:

```
[1. Domain Analysis & Hybrid Mapping] → [2. The Visual Brief] → [3. Triage Checkpoint & Schema] → [4. Execution & Algorithmic Verification]
```

See [CARD.md](CARD.md) for the quick-reference summary card, analogy matrix, and verification invariants.
Consult `/crafting-skills` for the underlying deep-module design standards and `/deepen-architecture` for seam optimization.

---

## 1. Domain Analysis & Hybrid Analogy Mapping

When triggered by an architectural request, refactor, or multi-agent design task, classify the problem domain into one of four cognitive lenses or declare a **Hybrid Composition**:

### The 4 Base Cognitive Lenses

1. **Interconnected Networks (The Graph Topology)**
   - *Mental Model Analogy*: Social networks (undirected), follower networks (directed), or route maps with variable travel costs (weighted).
   - *Agent Application*: Multi-agent routing, polyglot state flows, or microservice bridges. Identify **vertices** (Python, Prolog, Lisp modules) and **edges** (JSON-RPC bridges, APIs, event buses). Map directed edges to compute the exact **blast radius**.

2. **Hierarchical Lineage (The Tree Topology)**
   - *Mental Model Analogy*: Inverted family tree (root at top, branches spreading down) or binary search decision tree (halving problem space at each step).
   - *Agent Application*: Epistemic lineage, UI/DOM hierarchies, or Prolog decision trees. Identify the **root node** and trace strict **parent-child execution paths**.
   - *Hard Invariant*: Strictly forbidden from introducing cyclic dependencies (circular parent-child loops).

3. **Direct Access & Unique States (Hash Maps & Sets)**
   - *Mental Model Analogy*:
     - *Hash Map*: A magical machine that takes a key and instantly points to a specific drawer ($O(1)$ direct access, eliminating sequential scans).
     - *Set*: A VIP club guest list that automatically rejects duplicates and guarantees uniqueness.
   - *Agent Application*: IoC service registry lookups, configuration state maps, Semantic Memory Engine indexes ($O(1)$ key-value routing), and idempotency/subscriber sets (strict deduplication).

4. **Execution Order (Stacks, Queues, & Priority Heaps)**
   - *Mental Model Analogy*:
     - *Stack (LIFO)*: A pile of washed plates; last plate added is first removed (undo histories, recursive backtracking).
     - *Queue (FIFO)*: A fair ticket line; first come, first served (standard background task workers).
     - *Priority Queue / Max-Heap*: An emergency room triage desk where critical patients skip the line regardless of arrival time.
   - *Agent Application*: Task execution pipelines, gateway command routing, and human-in-the-loop triage interrupts.

### Hybrid Topology Compositions

For complex, multi-tiered architectures, declare how base topologies nest or compose:
- **Graph of Trees**: A microservice network where individual services manage internal hierarchical entity or rule trees.
- **Hash-Indexed Queue / Heap**: A priority task execution pipeline with $O(1)$ direct key lookup by Task ID for cancellation and status monitoring.
- **Tree of DAGs**: A hierarchical module packaging system where each subsystem encapsulates an internal directed acyclic workflow.

> **Completion criterion**: Core data structure category (or explicit hybrid composition) and mental model analogy are declared in the output.

---

## 2. The Visual Brief

Generate an interactive, self-contained HTML brief in `%TEMP%` to visually map the blast radius and architectural topology before touching code:

1. **Target Location**: Write to `%TEMP%\data-topology-review-<timestamp>.html` (Windows) or `/tmp/data-topology-review-<timestamp>.html` (Unix).
2. **Visual Standards**:
   - Load Tailwind CSS and Mermaid.js via CDN using dark theme (`#0d1117`).
   - Render a side-by-side **Before vs. After** Mermaid diagram illustrating node modifications, edge transitions, and blast radius.
   - Embed an **Interactive Blast Radius Table** detailing affected vertices, risk levels, and isolation boundaries.
3. **Delivery**: Surface the absolute file path with a clickable `file:///` link directly to the user.

```html
<!-- Location: %TEMP%\data-topology-review-<timestamp>.html -->
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Data Topology Review</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
  <script>mermaid.initialize({startOnLoad:true, theme:'dark'});</script>
</head>
<body class="bg-[#0d1117] text-[#c9d1d9] p-8 max-w-6xl mx-auto font-sans leading-relaxed">
  <header class="border-b border-[#30363d] pb-4 mb-6 flex items-center justify-between">
    <div>
      <h1 class="text-2xl font-bold text-white">Data Topology Review</h1>
      <p class="text-sm text-gray-400 mt-1">Pre-modification structural blast radius mapping</p>
    </div>
    <span class="bg-[#238636] text-white text-xs px-3 py-1 rounded-full font-mono font-semibold">Topology: Hybrid (DAG + Hash Index)</span>
  </header>

  <main class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
    <section class="bg-[#161b22] border border-[#30363d] rounded-xl p-5 shadow-lg">
      <h2 class="text-lg font-semibold text-gray-200 mb-3 border-b border-[#30363d] pb-2">Current Architecture</h2>
      <div class="mermaid">
        graph TD
          A[Client] --> B[Service]
      </div>
    </section>
    <section class="bg-[#161b22] border border-emerald-700/60 rounded-xl p-5 shadow-lg">
      <h2 class="text-lg font-semibold text-emerald-400 mb-3 border-b border-[#30363d] pb-2">Proposed Topology</h2>
      <div class="mermaid">
        graph TD
          A[Client] --> B[Service]
          B --> C[IoC Registry]
      </div>
    </section>
  </main>

  <section class="bg-[#161b22] border border-[#30363d] rounded-xl p-5">
    <h3 class="text-sm font-bold text-gray-300 uppercase tracking-wider mb-3">Blast Radius Impact Matrix</h3>
    <table class="w-full text-left text-xs border-collapse">
      <thead>
        <tr class="border-b border-[#30363d] text-gray-400">
          <th class="py-2">Vertex ID</th>
          <th class="py-2">Module / Seam</th>
          <th class="py-2">Topological Role</th>
          <th class="py-2">Impact Level</th>
        </tr>
      </thead>
      <tbody class="divide-y divide-[#30363d] text-gray-300">
        <tr>
          <td class="py-2 font-mono text-emerald-400">v_kernel</td>
          <td class="py-2">src/harness/kernel/</td>
          <td class="py-2">Root Coordinator</td>
          <td class="py-2"><span class="px-2 py-0.5 rounded bg-amber-900/50 text-amber-300 border border-amber-700/50">Direct Edit</span></td>
        </tr>
      </tbody>
    </table>
  </section>
</body>
</html>
```

> **Completion criterion**: Interactive HTML file written to `%TEMP%` and delivered to user as a clickable URI link.

---

## 3. Mandatory Checkpoint & Structured Schema Block

Halt execution to achieve consensus on the structural map before any modifications occur. This acts as an **ER Triage / Max-Heap Priority Interrupt**:

1. Generate or update the `implementation_plan.md` artifact detailing proposed topology changes.
2. Embed a formal **Structured Topology Specification Block** in JSON/Markdown format:

```markdown
### [Topology Specification Block]
```json
{
  "topology_type": "Directed Acyclic Graph (DAG)",
  "is_hybrid": false,
  "composition": null,
  "vertices": [
    {"id": "v_kernel", "label": "Kernel Micro-Core", "type": "module"},
    {"id": "v_registry", "label": "IoC Service Registry", "type": "hash_map"}
  ],
  "edges": [
    {"from": "v_kernel", "to": "v_registry", "protocol": "in_memory", "directed": true}
  ],
  "invariants": ["strictly_acyclic", "single_root", "o1_lookup"],
  "blast_radius_nodes": 2
}
```
```

3. Explicitly set `RequestFeedback: true` in artifact metadata.
4. **STOP and wait** for explicit user approval before executing any destructive or modifying code commands.

> **Completion criterion**: Agent pauses execution and requests human-in-the-loop approval on `implementation_plan.md` containing the structured topology block.

---

## 4. Execution & Algorithmic Invariant Verification

Upon receiving user approval, execute code modifications strictly aligned with the approved topology and run algorithmic verification:

1. **Confine Blast Radius**: Restrict edits exclusively to the vertices and edges defined in the approved Visual Brief.
2. **Algorithmic Invariant Verification Protocols**:
   - **Tree / DAG Acyclicity Protocol**: Verify that no circular references exist (e.g. Kahn's topological sort or DFS cycle detection).
   - **Hash Map / Set Uniqueness Protocol**: Verify that key mappings remain collision-free and set insertion enforces strict deduplication without $O(N)$ scanning.
   - **Queue Ordering & Starvation Protocol**: Verify that FIFO task orders are preserved and Priority Heap triage interrupts correctly preempt lower queues without indefinite starvation.
3. Run automated unit and integration tests to confirm zero regressions (`pytest -v`).

> **Completion criterion**: Code is modified, passing algorithmic invariant checks and 100% of automated test suites.

---

## In-File Reference

- **Vertex / Node**: A discrete module, agent, file, or data entity within the system.
- **Edge / Bridge**: The communication vector, JSON-RPC interface, dependency link, or transition between nodes.
- **Blast Radius**: The transitive set of vertices and edges impacted by modifying a target node.
- **Acyclic Invariant**: The structural guarantee that following directed edges will never form a closed loop.
- **Triage Interrupt**: A high-priority Max-Heap execution jump that halts lower-priority background tasks for critical human alignment.
- **Hybrid Composition**: A structured hierarchy combining two or more base data topologies (e.g., Graph of Trees).

---

## Anti-Patterns

- **Speculative Abstraction** — Applying complex design patterns before categorizing the base data structure analogy.
- **Blind Execution** — Modifying code without generating the Visual Brief and mapping the systemic blast radius.
- **Horizontal Slicing** — Modifying horizontal layers (e.g., all database adapters) instead of tracing vertical DAG execution paths.
- **Topology Confusion** — Permitting cyclic dependency loops in a designated Tree structure, or using $O(N)$ linear scans where Hash Map/Set lookups are required.
- **Unchecked Cycles** — Adding dependency edges across modules without running topological cycle verification.
