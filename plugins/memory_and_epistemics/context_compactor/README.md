# plugin.context_compactor (v1.0.0)

Agent trajectory summarization, context compaction, and persistent memory offloading via Memtext

---

## Overview & Metadata

| Property | Value |
|---|---|
| Plugin Directory | `plugins/memory_and_epistemics/context_compactor` |
| Category | `memory_and_epistemics` |
| Isolation Mode | `in_process` |
| Services Provided | `service.context_compactor` |
| Dependencies Required | None |

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `compact_conversation` | `(messages, preserve_recent)` | Compact a message list by summarizing earlier history while preserving recent messages |
| `offload_to_memory` | `(key, content, topic)` | Offload important notes, code snippets, or facts to Memtext persistent memory |
| `recall_context` | `(query, limit)` | Recall stored memories and context matching a query |

---

## Key Modules & AST Symbols

### Module [main.py](main.py)

Context compactor and Memtext memory offloading plugin.

#### Classes

- `class ContextCompactorEngine` — Encapsulated engine for conversation compaction and fallback memory offloading.
  - `def __init__() -> None`
  - `def compact_conversation(messages, preserve_recent) -> dict[str, Any]`
  - `def offload_to_memory(key, content, topic) -> dict[str, Any]`
  - `def recall_context(query, limit) -> dict[str, Any]`
- `class ContextCompactorPlugin` — Harness Plugin providing conversation compaction and memory offloading services.
  - `def __init__(engine) -> None`
  - `def provides() -> list[ServiceKey[Any]]`
  - `def requires() -> list[ServiceKey[Any]]`
  - `def on_load(ctx) -> None`
  - `def on_enable() -> None`
  - `def on_disable() -> None`
  - `def on_unload() -> None`
  - `def compact_conversation(messages, preserve_recent) -> CompactConversationResult`
  - `def offload_to_memory(key, content, topic) -> OffloadMemoryResult`
  - `def recall_context(query, limit) -> RecallMemoryResult`


#### Functions

- `def compact_conversation(messages, preserve_recent) -> dict[str, Any]` — Compress older conversation turns while keeping recent interactions intact.
- `def offload_to_memory(key, content, topic) -> dict[str, Any]` — Store fact or observation into memory.
- `def recall_context(query, limit) -> dict[str, Any]` — Search and recall relevant memories.


---

## Quickstart & Usage

```python
from harness.kernel.context import ServiceContext
from plugins.memory_and_epistemics.context_compactor.main import plugin

# Load plugin into harness service context
context = ServiceContext()
plugin.on_load(context)
```

---

## Architecture & Diátaxis Classification

- Diátaxis Quadrant: Reference (Track B) & How-To Guides
- Isolation: `in_process` execution sandbox
- Invariants: Slotted dataclass architecture (Rule 12), transactional context bounds (Rule 8), and zero-fork YAML configuration (Rule 44).
