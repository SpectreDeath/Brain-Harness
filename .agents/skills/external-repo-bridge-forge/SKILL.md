---
name: external-repo-bridge-forge
description: Ingest external GitHub repositories, introspect architectural commit trajectories, scaffold sandboxed Harness plugins, and generate Diátaxis documentation suites with C4 architecture models. Do not use for internal Harness kernel refactoring.
---

# External Repo Bridge Forge: Ingestion, Plugin Synthesis & Documentation

`external-repo-bridge-forge` is an authoritative composite meta-skill that orchestrates the ingestion of foreign GitHub repositories, architectural pattern extraction, automated Harness plugin synthesis, and production Diátaxis documentation generation with C4 architecture diagrams.

It coordinates four specialized capabilities:
1. **Repository Introspection & Commit Archaeology** ([`repo-reader`](../repo-reader/SKILL.md))
2. **Automated Plugin Scaffolding & Synthesis** ([`repo-to-plugin-forge`](../repo-to-plugin-forge/SKILL.md))
3. **Diátaxis Technical Documentation Architecture** ([`developer-docs-architect`](../developer-docs-architect/SKILL.md))
4. **Multimodal Diagram & Artifact Projection** ([`cellcog-multimodal`](../cellcog-multimodal/SKILL.md))

See [CARD.md](CARD.md) for the companion summary card, 5-stage progression matrix, and invariants checklist.
Consult `/repo-to-plugin-forge` for schema inference, `/developer-docs-architect` for Diátaxis structure, and [bridge-architecture.md](references/bridge-architecture.md) for bridge architecture patterns.

---

## The 5-Stage Bridge Forge Progression

```
[1. Repo Introspection] ──► [2. Seam Partitioning] ──► [3. Sandboxed Plugin Synthesis]
                                                                  │
                                                                  ▼
[5. Multimodal C4 Projection] ◄── [4. Diátaxis Documentation Suite] ◄─────┘
```

---

## 1. Repository Introspection & Trajectory Analysis

Analyze foreign codebases without polluting the local kernel or exposing credentials:

1. **Secure Ingestion & Trajectory Archaeology (Rule 15)**:
   - Ingest target repositories via isolated subprocess runners with in-memory credential redaction.
   - Trace commit history to uncover structural inflection points, refactoring churn, and architectural intent.
2. **Polyglot Manifest Inspection**:
   - Inspect package manifests (`pyproject.toml`, `package.json`, `Cargo.toml`, `go.mod`) to extract dependencies, versions, and build scripts.
3. **Public Entrypoint Identification**:
   - Locate primary exported classes, CLI commands, and top-level functions.

> **Completion criterion**: Repository profile generated with commit trajectory, dependencies, and public API symbols mapped.

---

## 2. Seam & Dependency Partitioning

Partition foreign capabilities into single-responsibility plugin modules:

1. **Domain-Partitioned Plugin Synthesis (Rule 18)**:
   - Never bundle disparate tools into a single monolithic plugin. Partition tools across appropriate category directories (`agent_orchestration`, `data_engineering`, `security_and_forensics`).
2. **Seam Isolation & Interface Elevation**:
   - Isolate external dependencies from the Harness kernel; introduce typed `ServiceKey[T]` abstractions (Rule 2).
3. **In-Place Deepening over Sprawl (Rule 20)**:
   - Identify existing Harness plugins that can be deepened in-place before creating redundant duplicate wrappers.

> **Completion criterion**: Seam boundaries mapped and partitioned into single-responsibility plugin candidates.

---

## 3. Sandboxed Plugin Scaffolding & Validation

Scaffold production-grade Harness plugins using `PluginCreator`:

1. **Subprocess Isolation by Default (Rule 5 & Rule 7)**:
   - Enforce `IsolationMode.SUBPROCESS` for all external plugins; configure lazy venv staging to eliminate startup lag.
2. **Manifest Specification (`plugin.json`)**:
   - Declare typed `provides` and `requires` dependencies for topological lifecycle resolution (Rule 3).
3. **Schema Inference & Tool Registration**:
   - Generate `main.py` registering tools into the IoC container via typed keys.
4. **Dual-Mode Plugin Validation (Rule 38)**:
   - Run `PluginValidator.validate_async()` or `validate_sync()` to guarantee 100% manifest and structural compliance.

> **Completion criterion**: Sandboxed plugin scaffolded and validated with 100% pass on `PluginValidator`.

---

## 4. Diátaxis Documentation Suite Generation

Generate a complete, structured documentation suite using the 4-quadrant Diátaxis framework:

1. **Tutorial (Learning-Oriented)**:
   - Guided hands-on walkthrough taking a developer from zero to a functioning plugin execution.
2. **How-To Guide (Task-Oriented)**:
   - Step-by-step recipes for solving concrete real-world problems.
3. **Reference (Information-Oriented)**:
   - Exact technical specifications of service keys, configuration parameters, and tool arguments.
4. **Explanation (Understanding-Oriented)**:
   - Architectural context, design trade-offs, and why subprocess isolation was selected.
5. **Agent-Optimized Index (`llms.txt`)**:
   - Structured plain-text index for AI agents discovering plugin capabilities.

> **Completion criterion**: Diátaxis documentation suite authored covering all four quadrants plus `llms.txt`.

---

## 5. Multimodal C4 Architecture Projection

Project the plugin's architecture into visual diagrams and multimodal documentation:

1. **C4 Architecture Mermaid Modeling**:
   - **Context Diagram (Level 1)**: User, Harness Kernel, and Foreign System interaction.
   - **Container Diagram (Level 2)**: Subprocess sandbox, IPC pipes, and storage databases.
   - **Component Diagram (Level 3)**: Internal classes, service providers, and event handlers.
2. **Subprocess Pipe Disposal Verification (Rule 14)**:
   - Verify async subprocess transports explicitly drain and close pipes in `finally` blocks.
3. **Knowledge Vault Commit (Rule 40)**:
   - Scaffolding canonical dual-file items (`metadata.json` + `summary.md`) capturing the bridged repository patterns.

> **Completion criterion**: Complete C4 Mermaid models rendered, pipe disposal verified, and Knowledge Vault item committed.

---

## The Three Foundational Pillars

### 1. The Visual Brief Pillar
Every bridge run renders an interactive HTML visual brief in `%TEMP%` displaying the foreign dependency graph, Diátaxis quadrant matrices, and interactive C4 container diagrams.

### 2. The Mandatory Checkpoint Pillar
The agent must never author plugin directories or run external installation scripts without first presenting `implementation_plan.md` with `RequestFeedback: true` and awaiting explicit user confirmation.

### 3. Explicit Anti-Patterns
Rigid architectural boundaries prevent unisolated script execution, documentation rot, and monolithic tool bundles.

---

## Anti-Patterns

- **Monolithic Tool Bundling** — Shoving disparate tools into a single massive plugin instead of domain-partitioned modules (Rule 18).
- **Unisolated External Execution** — Running external plugin code in-process instead of subprocess sandboxes (Rule 5).
- **Diátaxis Quadrant Muddle** — Mixing tutorials with technical API reference specifications in an undifferentiated markdown file.
- **Pipe Leakage in Sandboxes** — Failing to drain and close stdin/stdout/stderr pipes inside `finally` blocks (Rule 14).
- **Single-File Vault Pollution** — Dumping single flat JSON files into `.harness/knowledge/` instead of the canonical dual-file directory (`metadata.json` + `summary.md`).
- **Missing Negative Boundaries** — Scaffolding bridge skills without explicit `Do not use for...` constraints in frontmatter descriptions.
