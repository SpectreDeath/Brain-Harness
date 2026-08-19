# Service Keys and Service Context

## Overview

In Brain Harness, the kernel relies on a typed Inversion of Control (IoC) container. Rather than looking up services by raw string names (which leads to typos, lack of IDE autocomplete, and runtime type errors), Harness uses `ServiceKey[T]`.

```python
from harness.kernel.context import ServiceContext, ServiceKey

# 1. Define a typed service key
STORAGE_KEY: ServiceKey[MyStorage] = ServiceKey("storage.engine")

# 2. Register the service in the context
ctx = ServiceContext()
ctx.provide(STORAGE_KEY, MyStorage())

# 3. Retrieve the service with full type safety
storage: MyStorage = ctx.require(STORAGE_KEY)
```

## Key Concepts

- **Type Safety**: `ServiceKey[T]` carries the type parameter `T`, allowing static analyzers (`mypy`, `pyright`) to verify service operations.
- **Provider Tracking**: Every registered service records its provider plugin name.
- **Scoped Context**: Scoped contexts associate services with specific plugin lifecycles and prevent cross-plugin service leaks.
