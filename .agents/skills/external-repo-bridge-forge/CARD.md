```ascii
┌──────────────────────────────────────────────────────────────────────┐
│ SKILL: external-repo-bridge-forge                                    │
│ SKILL: external-repo-bridge-forge                                     │
│ Category: integration_and_io / meta-skills                           │
│ Version: 1.0.0                                                       │
│ Invocation: /external-repo-bridge-forge                              │
│ Triggers: "external repo bridge forge", "forge plugin from repo",    │
│           "repo to plugin", "bridge repo", "diataxis docs"           │
│ Requires: "repo-reader", "repo-to-plugin-forge",                      │
│           "developer-docs-architect", "cellcog-multimodal"           │
│ Target: End-to-end foreign repo ingestion, plugin & docs synthesis   │
└──────────────────────────────────────────────────────────────────────┘
```

# External Repo Bridge Forge — Companion Summary Card

## Stage Progression Table

| Stage | Core Responsibility | Primary Artifact | Completion Gate |
|---|---|---|---|
| **Stage 1: Repo Introspection** | Trace commit archaeology & inspect manifests | Repo Profile Report | Public entrypoints & dependencies charted |
| **Stage 2: Seam Partitioning** | Separate capabilities into domain plugins | Seam Partition Plan | Single-responsibility boundaries mapped |
| **Stage 3: Sandboxed Plugin** | Scaffold plugin with subprocess isolation | Validated Plugin | 100% pass on PluginValidator (Rule 38) |
| **Stage 4: Diátaxis Docs** | Author 4-quadrant docs suite & llms.txt | Documentation Suite | Tutorials, How-Tos, Reference & Explanation |
| **Stage 5: C4 Multimodal** | Model C4 diagrams & verify pipe disposal | C4 Diagrams & KI | C4 Mermaid rendered & dual-file KI committed |

---

## Vocabulary & Levers

- **Subprocess Isolation**: Running external plugins in sandboxed subprocess virtual environments (Rule 5 & Rule 7).
- **Domain-Partitioned Plugin Synthesis**: Splitting foreign capabilities across dedicated category plugins (Rule 18).
- **Diátaxis Documentation Taxonomy**: Stratifying docs into Tutorials, How-To Guides, Technical Reference, and Explanations.
- **C4 Architecture Model**: Four-level visual software architecture model: Context, Container, Component, and Code.
- **Subprocess Pipe Disposal Invariant**: Draining and closing stdin/stdout/stderr pipes inside `finally` blocks (Rule 14).
- **Dual-Mode Plugin Validation**: Validating plugin directories via coroutine or synchronous methods (Rule 38).

---

## Mandatory Invariants Checklist

- [ ] **Subprocess Sandbox by Default**: External/GitHub plugins must run in subprocess isolation (Rule 5).
- [ ] **Domain Partitioning**: Never combine unrelated tools into a single monolithic plugin (Rule 18).
- [ ] **Subprocess Pipe Disposal**: Drain and close all async subprocess pipes in `finally` blocks (Rule 14).
- [ ] **Diátaxis 4-Quadrant Completeness**: Documentation suites must cover all four distinct Diátaxis quadrants.
- [ ] **Canonical Dual-File Vault Format**: Persist architectural patterns as `metadata.json` and `summary.md` (Rule 40).
