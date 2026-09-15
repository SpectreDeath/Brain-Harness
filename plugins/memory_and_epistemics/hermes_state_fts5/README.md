# domain.hermes_state_fts5 (v1.0.0)

Hermes SQLite WAL state storage with FTS5 search, parent-child session compression splitting, and cross-session recall

---

## Overview & Metadata

| Property | Value |
|---|---|
| Plugin Directory | `plugins/memory_and_epistemics/hermes_state_fts5` |
| Category | `memory_and_epistemics` |
| Isolation Mode | `in_process` |
| Services Provided | `service.hermes_state_fts5` |
| Dependencies Required | None |

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `fts5_search_messages` | `(query, session_id, limit)` | Execute fast full-text search across historical conversation trajectories |
| `fork_session_tree` | `(parent_session_id, compression_checkpoint)` | Fork session history into a child branch with parent_session_id compression linkage |
| `compress_session_slice` | `(session_id, window_size)` | Apply AST/textual compression to a window of messages to bound token context |
| `query_session_provenance` | `(message_id)` | Retrieve full lineage and parent DAG coordinates for a given message or checkpoint |

---

## Key Modules & AST Symbols

### Module [main.py](main.py)

Hermes State FTS5 — persistent SQLite WAL message store and session lineage DAG.

#### Functions

- `def fts5_search_messages(query, session_id, limit) -> dict[str, Any]` — Execute FTS5 search across indexed conversation messages.
- `def fork_session_tree(parent_session_id, compression_checkpoint) -> dict[str, Any]` — Create child session linked to parent session DAG.
- `def compress_session_slice(session_id, window_size) -> dict[str, Any]` — Compress older turns in session while preserving active window.
- `def query_session_provenance(message_id) -> dict[str, Any]` — Retrieve ancestry lineage for a message.


---

## Quickstart & Usage

```python
from harness.kernel.context import ServiceContext
from plugins.memory_and_epistemics.hermes_state_fts5.main import plugin

# Load plugin into harness service context
context = ServiceContext()
plugin.on_load(context)
```

---

## Architecture & Diátaxis Classification

- Diátaxis Quadrant: Reference (Track B) & How-To Guides
- Isolation: `in_process` execution sandbox
- Invariants: Slotted dataclass architecture (Rule 12), transactional context bounds (Rule 8), and zero-fork YAML configuration (Rule 44).
