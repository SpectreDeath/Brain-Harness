# plugin.arch_linter (v1.0.0)

Codebase coupling/cohesion analyzer, circular import detector, and clean architecture boundary verifier

---

## Overview & Metadata

| Property | Value |
|---|---|
| Plugin Directory | `plugins/software_engineering/arch_linter` |
| Category | `software_engineering` |
| Isolation Mode | `in_process` |
| Services Provided | `service.arch_linter` |
| Dependencies Required | None |

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `detect_circular_imports` | `(root_path)` | Scan a Python directory, build the internal module import graph, and detect circular import cycles |
| `compute_module_coupling` | `(root_path)` | Compute afferent (Ca) and efferent (Ce) coupling and instability metrics for package modules |
| `verify_clean_boundaries` | `(root_path, layer_hierarchy)` | Verify that inner architectural layers (e.g. kernel, domain) do not import from outer layers (e.g. ui, cli) |

---

## Key Modules & AST Symbols

### Module [main.py](main.py)

Architecture Linter plugin — circular imports, module coupling, and layer boundary enforcement.

#### Classes

- `class ArchLinterPlugin` — Harness Plugin providing codebase coupling, cohesion, and boundary linting.
  - `def provides() -> list[ServiceKey[Any]]`
  - `def requires() -> list[ServiceKey[Any]]`
  - `def on_load(ctx) -> None`
  - `def on_enable() -> None`
  - `def on_disable() -> None`
  - `def on_unload() -> None`
  - `def detect_circular_imports(root_path) -> CircularImportResult`
  - `def compute_module_coupling(root_path) -> ModuleCouplingResult`
  - `def verify_clean_boundaries(root_path, layer_hierarchy) -> BoundaryCheckResult`


#### Functions

- `def detect_circular_imports(root_path) -> dict[str, Any]` — Detect cyclic import loops across Python modules.
- `def compute_module_coupling(root_path) -> dict[str, Any]` — Compute afferent (Ca), efferent (Ce), and Instability (I = Ce / (Ca + Ce)).
- `def verify_clean_boundaries(root_path, layer_hierarchy) -> dict[str, Any]` — Verify inward dependency rule (inner layers must not import outer layers).


---

## Quickstart & Usage

```python
from harness.kernel.context import ServiceContext
from plugins.software_engineering.arch_linter.main import plugin

# Load plugin into harness service context
context = ServiceContext()
plugin.on_load(context)
```

---

## Architecture & Diátaxis Classification

- Diátaxis Quadrant: Reference (Track B) & How-To Guides
- Isolation: `in_process` execution sandbox
- Invariants: Slotted dataclass architecture (Rule 12), transactional context bounds (Rule 8), and zero-fork YAML configuration (Rule 44).
