# Strict Dual-Engine Schema Validation & Integrity Invariants

## Context
When automated agents generate graph documents for visualization engines, syntactic JSON validity is insufficient. Subtle graph defects (such as dangling edge pointers, orphaned lane members, or invalid walkthrough references) crash layout rendering pipelines downstream.

## Distilled Learning
PR Lens establishes a two-tiered validation architecture:
1. **Structural Type Gate**: Zod runtime schema schemas mirror strict Ajv JSON Schemas (`GraphDocumentSchema`) enforcing field types, enums, and required properties.
2. **Semantic Graph Integrity Gate (`graphIntegrityIssues`)**:
   - Every `node.id` referenced in `edge.source` and `edge.target` MUST exist in the document.
   - Nodes assigning a `lane` attribute MUST match an extant `lane.id`.
   - Walkthrough steps (`walkthrough.steps`) MUST only reference existent node IDs.
   - Disconnected nodes or duplicate edge definitions are flagged as warnings or errors before layout calculation begins.

## Triggers & Seam Choices
- **Trigger**: Ingestion of agent-generated graph ASTs, pre-render layout pipeline, and graph mutation tools.
- **Seam Choice**: Scaffolding validator engines (`visualizer_engine.py`) and schema verification protocols in `src/harness/services/pr_lens.py`.
