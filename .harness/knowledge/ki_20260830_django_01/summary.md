# Thread-Safe Lazy App Registry & Topological Initialization

## Architectural Summary
`django.apps.registry.Apps` provides a thread-safe registry pattern that resolves circular dependencies and multi-phase startup coordination.

## Operational Guidelines
1. **Reentrant Lock Protection:** Guard registry state transitions (`populate()`, `get_models()`) using `threading.RLock()`.
2. **Explicit Readiness Flags:** Maintain `self.loading`, `self.apps_ready`, `self.models_ready`, and `self.ready` to fail fast on premature lookups (`AppRegistryNotReady`).
3. **Lazy String References:** Allow models and plugins to reference foreign dependencies as `"app_label.ModelName"` strings that are lazily resolved once all apps finish registering.
