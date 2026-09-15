# plugin.test_runner (v1.0.0)

Autonomous test discovery, test execution, and structured failure parsing for TDD workflows

---

## Overview & Metadata

| Property | Value |
|---|---|
| Plugin Directory | `plugins/software_engineering/test_runner` |
| Category | `software_engineering` |
| Isolation Mode | `in_process` |
| Services Provided | `service.test_runner` |
| Dependencies Required | None |

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `discover_tests` | `(root_dir)` | Discover test files, classes, and test functions across a directory tree |
| `run_tests` | `(target_path, markers, keyword_filter, timeout)` | Execute pytest on a target path and return structured pass/fail results with tracebacks |

---

## Key Modules & AST Symbols

### Module [main.py](main.py)

Test Runner & TDD Execution Service Plugin for Brain Harness.

Provides autonomous test discovery, test suite execution (pytest/unittest),
and structured failure/traceback extraction for iterative TDD agent loops.

#### Classes

- `class TestRunnerServiceImpl` — Implementation of TestRunnerService.
  - `def discover(root_dir) -> dict[str, Any]`
  - `def run(target_path) -> dict[str, Any]`
- `class TestRunnerPlugin` — Plugin providing test running and TDD capabilities.
  - `def __init__(service) -> None`
  - `def provides() -> list[ServiceKey[Any]]`
  - `def requires() -> list[ServiceKey[Any]]`
  - `def on_load(ctx) -> None`
  - `def on_enable() -> None`
  - `def on_disable() -> None`
  - `def on_unload() -> None`


#### Functions

- `def discover_tests(root_dir) -> dict[str, Any]` — Discover test files and test functions across a workspace.
- `def run_tests(target_path) -> dict[str, Any]` — Execute pytest on target paths and parse results into structured feedback.


---

## Quickstart & Usage

```python
from harness.kernel.context import ServiceContext
from plugins.software_engineering.test_runner.main import plugin

# Load plugin into harness service context
context = ServiceContext()
plugin.on_load(context)
```

---

## Architecture & Diátaxis Classification

- Diátaxis Quadrant: Reference (Track B) & How-To Guides
- Isolation: `in_process` execution sandbox
- Invariants: Slotted dataclass architecture (Rule 12), transactional context bounds (Rule 8), and zero-fork YAML configuration (Rule 44).
