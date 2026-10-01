# Micro-Kernel API Reference (`harness.kernel`)

The `harness.kernel` package provides the dependency injection container, lifecycle state machine, and dependency DAG solver for Brain Harness.

---

## 1. `ServiceKey[T]` & `ServiceContext`

### `ServiceKey[T]`
Typed identifier used for registering and resolving services in the IoC container.

```python
class ServiceKey[T]:
    def __init__(self, key: str, description: str | None = None) -> None: ...
```

### `ServiceContext`
Hierarchical dependency injection container supporting child scopes, typed resolution, and atomic step transactions.

#### Methods
- `provide(key: ServiceKey[T], instance: T) -> None`: Registers a service instance.
- `require(key: ServiceKey[T]) -> T`: Resolves a mandatory service or raises `KeyError`.
- `optional(key: ServiceKey[T]) -> T | None`: Resolves a service if present, else returns `None`.
- `transaction() -> AsyncContextManager[ContextTransaction]`: Creates an isolated transaction scope. Errors trigger automatic rollback.
- `create_child_context() -> ServiceContext`: Spawns a child context inheriting parent registrations.
- `revoke(key: ServiceKey[T]) -> None`: Revokes a registered service and executes matching cleanup closures (Rule 54).

---

## 2. `DependencyGraph`

Directed acyclic graph solver for calculating topological plugin resolution orders.

### Methods
- `add_node(node_id: str, dependencies: list[str]) -> None`: Inserts a node with required dependencies.
- `resolve_order() -> list[str]`: Computes a valid topological execution sequence using Kahn's algorithm. Raises `CyclicDependencyError` on circular references.

---

## 3. `PluginLifecycleManager` & `PluginState`

State machine governing the progression of plugins across runtime phases.

### Lifecycle States (`PluginState`)
- `DISCOVERED`: Manifest detected on filesystem.
- `VALIDATED`: AST signatures and dependencies verified.
- `LOADED`: Subprocess spawned or module imported; services registered in IoC container.
- `ENABLED`: All dependencies satisfied and plugin is active for dispatch.
- `DISABLED`: Temporarily deactivated; services revoked from IoC container.
- `FAILED`: Initialization failed; error logged to telemetry.

### Core Methods
- `discover_plugins(plugin_dir: Path) -> list[PluginState]`: Discovers local plugins on disk.
- `load_plugin(plugin_name: str) -> None`: Transitions a plugin from `VALIDATED` to `LOADED`.
- `enable_plugin(plugin_name: str) -> None`: Enables a loaded plugin and makes its tools accessible.
- `disable_plugin(plugin_name: str) -> None`: Disables a plugin and cleans up state.

---

## 4. `StateReconciler`

Reconciles active container states against desired declarative configurations.

### Methods
- `reconcile(desired_config: dict[str, Any]) -> ReconciliationReport`: Computes diffs between desired plugin configs and active states, applying required enables, disables, and reloads.

---

## 5. `HarnessRuntime`

Top-level runtime coordinator encapsulating the kernel context, event bus, storage engine, and lifecycle manager.

### Methods
- `create(config_path: Path | None = None) -> AsyncContextManager[HarnessRuntime]`: Async context manager factory initializing and cleanly disposing the runtime.
- `runtime.context`: Active root `ServiceContext`.
- `runtime.event_bus`: Active `EventBus`.
