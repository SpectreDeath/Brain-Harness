# Loop Engine Plugin — Quickstart Guide

The `domain.loop_engine` plugin implements Addy Osmani's Goal-Directed Loop Engineering architecture.

Instead of naive all-or-nothing linear pipelines, it executes tasks over a directed acyclic graph (DAG) using a state machine that handles:
- **Tri-State Resource Polling**: Distinguishes "resolved", "pending" (still resolving), and "missing" (permanently unavailable).
- **Decision Fixtures / HITL**: Tri-state ambiguity resolution.
- **Branch Isolation**: When one branch permanently deadlocks on a missing resource, unrelated branches continue executing to completion.
- **Retry & Revision**: Automatic retries for flaky or transient task steps before marking permanent failures.

## 🚀 Quick Usage

```python
from plugins.agent_orchestration.loop_engine.main import run_loop, benchmark_loop_vs_linear

# 1. Execute task graph with delayed resource
tasks = [
    {"task_id": "fetch_cfg", "requires_resource": "remote_config"},
    {"task_id": "process_data", "depends_on": ["fetch_cfg"], "max_retries": 2},
    {"task_id": "independent_job"},
]

res = run_loop(
    tasks=tasks,
    eventually_available_resources={"remote_config": 2},
    max_iterations=50
)
print(f"Completed: {res['result']['completed']}/3 in {res['result']['iterations']} iterations")
print(f"Recoveries: {res['result']['total_recoveries']}")

# 2. Benchmark against linear baseline
bench = benchmark_loop_vs_linear(num_scenarios=20, seed=42)
print(f"Loop Controller: {bench['loop_controller']['completion_rate_pct']}% completion")
print(f"Linear Baseline: {bench['linear_baseline']['completion_rate_pct']}% completion")
```
