# plugin.doc_synchronizer (v1.0.0)

Repository documentation coverage auditing, AST code-to-doc symbol drift verification, Diataxis scaffolding, and interactive visual brief generation

---

## Overview & Metadata

| Property | Value |
|---|---|
| Plugin Directory | `plugins/developer_tooling/doc_synchronizer` |
| Category | `developer_tooling` |
| Isolation Mode | `in_process` |
| Services Provided | `service.doc_synchronizer` |
| Dependencies Required | None |

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `doc_audit` | `(target, min_coverage)` | Audit Python codebase and calculate documentation coverage metrics with AST symbol depth |
| `doc_drift_check` | `(docs_dir, check_symbols)` | Verify markdown documentation for broken relative file links and stale AST code symbols |
| `doc_scaffold` | `(module_path, doc_type, output_path)` | Scaffold standardized Diataxis documentation using live Python module AST symbols |
| `doc_visual_brief` | `(target_dir, output_path)` | Generate interactive HTML coverage brief and scorecard with Mermaid topology diagram |

---

## Key Modules & AST Symbols

### Module [main.py](main.py)

DocSynchronizer Plugin — Repository documentation audit, drift check, and Diataxis scaffolding.

#### Classes

- `class DocSynchronizerPlugin` — Plugin providing in-memory documentation synchronization and drift verification.
  - `def __init__(root_dir) -> None`
  - `def name() -> str`
  - `def version() -> str`
  - `def description() -> str`
  - `def provides() -> list[ServiceKey[Any]]`
  - `def requires() -> list[ServiceKey[Any]]`
  - `def on_load(context) -> None` — Register self as the DocSynchronizerService into the IoC container.
  - `def enable(context) -> None`
  - `def on_disable() -> None`
  - `def disable(context) -> None`
  - `def audit(target_dir, min_coverage, exclude_patterns) -> DocCoverageReportData` — Audit Python codebase and calculate documentation coverage metrics.
  - `def drift_check(docs_dir, check_symbols) -> DocDriftReportData` — Inspect markdown documents for broken relative links and stale AST symbol references.
  - `def scaffold(module_path, doc_type, output_path) -> Path` — Scaffold standardized Diataxis documentation for a Python module.
  - `def visual_brief(target_dir, output_path) -> Path` — Render interactive HTML visual brief with Mermaid topology and coverage metrics.
  - `def get_cache_stats() -> dict[str, int]` — Return AST parsing cache statistics.


#### Functions

- `def doc_audit(target, min_coverage) -> dict[str, Any]` — Top-level entrypoint for doc_audit tool invocation.
- `def doc_drift_check(docs_dir, check_symbols) -> dict[str, Any]` — Top-level entrypoint for doc_drift_check tool invocation.
- `def doc_scaffold(module_path, doc_type, output_path) -> str` — Top-level entrypoint for doc_scaffold tool invocation.
- `def doc_visual_brief(target_dir, output_path) -> str` — Top-level entrypoint for doc_visual_brief tool invocation.


---

## Quickstart & Usage

```python
from harness.kernel.context import ServiceContext
from plugins.developer_tooling.doc_synchronizer.main import plugin

# Load plugin into harness service context
context = ServiceContext()
plugin.on_load(context)
```

---

## Architecture & Diátaxis Classification

- Diátaxis Quadrant: Reference (Track B) & How-To Guides
- Isolation: `in_process` execution sandbox
- Invariants: Slotted dataclass architecture (Rule 12), transactional context bounds (Rule 8), and zero-fork YAML configuration (Rule 44).
