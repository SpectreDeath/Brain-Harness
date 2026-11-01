# Harness Kernel Runtime

The `harness.kernel.runtime` package provides the top-level runtime orchestrator, lifecycle coordinator, plugin discovery pipeline, and execution state reconciler for the Harness micro-kernel.

---

## Architectural Invariants

- **Subprocess Isolation by Default (`Rule 5`)**: Untrusted and external plugins execute in isolated subprocess sandboxes with dedicated proactors.
- **Lazy Subprocess Staging (`Rule 7`)**: External plugins remain in `DISCOVERED`/`VALIDATED` state during startup and test runs, provisioning virtual environments lazily on first invocation.
- **Subprocess Pipe Transport Disposal (`Rule 14`)**: Asynchronous subprocess pipes drain and close cleanly in `finally` blocks to guarantee resource disposal.
- **Windows UTF-8 Stream Codec Entrypoint Invariant (`Rule 23`)**: Runtime processes enforce UTF-8 standard stream codecs (`PYTHONIOENCODING=utf-8`).

---

## Module & Symbol Reference

| Module | Core Classes / Symbols | Description |
|---|---|---|
| [`coordinator.py`](coordinator.py) | `HarnessRuntime` | Primary coordinator managing plugin lifecycles, service contexts, and tool dispatchers. |
| [`models.py`](models.py) | `RuntimeConfig`, `RuntimeState` | Slotted configuration and runtime execution state data models. |
| [`factory.py`](factory.py) | `create_runtime`, `create_diagnostic_runtime`, `create_runtime_from_config` | Factory functions initializing configured runtime instances. |
| [`lifecycle_runner.py`](lifecycle_runner.py) | `start_runtime`, `stop_runtime` | Topologically sorted startup and teardown execution routines. |
| [`plugins.py`](plugins.py) | `ingest_plugin_from_source`, `enable_all_plugins`, `disable_all_plugins` | Batch plugin ingestion and lifecycle state management. |
| [`plugin_ops.py`](plugin_ops.py) | `RuntimePluginOpsMixin` | Dynamic plugin loading, unloading, and validation operations mixin. |
| [`tools.py`](tools.py) | `enable_tool`, `disable_tool`, `toggle_tool` | Granular tool enablement, isolation toggles, and dispatch controls. |
| [`services.py`](services.py) | `RuntimeServicesMixin` | Micro-kernel IoC service accessor and resolution bindings. |
| [`reconcile.py`](reconcile.py) | `parse_runtime_config`, `reconcile_runtime` | Declarative state reconciler aligning live runtime with configuration specs. |
| [`defaults.py`](defaults.py) | `get_default_plugins` | Core discovery suite locating trusted built-in ecosystem plugins. |

---

## Usage Recipes

### Constructing and Starting a Runtime Instance
```python
from harness.kernel.runtime import create_runtime

async def main():
    runtime = create_runtime(workspace_root=".")
    await runtime.start()
    try:
        # Resolve services and dispatch tools
        tools = runtime.list_tools()
        print(f"Active tools: {len(tools)}")
    finally:
        await runtime.stop()
```

