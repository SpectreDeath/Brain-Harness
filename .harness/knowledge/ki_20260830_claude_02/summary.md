# Aspect-Oriented Multi-Agent Review Swarm

## Context
Monolithic code review prompts suffer from attention dilution, hallucinated positives, and shallow checks when tasked with analyzing complex diffs across multiple dimensions (tests, comments, type design, error handling, performance).

## Distilled Learning
Structure code review workflows as an aspect-oriented multi-agent swarm:
1. **Aspect Routing**: Classify modified files and dispatch targeted sub-agents:
   - `pr-test-analyzer`: Focuses exclusively on behavioral test coverage and regression gaps.
   - `comment-analyzer`: Verifies comments vs code truth and identifies comment rot.
   - `silent-failure-hunter`: Scans exception handlers and empty catch blocks.
   - `type-design-analyzer`: Evaluates type encapsulation and invariant expressiveness.
   - `code-reviewer`: Assesses general architecture and coding standards compliance.
2. **Fan-In Aggregation**: Collect findings into a unified triage matrix (Critical, Important, Suggestions).
3. **Downstream Polish**: Optionally invoke a specialized `code-simplifier` agent to refine code clarity after passing critical verification gates.

## Triggers & Seam Choices
- **Trigger**: Pre-commit verification, pull request generation, or deep architectural audits.
- **Seam Choice**: Orchestrate via a top-level command (`review-pr`) that dynamically spawns isolated sub-agents and rolls up their findings.
