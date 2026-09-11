# Architecture Explanation: Google Multi-Repository Integration

Deep dive into design decisions, seam partitioning, and execution invariants.

---

## 1. The Seam Partitioning Rationale (Rule 18)

Rather than assembling a monolithic Google omnibus plugin, capabilities are partitioned strictly across four primary functional domains:
- **`agent_orchestration`**: High-concurrency agent workflows and prompt mutation (ADK Runtime & Optimizer).
- **`developer_tooling`**: Human and agent introspection interfaces (Docs Navigator & Web Bridge).
- **`machine_learning`**: Heavy matrix calculus and TPU post-training (Tunix).
- **`software_engineering`**: Codebase conformance and system execution tracing (Styleguide & Perfetto).

Partitioning guarantees that an agent utilizing Perfetto trace processing does not load unnecessary JAX dependencies, eliminating cold-start timeouts and memory bloat.

---

## 2. Subprocess Isolation & Lazy Staging (Rule 5 & Rule 7)

External plugins sourced from outside the core kernel execute with `isolation: "subprocess"`:
1. **Safety Boundary**: Foreign C/C++ or JAX bindings execute in separate process spaces, preventing segfaults from crashing the Harness kernel.
2. **Lazy Staging**: Heavy virtual environments are validated during start-up but only provisioned upon initial invocation, ensuring deterministic sub-second boot times.

---

## 3. Subprocess Pipe Transport Disposal Invariant (Rule 14)

All asynchronous subprocess transports in the Harness must explicitly drain and close stdin, stdout, and stderr pipes inside `finally` blocks:

```python
try:
    await transport.start()
    return await transport.execute(...)
finally:
    await transport.drain_and_close()
```

This prevents dangling proactor handles and pipe corruptions on Windows environments.
