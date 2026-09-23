# IoC Dispose Stack Inverse Accumulator Synchronization & Lifecycle Epoch Caching

## Problem
In micro-kernel architectures supporting hot-reloading and dynamic plugin lifecycle transitions, service registrations in the IoC container (`ServiceContext.provide()`) record inverse teardown effects onto a LIFO `_dispose_stack`. When services are subsequently unregistered or overridden via `revoke()` or `revoke_all_from()`, entries were purged from the service registry (`_entries`), but their corresponding inverse closures remained trapped in `_dispose_stack`. During final context disposal (`dispose()`), these orphaned closures would execute in reverse order, attempting to tear down already-revoked resources or throwing stale reference exceptions. Additionally, cascading lifecycle operations (such as disabling or unloading dependent plugins) repeatedly recomputed full Kahn topological sorts on unchanging dependency graphs.

## Solution
1. **Metadata-Tagged Inverse Closures**: When `ServiceContext.provide()` registers a service, attach metadata attributes directly to the inverse closure (`_inverse._realm_key = key` and `_inverse._provider = provider`).
2. **Active Pruning on Revocation**: During `revoke(key)` or `revoke_all_from(provider)`, filter and purge all closures matching the key or provider from `_dispose_stack`.
3. **Self-Healing Lifecycle Transitions**: Provide an explicit `ERROR → DISCOVERED` recovery path in `PluginLifecycle.ensure_enabled()`, allowing transient initialization failures to be retried without restarting the daemon.
4. **Lifecycle Epoch Caching**: Maintain a `_graph_epoch` monotonic counter in `PluginLifecycle` that increments only upon state mutations (`discover()`, `_transition()`). Cache `build_dependency_graph()` results within identical epochs.

## Operational Guideline
- Whenever designing inversion-of-control container teardown mechanisms, ensure registration inverse accumulators are two-way synchronized with unregistration operations.
- Memoize topological sort graphs across static lifecycle epochs to eliminate redundant DAG traversals.
- Enforce `AGENTS.md` Rule 54 in all kernel IoC extensions.

## Provenance
- Source files: `src/harness/kernel/context.py`, `src/harness/kernel/lifecycle.py`
- Verification suite: `tests/test_architecture_hardening.py`, `tests/test_context.py`, `tests/test_lifecycle.py`
- Repository Standard: `AGENTS.md` Rule 54
