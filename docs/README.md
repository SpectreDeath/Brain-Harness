# Brain Harness Documentation Suite

Welcome to the comprehensive documentation suite for Brain Harness. This documentation is organized according to the Diátaxis documentation framework, systematically separating content into four cognitive modes: learning, practical problem solving, theoretical understanding, and factual lookup.

```text
                           PRACTICAL
                              ▲
                              │
               HOW-TO GUIDES  │  TUTORIALS
               Problem-oriented│  Learning-oriented
                              │
    WORK  ◄───────────────────┼───────────────────► STUDY
                              │
               REFERENCE      │  EXPLANATION
               Information-   │  Understanding-
               oriented       │  oriented
                              │
                              ▼
                         THEORETICAL
```

---

## Documentation Quadrants

### 1. [Tutorials](TUTORIAL.md) — Learning-Oriented
Step-by-step lessons for newcomers to get started and build foundational mental models.
- [Zero-to-One Quickstart](TUTORIAL.md#lesson-1-environment-setup--workspace-init): Initialize a workspace and configure your runtime environment.
- [Your First Autonomous Agent](TUTORIAL.md#lesson-2-running-your-first-autonomous-agent-task): Dispatch a task to the ReAct agent engine and inspect step execution.
- [Trajectory Inspection](TUTORIAL.md#lesson-3-inspecting-execution-trees--transcripts): Visualize execution DAGs and transcripts via CLI and Web Dashboard.

### 2. [How-To Guides](HOWTO.md) — Problem-Oriented
Goal-focused, practical recipes for solving real-world engineering tasks.
- [Authoring a Custom Plugin](HOWTO.md#authoring-a-custom-plugin): Scaffold, implement, and validate plugins with typed IoC services.
- [Registering Agent Tools](HOWTO.md#registering-tools-for-autonomous-agents): Expose typed, schema-validated tools for ReAct reasoning loops.
- [Crafting an Agent Skill](HOWTO.md#crafting-production-grade-agent-skills): Author `SKILL.md` and `CARD.md` adhering to SDLC craft standards.
- [Orchestrating Multi-Agent Swarms](HOWTO.md#orchestrating-multi-agent-swarms): Run hierarchical agent DAGs with token governance and consensus.
- [Auditing Documentation Coverage](HOWTO.md#auditing-documentation-coverage--drift): Execute AST coverage audits and link drift repair.

### 3. [Architecture Explanation](EXPLANATION.md) — Understanding-Oriented
Deep architectural discussions illuminating design choices, invariants, and mechanics.
- [Micro-Kernel & IoC Architecture](EXPLANATION.md#1-micro-kernel--ioc-architecture): Why everything is a plugin and how typed service keys work.
- [ReAct Agent Step Engine](EXPLANATION.md#2-react-agent-step-engine--context-optimization): In-flight tool repair, context optimization, and transactional isolation.
- [Subprocess Sandboxing & IPC](EXPLANATION.md#3-subprocess-sandboxing--ipc-transports): Lazy virtual environment staging and process isolation.
- [Immutable Event Bus](EXPLANATION.md#5-immutable-event-bus--telemetry): Append-only state logging and reactive telemetry streams.

### 4. [Reference Specifications](reference/README.md) — Information-Oriented
Deterministic, technical catalogs and API signatures for day-to-day engineering.
- [Kernel Reference](reference/kernel.md): `ServiceContext`, `ServiceKey`, `PluginLifecycleManager`, `DependencyGraph`.
- [Agent Reference](reference/agent.md): `ReActAgentLoop`, `StepExecutionEngine`, `SwarmCoordinator`, `ContextOptimizer`.
- [Ingestion Reference](reference/ingestion.md): `UniversalSourceRegistry`, `RepoFetcher`, `RepoInspector`, `RepoConverter`.
- [Core Services Registry](reference/services.md): 70+ typed `ServiceKey[T]` identifiers and protocols.
- [Click CLI Reference](reference/cli.md): Complete CLI command hierarchy, options, and usage syntax.
- [Plugin Manifest Reference](reference/plugin-manifest.md): `plugin.json` schema specification and lifecycle state rules.

---

## Domain Architecture Deep-Dives

Detailed architectural boundaries and ubiquitous languages for specific capability categories:
- [Agent Orchestration](domains/agent-orchestration/EXPLANATION.md): Swarms, supervisors, dialectical debaters, and reflection checkpoints.
- [Data Engineering](domains/data-engineering/EXPLANATION.md): Curated tabular pipelines, out-of-core profiling, and BigQuery TVFs.
- [Infrastructure & Cloud](domains/infra-and-cloud/EXPLANATION.md): Container management, Kubernetes manifest validation, and IaC specs.
- [Integration & I/O](domains/integration-and-io/EXPLANATION.md): Web fetching, OpenAPI tool generation, and external repo ingestion.
- [Memory & Epistemics](domains/memory-and-epistemics/EXPLANATION.md): Skill Knowledge Graph, OKF memory, and Isnad chain-of-custody.
- [Security & Forensics](domains/security-and-forensics/EXPLANATION.md): Threat modeling, pre-commit SAST scanning, and trajectory audits.
- [Software Engineering](domains/software-engineering/EXPLANATION.md): AST refactoring, architecture linting, and slotted dataclass patterns.

---

## Machine & AI Navigation

- [`llms.txt`](llms.txt): Token-optimized markdown index designed for AI agents and LLM context ingestion.
- [`_toctree.yml`](_toctree.yml): Navigation tree manifest utilized by the HuggingFace doc-builder engine.
- [`USER_MANUAL.md`](../USER_MANUAL.md): Comprehensive standalone operator manual.
