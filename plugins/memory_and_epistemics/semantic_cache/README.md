# plugin.semantic_cache (v1.0.0)

Similarity-based semantic cache for LLM prompts and agent task results

---

## Overview & Metadata

| Property | Value |
|---|---|
| Plugin Directory | `plugins/memory_and_epistemics/semantic_cache` |
| Category | `memory_and_epistemics` |
| Isolation Mode | `in_process` |
| Services Provided | `service.semantic_cache` |
| Dependencies Required | None |

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `cache_set` | `(prompt, response, ttl)` | Store a prompt and response in the semantic cache with optional TTL |
| `cache_get` | `(prompt, similarity_threshold)` | Retrieve cached response based on prompt token similarity threshold |
| `cache_stats` | `()` | Get current cache metrics including hits, misses, and hit rate |
| `cache_clear` | `()` | Purge all cached entries |

---

## Key Modules & AST Symbols

### Module [main.py](main.py)

Semantic Cache Plugin for Brain Harness.

Provides similarity-based caching for LLM prompts and computational results,
reducing redundant token costs and latency across agent workflows.

#### Classes

- `class SemanticCachePlugin` — Plugin providing semantic response caching capabilities.
  - `def __init__(service) -> None`
  - `def provides() -> list[ServiceKey[Any]]`
  - `def requires() -> list[ServiceKey[Any]]`
  - `def on_load(ctx) -> None`
  - `def on_enable() -> None`
  - `def on_disable() -> None`
  - `def on_unload() -> None`


#### Functions

- `def cache_set(prompt, response, ttl) -> dict[str, Any]` — Cache a prompt response pair.
- `def cache_get(prompt, similarity_threshold) -> dict[str, Any]` — Retrieve a cached response if similarity >= threshold.
- `def cache_stats() -> dict[str, Any]` — Return cache statistics.
- `def cache_clear() -> dict[str, Any]` — Clear the cache.


---

## Quickstart & Usage

```python
from harness.kernel.context import ServiceContext
from plugins.memory_and_epistemics.semantic_cache.main import plugin

# Load plugin into harness service context
context = ServiceContext()
plugin.on_load(context)
```

---

## Architecture & Diátaxis Classification

- Diátaxis Quadrant: Reference (Track B) & How-To Guides
- Isolation: `in_process` execution sandbox
- Invariants: Slotted dataclass architecture (Rule 12), transactional context bounds (Rule 8), and zero-fork YAML configuration (Rule 44).
