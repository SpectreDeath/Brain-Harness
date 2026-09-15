# plugin.kimi_minidb (v1.0.0)

Zero-dependency embedded hybrid KV and document database with CRC32-checksummed write-ahead logging (WAL) and generational snapshot compaction.

---

## Overview & Metadata

| Property | Value |
|---|---|
| Plugin Directory | `plugins/data_engineering/kimi_minidb` |
| Category | `data_engineering` |
| Isolation Mode | `in_process` |
| Services Provided | None |
| Dependencies Required | None |

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `kimi_minidb_put` | `(collection, key, value)` | Insert or update a document in an embedded collection with CRC32-checksummed write-ahead log (WAL) persistence. |
| `kimi_minidb_get` | `(collection, key)` | Retrieve a stored document by collection name and key with CRC32 integrity verification. |
| `kimi_minidb_compact` | `(target_generation)` | Triggers generational snapshot compaction, consolidating write-ahead logs into a clean baseline snapshot. |

---

## Key Modules & AST Symbols

### Module [main.py](main.py)

Kimi MiniDb Plugin — Zero-dependency embedded hybrid KV with durable WAL and snapshot compaction.

#### Classes

- `class MiniDbEngine` — Authoritative MiniDb storage engine implementing WAL framing, CRC32, and compaction.
  - `def __init__() -> None`
  - `def put(collection, key, value) -> MiniDbRecord` — Insert or update a record, committing a CRC32 frame to the WAL.
  - `def get(collection, key) -> MiniDbRecord | None` — Retrieve record by collection and key, verifying CRC32 integrity.
  - `def scan(collection, filter_fn) -> list[MiniDbRecord]` — Scan records in a collection with optional filter.
  - `def compact(target_generation) -> dict[str, Any]` — Trigger generational snapshot compaction.
- `class KimiMiniDbPlugin` — Brain Harness Plugin providing zero-dependency embedded MiniDb storage.
  - `def __init__(service) -> None`
  - `def on_enable(context) -> None` — Register KimiMiniDbService into IoC context.
  - `def on_disable(context) -> None` — Unregister service on disable.


#### Functions

- `def kimi_minidb_put(collection, key, value) -> dict[str, Any]` — Insert or update a document in MiniDb with WAL durability.
- `def kimi_minidb_get(collection, key) -> dict[str, Any]` — Retrieve a stored document by collection name and key.
- `def kimi_minidb_compact(target_generation) -> dict[str, Any]` — Triggers snapshot compaction, consolidating WAL frames.


---

## Quickstart & Usage

```python
from harness.kernel.context import ServiceContext
from plugins.data_engineering.kimi_minidb.main import plugin

# Load plugin into harness service context
context = ServiceContext()
plugin.on_load(context)
```

---

## Architecture & Diátaxis Classification

- Diátaxis Quadrant: Reference (Track B) & How-To Guides
- Isolation: `in_process` execution sandbox
- Invariants: Slotted dataclass architecture (Rule 12), transactional context bounds (Rule 8), and zero-fork YAML configuration (Rule 44).
