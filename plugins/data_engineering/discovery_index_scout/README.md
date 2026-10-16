# domain.discovery_index_scout (v1.0.0)

Discovery Index Scout engine: multi-domain search across transcripts, public records, research corpora, and open data indexes

---

## Overview & Metadata

| Property | Value |
|---|---|
| Plugin Directory | `plugins/data_engineering/discovery_index_scout` |
| Category | `data_engineering` |
| Isolation Mode | `in_process` |
| Services Provided | `service.discovery_index` |
| Dependencies Required | None |

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `discovery_search` | `(query, category, tag, provenance_tier, export_format, limit)` | Execute weighted multi-field search across 46+ discovery indexes with faceted filters |
| `discovery_get_source` | `(source_id)` | Retrieve detailed metadata for a specific discovery source by ID |
| `discovery_get_stats` | `()` | Retrieve faceted counts and category distributions for all registered discovery sources |

---

## Key Modules & AST Symbols

### Module [main.py](main.py)

Discovery Index Scout engine: multi-domain search across transcripts, public records, research corpora, and open data indexes

#### Classes

- `class DiscoveryIndexScoutPlugin` — Brain Harness Plugin providing in-memory discovery index scouting and catalog queries.
Elevates .agents/skills/discovery-index-scout into an authoritative IoC micro-kernel seam.
  - `def __init__()` — Executes the operation.
  - `def provides()` — Executes the operation.
  - `def requires()` — Executes the operation.
  - `def on_load(ctx)` — Executes the operation.
  - `def on_enable()` — Executes the operation.
  - `def on_disable()` — Executes the operation.
  - `def search(query, category, tag, provenance_tier, export_format, limit)` — Executes the operation.
  - `def get_source(source_id)` — Executes the operation.
  - `def list_sources(category)` — Executes the operation.
  - `def register_source(source_data, persist)` — Executes the operation.
  - `def get_stats()` — Executes the operation.

---

## Quickstart & Usage

```python
from harness.kernel.context import ServiceContext
from plugins.data_engineering.discovery_index_scout.main import plugin

context = ServiceContext()
# Load plugin into service context
plugin.on_load(context)
```

---

## Architecture & Diátaxis Classification

- Diátaxis Quadrant: Reference (Track B) & How-To Guides
- Isolation: `in_process` execution sandbox
- Invariants: Slotted dataclass architecture (Rule 12), transactional context bounds (Rule 8), and zero-fork YAML configuration (Rule 44).
