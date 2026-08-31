# KI: Typed IoC Context Pipeline & Authoritative Swarm DAG Store

## Operational Summary
Pre-LLM context transformations and multi-agent swarm coordinate trees require deep, unified IoC service seams. Context pruning and AST RepoMap injection must be encapsulated behind strongly-typed service protocols rather than string lookups or duck-typing. Simultaneously, multi-agent hierarchies must maintain directional execution graphs with token and runtime rollups for observability and export.

## Architecture Invariants

1. **Typed Unified Context Pipeline (`UNIFIED_CONTEXT_PIPELINE_KEY`)**:
   - Registered under `ServiceKey[UnifiedContextPipelineService]("service.unified_context_pipeline")`.
   - Encapsulates 5 multi-pass optimization stages behind a unified `process_context(request)` call:
     1. Whitespace deduplication and observation character ceiling enforcement.
     2. PageRanked AST Repo Map injection (`RepoMapService`).
     3. Progressive middle-out tool output compaction (`ContextCompactorService`).
     4. Sliding window preservation with structured conversation summarization.
     5. Strict token budget enforcement.
   - Eliminates untyped string lookups (e.g. `ServiceKey[Any]("domain.unified_context_pipeline")`) and duck-typed `hasattr` probes across the codebase.

2. **Authoritative Agent Execution Graph Store (`AGENT_GRAPH_STORE_KEY`)**:
   - Registered under `ServiceKey[AgentExecutionGraphService]("service.agent_graph_store")`.
   - Tracks directional spawn edges with explicit lifecycle states (`Open`, `Closed`, `Failed`, `Completed`).
   - Automatically rolls up token consumption and runtime duration across parent-child agent swarms.
   - Exposes headless inspection seams producing structured JSON DAG models and formatted ASCII trees (`harness session tree`).

## Key Code References
- Context Pipeline Protocol & Implementation: [`src/harness/services/unified_context.py`](file:///D:/GitHub/projects/Brain%20Harness/src/harness/services/unified_context.py)
- Agent Graph Store Protocol & Implementation: [`src/harness/services/agent_graph.py`](file:///D:/GitHub/projects/Brain%20Harness/src/harness/services/agent_graph.py)
- Agent Step Context Optimizer: [`src/harness/agent/context_optimizer.py`](file:///D:/GitHub/projects/Brain%20Harness/src/harness/agent/context_optimizer.py)
- Unit Tests: [`tests/test_unified_context_pipeline.py`](file:///D:/GitHub/projects/Brain%20Harness/tests/test_unified_context_pipeline.py), [`tests/test_agent_graph_store.py`](file:///D:/GitHub/projects/Brain%20Harness/tests/test_agent_graph_store.py)
