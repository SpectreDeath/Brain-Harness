# Software Engineering Domain Architecture

The Software Engineering domain governs AST-aware code refactoring, architectural boundary linting, sandbox script execution, version control operations, and visual artifact reporting.

---

## Domain Scope & Boundaries

This domain coordinates code editing, structural verification, and tool-driven development:
- In Scope: AST code manipulation, circular import analysis, Git transactional checkpoints, slotted dataclass architectures, Diátaxis documentation pipelines, and interactive HTML Visual Briefs.
- Out of Scope: Untyped ad-hoc script mutations, raw bash string execution, or unauthenticated git pushes.

---

## Ubiquitous Language & Core Terminology

- *Refactor Engine*: An AST-manipulation pipeline that performs structural code transformations, seam consolidations, and import cleanup. (*Avoid*: Code editor, rewriter, mutator)
- *Architecture Linter*: A static analysis tool that enforces module depth, detects cyclic dependencies, and verifies public seam invariants. (*Avoid*: Style checker, code reviewer, syntax linter)
- *Visual Brief*: A self-contained, interactive HTML document rendered in temporary storage showing before-and-after topology diagrams and metrics. (*Avoid*: Diff report, summary page, HTML preview)
- *Runner*: An isolated execution wrapper that runs test scripts and evaluates return codes without mutating host process state. (*Avoid*: Script launcher, terminal runner)
- *Deep Module*: A software component with a simple, narrow interface hiding extensive internal complexity and implementation details. (*Avoid*: Big class, fat service, monolithic package)
- *Skill Engine*: A standardized multi-stage agent blueprint combining visual HTML briefs, human-in-the-loop checkpoints, and explicit anti-patterns. (*Avoid*: Prompt template, agent prompt, runbook script)
- *Compute Budget*: A calibrated tiering of model capacity and reasoning effort (High, Medium, Low, Off) matched to task complexity. (*Avoid*: Model picker, reasoning level, prompt token budget)

---

## Architectural Invariants & Patterns

- Slotted & Frozen Dataclasses (Rule 12): High-volume internal entities use `slots=True`, `frozen=True`, and `__post_init__` assertions.
- Inspect-Before-Edit & Seam Verification (Rule 13): Agents map DAG component seams, author failing test contracts, and validate changes against strict diffs before modifying code.
- In-Flight Lint-After-Edit Self-Repair (Rule 16): File writes immediately run syntax verification (`ArchLinterService.lint_file()`) and append diagnostics into tool observations.
- In-Place Deepening over Sprawl (Rule 20): Deepen existing foundational plugins in-place rather than spawning parallel duplicate tool wrappers.

---

## Co-Located Plugins & Micro-Kernel Services

- Filesystem Git Service: [`src/harness/services/filesystem_git.py`](../../../src/harness/services/filesystem_git.py) providing `FILESYSTEM_GIT_KEY`.
- Refactor Engine Service: [`src/harness/services/refactor_engine.py`](../../../src/harness/services/refactor_engine.py) providing `REFACTOR_ENGINE_KEY`.
- Code Runner Service: [`src/harness/services/code_runner.py`](../../../src/harness/services/code_runner.py) providing `CODE_RUNNER_KEY`.
- Artifact Generator: [`src/harness/services/artifact_generator.py`](../../../src/harness/services/artifact_generator.py) providing `ARTIFACT_GENERATOR_KEY`.
- HF Doc Builder Plugin: [`plugins/developer_tooling/hf_doc_builder/`](../../../plugins/developer_tooling/hf_doc_builder/README.md).

---

## Associated Agent Skills

- [`codebase-context-architect`](../../../.agents/skills/codebase-context-architect/SKILL.md): Architects multi-layer codebase context files and linters.
- [`deepen-architecture`](file:///C:/Users/spectre/.gemini/config/plugins/pocock-skills/skills/deepen-architecture/SKILL.md): Iterative architecture deepening loop eliminating shallow modules.
- [`repo-doc-synchronizer`](../../../.agents/skills/repo-doc-synchronizer/SKILL.md): Audits documentation coverage, detects drift, and scaffolds Diátaxis suites.
- [`python-dataclass-architect`](../../../.agents/skills/python-dataclass-architect/SKILL.md): Designs type-safe, slotted and frozen Python data structures.
