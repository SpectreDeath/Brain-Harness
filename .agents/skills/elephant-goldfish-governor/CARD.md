```ascii
┌──────────────────────────────────────────────────────────────────────┐
│ SKILL: elephant-goldfish-governor                                    │
│ Category: agent_orchestration / architecture                         │
│ Version: 1.0.0                                                       │
│ Invocation: /elephant-goldfish-governor                              │
│ Triggers: "elephant goldfish", "egm review", "spec driven design",   │
│           "zero context review", "spec drift report", "goldfish"     │
│ Requires: "agent-instruction-architect", "deep-repo-auditor"        │
│ Target: Bifurcated context spec drafting, review and drift auditing  │
└──────────────────────────────────────────────────────────────────────┘
```

# Elephant-Goldfish Governor — Companion Summary Card

## Stage Progression Table

| Stage | Core Responsibility | Primary Artifact | Completion Gate |
|---|---|---|---|
| **Stage 1: Ideation & Brainstorm** | Anchor hypothesis & run 6-lens brainstorm | `concepts_brief.md` | Verified brief written with explicit non-goals |
| **Stage 2: Spec Compilation** | Draft spec with semantic altitude ranges | `docs/designs/<feature>.md` | Clean boundary between FeatureRange & DetailedRange |
| **Stage 3: Antagonistic Review** | Execute 5-stage zero-context Goldfish review | `goldfish_review_report.md` | All 5 review gates evaluated & findings normalized |
| **Stage 4: In-Thread Remediation** | Resolve findings with Elephant in-thread | Updated Design Specification | Blockers & majors resolved with human approval |
| **Stage 5: Drift Governance** | Compare live source AST against checked-in spec | `{DATE}_DRIFT_REPORT.md` | Differential report highlighting missing features/models |

---

## Vocabulary & Levers

- **The Elephant**: Deep-context authoring partner holding repository context, user requirements, and system history.
- **The Goldfish**: Isolated, zero-context reviewer subagents evaluating drafts against rubrics without conversational bias.
- **Semantic Altitude Ranges**: Partitioning specifications into `FeatureRange` (architecture/YAGNI) and `DetailedRange` (signatures/tests/rollout).
- **Anti-Weeds Altitude Control**: Strictly blocking implementation-level code from high-level architecture sections.
- **Synthesizer Compiler**: Intermediate persona that fans out to subagents, normalizes disparate natural language findings, and deduplicates overlaps.
- **AST Drift Taxonomy**: 4-part divergence classification: Missing Features, Incomplete Models, Logic Shortcuts, and Architectural Divergence.

---

## Mandatory Invariants Checklist

- [ ] **Zero-Context Subagent Isolation**: Reviewer subagents must never inherit the authoring agent's conversation history.
- [ ] **Artifact-First Delivery**: Long-form proposals, drafts, and review reports must be written to disk; chat dumps are strictly barred.
- [ ] **Anti-Sycophancy Review Standard**: Reviewers must lead with technical objections and failure modes; flattery and apologies are banned.
- [ ] **Semantic Altitude Boundary**: High-level architecture sections must not contain low-level helper functions or code implementations.
- [ ] **Differential Drift Reporting**: Drift reports must report strictly discrepancies without reciting matching or conforming code.
- [ ] **Human-in-the-Loop Tri-State Gates**: All review stages must pause at tri-state checkpoint gates for human triage and approval.

