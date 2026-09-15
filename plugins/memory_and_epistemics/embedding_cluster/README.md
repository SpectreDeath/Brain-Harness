# plugin.embedding_cluster (v1.0.0)

Unsupervised text chunk clustering, topic keyword extraction, and cluster summary generator

---

## Overview & Metadata

| Property | Value |
|---|---|
| Plugin Directory | `plugins/memory_and_epistemics/embedding_cluster` |
| Category | `memory_and_epistemics` |
| Isolation Mode | `in_process` |
| Services Provided | `service.embedding_cluster` |
| Dependencies Required | None |

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `cluster_text_chunks` | `(texts, num_clusters)` | Cluster a collection of text documents or chunks into K topic groups based on TF-IDF representation |
| `extract_cluster_topic_keywords` | `(cluster_texts, top_n)` | Extract top TF-IDF keywords characterizing a cluster group |

---

## Key Modules & AST Symbols

### Module [main.py](main.py)

Unsupervised text clustering and topic extraction plugin for Brain Harness.

#### Classes

- `class EmbeddingClusterPlugin` — Harness Plugin providing unsupervised text clustering and topic extraction services.
  - `def provides() -> list[ServiceKey[Any]]`
  - `def requires() -> list[ServiceKey[Any]]`
  - `def on_load(ctx) -> None`
  - `def on_enable() -> None`
  - `def on_disable() -> None`
  - `def on_unload() -> None`
  - `def cluster_text_chunks(texts, num_clusters) -> ClusterTextResult`
  - `def extract_cluster_topic_keywords(cluster_texts, top_n) -> ClusterKeywordsResult`


#### Functions

- `def cluster_text_chunks(texts, num_clusters) -> dict[str, Any]` — K-Means clustering over text documents using TF-IDF representation.
- `def extract_cluster_topic_keywords(cluster_texts, top_n) -> dict[str, Any]` — Extract most salient terms in a text cluster.


---

## Quickstart & Usage

```python
from harness.kernel.context import ServiceContext
from plugins.memory_and_epistemics.embedding_cluster.main import plugin

# Load plugin into harness service context
context = ServiceContext()
plugin.on_load(context)
```

---

## Architecture & Diátaxis Classification

- Diátaxis Quadrant: Reference (Track B) & How-To Guides
- Isolation: `in_process` execution sandbox
- Invariants: Slotted dataclass architecture (Rule 12), transactional context bounds (Rule 8), and zero-fork YAML configuration (Rule 44).
