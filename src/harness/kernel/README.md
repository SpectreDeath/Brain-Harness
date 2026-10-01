# Harness Micro-Kernel Architecture (`harness.kernel`)

The `harness.kernel` package provides the dependency injection (IoC) container, service registry, state reconciliation graph, and lifecycle engine that power the Brain Harness runtime.

---

## Architectural Invariants

Brain Harness strictly separates kernel mechanisms from domain capabilities:
- **Everything is a Plugin (Rule 1)**: No business domain logic is hardcoded into the kernel. Storage, models, tools, and agent execution engines register as plugins into the IoC container.
- **Typed Service Keys (Rule 2)**: All service bindings use generic `ServiceKey[T]` instances for registration (`context.provide(key, instance)`) and resolution (`context.require(key)` or `context.optional(key)`).
- **Subprocess Isolation by Default (Rule 5 & Rule 7)**: External plugins run in subprocess sandboxes with lazy staging, only provisioning virtual environments upon first invocation.
- **Transactional State Isolation (Rule 8)**: ReAct step operations execute inside transactional scopes (`async with context.transaction()`) with automatic rollback on failure.
- **Subprocess Transport Disposal (Rule 14 & Rule 53)**: Subprocess sandbox IPC transports drain and close `stdin`/`stdout`/`stderr` inside `finally` blocks, draining stderr into a bounded ring buffer to prevent OS pipe deadlocks.
- **Dispose Stack Synchronization (Rule 54)**: Inverse effect closures in `_dispose_stack` carry realm key and provider metadata, purging matching closures upon service revocation.
- **Non-Invasive Extensibility (Rule 19)**: Extensibility is achieved through adapters, metadata decorators, and inspectors without mutating core `ServiceContext` constructor contracts.

---

## Key Modules & Classes

| Module | Core Classes | Description |
|---|---|---|
| [`context.py`](context.py) | `ServiceContext`, `ServiceKey`, `ServiceBinding` | Hierarchical IoC container supporting scoped child contexts, typed resolution, and atomic transactions. |
| [`graph.py`](graph.py) | `DependencyGraph`, `ResolutionOrder` | Directed acyclic graph (DAG) solver for topological dependency resolution and cycle detection. |
| [`lifecycle.py`](lifecycle.py) | `PluginLifecycleManager`, `PluginState` | State machine governing plugin phases (`DISCOVERED` $\rightarrow$ `LOADED` $\rightarrow$ `ENABLED`). |
| [`reconciler.py`](reconciler.py) | `StateReconciler` | Convergence engine comparing desired plugin configurations with active container states. |
| [`runtime.py`](runtime.py) | `HarnessRuntime` | Top-level runtime coordinator managing kernel boot, storage, and agent task execution. |

---

## Plugin Lifecycle States

```
[DISCOVERED] ──► [VALIDATED] ──► [LOADED] ──► [ENABLED]
                                   │              │
                                   ▼              ▼
                               [FAILED]     [DISABLED]
```

1. **DISCOVERED**: The plugin directory and `plugin.json` manifest were identified on disk.
2. **VALIDATED**: The manifest schema, dependencies, and entrypoint signatures passed AST verification.
3. **LOADED**: The plugin module was imported or the subprocess sandbox was initialized; services were provided to the IoC container.
4. **ENABLED**: Dependencies were resolved and the plugin is active for tool dispatch and agent reasoning.

---

## Programmatic Usage Example

```python
import asyncio
from harness.kernel.runtime import HarnessRuntime
from harness.kernel.context import ServiceKey

async def main():
    # Bootstrap the micro-kernel runtime
    async with HarnessRuntime.create() as runtime:
        ctx = runtime.context
        
        # Scoped transactional step
        async with ctx.transaction() as tx:
            # Operations performed here are tracked and rolled back on error
            pass

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Related Documentation

- [Kernel Reference Page](../../../docs/reference/kernel.md)
- [Plugin System Architecture](../plugins/README.md)
- [Core Services Registry](../services/README.md)
- [CLI Commands](../commands/README.md)
