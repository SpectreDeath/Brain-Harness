# plugin.conversation_trajectory_miner (v0.1.0)

Autobiographical trajectory archaeology engine for mining IDE conversation databases, friction patterns, and dual-lens cognitive bifurcation

---

## Overview & Metadata

| Property | Value |
|---|---|
| Plugin Directory | `plugins/memory_and_epistemics/conversation_trajectory_miner` |
| Category | `memory_and_epistemics` |
| Isolation Mode | `in_process` |
| Services Provided | `service.conversation_trajectory_miner` |
| Dependencies Required | None |

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `connect_ro` | `(db_path)` | Executes the operation. |
| `inspect_conversation` | `(db_path)` | Executes the operation. |
| `scan_corpus` | `(corpus_dir, max_dbs)` | Executes the operation. |
| `compile_friction_scorecard` | `(manifests)` | Executes the operation. |
| `mine_failure_clusters` | `(corpus_dir, max_dbs)` | Executes the operation. |
| `bifurcate_distillation` | `(cid, db_path, output_vault_dir, output_skills_dir)` | Executes the operation. |
| `export_knowledge_item` | `(output_dir, ki_id, title, category, summary, claims)` | Executes the operation. |

---

## Key Modules & AST Symbols

### Module [main.py](main.py)

Autobiographical trajectory archaeology engine for mining IDE conversation databases, friction patterns, and dual-lens cognitive bifurcation

#### Classes

- `class ConversationTrajectoryMinerPlugin` — Domain-partitioned plugin for autobiographical trajectory mining and friction analysis.
  - `def __init__()` — Executes the operation.
  - `def provides()` — Executes the operation.
  - `def requires()` — Executes the operation.
  - `def on_load(ctx)` — Executes the operation.
  - `def on_enable()` — Executes the operation.
  - `def on_disable()` — Executes the operation.
  - `def on_unload()` — Executes the operation.
  - `def connect_ro(db_path)` — Executes the operation.
  - `def inspect_conversation(db_path)` — Executes the operation.
  - `def scan_corpus(corpus_dir, max_dbs)` — Executes the operation.
  - `def compile_friction_scorecard(manifests)` — Executes the operation.
  - `def mine_failure_clusters(corpus_dir, max_dbs)` — Executes the operation.
  - `def bifurcate_distillation(cid, db_path, output_vault_dir, output_skills_dir)` — Executes the operation.
  - `def export_knowledge_item(output_dir, ki_id, title, category, summary, claims)` — Executes the operation.

---

## Quickstart & Usage

```python
from harness.kernel.context import ServiceContext
from plugins.memory_and_epistemics.conversation_trajectory_miner.main import plugin

context = ServiceContext()
# Load plugin into service context
plugin.on_load(context)
```

---

## Architecture & Diátaxis Classification

- Diátaxis Quadrant: Reference (Track B) & How-To Guides
- Isolation: `in_process` execution sandbox
- Invariants: Slotted dataclass architecture (Rule 12), transactional context bounds (Rule 8), and zero-fork YAML configuration (Rule 44).
