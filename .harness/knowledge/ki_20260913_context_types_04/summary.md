# Context Item Typing & Evidence Boundary Invariants

## Context
Passing untyped string blobs into LLM prompts allows tool outputs, untrusted web content, and instructions to bleed into one another, creating prompt injection vulnerabilities and architectural drift.

## Distilled Learning
Adopt an explicit runtime type system for agent context items:
- Define discrete context item types: `SystemInstruction`, `DeveloperRule`, `WorkspaceEvidence`, `ToolObservation`, and `UserConstraint`.
- Validate metadata and schema invariants at construction time using slotted/frozen dataclasses.
- Enforce strict priority ordering during context assembly: Constraints override Instructions, which bound Evidence.
- Apply sanitization and fence isolation to all `WorkspaceEvidence` and `ToolObservation` items before prompt injection.

## Triggers & Seam Choices
- **Trigger**: ReAct agent prompt compilation, context pruning, and multi-turn message assembly.
- **Seam Choice**: Standardize in `harness.services.context_compiler` and `harness.agent.prompt_builder`.
