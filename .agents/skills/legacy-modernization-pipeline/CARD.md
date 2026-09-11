```ascii
┌──────────────────────────────────────────────────────────────────────┐
│ SKILL: legacy-modernization-pipeline                                 │
│ SKILL: legacy-modernization-pipeline                                  │
│ Category: software_engineering / meta-skills                         │
│ Version: 1.0.0                                                       │
│ Invocation: /legacy-modernization-pipeline                           │
│ Triggers: "legacy modernization", "refactor legacy codebase",        │
│           "characterization testing", "modernization pipeline"       │
│ Requires: "deep-repo-auditor", "data-topology-mapper",               │
│           "legacy-refactoring-guardian",                             │
│           "adversarial-agent-verifier", "deepen-architecture"        │
│ Target: Safe end-to-end modernization of complex legacy codebases    │
└──────────────────────────────────────────────────────────────────────┘
```

# Legacy Modernization Pipeline — Companion Summary Card

## Stage Progression Table

| Stage | Core Responsibility | Primary Artifact | Completion Gate |
|---|---|---|---|
| **Stage 1: Multi-Axis Audit** | Survey complexity, dependencies & 5D score | Audit Profile Report | Hotspots & seam boundaries identified |
| **Stage 2: DAG Topology Mapping** | Trace data flow, state mutation & call trees | Causal Topology DAG | State flows & coupling bottlenecks mapped |
| **Stage 3: Characterization** | Author golden master tests with mutation check | Golden Master Test Suite | $\ge 90\%$ coverage & mutant detection verified |
| **Stage 4: Adversarial Refactor** | Isolate seams, refactor & verify git diff | Modernized Seam Code | Clean diff & green characterization suite |
| **Stage 5: Deepen & Verify** | Elevate module depth & commit Knowledge Vault | Deep Module & KI Item | End-to-end suites pass & dual-file KI saved |

---

## Vocabulary & Levers

- **Characterization Test (Golden Master)**: Black-box test capturing existing system behavior without asserting prior correctness.
- **Seam**: A place where you can alter behavior in a program without editing in that place (Michael Feathers).
- **Causal DAG**: Directional acyclic graph tracking mutable state, caller hierarchies, and execution blast radius.
- **Inspect-Before-Edit Protocol**: Read-only AST analysis and contract drafting before modifying any existing code (Rule 13).
- **Synthetic Mutation Invariant**: Invariant test confirming that introduced mutations force characterization tests to fail loudly.
- **Slotted/Frozen Domain Entities**: Ensuring transformed data models use `slots=True, frozen=True` (Rule 12).

---

## Mandatory Invariants Checklist

- [ ] **Characterization Before Modification**: Never modify legacy production code before golden master tests pass.
- [ ] **Synthetic Mutation Verification**: Verify characterization test sensitivity by confirming synthetic mutations fail.
- [ ] **Inspect-Before-Edit Seam Analysis**: Map DAG dependencies and author failing contracts before editing (Rule 13).
- [ ] **Atomic Transactional Rollback**: Revert unverified or failing edits via context transactions (Rule 8).
- [ ] **Canonical Dual-File Vault Format**: Persist architectural patterns as `metadata.json` and `summary.md` (Rule 40).
