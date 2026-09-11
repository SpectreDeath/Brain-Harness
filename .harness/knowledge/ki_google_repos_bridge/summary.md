# Knowledge Item: Google Multi-Repository Bridge & Architectural Suite

## Executive Summary
This Knowledge Item captures the architectural patterns, seam partitioning strategies, and integration points distilled from six production Google open-source codebases:
1. **Google ADK (Agent Development Kit)**: High-scale ReAct and workflow agent paradigms, multi-turn state machines, Generative Prompt Optimization (GEPA), scenario evaluation benchmarks, and Angular/A2UI visualization.
2. **Google Style Guide**: Canonical enterprise style rules for Python, C++, TypeScript, Java, and Shell, including AST checking criteria for wildcard imports, mutable defaults, and bare exceptions.
3. **Google Tunix (Tune-in-JAX)**: State-of-the-art TPU/GPU post-training pipelines, Group Relative Policy Optimization (GRPO), parameter-efficient fine-tuning (PEFT/LoRA), and mathematical formatting/reasoning reward scoring.
4. **Google Perfetto**: Industry standard trace ingestion, SQL-based trace processor schema querying (`slice`, `sched`, `process`, `thread`), and call stack flame graph generation.

---

## Architectural Lessons & Invariants

### 1. Domain-Partitioned Plugin Synthesis (Rule 18)
Monorepo and multi-capability repositories must be decomposed along domain seams into single-responsibility plugins co-located in matching category folders (`agent_orchestration`, `developer_tooling`, `machine_learning`, `software_engineering`).

### 2. Subprocess Isolation & Windows Stdout Cleanliness (Rule 5, 7 & 14)
When executing subprocess sandboxes over JSON-RPC transports:
- Standard streams (`sys.stdout`) must be strictly reserved for JSON-RPC messages; background logging must never pollute stdout during top-level module imports.
- Subprocess transports must explicitly drain and close stdin/stdout/stderr pipes inside `finally` blocks to guarantee resource reclamation.
- Python 3.13 dataclass instantiation under custom `spec_from_file_location` requires module registration in `sys.modules[__name__]` prior to class decoration.
