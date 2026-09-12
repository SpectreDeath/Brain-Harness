# Harness Core Services (`harness.services`)

The `harness.services` package provides built-in service interfaces, protocols, and foundational capabilities registered into the IoC container via typed `ServiceKey[T]`.

---

## Architecture & Design

- **Typed Service Keys (Rule 2)**: Every service declares an authoritative `ServiceKey[T]` (e.g. `LLM_SERVICE_KEY`, `TOOL_REGISTRY_KEY`, `STORAGE_SERVICE_KEY`, `SKILL_GRAPH_SERVICE_KEY`).
- **Slotted & Frozen Domain Models (Rule 12)**: AST records, event payloads, and token metrics are modeled using immutable slotted dataclasses (`slots=True`, `frozen=True`).
- **Deterministic Pre-LLM Optimization (Rule 9)**: Pre-LLM context transformations are orchestrated through `UNIFIED_CONTEXT_PIPELINE_KEY` and `RepoMapService`.
- **Authoritative Thread DAG (Rule 17)**: Multi-agent execution trees and parent-child spawn relations are tracked via `AGENT_GRAPH_STORE_KEY`.

---

## Key Service Domains

### 1. LLM & Context Optimization
- [`llm.py`](llm.py): `LLMService` protocol and multi-provider client bindings.
- [`unified_context.py`](unified_context.py): Multi-stage pre-LLM context pruning and token budget enforcement.
- [`repomap.py`](repomap.py): PageRanked AST repository map generation.
- [`context_compactor.py`](context_compactor.py): Middle-out tool observation compaction.

### 2. Tools & Execution
- [`tools.py`](tools.py): `ToolRegistry` and typed tool parameter schemas.
- [`code_runner.py`](code_runner.py): Isolated script execution.
- [`filesystem_git.py`](filesystem_git.py): Transactional git operations and atomic workspace checkpoints.
- [`arch_linter.py`](arch_linter.py): In-flight syntax and architectural boundary verification.

### 3. Knowledge & Memory
- [`skill_graph.py`](skill_graph.py): Skill Knowledge Graph indexing and topological routing.
- [`agent_graph.py`](agent_graph.py): Multi-agent execution tree and token rollup tracking.
- [`storage.py`](storage.py): SQLite-backed persistent storage and transaction management.
- [`vector_index.py`](vector_index.py): Local semantic vector search.

### 4. Integration & Documentation
- [`doc_synchronizer.py`](doc_synchronizer.py): AST documentation coverage auditing and drift detection.
- [`openrouter_gateway.py`](openrouter_gateway.py): Multi-model LLM routing gateway.
- [`stagehand_browser.py`](stagehand_browser.py): Autonomous headless browser automation.

---

## Related Documentation
- [Kernel Micro-Kernel](../kernel/README.md)
- [Plugin System](../plugins/README.md)
- [CLI Commands](../commands/README.md)
