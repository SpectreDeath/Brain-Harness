# Google Research `model_pruning`: Polynomial Sparsity Schedules & Cross-Package Coupling

## 1. Context & Provenance

- **Upstream Repository**: `https://github.com/google-research/google-research` (`model_pruning/`)
- **Snapshot Reference**: `google-research-master` (archive snapshot, non-git)
- **Primary Verified Sources**:
  - `model_pruning/README.md` (`L1-L90`)
  - `model_pruning/python/pruning.py` (`L30-L110`, sha256 `91c528c2951e903a3100473e758a524a192155faa5e12d174a752db3c8d80f9a`)

## 2. Core Architectural & Structural Findings

1. **Gradual Cubic Sparsity Schedule (`README.md`, `L61-L75`)**: Transitions smoothly from `initial_sparsity` (`0.0`) to `target_sparsity` (`0.5`) across `[sparsity_function_begin_step, sparsity_function_end_step]` updated every `pruning_frequency` steps with polynomial exponent `3.0`, supporting structured `block_height x block_width` pooling (`AVG` or `MAX`) and weight/gradient criteria.
2. **Bidirectional Cross-Project Cycle (`pruning.py`, `L93`)**: `model_pruning/python/pruning.py#L93` imports `graph_compression.compression_lib.compression_op_utils`, while `graph_compression` also imports `model_pruning` — the exact cycle flagged by `Ontology-Spider` (`graph_compression -> model_pruning -> graph_compression`).

## 3. Applicability to Brain Harness

- Reinforces both **monotonic budget decay curves** (for staged pruning / context reduction) and **acyclic shared-helper extraction** (`Rule 3` / `Rule 13`).
