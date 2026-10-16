# plugin.temp_artifact_miner (v0.1.0)

Ephemeral workspace archaeology engine for mining HTML visual briefs, test sandbox environments, and dual-lens cognitive bifurcation

---

## Overview & Metadata

| Property | Value |
|---|---|
| Plugin Directory | `plugins/memory_and_epistemics/temp_artifact_miner` |
| Category | `memory_and_epistemics` |
| Isolation Mode | `in_process` |
| Services Provided | `service.temp_artifact_miner` |
| Dependencies Required | None |

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `scan_briefs` | `(temp_dir, max_depth, heavy_threshold)` | Executes the operation. |
| `triage_sandbox` | `(pytest_dir, max_depth)` | Executes the operation. |
| `tail_diagnostic_log` | `(log_path, max_lines)` | Executes the operation. |
| `generate_salvage_markdown` | `(catalog, sandbox)` | Executes the operation. |
| `bifurcate_brief` | `(brief_path, target_vault_dir, target_docs_dir)` | Executes the operation. |
| `salvage_diagrams` | `(brief_path, target_docs_dir)` | Executes the operation. |
| `parse_html_brief` | `(file_path, heavy_threshold)` | Executes the operation. |

---

## Key Modules & AST Symbols

### Module [main.py](main.py)

Ephemeral workspace archaeology engine for mining HTML visual briefs, test sandbox environments, and dual-lens cognitive bifurcation

#### Classes

- `class TempArtifactMinerPlugin` — Domain-partitioned plugin for ephemeral artifact mining, visual brief extraction, and sandbox triage.
  - `def __init__()` — Executes the operation.
  - `def provides()` — Executes the operation.
  - `def requires()` — Executes the operation.
  - `def on_load(ctx)` — Executes the operation.
  - `def on_enable()` — Executes the operation.
  - `def on_disable()` — Executes the operation.
  - `def on_unload()` — Executes the operation.
  - `def scan_briefs(temp_dir, max_depth, heavy_threshold)` — Executes the operation.
  - `def triage_sandbox(pytest_dir, max_depth)` — Executes the operation.
  - `def tail_diagnostic_log(log_path, max_lines)` — Executes the operation.
  - `def generate_salvage_markdown(catalog, sandbox)` — Executes the operation.
  - `def bifurcate_brief(brief_path, target_vault_dir, target_docs_dir)` — Executes the operation.
  - `def salvage_diagrams(brief_path, target_docs_dir)` — Executes the operation.
  - `def parse_html_brief(file_path, heavy_threshold)` — Executes the operation.

---

## Quickstart & Usage

```python
from harness.kernel.context import ServiceContext
from plugins.memory_and_epistemics.temp_artifact_miner.main import plugin

context = ServiceContext()
# Load plugin into service context
plugin.on_load(context)
```

---

## Architecture & Diátaxis Classification

- Diátaxis Quadrant: Reference (Track B) & How-To Guides
- Isolation: `in_process` execution sandbox
- Invariants: Slotted dataclass architecture (Rule 12), transactional context bounds (Rule 8), and zero-fork YAML configuration (Rule 44).
