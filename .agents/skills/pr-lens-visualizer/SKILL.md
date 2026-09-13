---
name: pr-lens-visualizer
description: Draw pull request diffs and codebase structures as animated, self-contained SVG architecture and data-flow diagrams. Author and validate graph documents, render standalone SVGs, and compose PR comments. Do not use for non-code diagrams or general image generation.
---

# PR Lens Visualizer: Standalone Animated Architecture & Data-Flow Diagrams

`pr-lens-visualizer` transforms git pull request diffs and codebase directory structures into self-contained, zero-dependency animated SVG architecture and data-flow diagrams.

See [CARD.md](CARD.md) for the companion summary card, stage progression table, and invariants checklist.
Consult [config.default.yaml](config.default.yaml) for baseline operational budgets and layout parameters.

---

## The 4-Stage Visualizer Progression

```
[1. Diff Ingestion & Topology Extraction] ──► [2. Graph Schema & Semantic Validation]
                                                            │
                                                            ▼
[4. PR Comment & Walkthrough Composition] ◄── [3. Standalone Animated SVG Rendering]
```

---

## 1. Diff Ingestion & Topology Extraction

Ingest git diffs or codebase structures and extract architectural topology:

1. **Ingest Git Diff**:
   - Extract modified, added, and deleted files and entities using `parse_git_diff()`.
   - Identify module boundaries, ingress endpoints, services, and storage entities.
2. **Apply Architectural Overlay**:
   - If a human-curated `.pr-lens/map.json` exists in the repository, apply idempotent overlays using `apply_overlay()`.
   - Preserve human subsystem boundaries, lane assignments, and curated labels while mapping diff delta nodes into designated lanes.
3. **Construct Graph Document**:
   - Build a structured `GraphDocument` entity with nodes, directed edges, lanes, and progressive disclosure walkthrough steps.

> **Completion criterion**: Structured `GraphDocument` assembled with all nodes, edges, lanes, and walkthrough steps populated.

---

## 2. Graph Schema & Semantic Validation

Validate graph documents prior to rendering to eliminate layout engine failure modes:

1. **Structural Type Verification**:
   - Assert all required fields (`version`, `title`, `nodes`, `edges`) are present and valid.
2. **Semantic Graph Integrity Verification**:
   - Enforce terminal validity: every `edge.source` and `edge.target` MUST resolve to an existing `node.id`.
   - Enforce lane membership: every `node.lane` MUST resolve to an existing `lane.id`.
   - Enforce walkthrough references: every `focus_nodes` reference in walkthrough steps MUST resolve to an existing node.
   - Enforce node uniqueness: duplicate node identifiers are strictly rejected.

> **Completion criterion**: `validate_graph()` returns `valid == True` with zero blocking validation errors.

---

## 3. Standalone Animated SVG Rendering

Compile the validated graph document into a zero-dependency standalone SVG:

1. **Inline CSS Keyframe Animation**:
   - Embed pure CSS `@keyframes pulse` in the SVG `<style>` block to animate stroke offsets along directed edges.
   - Requires zero external CDNs, client-side JavaScript, or iframe wrappers.
2. **Responsive Color Themes**:
   - Inject `@media (prefers-color-scheme: dark)` styling to adapt node fills, borders, text, and edge paths seamlessly between light and dark modes.
3. **Geometry & Lane Layout**:
   - Position nodes within lane clusters, routing orthogonal or cubic bezier curves for edge transitions.

> **Completion criterion**: Standalone `<svg>` generated with valid XML syntax, inline CSS keyframes, and dark/light mode responsiveness.

---

## 4. PR Comment & Walkthrough Composition

Compose an actionable GitHub PR markdown comment:

1. **Progressive Disclosure Walkthrough (ELI5)**:
   - Scaffold ordered walkthrough steps beginning with the 2-node core mental model and expanding outwards.
2. **Collapsible Architecture Details**:
   - Wrap the full animated SVG inside a `<details>` block with summary statistics (files touched, lane distribution, node count).
3. **Reviewer Guidance**:
   - Highlight high-impact blast radius areas and architectural invariants.

> **Completion criterion**: Markdown PR comment formatted with embedded SVG, ELI5 walkthrough, and architectural impact summary.

---

## The Three Foundational Pillars

### 1. The Zero-Dependency Invariant
All generated SVG diagrams must be 100% self-contained. Never reference external stylesheets, external fonts, or client-side JavaScript that would be stripped by GitHub comment sanitizers.

### 2. The Semantic Integrity Invariant
Every edge endpoint and lane reference must be verified against extant nodes and lanes prior to rendering to eliminate downstream layout engine crashes.

### 3. Progressive Disclosure Pedagogy
Diagram walkthroughs must present architectures progressively—starting from high-level entry points before unfolding subsystem internals.

---

## Anti-Patterns

- **External Dependency Leaks** — Referencing CDN scripts or remote styles that fail inside sanitized GitHub PR comments.
- **Dangling Edge Pointers** — Emitting graph edges whose source or target nodes do not exist in the node catalog.
- **Monolithic Cognitive Flooding** — Dumping 50+ unclustered nodes in a single flat view without lanes or progressive walkthrough steps.
- **Destructive Map Overwrites** — Overwriting human-curated `.pr-lens/map.json` architecture definitions during automated diff analysis.
- **Mutable Graph State** — Using mutable dictionary state instead of immutable slotted/frozen dataclasses for graph entities.
