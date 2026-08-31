# KI: Unified 5-Stage Pre-LLM Context Pipeline Seam

## Operational Summary
Pre-LLM context compilation must not rely on fragmented, duck-typed string lookups or simple head/tail string chopping. All token governance, code structure injection, and middle-out compaction are encapsulated inside `UnifiedContextPipelineService` registered under `UNIFIED_CONTEXT_PIPELINE_KEY`.

## Pipeline Execution Stages
1. **Observation Truncation & Normalization**: Enforces character ceilings on large output buffers while preserving head/tail snippets.
2. **PageRanked AST Repo Map Injection**: Queries `RepoMapService` to inject an indexed code skeleton prioritized by token budget and query context into the system message.
3. **Progressive Middle-Out Tool Compaction**: Invokes `ContextCompactorService` applying progressive 0% -> 50% tool output truncation for older turns.
4. **Sliding Window Preservation & Summarization**: Preserves initial prompt anchors and the most recent N turns while condensing intermediate dialogue.
5. **Strict Token Budget Enforcement**: Verifies total token estimates against the configured budget before model dispatch.

## Key Code References
- Implementation: [`src/harness/services/unified_context.py`](file:///D:/GitHub/projects/Brain%20Harness/src/harness/services/unified_context.py)
- Delegation Seam: [`src/harness/agent/context_optimizer.py`](file:///D:/GitHub/projects/Brain%20Harness/src/harness/agent/context_optimizer.py)
- Unit Tests: [`tests/test_unified_context_pipeline.py`](file:///D:/GitHub/projects/Brain%20Harness/tests/test_unified_context_pipeline.py)
