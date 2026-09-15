# plugin.refactor_engine (v1.0.0)

Python AST refactoring engine, dead/unused code identifier, and function extraction tool

---

## Overview & Metadata

| Property | Value |
|---|---|
| Plugin Directory | `plugins/software_engineering/refactor_engine` |
| Category | `software_engineering` |
| Isolation Mode | `in_process` |
| Services Provided | `service.refactor_engine` |
| Dependencies Required | None |

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `find_unused_functions` | `(code)` | Find declared functions in Python source code that are never called internally within the module |
| `extract_function_preview` | `(code, start_line, end_line, new_func_name)` | Preview extracting a block of lines into a new helper function with parameter discovery |

---

## Key Modules & AST Symbols

### Module [main.py](main.py)

AST refactoring engine, unused function identifier, and function extractor plugin.

#### Classes

- `class RefactorEnginePlugin` — Harness Plugin providing AST-based unused function detection and function extraction.
  - `def provides() -> list[ServiceKey[Any]]`
  - `def requires() -> list[ServiceKey[Any]]`
  - `def on_load(ctx) -> None`
  - `def on_enable() -> None`
  - `def on_disable() -> None`
  - `def on_unload() -> None`
  - `def find_unused_functions(code) -> UnusedFunctionsResult`
  - `def extract_function_preview(code, start_line, end_line, new_func_name) -> FunctionExtractResult`


#### Functions

- `def find_unused_functions(code) -> dict[str, Any]` — Find declared top-level functions in a module that are never invoked within that module.
- `def extract_function_preview(code, start_line, end_line, new_func_name) -> dict[str, Any]` — Generate a refactored preview extracting lines into a new function.


---

## Quickstart & Usage

```python
from harness.kernel.context import ServiceContext
from plugins.software_engineering.refactor_engine.main import plugin

# Load plugin into harness service context
context = ServiceContext()
plugin.on_load(context)
```

---

## Architecture & Diátaxis Classification

- Diátaxis Quadrant: Reference (Track B) & How-To Guides
- Isolation: `in_process` execution sandbox
- Invariants: Slotted dataclass architecture (Rule 12), transactional context bounds (Rule 8), and zero-fork YAML configuration (Rule 44).
