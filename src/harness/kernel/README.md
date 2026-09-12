# Harness Micro-Kernel Architecture (`harness.kernel`)

The `harness.kernel` package provides the dependency injection (IoC) container, service registry, state reconciliation graph, and lifecycle engine that power the Brain Harness runtime.

---

## Architecture & Design

Brain Harness strictly separates kernel mechanisms from domain capabilities:
- **Everything is a Plugin (Rule 1)**: No business domain logic is hardcoded into the kernel. Storage, models, tools, and agent execution engines register as plugins into the IoC container.
- **Typed Service Keys (Rule 2)**: All service bindings use generic `ServiceKey[T]` instances for registration (`context.provide(key, instance)`) and resolution (`context.require(key)` or `context.optional(key)`).
- **Transactional State (Rule 8)**: ReAct step operations execute inside transactional scopes (`async with context.transaction()`) with automatic rollback on failure.
- **Non-Invasive Kernel Extensibility (Rule 19)**: System extensibility is achieved through adapters and decorators rather than mutating kernel constructor contracts.

---

## Key Modules

| Module | Core Classes | Description |
|---|---|---|
| [`context.py`](context.py) | `ServiceContext`, `ServiceKey`, `ServiceBinding` | Hierarchical IoC container supporting scoped child contexts and atomic transactions. |
| [`graph.py`](graph.py) | `DependencyGraph`, `ResolutionOrder` | Directed acyclic graph (DAG) solver for topological dependency resolution. |
| [`lifecycle.py`](lifecycle.py) | `PluginLifecycleManager`, `PluginState` | State machine governing plugin phases (`DISCOVERED` $\rightarrow$ `LOADED` $\rightarrow$ `ENABLED`). |
| [`reconciler.py`](reconciler.py) | `StateReconciler` | Convergence engine comparing desired plugin configurations with active container states. |
| [`runtime.py`](runtime.py) | `HarnessRuntime` | Top-level runtime coordinator managing kernel boot, storage, and agent task execution. |

---

## Programmatic Usage Example

```python
from harness.kernel.runtime import HarnessRuntime
from harness.kernel.context import ServiceKey

async def example():
    async with HarnessRuntime.create() as runtime:
        # Resolve services via typed ServiceKey
        ctx = runtime.context
        # Provide or require typed services
```

---

## Related Documentation
- [Plugin Architecture](../plugins/README.md)
- [Service Providers](../services/README.md)
- [CLI Commands](../commands/README.md)
