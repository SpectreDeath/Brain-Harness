# Resolver & Singleton Code Recipes

## Recipe 1: Rule 58 Single-Seam Resolver
```python
from __future__ import annotations
from typing import Optional
from harness.kernel.context import ServiceContext
from .protocol import MY_SERVICE_KEY, MyServiceProtocol
from .service import DefaultMyService

def resolve_my_service(
    ctx: Optional[ServiceContext] = None,
) -> MyServiceProtocol:
    """Resolve service from IoC container with fallback to DefaultMyService (Rule 58)."""
    if ctx is not None:
        try:
            svc = ctx.optional(MY_SERVICE_KEY)
            if svc is not None:
                return svc
        except Exception:
            pass
    return DefaultMyService()
```

## Recipe 2: Rule 45 Plugin Module Singleton
```python
from harness.plugins.base import HarnessPlugin

class MyPlugin(HarnessPlugin):
    name = "plugin.my_domain"
    # ... implementation ...

# Rule 45: instantiated module-level singleton
plugin = MyPlugin()
```
