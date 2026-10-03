# Copy-on-Write (COW) Lock-Free Context Registry & Transaction Inverse Compaction

## Problem
In concurrent multi-agent executions, agent step loops constantly perform read operations on the `ServiceContext` IoC container (`require`, `optional`, `has`). Concurrently, background workers, tools, and interceptors perform writes (`provide`, `transaction` commit, `revoke`).
Traditional implementations using locks (`threading.Lock` or `asyncio.Lock`) on read paths introduce significant overhead and reader-writer contention.
Additionally, when ReAct agent tool transactions commit changes into the parent context, accumulating inverse rollback closures in `_dispose_stack` creates massive memory bloat if multiple steps touch the same realm key (e.g. repeated temporary overrides), leading to cascading, duplicate rollbacks on teardown.

## Solution
1. **Lock-Free Read Fast Path (COW Pattern)**:
   - On mutation (`provide`, `transaction` commit), `_entries` is shallow-copied, mutated, and swapped atomically via pointer reassignment (`self._entries = new_entries`). Under the Python GIL, atomic pointer reassignment allows concurrent readers to access `_entries` without acquiring locks.
   - Cache invalidation for compiled interceptors is governed by `_interceptor_epoch` integers incremented on mutation on both root and local contexts.
2. **Transaction Inverse Compaction**:
   - During transaction commit (`tx_ctx._dispose_stack` merging into `self._dispose_stack`), inverses are scanned in reversed order.
   - Only the latest inverse closure per `_realm_key` is retained, pruning superseded inverse actions and bounding `_dispose_stack` growth.

## Operational Guideline
- Never acquire `_mutation_lock` on read paths (`require`, `optional`). Reads must resolve directly from the immutable `_entries` dict.
- Tag inverse closures with `_realm_key` and `_provider` attributes so compaction can deduplicate them.
- Always increment `_interceptor_epoch` on the root context when modifying interceptors to invalidate child caches.

## Provenance
- Source code: `src/harness/kernel/context.py`
- Test contracts: `tests/test_context.py::test_context_lock_free_read_latency`, `test_transaction_inverse_compaction`, `test_interceptor_epoch_increments_on_write`
- Verification: 42/42 tests passing in 10.09s
