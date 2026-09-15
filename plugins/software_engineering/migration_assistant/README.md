# plugin.migration_assistant (v1.0.0)

Python framework migration checker (Pydantic v1 to v2, Python 3.10+ union syntax, unittest to pytest)

---

## Overview & Metadata

| Property | Value |
|---|---|
| Plugin Directory | `plugins/software_engineering/migration_assistant` |
| Category | `software_engineering` |
| Isolation Mode | `in_process` |
| Services Provided | `service.migration_assistant` |
| Dependencies Required | None |

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `check_pydantic_v2_readiness` | `(code)` | Scan Python code for deprecated Pydantic v1 patterns (class Config, regex field parameter, validator decorator) |
| `check_python_version_compat` | `(code)` | Scan for deprecated legacy Python patterns (typing.Union instead of |, typing.Optional, distutils) |

---

## Key Modules & AST Symbols

### Module [main.py](main.py)

Migration Assistant plugin — Pydantic v2 and Python 3.10+ modern syntax migration checker.

#### Classes

- `class MigrationAssistantPlugin` — Harness Plugin providing Python and Pydantic migration analysis.
  - `def provides() -> list[ServiceKey[Any]]`
  - `def requires() -> list[ServiceKey[Any]]`
  - `def on_load(ctx) -> None`
  - `def on_enable() -> None`
  - `def on_disable() -> None`
  - `def on_unload() -> None`
  - `def check_pydantic_v2_readiness(code) -> PydanticMigrationResult`
  - `def check_python_version_compat(code) -> PythonCompatResult`


#### Functions

- `def check_pydantic_v2_readiness(code) -> dict[str, Any]` — Scan Python code for deprecated Pydantic v1 patterns.
- `def check_python_version_compat(code) -> dict[str, Any]` — Scan for pre-Python 3.10 legacy patterns.


---

## Quickstart & Usage

```python
from harness.kernel.context import ServiceContext
from plugins.software_engineering.migration_assistant.main import plugin

# Load plugin into harness service context
context = ServiceContext()
plugin.on_load(context)
```

---

## Architecture & Diátaxis Classification

- Diátaxis Quadrant: Reference (Track B) & How-To Guides
- Isolation: `in_process` execution sandbox
- Invariants: Slotted dataclass architecture (Rule 12), transactional context bounds (Rule 8), and zero-fork YAML configuration (Rule 44).
