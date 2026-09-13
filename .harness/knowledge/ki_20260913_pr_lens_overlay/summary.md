# Idempotent Human Architectural Overlay Invariant

## Context
Purely automated code-diff analysis generates raw symbol-level or file-level graphs that lack domain semantic context (e.g. knowing that `src/kernel/` is the Core IoC Micro-Kernel). However, human architects often define curated domain lanes and architectural component maps.

## Distilled Learning
PR Lens establishes an idempotent graph overlay pipeline:
- **Base Overlay (`.pr-lens/map.json`)**: Developers check in a high-level architectural map defining lanes, system boundaries, and critical path nodes.
- **Delta Node Merging**: When a git diff is analyzed, modified files and functions are matched against the base map. If a node matches an existing domain entity, its curated attributes (label, lane, metadata) are preserved.
- **New Symbol Induction**: Unmapped files/symbols are inducted into a dynamic `Changes` or `Unassigned` lane without mutating or clobbering curated definitions.
- **Idempotency**: Successive runs of the graph generator produce deterministic outputs that honor human overrides.

## Triggers & Seam Choices
- **Trigger**: Diff-to-graph synthesis and multi-agent architecture reviews.
- **Seam Choice**: Integration into `visualizer_engine.py` overlay merge routines and `pr_lens_graph` plugin tools.
