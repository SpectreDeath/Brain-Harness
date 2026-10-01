# Core Services Registry (`harness.services`)

This reference documents the typed `ServiceKey[T]` tokens, interfaces, and module locations for the services powering Brain Harness.

---

## Service Registration & Resolution Overview

In Brain Harness, every capability is an in-memory service registered in the IoC container:
```python
# To resolve a required service:
service = context.require(SERVICE_KEY)

# To check for an optional service:
service = context.optional(SERVICE_KEY)
```

---

## 1. Agent Reasoning & Swarm Services

| ServiceKey Constant | Inferred Type | Defining Module | Central Function |
|---|---|---|---|
| `AGENT_LOOP_KEY` | `AgentLoopService` | [`harness.agent.base`](../../src/harness/agent/base.py) | Autonomous ReAct agent reasoning and execution loop. |
| `AGENT_SESSION_MANAGER_KEY` | `AgentSessionManager` | [`harness.agent.session`](../../src/harness/agent/session.py) | Branchable session tree manager and checkpoint store. |
| `SWARM_COORDINATOR_KEY` | `SwarmCoordinator` | [`harness.agent.swarm`](../../src/harness/agent/swarm.py) | Multi-agent DAG swarm coordinator and consensus engine. |
| `AGENT_GRAPH_STORE_KEY` | `AgentExecutionGraphService` | [`harness.services.agent_graph`](../../src/harness/services/agent_graph.py) | Authoritative thread DAG tracking subagent spawns and token rollups. |
| `AGENT_HARNESS_ARCHITECT_SERVICE_KEY` | `AgentHarnessArchitectService` | [`harness.services.agent_harness`](../../src/harness/services/agent_harness.py) | 5-part harness architecture and 4-mechanism reliability auditor. |
| `AI_NATIVE_HARNESS_SERVICE_KEY` | `AiNativeHarnessService` | [`harness.services.ai_native_harness`](../../src/harness/services/ai_native_harness.py) | 4-gate behavioral pipeline and credential-free MCP security. |
| `CODING_HARNESS_CALIBRATOR_KEY` | `CodingHarnessCalibratorService` | [`harness.services.coding_harness_calibrator`](../../src/harness/services/coding_harness_calibrator.py) | Context staging calibration (T0-T4) and action space benchmarking. |
| `COMPUTE_ASSESSOR_SERVICE_KEY` | `ComputeAssessorService` | [`harness.services.compute_assessor`](../../src/harness/services/compute_assessor.py) | 5D task complexity assessment and model tier allocation. |
| `DYNAMIC_MODEL_ROUTER_SERVICE_KEY` | `DynamicModelRouterService` | [`harness.services.dynamic_model_router`](../../src/harness/services/dynamic_model_router.py) | Sub-5ms query complexity classification and dynamic failover. |
| `HARNESS_COMPASS_SERVICE_KEY` | `HarnessCompassService` | [`harness.services.harness_compass`](../../src/harness/services/harness_compass.py) | Autonomous agent harness benchmarking and constrained evolution. |
| `SELF_EVAL_PIPELINE_SERVICE_KEY` | `SelfEvaluatingPipelineService` | [`harness.services.self_evaluating_pipeline`](../../src/harness/services/self_evaluating_pipeline.py) | Prompt evaluation pipelines, gold standard assertions, and tuning. |
| `DETERMINISTIC_VALIDATION_SERVICE_KEY` | `DeterministicValidationService` | [`harness.services.deterministic_validation`](../../src/harness/services/deterministic_validation.py) | Spec-first deterministic validation loops with error injection. |
| `UNCERTAINTY_GUARD_SERVICE_KEY` | `UncertaintyGuardService` | [`harness.services.uncertainty_guard`](../../src/harness/services/uncertainty_guard.py) | 3-layer boundary check, retrieval scoring, and logprob validation. |

---

## 2. Code Intelligence, AST & Security Services

| ServiceKey Constant | Inferred Type | Defining Module | Central Function |
|---|---|---|---|
| `TOOL_REGISTRY_KEY` | `ToolRegistry` | [`harness.services.tools`](../../src/harness/services/tools.py) | Registry of callable, schema-validated agent tools. |
| `FILESYSTEM_GIT_KEY` | `FilesystemGitService` | [`harness.services.filesystem_git`](../../src/harness/services/filesystem_git.py) | Transactional Git checkpoints, atomic commits, and rollbacks. |
| `ARCH_LINTER_KEY` | `ArchLinterService` | [`harness.services.arch_linter`](../../src/harness/services/arch_linter.py) | In-flight syntax checking and architectural boundary verification. |
| `CODE_RUNNER_KEY` | `CodeRunnerService` | [`harness.services.code_runner`](../../src/harness/services/code_runner.py) | Isolated execution of test scripts and subprocesses. |
| `PRE_COMMIT_SECURITY_GUARD_KEY` | `PreCommitSecurityGuardService` | [`harness.services.pre_commit_security_guard`](../../src/harness/services/pre_commit_security_guard.py) | Pre-commit security interceptor executing SAST and secret checks. |
| `REFACTOR_ENGINE_KEY` | `RefactorEngineService` | [`harness.services.refactor_engine`](../../src/harness/services/refactor_engine.py) | AST-aware automated code refactoring and seam consolidation. |
| `TEST_RUNNER_KEY` | `TestRunnerService` | [`harness.services.test_runner`](../../src/harness/services/test_runner.py) | Dispatches unit and integration test suites. |
| `REPO_MAP_SERVICE_KEY` | `RepoMapService` | [`harness.services.repomap`](../../src/harness/services/repomap.py) | Dynamic PageRanked AST repo map generator for context prompts. |
| `UNIFIED_CONTEXT_PIPELINE_KEY` | `UnifiedContextPipelineService` | [`harness.services.unified_context`](../../src/harness/services/unified_context.py) | Multi-pass pre-LLM context pruner and token budgeter. |
| `CONTEXT_COMPACTOR_KEY` | `ContextCompactorService` | [`harness.services.context_compactor`](../../src/harness/services/context_compactor.py) | Middle-out reduction of large tool outputs in session history. |
| `ARTIFACT_GENERATOR_KEY` | `ArtifactGeneratorService` | [`harness.services.artifact_generator`](../../src/harness/services/artifact_generator.py) | Generates interactive HTML Visual Briefs and Mermaid diagrams. |
| `NETWORK_FORENSICS_SERVICE_KEY` | `NetworkForensicsService` | [`harness.services.network_forensics`](../../src/harness/services/network_forensics.py) | Packet capture dissection and TCP flag network analysis. |

---

## 3. Knowledge, Epistemics & Memory Services

| ServiceKey Constant | Inferred Type | Defining Module | Central Function |
|---|---|---|---|
| `SKILL_GRAPH_SERVICE_KEY` | `SkillKnowledgeGraphService` | [`harness.services.skill_graph`](../../src/harness/services/skill_graph.py) | Directed skill knowledge graph with shortest-path chaining. |
| `SKILL_PARSER_SERVICE_KEY` | `SkillCardParserService` | [`harness.services.skill_parser`](../../src/harness/services/skill_parser.py) | Parses `CARD.md` metadata boxes and `SKILL.md` documents. |
| `SKILL_CLUSTERING_SERVICE_KEY` | `SkillClusteringService` | [`harness.services.skill_clustering`](../../src/harness/services/skill_clustering.py) | Semantic and topological clustering across skill catalogs. |
| `SKILL_VISUALIZER_SERVICE_KEY` | `SkillVisualizerService` | [`harness.services.skill_visualizer`](../../src/harness/services/skill_visualizer.py) | Renders interactive HTML Visual Briefs of skill graphs. |
| `OKF_MEMORY_SERVICE_KEY` | `OkfMemoryService` | [`harness.services.okf_memory`](../../src/harness/services/okf_memory.py) | Open Knowledge Framework (OKF v0.2) Git-native memory. |
| `VECTOR_INDEX_SERVICE_KEY` | `VectorIndexService` | [`harness.services.vector_index`](../../src/harness/services/vector_index.py) | Dense vector cosine similarity search and embedding store. |
| `MEMGRAPHRAG_SERVICE_KEY` | `MemGraphRagService` | [`harness.services.memgraphrag`](../../src/harness/services/memgraphrag.py) | Hybrid graph and retrieval-augmented generation memory index. |
| `GRAPHITI_SERVICE_KEY` | `GraphitiService` | [`harness.services.graphiti`](../../src/harness/services/graphiti.py) | Temporal knowledge graph tracking entity evolutions over time. |
| `DISCOVERY_INDEX_SERVICE_KEY` | `DiscoveryIndexService` | [`harness.services.discovery_index`](../../src/harness/services/discovery_index.py) | Discovers and catalogs public record archives and research corpora. |

---

## 4. Data Engineering, Documentation & External Bridges

| ServiceKey Constant | Inferred Type | Defining Module | Central Function |
|---|---|---|---|
| `DOC_BUILDER_SERVICE_KEY` | `HfDocBuilderService` | [`harness.services.doc_builder`](../../src/harness/services/doc_builder.py) | HuggingFace doc-builder AST compiler, autodoc, and mock loader. |
| `DOC_SYNCHRONIZER_KEY` | `DocSynchronizerService` | [`harness.services.doc_synchronizer`](../../src/harness/services/doc_synchronizer.py) | Codebase doc coverage auditor, drift checker, and scaffolder. |
| `BIGQUERY_AUGMENTED_ANALYTICS_SERVICE_KEY` | `BigQueryAugmentedAnalyticsService` | [`harness.services.bigquery_augmented_analytics`](../../src/harness/services/bigquery_augmented_analytics.py) | BigQuery Table-Valued Functions (TVFs) and causal inference. |
| `GARF_REPORTING_SERVICE_KEY` | `GarfReportingService` | [`harness.services.garf_reporting`](../../src/harness/services/garf_reporting.py) | Declarative SQL reporting pipelines across heterogeneous APIs. |
| `OPEN_SOURCE_GIS_SERVICE_KEY` | `OpenSourceGisService` | [`harness.services.open_source_gis`](../../src/harness/services/open_source_gis.py) | Multi-engine geospatial analysis with CRS safety verification. |
| `PAPERLESS_NGX_SERVICE_KEY` | `PaperlessNgxService` | [`harness.services.paperless_ngx`](../../src/harness/services/paperless_ngx.py) | Document classification and hybrid Tantivy/SQLite-Vec search. |
| `HF_DATASETS_SERVICE_KEY` | `HfDatasetsService` | [`harness.services.hf_datasets`](../../src/harness/services/hf_datasets.py) | Arrow memory mapping and streaming for large datasets. |
| `DATA_MANAGEMENT_SERVICE_KEY` | `DataManagementService` | [`harness.services.data_management`](../../src/harness/services/data_management.py) | DAMA-DMBOK data lifecycle governance and open data contracts. |
| `TAU_BRIDGE_SERVICE_KEY` | `TauBridgeService` | [`harness.services.tau_bridge`](../../src/harness/services/tau_bridge.py) | Bidirectional bridge to the HuggingFace Tau coding harness. |
| `CLAUDE_CODE_BRIDGE_KEY` | `ClaudeCodeBridgeService` | [`harness.services.claude_code`](../../src/harness/services/claude_code.py) | Claude Code prompt compaction and dangerous bash hooks. |
| `STAGEHAND_BROWSER_KEY` | `StagehandBrowserService` | [`harness.services.stagehand_browser`](../../src/harness/services/stagehand_browser.py) | Autonomous headless browser orchestration and DOM extraction. |
| `WEB_FETCHER_KEY` | `WebFetcherService` | [`harness.services.web_fetcher`](../../src/harness/services/web_fetcher.py) | Direct HTTP streaming and HTML-to-markdown conversion. |
| `CELLCOG_SERVICE_KEY` | `CellCogService` | [`harness.services.cellcog`](../../src/harness/services/cellcog.py) | Multimodal sub-agent delegation for 3D, video, and audio. |
| `CHATBOTX_SERVICE_KEY` | `ChatbotXService` | [`harness.services.chatbotx`](../../src/harness/services/chatbotx.py) | Omnichannel messaging bot orchestration and webhook routing. |

---

## 5. Storage, Events & Core Infrastructure Services

| ServiceKey Constant | Inferred Type | Defining Module | Central Function |
|---|---|---|---|
| `STORAGE_SERVICE_KEY` | `StorageService` | [`harness.services.storage`](../../src/harness/services/storage.py) | SQLite persistence engine with transactional support. |
| `EVENT_BUS_KEY` | `EventBus` | [`harness.events.bus`](../../src/harness/events/bus.py) | Async event bus dispatching immutable domain events. |
| `LLM_SERVICE_KEY` | `LLMService` | [`harness.services.llm`](../../src/harness/services/llm.py) | Multi-provider LLM client protocol and completion gateway. |
| `CREATOR_SERVICE_KEY` | `CreatorService` | [`harness.creator.synthesis`](../../src/harness/creator/synthesis.py) | Autonomous plugin synthesis and capability creator. |
| `OPENROUTER_GATEWAY_KEY` | `OpenRouterGatewayService` | [`harness.services.openrouter_gateway`](../../src/harness/services/openrouter_gateway.py) | Multi-model routing gateway with token telemetry. |
