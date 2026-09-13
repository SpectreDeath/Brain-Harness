```ascii
┌──────────────────────────────────────────────────────────────────────┐
│ SKILL: pr-lens-visualizer                                            │
│ Category: software_engineering / code_review                         │
│ Version: 1.0.0                                                       │
│ Invocation: /pr-lens-visualizer                                      │
│ Triggers: "pr lens", "visualize pr", "pr architecture diagram",      │
│           "animated svg diagram", "diff flow graph"                  │
│ Requires: "code-review", "codebase-design"                           │
│ Target: Render animated standalone SVG diagrams from PR diffs        │
└──────────────────────────────────────────────────────────────────────┘
```

# PR Lens Visualizer — Companion Summary Card

## Stage Progression Table

| Stage | Core Responsibility | Primary Artifact | Completion Gate |
|---|---|---|---|
| **Stage 1: Ingest & Extract** | Parse git diff & extract topology | `GraphDocument` entity | Nodes, edges & lanes extracted from diff |
| **Stage 2: Validate Schema** | Enforce structural & semantic integrity | `ValidationResult` | Terminal existence & lane membership verified |
| **Stage 3: Render SVG** | Compile standalone animated SVG | Standalone SVG string | Inline `@keyframes` & zero external deps |
| **Stage 4: Compose PR** | Author markdown comment & walkthrough | Markdown PR comment | Embedded SVG & progressive walkthrough ready |

---

## Vocabulary & Levers

- **Standalone Animated SVG**: Zero-dependency SVG containing inline CSS `@keyframes` and media queries that render directly in GitHub PR comments without JavaScript.
- **Dual-Engine Integrity**: Validating structural types and cross-entity semantic references (edge endpoints, lane IDs, walkthrough node references).
- **Idempotent Human Overlay**: Preserving human-curated `.pr-lens/map.json` boundary lanes and labels when merging automated diff changes.
- **Progressive Disclosure (ELI5)**: Structuring diagram walkthroughs to grow from a 2-node minimal mental model to full system complexity.
- **Slotted/Frozen Graph Entities**: Immutable, memory-efficient `@dataclass(slots=True, frozen=True)` domain models (Rule 12).

---

## Mandatory Invariants Checklist

- [ ] **Zero-Dependency SVG Embeds**: All SVGs must be standalone without external CSS, JS, or fonts.
- [ ] **Terminal & Lane Semantic Integrity**: Every edge source/target and node lane must exist in the document.
- [ ] **Idempotent Map Preservation**: Automated analysis must never clobber curated human `.pr-lens/map.json` overlays.
- [ ] **Slotted & Frozen Dataclasses**: All graph models must use `slots=True, frozen=True` (Rule 12).
- [ ] **Progressive Walkthrough Bounds**: Walkthroughs must limit initial focus to $\le 3$ core nodes before expanding.
