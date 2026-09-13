# Progressive Disclosure Diagram Generation Pedagogy (ELI5)

## Context
Monolithic architecture diagrams attempting to illustrate every file, function, and database table at once overwhelm reviewers. Cognitive load spikes, causing reviewers to skim or overlook critical architectural flaws.

## Distilled Learning
The PR Lens ELI5 skill defines a progressive disclosure methodology:
1. **Core Abstraction (Step 1)**: Start with the absolute minimum viable mental model (2–3 key nodes representing Caller and Callee / Ingestion and Output).
2. **Layered Expansion (Steps 2–4)**: Progressively introduce intermediate transformations, storage layers, and error boundaries.
3. **Walkthrough Focal Highlight**: Each walkthrough step highlights a specific subgraph with accompanying explanatory text, focusing the reviewer's visual attention on the exact causal flow.
4. **Cognitive Tier Calibration**: Bound total visible nodes to ≤12 per view to prevent cognitive saturation.

## Triggers & Seam Choices
- **Trigger**: Multi-step PR explanations, architecture documentation onboarding, and code review comments.
- **Seam Choice**: Scaffolding walkthrough generators in `pr-lens-visualizer` skill and PR comment composer tools.
