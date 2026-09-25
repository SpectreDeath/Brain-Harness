# Bounded ReAct Context Accumulator Rotation, Interceptor Epoch Invalidation, and AST Codeblock Anti-Pattern Interception

## Problem
In autonomous agent runtimes executing deep reasoning trajectories:
1. **Unbounded Inverse Closure Accumulation**: Every transactional tool execution or service registration pushes cleanup closures to `ServiceContext._dispose_stack`. In multi-agent swarms executing 100+ steps, these closures accumulate in memory, retaining references to completed intermediate steps.
2. **Stale Hierarchical Interceptor Pipelines**: Fast-path caching of compiled interceptor chains in `ServiceContext` must be invalidated when a child or parent registers a new interceptor. Without epoch tracking tied to the root context, deep context trees may execute stale interceptor chains.
3. **Late-Stage Action Failures**: Model-generated tool inputs often contain dangerous or interactive code patterns (such as `input()`, `eval()`, or `exec()`). If checked only upon execution, the step crashes and the agent must consume a full conversational turn and additional token budget to diagnose the error.

## Solution
1. **Cadenced Context Rotation**: In `StepExecutionEngine.step()`, evaluate `_step_count % self._context_rotation_cadence == 0` (cadence: 25 steps). If true and the context is a child, dispose the child context (executing pending inverse closures) and spawn a clean child context from the parent.
2. **Root Interceptor Epoch Tracking**: `ServiceContext.intercept()` increments `_interceptor_epoch` on the root context (`_get_root()`). The compilation cache stores `(root_epoch, chain)`, guaranteeing $O(1)$ validity checks and automatic re-compilation on changes.
3. **AST Syntax Tree Anti-Pattern Interception**: `AntiPatternGuard._check_code_ast()` extracts fenced Python blocks with regex and parses the AST. It walks the tree (`ast.walk()`) for `ast.Call` nodes invoking blocked identifiers (`eval`, `exec`, `input`, `__import__`). If detected, `format_self_repair_observation()` returns a structured ReAct observation with `status: "error"` and `corrective_action_required: True` for immediate in-flight self-repair before tool execution.
4. **Zero-Synthetic Reachability**: `BuiltinSkillRegistryService.route_intent()` strictly returns `recommended_chain = []` whenever `get_chain()` between matched skills returns `status: "no_path"` (Rule 55).

## Operational Guideline
- Keep session contexts bounded in ReAct loops by rotating child contexts at regular step intervals.
- Always use `ast.parse` and `ast.walk` rather than raw string regular expressions when screening code proposals for anti-patterns.
- Enforce strict reachability across skill DAG routing without synthesizing fake single-node or direct edges.

## Provenance
- Source files: `src/harness/agent/react.py`, `src/harness/kernel/context.py`, `src/harness/services/skill_graph.py`
- Test suites: `tests/test_architectural_modernization.py`
- Architectural Rules: `AGENTS.md` Rules 21, 51, 54, 55
