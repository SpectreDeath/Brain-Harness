# QuerySpec Parameter Pass-Through Invariant

> **Identifier:** `ki_self_20261109_02_reasoner_parameter_propagation_invariant`  
> **Category:** `software_engineering`  
> **Author:** Brain Harness Reflector (`harness-reflector`)  
> **Status:** `ACTIVE` | **Isnād Status:** `VERIFIED`

---

## 1. Context & The Parameter Shadowing Defect

In modular AI harnesses and MCP tools, callers specify execution budgets using domain request objects (e.g. `QuerySpec(timeout_seconds=0.05, max_inferences=50000)`).

In `PrologReasoner.query`, these parameters were unpacked:
```python
to = spec.timeout_seconds if spec.timeout_seconds is not None else timeout_seconds
mi = spec.max_inferences if spec.max_inferences is not None else max_inferences
```
However, the downstream call to the worker process was authored as:
```python
worker.execute_goal(goal_str, max_inferences=max_inferences, timeout_seconds=timeout_seconds)
```
Because `max_inferences` and `timeout_seconds` matched the outer function's default arguments (`1_000_000` and `10.0`), the unpacked variables `to` and `mi` were silently abandoned. Custom timeout requests (such as 0.05s tight SLA deadlines) were completely ignored, falling back to a 10.0s blocking wait.

---

## 2. Invariant & Resolution

1. **Strict Variable Propagation**:
   - Subprocess invocation calls must pass the resolved operational constraints (`timeout_seconds=to`, `max_inferences=mi`).
2. **Exception Payload Fidelity**:
   - When raising `QueryTimeoutError` or `QueryInferenceLimitError`, exception error messages must display the actual caller-configured limit (`to` or `mi`), rather than outer defaults.
3. **Anti-Shadowing Linter Seam**:
   - Unused local variables unpacked from spec objects must be flagged by static linters to prevent silent abandonment.

---

## 3. Empirical Verification & Isnād Lineage

- **Fixed Commit**: `SpectreDeath/Ontology-Spider@8614a82`
- **Test Contract**: `test_mcp.py::test_large_chain_query_memory_bounded` (0.05s timeout raises `QueryTimeoutError` in 0.050s).
- **CI Receipt**: GitHub Actions Run `#42536702405`.
