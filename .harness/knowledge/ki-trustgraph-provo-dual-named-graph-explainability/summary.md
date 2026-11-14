# TrustGraph: PROV-O Dual Named Graph Isolation & 5-Stage Explainability

## Overview
- **Source Repository**: `https://github.com/trustgraph-ai/trustgraph` (`17e5d742`)
- **Primary Files**:
  - `trustgraph-base/trustgraph/provenance/uris.py#L1-L140`
  - `trustgraph-base/trustgraph/provenance/triples.py#L1-L140`

## Core Architecture & Invariants
1. **Dual Named-Graph Partitioning (`set_graph`)**: Extraction and document ingestion records target `urn:graph:source`, while query reasoning and explainability triples target `urn:graph:retrieval`.
2. **Namespace Separation**: Extraction entities emit canonical `https://trustgraph.ai/...` URIs via `document_triples()`, whereas per-query explainability entities emit `urn:trustgraph:question:{id}` and `urn:trustgraph:prov:{stage}:{id}` URIs.
3. **Five-Stage Query Explainability Chain**: Reasoning traces emit structured PROV-O lineage across five deterministic stages in order: `question`, `grounding`, `exploration`, `focus`, and `synthesis`.
4. **Token Telemetry Binding (`_append_token_triples`)**: Synthesis and intermediate stage nodes optionally attach prompt/completion token counts directly as PROV-O triples so cost attribution travels alongside citation lineage.

## Decision Heuristics & Anti-Patterns
- **Never mix ingestion lineage and runtime RAG traces into the default unnamed graph**: Partition strictly between `urn:graph:source` and `urn:graph:retrieval`.
- **Never emit partial explainability graphs with unlinked stages**: Anchor every reasoning stage (`grounding`, `exploration`, `focus`, `synthesis`) back to `urn:trustgraph:question:{id}`.
