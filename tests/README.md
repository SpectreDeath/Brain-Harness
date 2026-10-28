# Brain Harness — Test Suite Architecture & Conventions

Welcome to the Brain Harness test suite. The test suite contains **2,820+ passing tests** providing comprehensive contract verification, regression prevention, and architecture invariant checks across the micro-kernel, service mesh, plugins, and CLI commands.

---

## 1. Directory Structure & Naming Conventions

All test files are organized in a flat root layout under `tests/` using **domain-prefixed naming**. This provides immediate visibility across all test modules and simplifies cross-module test filtering:

| Domain Prefix | Subsystem Under Test | Example Test Modules |
|---|---|---|
| `test_kernel_*` | Micro-kernel IoC container, lifecycle manager, reconciler | `test_kernel_lifecycle_transitions.py`, `test_kernel_reconciler_edge_cases.py` |
| `test_service_*` | Core micro-kernel services and protocols | `test_service_taxonomy_consolidation.py`, `test_service_keys_strict_typing.py` |
| `test_plugin_*` | Concrete domain plugins and sandboxed execution | `test_plugin_webwright_harness.py`, `test_plugin_symbolic_solver.py` |
| `test_command_*` / `test_cli_*` | Headless Click CLI commands and aliases | `test_cli_aliases.py`, `test_cli_rule6_single_source.py` |
| `test_agent_*` | ReAct step loop, prompt pruning, context optimization | `test_agent_step_execution_engine.py`, `test_agent_dag_execution.py` |
| `test_ingestion_*` | Universal multi-provider repo fetcher, inspector, converters | `test_universal_ingestion.py`, `test_monorepo_partitioning.py` |
| `test_*_decomposition.py` | Architecture deepening contract verifications | `test_storage_service_decomposition.py`, `test_runtime_core_decomposition.py` |

Subdirectories in `tests/`:
- `tests/plugins/`: Integration tests for external and community plugin packs (`plugins/external/`).
- `tests/skills/`: Diagnostic craft validator test suites for skill frontmatters and summary cards.
- `tests/unit/`: Standalone atomic unit tests.

---

## 2. Decomposition Test Policy

When monolithic hotspots are decomposed into modular subpackages ($\le 200$ lines per Rule 11), companion decomposition tests (`test_<module>_decomposition.py`) are created to prevent behavioral regression:

1. **Assert Behavior, Not Brittle Layout**: Decomposition tests must assert observable behaviors, public API invariants, and typed service protocol contracts—never arbitrary line counts or brittle private file paths.
2. **Slotted Model Contract Invariants**: Assert immutability of slotted/frozen dataclasses (Rule 12, Rule 43) using `pytest.raises((AttributeError, TypeError))` on attribute mutation.
3. **Submodule Line Bounds (Rule 11)**: Verify that all decomposed submodule files strictly adhere to the $\le 200$ physical line limit.
4. **Lifecycle & Transaction Semantics**: Verify that transactional context operations, Git checkpoints (Rule 8), and inverse accumulator cleanup on disposal (Rule 54) function identically before and after decomposition.

---

## 3. Running Tests

### Targeted Domain Runs
Use pytest keyword filtering or explicit test paths:

```bash
# Run all kernel tests
pytest -k "test_kernel" -v

# Run all CLI command tests
pytest -k "test_cli" -v

# Run specific module test
pytest tests/test_cli_aliases.py -v
```

### PowerShell Glob Non-Expansion Workaround (Rule 30)
PowerShell does not automatically expand wildcard globs (e.g. `pytest tests/test_*.py`) into file lists. Always use pytest keyword matching:

```powershell
# Correct in PowerShell (Rule 30):
pytest -k "test_kernel"

# Avoid in PowerShell (fails to expand globs):
pytest tests/test_kernel_*.py
```

### Marker-Based Execution
Tests are tagged with standard pytest markers:

```bash
# Fast unit tests only (<60s)
pytest -m "unit" -q

# Integration tests
pytest -m "integration" -q

# Exclude intentionally slow benchmarks
pytest -m "not slow" -q
```

---

## 4. Test Environment Standards

- **UTF-8 Codecs (Rule 23 & 50)**: All test runners and mocks must support UTF-8 encodings to avoid `cp1252` encoding issues on Windows platforms.
- **Async Test Isolation**: Mark asynchronous test methods with `@pytest.mark.asyncio`.
- **Proactor Event Loop Isolation (Rule 56)**: When testing subprocess or air-gapped network execution, ensure localhost loopback sockets (`127.0.0.1`) remain accessible to allow Windows Proactor self-pipes.
- **Coverage Target**: Maintain $\ge 80\%$ test coverage on kernel and plugin subsystems.
