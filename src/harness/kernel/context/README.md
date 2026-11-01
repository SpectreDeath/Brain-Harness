# Kernel Service Context & IoC Container

The `harness.kernel.context` package provides the dependency injection micro-kernel, typed `ServiceKey[T]` registry, scoped container isolation, effect disposal stacks, and transactional context checkpoints for the Harness architecture.

---

## Architectural Invariants

- **Everything is a Plugin (`Rule 1`)**: Zero functionality is hardcoded into the kernel; components register capabilities into `ServiceContext`.
- **Typed Service Keys (`Rule 2`)**: All service registration and resolution must use `ServiceKey[T]` instances via `context.provide(key, instance)` and `context.require(key)` or `context.optional(key)`. Raw strings or non-existent methods (`register_instance`, `resolve`) are forbidden.
- **Dispose Stack Inverse Accumulator Synchronization (`Rule 54`)**: Inverse effect closures in `_dispose_stack` carry provider metadata. Targeted revocations (`revoke()`) purge matching inverse closures to prevent orphaned closures from executing during shutdown.
- **Transactional Isolation & Workspace Checkpoints (`Rule 8`)**: Step transactions execute via `async with context.transaction()` providing atomic commits and automatic LIFO rollbacks.

---

## Module & Symbol Reference

| Module | Core Classes / Symbols | Description |
|---|---|---|
| [`core.py`](core.py) | `ServiceContext` | Authoritative IoC container managing provider registries, service scopes, and disposal lifecycles. |
| [`models.py`](models.py) | `ServiceKey`, `ServiceScope`, `ServiceRegistration` | Typed, generic service key descriptors (`ServiceKey[T]`) and scope definitions. |
| [`scoped.py`](scoped.py) | `ScopedServiceContext` | Scoped child context isolating plugin-local services and automatic teardown boundaries. |
| [`transactions.py`](transactions.py) | `ContextTransaction`, `execute_transaction` | Context transaction manager coordinating atomic git/state checkpoints and rollback hooks. |
| [`effects.py`](effects.py) | `EffectRegistration`, `DisposeStack` | LIFO effect stack tracking provider cleanups and inverse revocation hooks. |
| [`mutations.py`](mutations.py) | `provide_service`, `revoke_service` | Low-level container mutation routines maintaining realm consistency. |
| [`lookup.py`](lookup.py) | `require_service`, `optional_service` | Type-safe lookup primitives verifying service existence and contracts. |
| [`realms.py`](realms.py) | `resolve_realm`, `create_isolated_context` | Security realm partitioning separating trusted kernel plugins from subprocess sandboxes. |
| [`interceptors.py`](interceptors.py) | `ContextInterceptor` | Interceptor hooks observing service resolution and injection events. |
| [`resolvers.py`](resolvers.py) | `resolve_service_context` | Single-seam resolver returning the active micro-kernel context. |

---

## Usage Recipes

### Registering and Resolving Typed Services
```python
from harness.kernel.context import ServiceContext, ServiceKey

# 1. Define typed service key
LOGGER_KEY = ServiceKey[MyLogger]("system.logger")

# 2. Register into context
context = ServiceContext()
context.provide(LOGGER_KEY, MyLogger())

# 3. Resolve with full static type safety
logger = context.require(LOGGER_KEY)
logger.info("Service initialized cleanly")
```

### Atomic Context Transactions
```python
async with context.transaction() as tx:
    context.provide(TEMP_KEY, temp_instance)
    # If an exception occurs, all mutations in the transaction roll back automatically
```

