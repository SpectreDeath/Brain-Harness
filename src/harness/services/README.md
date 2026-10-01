# Harness Core Services (`harness.services`)

The `harness.services` package provides the authoritative domain service interfaces, slotted domain models, and protocols registered into the micro-kernel IoC container via typed `ServiceKey[T]`.

---

## Architecture & Design

Brain Harness implements an extensible micro-kernel architecture with strict contracts:
- **Typed Service Keys (Rule 2)**: Every capability exposes a typed `ServiceKey[T]`. Callers register implementations via `context.provide(KEY, instance)` and resolve them via `context.require(KEY)` or `context.optional(KEY)`.
- **Slotted & Frozen Value Objects (Rule 12)**: High-frequency internal data structures, telemetry metrics, and AST results use `slots=True` and `frozen=True` to minimize memory overhead and prevent state mutations.
- **Skill-to-IoC Micro-Kernel Seam Elevation (Rule 49)**: Capabilities authored in agent skills are elevated to first-class in-memory micro-kernel services rather than subprocess CLI forks.
- **Non-Invasive Extensibility (Rule 19)**: Services extend kernel functionality via IoC resolution without modifying the `ServiceContext` core constructor.

---

## Service Registry by Domain

### 1. Agent Reasoning & Swarm Orchestration
| Service Module | Authoritative ServiceKey | Protocol / Class | Description |
|---|---|---|---|
| [`agent_harness.py`](agent_harness.py) | `AGENT_HARNESS_ARCHITECT_SERVICE_KEY` | `AgentHarnessArchitectService` | Audits 5-part harnesses, 4-mechanism reliability gates, and 4-layer runtime stacks. |
| [`ai_native_harness.py`](ai_native_harness.py) | `AI_NATIVE_HARNESS_SERVICE_KEY` | `AiNativeHarnessService` | Evaluates 4-gate behavioral pipelines, credential-free MCP security, and telemetry drift. |
| [`coding_harness_calibrator.py`](coding_harness_calibrator.py) | `CODING_HARNESS_CALIBRATOR_KEY` | `CodingHarnessCalibratorService` | Calibrates context staging (T0-T4), action spaces, and planning scaffolds. |
| [`agent_graph.py`](agent_graph.py) | `AGENT_GRAPH_STORE_KEY` | `AgentExecutionGraphService` | Authoritative thread DAG tracking execution states, sub-agent spawns, and token rollups. |
| [`compute_assessor.py`](compute_assessor.py) | `COMPUTE_ASSESSOR_SERVICE_KEY` | `ComputeAssessorService` | Evaluates composite 5D complexity and dynamically allocates model reasoning tiers. |
| [`dynamic_model_router.py`](dynamic_model_router.py) | `DYNAMIC_MODEL_ROUTER_SERVICE_KEY` | `DynamicModelRouterService` | Sub-5ms heuristic complexity classifier and multi-provider failover router. |
| [`harness_compass.py`](harness_compass.py) | `HARNESS_COMPASS_SERVICE_KEY` | `HarnessCompassService` | Evaluates and benchmarks autonomous agent harnesses with dual-track optimization. |
| [`self_evaluating_pipeline.py`](self_evaluating_pipeline.py) | `SELF_EVAL_PIPELINE_SERVICE_KEY` | `SelfEvaluatingPipelineService` | Autonomous prompt evaluation, gold standard assertions, and iterative tuning. |
| [`deterministic_validation.py`](deterministic_validation.py) | `DETERMINISTIC_VALIDATION_SERVICE_KEY` | `DeterministicValidationService` | 3-tier deterministic validation loops with machine-error injection and bounded retries. |

### 2. Code Intelligence, AST & Verification
| Service Module | Authoritative ServiceKey | Protocol / Class | Description |
|---|---|---|---|
| [`arch_linter.py`](arch_linter.py) | `ARCH_LINTER_KEY` | `ArchLinterService` | In-flight syntax checking, circular import detection, and architectural boundary rules. |
| [`code_runner.py`](code_runner.py) | `CODE_RUNNER_KEY` | `CodeRunnerService` | Executes scripts within sandboxed runtime environments with resource limits. |
| [`filesystem_git.py`](filesystem_git.py) | `FILESYSTEM_GIT_KEY` | `FilesystemGitService` | Transactional Git workspace checkpoints, atomic commits, and safe rollbacks. |
| [`pre_commit_security_guard.py`](pre_commit_security_guard.py) | `PRE_COMMIT_SECURITY_GUARD_KEY` | `PreCommitSecurityGuardService` | Pre-commit security interceptor running DevSkim SAST, Gitleaks, and dual-gate CI. |
| [`refactor_engine.py`](refactor_engine.py) | `REFACTOR_ENGINE_KEY` | `RefactorEngineService` | AST-aware automated refactoring, symbol renaming, and module partitioning. |
| [`test_runner.py`](test_runner.py) | `TEST_RUNNER_KEY` | `TestRunnerService` | Dispatches test suites (`pytest`, `unittest`) and parses structured test results. |
| [`repomap.py`](repomap.py) | `REPO_MAP_SERVICE_KEY` | `RepoMapService` | Dynamic PageRanked AST repository map generator injected before LLM context. |
| [`unified_context.py`](unified_context.py) | `UNIFIED_CONTEXT_PIPELINE_KEY` | `UnifiedContextPipelineService` | Multi-pass pre-LLM context pruner (whitespace, middle-out tool reduction). |
| [`context_compactor.py`](context_compactor.py) | `CONTEXT_COMPACTOR_KEY` | `ContextCompactorService` | Compresses historical tool outputs and transcripts to prevent context blowout. |

### 3. Knowledge, Epistemics & Memory
| Service Module | Authoritative ServiceKey | Protocol / Class | Description |
|---|---|---|---|
| [`skill_graph.py`](skill_graph.py) | `SKILL_GRAPH_SERVICE_KEY` | `SkillKnowledgeGraphService` | Directed knowledge graph of agent skills with topological shortest-path routing. |
| [`skill_parser.py`](skill_parser.py) | `SKILL_PARSER_SERVICE_KEY` | `SkillCardParserService` | Parses `CARD.md` metadata boxes and `SKILL.md` documents into structured schemas. |
| [`skill_clustering.py`](skill_clustering.py) | `SKILL_CLUSTERING_SERVICE_KEY` | `SkillClusteringService` | Computes semantic and topological clusters across agent capability catalogs. |
| [`skill_visualizer.py`](skill_visualizer.py) | `SKILL_VISUALIZER_SERVICE_KEY` | `SkillVisualizerService` | Generates self-contained interactive HTML Visual Briefs of skill topologies. |
| [`storage.py`](storage.py) | `STORAGE_SERVICE_KEY` | `StorageService` | Relational SQLite persistence supporting read-only URI mode and transactions. |
| [`vector_index.py`](vector_index.py) | `VECTOR_INDEX_SERVICE_KEY` | `VectorIndexService` | In-memory and disk-persisted dense vector indexing and cosine similarity search. |
| [`okf_memory.py`](okf_memory.py) | `OKF_MEMORY_SERVICE_KEY` | `OkfMemoryService` | Open Knowledge Framework (OKF v0.2) Git-native episodic and semantic memory. |
| [`memgraphrag.py`](memgraphrag.py) | `MEMGRAPHRAG_SERVICE_KEY` | `MemGraphRagService` | Hybrid graph and retrieval-augmented generation memory indexing. |
| [`graphiti.py`](graphiti.py) | `GRAPHITI_SERVICE_KEY` | `GraphitiService` | Temporal knowledge graph tracking entity evolutions and relationship lifespans. |
| [`discovery_index.py`](discovery_index.py) | `DISCOVERY_INDEX_SERVICE_KEY` | `DiscoveryIndexService` | Catalogs and searches open public record archives and research corpora. |

### 4. Data Engineering, Documentation & External Bridges
| Service Module | Authoritative ServiceKey | Protocol / Class | Description |
|---|---|---|---|
| [`doc_builder.py`](doc_builder.py) | `DOC_BUILDER_SERVICE_KEY` | `HfDocBuilderService` | AST autodoc generation, Diátaxis compilation, and zero-dependency mock loading. |
| [`doc_synchronizer.py`](doc_synchronizer.py) | `DOC_SYNCHRONIZER_KEY` | `DocSynchronizerService` | Code-to-doc coverage auditing, stale symbol detection, and link drift checking. |
| [`bigquery_augmented_analytics.py`](bigquery_augmented_analytics.py) | `BIGQUERY_AUGMENTED_ANALYTICS_SERVICE_KEY` | `BigQueryAugmentedAnalyticsService` | In-database augmented analytics via Table-Valued Functions (TVFs) and ARIMA_PLUS. |
| [`garf_reporting.py`](garf_reporting.py) | `GARF_REPORTING_SERVICE_KEY` | `GarfReportingService` | Declarative SQL reporting pipelines and analytical workflow DAGs across APIs. |
| [`open_source_gis.py`](open_source_gis.py) | `OPEN_SOURCE_GIS_SERVICE_KEY` | `OpenSourceGisService` | Geospatial processing across 14 GIS engines with CRS safety verification. |
| [`paperless_ngx.py`](paperless_ngx.py) | `PAPERLESS_NGX_SERVICE_KEY` | `PaperlessNgxService` | Document ingestion, classification, and hybrid Tantivy/SQLite-Vec search. |
| [`hf_datasets.py`](hf_datasets.py) | `HF_DATASETS_SERVICE_KEY` | `HfDatasetsService` | Arrow zero-copy memory mapping and streaming pipelines for large datasets. |
| [`tau_bridge.py`](tau_bridge.py) | `TAU_BRIDGE_SERVICE_KEY` | `TauBridgeService` | Bidirectional integration with HuggingFace Tau coding agent harness. |
| [`claude_code.py`](claude_code.py) | `CLAUDE_CODE_BRIDGE_KEY` | `ClaudeCodeBridgeService` | Claude Code prompt compaction and dangerous bash command guardrails. |
| [`stagehand_browser.py`](stagehand_browser.py) | `STAGEHAND_BROWSER_KEY` | `StagehandBrowserService` | Autonomous headless browser orchestration and DOM extraction. |

---

## Programmatic Registration & Resolution

```python
import asyncio
from harness.kernel.runtime import HarnessRuntime
from harness.services.tools import TOOL_REGISTRY_KEY
from harness.services.skill_graph import SKILL_GRAPH_SERVICE_KEY

async def resolve_services():
    async with HarnessRuntime.create() as runtime:
        ctx = runtime.context
        
        # 1. Require mandatory core services
        tool_registry = ctx.require(TOOL_REGISTRY_KEY)
        skill_graph = ctx.require(SKILL_GRAPH_SERVICE_KEY)
        
        print(f"Registered tools: {len(tool_registry.list_tools())}")
        print(f"Indexed skills: {len(skill_graph.nodes)}")
        
        # 2. Check for optional specialized service
        from harness.services.doc_builder import DOC_BUILDER_SERVICE_KEY
        doc_builder = ctx.optional(DOC_BUILDER_SERVICE_KEY)
        if doc_builder:
            print("HF Doc Builder service is active and available.")

if __name__ == "__main__":
    asyncio.run(resolve_services())
```

---

## Related Documentation

- [Services Reference Page](../../../docs/reference/services.md)
- [Kernel Architecture](../kernel/README.md)
- [Plugin Development Guide](../../../docs/HOWTO.md#authoring-a-custom-plugin)
