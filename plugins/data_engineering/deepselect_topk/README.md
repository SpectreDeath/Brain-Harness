# plugin.deepselect_topk (v1.0.0)

DeepSelect High-Performance TopK Selection & DSA Routing Plugin with Monotonic Threshold Compaction and Hardware Contention Mitigation

---

## Overview & Metadata

| Property | Value |
|---|---|
| Plugin Directory | `plugins/data_engineering/deepselect_topk` |
| Category | `data_engineering` |
| Isolation Mode | `subprocess` |
| Services Provided | `deepselect.topk.service` |
| Dependencies Required | None |

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `deepselect_analyze_workload` | `(batch_size, vocab_size, topk, dtype, scenario)` | Analyze TopK workload dimensions and determine kernel variant dispatch with alignment constraints |
| `deepselect_estimate_bounds` | `(batch_size, vocab_size, topk, block_size, compact_threshold, dtype)` | Compute theoretical upper bounds on candidate elements E[W] and speedup relative to vanilla torch.topk |
| `deepselect_recommend_config` | `(batch_size, vocab_size, topk, dtype)` | Recommend optimal block sizes, compaction threshold, and Threadblock Cluster size for workload |
| `deepselect_simulate_selection` | `(input_matrix, topk, block_size, compact_threshold)` | Simulate randomized block scanning and monotonic threshold compaction on a 2D matrix of numbers |

---

## Key Modules & AST Symbols

### Module [main.py](main.py)

DeepSelect TopK Selection Plugin for Brain Harness.

#### Classes

- `class DeepSelectTopkPlugin` — Brain Harness Plugin bridging DeepSelect TopK kernel architecture & DSA routing.
  - `def name() -> str`
  - `def version() -> str`
  - `def description() -> str`
  - `def provides() -> list[ServiceKey[Any]]`
  - `def requires() -> list[ServiceKey[Any]]`
  - `def on_load(context) -> None`
  - `def enable(context) -> None`
  - `def on_disable() -> None`
  - `def disable(context) -> None`


#### Functions

- `def deepselect_analyze_workload(batch_size, vocab_size, topk, dtype, scenario) -> dict[str, Any]` — Analyze TopK workload dimensions and determine kernel variant dispatch.
- `def deepselect_estimate_bounds(batch_size, vocab_size, topk, block_size, compact_threshold, dtype) -> dict[str, Any]` — Compute theoretical upper bounds on candidate elements and speedup.
- `def deepselect_recommend_config(batch_size, vocab_size, topk, dtype) -> dict[str, Any]` — Recommend optimal block sizes and Threadblock Cluster size for workload.
- `def deepselect_simulate_selection(input_matrix, topk, block_size, compact_threshold) -> dict[str, Any]` — Simulate randomized block scanning and monotonic threshold compaction.

### Module [service.py](service.py)

Implementation of DeepSelectTopkService adhering to Rule 14 pipe drainage.

#### Classes

- `class DeepSelectTopkService` — Service providing DeepSelect TopK kernel planning, bounds estimation, and simulation.
  - `def analyze_workload(batch_size, vocab_size, topk, dtype, scenario) -> dict[str, Any]` — Analyze workload feasibility and generate kernel dispatch plan.
  - `def estimate_bounds(batch_size, vocab_size, topk, block_size, compact_threshold, dtype) -> dict[str, Any]` — Estimate mathematical bounds on candidate volume and throughput speedup.
  - `def recommend_config(batch_size, vocab_size, topk, dtype) -> dict[str, Any]` — Recommend optimal block size B, threshold B2, and Threadblock Cluster size.
  - `def simulate_selection(input_matrix, topk, block_size, compact_threshold) -> dict[str, Any]` — Simulate randomized block scan and monotonic threshold filtering.
  - `def run_sandboxed_benchmark(script_path) -> dict[str, Any]` — Run an isolated subprocess benchmark adhering strictly to Rule 14 pipe drainage.


---

## Quickstart & Usage

```python
from harness.kernel.context import ServiceContext
from plugins.data_engineering.deepselect_topk.main import plugin

# Load plugin into harness service context
context = ServiceContext()
plugin.on_load(context)
```

---

## Architecture & Diátaxis Classification

- Diátaxis Quadrant: Reference (Track B) & How-To Guides
- Isolation: `subprocess` execution sandbox
- Invariants: Slotted dataclass architecture (Rule 12), transactional context bounds (Rule 8), and zero-fork YAML configuration (Rule 44).
