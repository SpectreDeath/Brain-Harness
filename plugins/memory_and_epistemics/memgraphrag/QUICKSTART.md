# 🧠 MemGraphRAG Plugin Quickstart & Architecture Card

## Overview

The `plugin.memgraphrag` plugin provides a **Three-Layer Memory Hierarchy** and **Hybrid Graph Retrieval Engine** for Brain Harness agents.

It structures conversational, episodic, and document knowledge across three interconnected layers:
1. **Schema Layer (Ontology)**: Abstract triples `(head_type, relation, tail_type)` representing high-level conceptual patterns.
2. **Fact Layer (Triples)**: Concrete factual relations `(head, relation, tail)` with passage citation links and frequency tracking.
3. **Passage Layer (Text Chunks)**: Original grounded text chunks and evidence sources.

---

## 🛠️ Exported Agent Tools

| Tool Name | Purpose | Key Parameters |
|---|---|---|
| `memgraphrag_index` | Ingests document passages, extracts triples, induces ontology schemas, resolves conflicts, and compiles graph. | `docs`, `save_dir`, `chunk_size`, `skip_conflict_resolution` |
| `memgraphrag_retrieve` | Executes hybrid multi-layer graph retrieval (TF-IDF seeds + Personalized PageRank graph propagation). | `query`, `save_dir`, `num_to_retrieve`, `damping` |
| `memgraphrag_query` | End-to-end question answering synthesized from retrieved memory graph evidence. | `query`, `save_dir`, `num_passages` |
| `memgraphrag_add_passage` | Incrementally adds a passage chunk and updates memory graph indices. | `chunk_id`, `content`, `extracted_triples`, `schema_tuple` |
| `memgraphrag_get_memory_summary` | Inspects schema, fact, and passage layer counts and graph density. | `save_dir` |
| `memgraphrag_detect_conflicts` | Identifies contradictory facts and clusters them with supporting passage citations. | `save_dir` |

---

## ⚡ Usage Examples

### 1. Ingest Documents & Compile Memory Graph
```python
from harness.plugins.loader import PluginLoader

res = memgraphrag_index(
    docs=[
        "MemGraphRAG organizes knowledge into three connected layers: schema, fact, and passage.",
        "The schema layer stores abstract ontology triples, while the fact layer stores concrete relations.",
        "MemGraphRAG was developed by researchers at Xiamen University.",
    ],
    save_dir="outputs/default",
)
print(res)
# {"status": "ok", "passages_count": 3, "facts_count": 4, "schemas_count": 3, ...}
```

### 2. Hybrid Graph Retrieval
```python
ret = memgraphrag_retrieve(
    query="How does MemGraphRAG organize knowledge?",
    num_to_retrieve=3,
    damping=0.5,
)
for p in ret["passages"]:
    print(f"Passage [{p['chunk_id']}]: {p['content']} (Score: {p['score']})")
```

### 3. Service Protocol Resolution
```python
from harness.kernel.context import ServiceContext
from harness.services.memgraphrag import MEMGRAPHRAG_MEMORY_KEY

# In an agent loop or plugin:
mem_service = context.resolve(MEMGRAPHRAG_MEMORY_KEY)
query_result = await mem_service.query("What layers exist in MemGraphRAG?")
print(query_result.answer)
```
