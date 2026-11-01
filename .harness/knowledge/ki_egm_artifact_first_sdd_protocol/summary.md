# Artifact-First Spec-Driven Development & Altitude Boundary Protocol

## Core Architectural Axiom
Spec-Driven Development (SDD) fails when specifications are either conversational ephemera or monolithic dumps that conflate high-altitude architectural goals with low-altitude implementation details.

The EGM protocol establishes two strict structural invariants:

### 1. Chat Dump Prohibition (Artifact-First Delivery)
- Agents are strictly forbidden from dumping full specs, draft sections, or raw review reports into the chat stream.
- All documents (`concepts_brief.md`, `design_draft.md`, `*_report.md`) are persisted directly to workspace files or harness artifacts.
- Chat interactions are limited to concise links, tri-state checkpoint questions, and high-leverage decision prompts.

### 2. Semantic Altitude Partitioning
Specifications must enforce explicit line and header boundaries:

```
┌───────────────────────────────────────────────────────────┐
│                     FeatureRange                          │
│  Altitude: High (High-Level Architecture)                 │
│  Focus: Root problem, goals/non-goals, YAGNI simplicity,  │
│         minimalist data flows, alternatives considered    │
│  Audited by: Zoom Out Reviewer, Design Critic             │
├───────────────────────────────────────────────────────────┤
│                     DetailedRange                         │
│  Altitude: Low (Implementation Plan)                      │
│  Focus: Concrete file paths, class/function signatures,   │
│         unit/contract test cases, rollout phases          │
│  Audited by: Implementation Readiness, Codebase Details   │
└───────────────────────────────────────────────────────────┘
```

This altitude boundary prevents the "Weeds Syndrome" where coding agents prematurely jump into writing utility functions before validating root architecture.
