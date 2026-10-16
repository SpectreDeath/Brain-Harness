# plugin.codebase_context (v1.0.0)

Multi-layer codebase context architecture, token budgeting, SSOT synchronization, and 5-stage context governance

---

## Overview & Metadata

| Property | Value |
|---|---|
| Plugin Directory | `plugins/developer_tooling/codebase_context` |
| Category | `developer_tooling` |
| Isolation Mode | `in_process` |
| Services Provided | `harness.services.codebase_context` |
| Dependencies Required | None |

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `context_lint` | `(root)` | Verify repository context files across token budgets, path integrity, manifest scripts, and sync drift |
| `context_sync` | `(root, source, dry_run)` | Synchronize downstream vendor context files (CLAUDE.md, copilot-instructions.md) against canonical SSOT |
| `context_govern` | `(root, complexity)` | Execute complete 5-stage context governance cycle and dynamic 5D compute tier assessment |

---

## Key Modules & AST Symbols

### Module [main.py](main.py)

Multi-layer codebase context architecture, token budgeting, SSOT synchronization, and 5-stage context governance

#### Classes

- `class CodebaseContextPlugin` — Plugin providing in-memory codebase context architecture, linting, and governance.
  - `def __init__(root)` — Executes the operation.
  - `def name()` — Executes the operation.
  - `def version()` — Executes the operation.
  - `def description()` — Executes the operation.
  - `def provides()` — Executes the operation.
  - `def requires()` — Executes the operation.
  - `def on_load(context)` — Register the service into the micro-kernel IoC container (Rule 1 & Rule 2).
  - `def enable(context)` — Executes the operation.
  - `def on_disable()` — Executes the operation.
  - `def disable(context)` — Executes the operation.
  - `def lint(root)` — Executes the operation.
  - `def sync(root, source_rel, dry_run)` — Executes the operation.
  - `def govern(root, target_file, complexity_score)` — Executes the operation.

---

## Quickstart & Usage

```python
from harness.kernel.context import ServiceContext
from plugins.developer_tooling.codebase_context.main import plugin

context = ServiceContext()
# Load plugin into service context
plugin.on_load(context)
```

---

## Architecture & Diátaxis Classification

- Diátaxis Quadrant: Reference (Track B) & How-To Guides
- Isolation: `in_process` execution sandbox
- Invariants: Slotted dataclass architecture (Rule 12), transactional context bounds (Rule 8), and zero-fork YAML configuration (Rule 44).
