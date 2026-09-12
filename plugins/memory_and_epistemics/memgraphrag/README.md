# plugin.memgraphrag (v0.1.0)

Three-layer memory knowledge graph engine with conflict-aware graph construction and hybrid PPR retrieval

---

## Overview & Metadata

- **Plugin Directory**: `plugins/memory_and_epistemics/memgraphrag`
- **Isolation Mode**: `subprocess`
- **Services Provided**: None
- **Dependencies Required**: None

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `memgraphrag_index` | `(docs, save_dir, chunk_size, chunk_overlap, skip_conflict_resolution)` | Ingest document passages, construct the 3-layer memory hierarchy, and build the retrieval graph |
| `memgraphrag_retrieve` | `(query, save_dir, num_to_retrieve, damping, passage_node_weight)` | Execute hybrid multi-layer graph retrieval combining dense similarity and Personalized PageRank |
| `memgraphrag_query` | `(query, save_dir, num_passages)` | Synthesize an answer using retrieved multi-layer knowledge graph evidence |
| `memgraphrag_add_passage` | `(chunk_id, content, extracted_triples, schema_tuple, save_dir)` | Incrementally inject a passage chunk and factual relation triples into the active memory graph |
| `memgraphrag_get_memory_summary` | `(save_dir)` | Inspect statistical distribution and count metrics for schema, fact, and passage layers |
| `memgraphrag_detect_conflicts` | `(save_dir)` | Scan candidate facts for hard semantic contradictions with supporting passage evidence groups |

---

## Key Modules & AST Symbols

### Module [`engine.py`](engine.py)

Core Three-Layer Memory & Hybrid Graph Retrieval Engine for MemGraphRAG.

#### Classes

- `class ThreeLayerMemory`
  Three-layer hierarchical memory holding Schemas, Facts, and Passages.
  - `def __init__() -> None`
  - `def get_or_create_schema(ontology) -> int`
  - `def get_or_create_fact(triple, schema_idx) -> int`
  - `def get_or_create_passage(chunk_id, content) -> int`
  - `def link_passage_and_fact(passage_idx, fact_idx) -> None`
  - `def link_fact_and_schema(fact_idx, schema_idx) -> None`
  - `def to_dict() -> dict[str, Any]`
  - `def from_dict(cls, data) -> 'ThreeLayerMemory'`
- `class MemGraphRAGEngine`
  Full-featured Three-Layer Memory and Hybrid Graph Retrieval Engine.
  - `def __init__(default_save_dir) -> None`
  - `def get_memory(save_dir) -> ThreeLayerMemory`
  - `def index(docs, save_dir, chunk_size, chunk_overlap, skip_conflict_resolution) -> dict[str, Any]`
  - `def retrieve(query, save_dir, num_to_retrieve, damping, passage_node_weight) -> dict[str, Any]`
  - `def query(query, save_dir, num_passages) -> dict[str, Any]`
  - `def add_passage(chunk_id, content, extracted_triples, schema_tuple, save_dir) -> dict[str, Any]`
  - `def get_summary(save_dir) -> dict[str, Any]`
  - `def detect_conflicts(save_dir) -> dict[str, Any]`


### Module [`main.py`](main.py)

MemGraphRAG Plugin & HarnessPlugin Service Implementation.

#### Classes

- `class MemGraphRAGPlugin`
  Harness Plugin implementing MemGraphRAGService and registering MEMGRAPHRAG_MEMORY_KEY.
  - `def __init__() -> None`
  - `def provides() -> list[ServiceKey[Any]]`
  - `def requires() -> list[ServiceKey[Any]]`
  - `def on_load(ctx) -> None`
  - `def on_enable() -> None`
  - `def on_disable() -> None`
  - `def on_unload() -> None`
  - `def index(docs, save_dir, chunk_size, chunk_overlap, skip_conflict_resolution) -> MemGraphRAGIndexResult`
  - `def retrieve(query, num_to_retrieve, damping, passage_node_weight) -> MemGraphRAGRetrieveResult`
  - `def query(query, num_passages) -> MemGraphRAGQueryResult`
  - `def add_passage(chunk_id, content, extracted_triples, schema_tuple) -> PassageResult`
  - `def get_summary(save_dir) -> MemGraphRAGSummaryResult`
  - `def detect_conflicts(save_dir) -> MemGraphRAGConflictResult`


#### Functions

- `def memgraphrag_index(docs, save_dir, chunk_size, chunk_overlap, skip_conflict_resolution) -> dict[str, Any]`
  - Ingest document passages, construct the 3-layer memory hierarchy, and build the retrieval graph.
- `def memgraphrag_retrieve(query, save_dir, num_to_retrieve, damping, passage_node_weight) -> dict[str, Any]`
  - Execute hybrid multi-layer graph retrieval combining dense similarity and Personalized PageRank.
- `def memgraphrag_query(query, save_dir, num_passages) -> dict[str, Any]`
  - Synthesize an answer using retrieved multi-layer knowledge graph evidence.
- `def memgraphrag_add_passage(chunk_id, content, extracted_triples, schema_tuple, save_dir) -> dict[str, Any]`
  - Incrementally inject a passage chunk and factual relation triples into the active memory graph.
- `def memgraphrag_get_memory_summary(save_dir) -> dict[str, Any]`
  - Inspect statistical distribution and count metrics for schema, fact, and passage layers.
- `def memgraphrag_detect_conflicts(save_dir) -> dict[str, Any]`
  - Scan candidate facts for hard semantic contradictions with supporting passage evidence groups.


### Module [`models.py`](models.py)

Data models for MemGraphRAG 3-Layer Memory (Schema, Fact, Passage) and Conflict Groups.

#### Classes

- `class SchemaNode`
  Schema layer node: stores abstract ontology triple (head_type, relation, tail_type).
  - `def to_dict() -> dict[str, Any]`
  - `def from_dict(cls, data) -> 'SchemaNode'`
- `class FactNode`
  Fact layer node: stores concrete relational triple (head, relation, tail).
  - `def to_dict() -> dict[str, Any]`
  - `def from_dict(cls, data) -> 'FactNode'`
- `class PassageNode`
  Passage layer node: stores original text chunks and citation identifiers.
  - `def to_dict() -> dict[str, Any]`
  - `def from_dict(cls, data) -> 'PassageNode'`
- `class ConflictGroupModel`
  Pydantic model representing a semantic conflict group.


### Module [`test_memgraphrag.py`](test_memgraphrag.py)

Tests for MemGraphRAG 3-Layer Memory Plugin and Engine.

#### Functions

- `def temp_output_dir(tmp_path) -> str`
- `def test_three_layer_memory_basic_operations()`
- `def test_memgraphrag_index_and_conflict_resolution(temp_output_dir)`
- `def test_memgraphrag_retrieve_and_query(temp_output_dir)`
- `def test_memgraphrag_incremental_add_passage(temp_output_dir)`
- `def test_memgraphrag_plugin_service_lifecycle(temp_output_dir)`



---

## Related Documentation & Configuration
- Manifest: [`plugin.json`](plugin.json)
- Architecture Seams: [Context Architecture](../../../CONTEXT-MAP.md) | [User Manual](../../../USER_MANUAL.md)
