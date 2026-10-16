# plugin.brain_artifact_miner (v0.1.0)

Filesystem-native workspace archaeology engine for mining artifacts, reusable scratch tools, and dual-transcript execution streams

---

## Overview & Metadata

| Property | Value |
|---|---|
| Plugin Directory | `plugins/memory_and_epistemics/brain_artifact_miner` |
| Category | `memory_and_epistemics` |
| Isolation Mode | `in_process` |
| Services Provided | `service.brain_artifact_miner` |
| Dependencies Required | None |

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `build_offset_index` | `(path)` | Executes the operation. |
| `get_step` | `(transcript_path, step_index, dereference_truncated)` | Executes the operation. |
| `stream_steps` | `(transcript_path, dereference_truncated)` | Executes the operation. |
| `scan_scratch_tools` | `(brain_dir, max_depth)` | Executes the operation. |
| `triage_task_logs` | `(brain_dir, max_depth)` | Executes the operation. |
| `generate_html_brief` | `(data)` | Executes the operation. |
| `export_knowledge_item` | `(output_dir, ki_id, title, category, summary, claims)` | Executes the operation. |

---

## Key Modules & AST Symbols

### Module [main.py](main.py)

Filesystem-native workspace archaeology engine for mining artifacts, reusable scratch tools, and dual-transcript execution streams

#### Classes

- `class BrainArtifactMinerPlugin` — Domain-partitioned plugin for brain artifact mining and scratch tool archaeology.
  - `def __init__()` — Executes the operation.
  - `def provides()` — Executes the operation.
  - `def requires()` — Executes the operation.
  - `def on_load(ctx)` — Executes the operation.
  - `def on_enable()` — Executes the operation.
  - `def on_disable()` — Executes the operation.
  - `def on_unload()` — Executes the operation.
  - `def build_offset_index(path)` — Executes the operation.
  - `def get_step(transcript_path, step_index, dereference_truncated)` — Executes the operation.
  - `def stream_steps(transcript_path, dereference_truncated)` — Executes the operation.
  - `def scan_scratch_tools(brain_dir, max_depth)` — Executes the operation.
  - `def triage_task_logs(brain_dir, max_depth)` — Executes the operation.
  - `def generate_html_brief(data)` — Executes the operation.
  - `def export_knowledge_item(output_dir, ki_id, title, category, summary, claims)` — Executes the operation.

---

## Quickstart & Usage

```python
from harness.kernel.context import ServiceContext
from plugins.memory_and_epistemics.brain_artifact_miner.main import plugin

context = ServiceContext()
# Load plugin into service context
plugin.on_load(context)
```

---

## Architecture & Diátaxis Classification

- Diátaxis Quadrant: Reference (Track B) & How-To Guides
- Isolation: `in_process` execution sandbox
- Invariants: Slotted dataclass architecture (Rule 12), transactional context bounds (Rule 8), and zero-fork YAML configuration (Rule 44).
