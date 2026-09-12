# domain.loop_engine (v1.1.0)

Goal-directed agent loop state machine with tri-state resource polling, decision fixtures, stepwise control, and checkpoint persistence

---

## Overview & Metadata

- **Plugin Directory**: `plugins/agent_orchestration/loop_engine`
- **Isolation Mode**: `subprocess`
- **Services Provided**: None
- **Dependencies Required**: None

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `run_loop` | `(tasks, available_resources, eventually_available_resources, decision_answers, max_iterations, initial_context)` | Execute a goal-directed task DAG loop with tri-state polling, decision recovery, and branch deadlock isolation |
| `step_loop` | `(checkpoint, context, new_tasks)` | Execute a single iteration step on an existing loop checkpoint, optionally injecting dynamic tasks |
| `export_loop_checkpoint` | `(tasks, available_resources, eventually_available_resources, decision_answers, max_iterations)` | Initialize and export a pristine loop state checkpoint without running it |
| `validate_task_dag` | `(tasks)` | Validate task DAG for cyclic dependencies, missing task IDs, and structural correctness |
| `benchmark_loop_vs_linear` | `(num_scenarios, seed, max_iterations)` | Benchmark goal-directed LoopController against one-shot linear baseline across failure topologies |
| `create_scenario_graph` | `(num_branches, tasks_per_branch, seed, failure_mix)` | Generate a synthetic task graph scenario with controlled failure and latency injection |

---

## Key Modules & AST Symbols

### Module [`loop_core.py`](loop_core.py)

Core Goal-Directed Loop Engine: Task Graph DAG, Tri-State Polling, Stepwise Control, and Checkpointing.

#### Classes

- `class Status`
- `class Task`
  - `def log(event) -> None`
  - `def to_dict() -> dict[str, Any]`
  - `def from_dict(cls, d) -> Task`
- `class TaskGraph`
  - `def __init__(tasks)`
  - `def add_dynamic_task(task) -> None`
  - `def add_dependency(task_id, depends_on_id) -> None`
  - `def dependencies_satisfied(task) -> bool`
  - `def blocked_dependency(task) -> str | None`
  - `def counts() -> dict[str, int]`
  - `def is_terminal() -> bool`
- `class ResourceStore`
  - `def retrieve(key) -> tuple[str, Any]`
  - `def to_dict() -> dict[str, Any]`
  - `def from_dict(cls, d) -> ResourceStore`
- `class DecisionFixture`
  - `def ask(key) -> tuple[str, Any]`
  - `def to_dict() -> dict[str, Any]`
  - `def from_dict(cls, d) -> DecisionFixture`
- `class IterationSnapshot`
  - `def to_dict() -> dict[str, Any]`
  - `def from_dict(cls, d) -> IterationSnapshot`
- `class LoopResult`
  - `def completed() -> int`
  - `def progress_efficiency() -> float`
  - `def to_dict() -> dict[str, Any]`
- `class LoopController`
  Goal-directed agent loop state machine with stepwise execution, checkpointing, and dynamic task injection.
  - `def __init__(graph, resources, decisions, max_iterations)`
  - `def register_observer(observer) -> None`
  - `def step(context) -> tuple[int, dict[str, Any], bool]`
  - `def run(context) -> LoopResult`
  - `def export_checkpoint() -> dict[str, Any]`
  - `def restore_checkpoint(cls, data) -> LoopController`


#### Functions

- `def run_linear(graph, resources, decisions, context) -> dict[str, Any]`
- `def build_scenario(num_branches, tasks_per_branch, seed, failure_mix) -> tuple[list[Task], ResourceStore, DecisionFixture]`


### Module [`main.py`](main.py)

Main entrypoint and typed tool registrations for Goal-Directed Loop Engine plugin.

#### Classes

- `class LoopEngineService`
  Service provider for Goal-Directed Loop Engineering.
  - `def run(tasks, available_resources, eventually_available_resources, decision_answers, max_iterations, initial_context) -> dict[str, Any]`
  - `def step(checkpoint, context, new_tasks) -> dict[str, Any]`
  - `def export_checkpoint(tasks, available_resources, eventually_available_resources, decision_answers, max_iterations) -> dict[str, Any]`
  - `def validate(tasks) -> dict[str, Any]`
  - `def benchmark(num_scenarios, seed, max_iterations) -> dict[str, Any]`
  - `def generate_scenario(num_branches, tasks_per_branch, seed, failure_mix) -> dict[str, Any]`


#### Functions

- `def run_loop(tasks, available_resources, eventually_available_resources, decision_answers, max_iterations, initial_context) -> dict[str, Any]`
  - Execute a goal-directed task DAG loop with tri-state resource polling and deadlock isolation.
- `def step_loop(checkpoint, context, new_tasks) -> dict[str, Any]`
  - Execute a single iteration step on an existing loop checkpoint, optionally injecting dynamic tasks.
- `def export_loop_checkpoint(tasks, available_resources, eventually_available_resources, decision_answers, max_iterations) -> dict[str, Any]`
  - Initialize and export a pristine loop state checkpoint without running it.
- `def validate_task_dag(tasks) -> dict[str, Any]`
  - Validate task DAG for cyclic dependencies, missing task IDs, and structural correctness.
- `def benchmark_loop_vs_linear(num_scenarios, seed, max_iterations) -> dict[str, Any]`
  - Benchmark goal-directed LoopController against one-shot linear baseline across failure topologies.
- `def create_scenario_graph(num_branches, tasks_per_branch, seed, failure_mix) -> dict[str, Any]`
  - Generate a synthetic task graph scenario with controlled failure and latency injection.



---

## Related Documentation & Configuration
- Manifest: [`plugin.json`](plugin.json)
- Architecture Seams: [Context Architecture](../../../CONTEXT-MAP.md) | [User Manual](../../../USER_MANUAL.md)
