# 5-Stage Antagonistic Review Pipeline with In-Thread Remediation

## The 5-Stage Review Sequence
Rather than a single monolithic prompt, EGM executes a sequential, gated review pipeline:

```
[Target Specification: docs/designs/*.md]
                   │
                   ▼
[Stage 5: Initial Zoom Out Review] ──► Simplicity, YAGNI, Codebase Reuse
                   │
                   ▼
[Stage 6: Comprehension Test] ──────► Naive reader: tests self-containment without tribal knowledge
                   │
                   ▼
[Stage 7: Critic Review] ───────────► Scalability, race conditions, edge cases, failure modes
                   │
                   ▼
[Stage 8: Intermediate Zoom Out] ──► Re-evaluates additions from Stages 6-7 to block creep
                   │
                   ▼
[Stage 9: Implementation Readiness] ► Concrete file paths, exact signatures, verified tests
```

## The Synthesizer Fan-Out/Fan-In Engine
1. **Parallel Spawning**: Spawns multiple subagent instances (optionally paired A/B instances for maximum recall).
2. **Finding Normalization**: Maps unstructured text to structured finding models with exact line ranges and severities (`Blocker`, `Major`, `Nit`).
3. **Deduplication**: Merges overlapping critiques across lenses into coherent items.
4. **Tri-State Checkpoint**: At each stage, the engineer can proceed, resolve findings with the Elephant agent in-thread, edit manually, or pause.
