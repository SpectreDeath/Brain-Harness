# plugin.vector_index (v1.0.0)

Local semantic vector index, natural language code/doc retrieval, and hybrid search

---

## Overview & Metadata

| Property | Value |
|---|---|
| Plugin Directory | `plugins/memory_and_epistemics/vector_index` |
| Category | `memory_and_epistemics` |
| Isolation Mode | `in_process` |
| Services Provided | `service.vector_index` |
| Dependencies Required | None |

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `vector_index_directory` | `(path, extensions, chunk_lines)` | Scan and index source code or markdown documents in a directory for semantic search |
| `vector_search_semantic` | `(query, top_k)` | Perform natural language semantic cosine search over the indexed chunks |
| `vector_search_hybrid` | `(query, keyword, top_k)` | Perform hybrid lexical + semantic search combining exact keyword and vector ranking |

---

## Key Modules & AST Symbols

### Module [main.py](main.py)

Local semantic vector index and retrieval plugin for Brain Harness.

#### Classes

- `class VectorIndexEngine` — Encapsulated engine managing local vector indexing and semantic retrieval.
  - `def __init__() -> None`
  - `def index_directory(path, extensions, chunk_lines) -> dict[str, Any]`
  - `def search_semantic(query, top_k) -> dict[str, Any]`
  - `def search_hybrid(query, keyword, top_k) -> dict[str, Any]`
- `class VectorIndexPlugin` — Harness Plugin providing local document vector indexing, semantic search, and hybrid retrieval.
  - `def __init__(engine) -> None`
  - `def provides() -> list[ServiceKey[Any]]`
  - `def requires() -> list[ServiceKey[Any]]`
  - `def on_load(ctx) -> None`
  - `def on_enable() -> None`
  - `def on_disable() -> None`
  - `def on_unload() -> None`
  - `def index_directory(path, extensions, chunk_lines) -> VectorIndexResult`
  - `def index_directory_async(path, extensions, chunk_lines) -> VectorIndexResult`
  - `def search_semantic(query, top_k) -> VectorSearchResult`
  - `def search_semantic_async(query, top_k) -> VectorSearchResult`
  - `def search_hybrid(query, keyword, top_k) -> VectorHybridSearchResult`
  - `def search_hybrid_async(query, keyword, top_k) -> VectorHybridSearchResult`


#### Functions

- `def vector_index_directory(path, extensions, chunk_lines) -> dict[str, Any]` — Scan and index documents in a directory for semantic search.
- `def vector_search_semantic(query, top_k) -> dict[str, Any]` — Perform natural language cosine similarity search.
- `def vector_search_hybrid(query, keyword, top_k) -> dict[str, Any]` — Perform hybrid search combining semantic score with exact keyword boosting.


---

## Quickstart & Usage

```python
from harness.kernel.context import ServiceContext
from plugins.memory_and_epistemics.vector_index.main import plugin

# Load plugin into harness service context
context = ServiceContext()
plugin.on_load(context)
```

---

## Architecture & Diátaxis Classification

- Diátaxis Quadrant: Reference (Track B) & How-To Guides
- Isolation: `in_process` execution sandbox
- Invariants: Slotted dataclass architecture (Rule 12), transactional context bounds (Rule 8), and zero-fork YAML configuration (Rule 44).
