# ICM Workspace-Builder Self-Hosting Meta-Pipeline & Cold Walk Validation

## The Self-Hosting Meta-Pipeline
The `workspace-builder` embodies the Unix philosophy applied to agent scaffolding. It is an ICM pipeline whose product is a newly scaffolded, fully compliant ICM workspace.

```
[01-discovery] ──► Extract domain, stages, and creative boundaries
       │
       ▼
[02-mapping]   ──► Map sequences, inputs/outputs handoffs, and reference dependencies
       │
       ▼
[03-scaffolding] ──► Generate folder tree, CLAUDE.md, CONTEXT.md, and .gitkeep files
       │
       ▼
[04-questionnaire] ► Design flat onboarding questionnaire and {{PLACEHOLDER}} syntax
       │
       ▼
[05-validation] ──► Execute Cold Walk Test, 15-convention audit, and token-bound checks
```

## The Cold Walk Test Invariant
Validation is not merely static AST schema checking. The workspace must pass the **Cold Walk Test**:
1. Start at `CLAUDE.md` ("Where am I?").
2. Follow `CONTEXT.md` routing table to Stage 01 ("Where do I go?").
3. Inspect `01-name/CONTEXT.md` Inputs table and verify all relative paths resolve to valid files.
4. Verify Stage $N$ output path matches Stage $N+1$ input path exactly.
5. Confirm no circular references or dead-end links exist across the entire workspace tree.
