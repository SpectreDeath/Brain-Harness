# Architectural Decision Record: REA Size Exemptions & Decomposition Triggers

- **Status**: Accepted / Active
- **Date**: 2026-11-11
- **Deciders**: Architecture / Core Runtime Team
- **Context**: Brain Harness Rule 11 enforces module bounds (<=200 LOC per submodule in decomposed packages, and bounded service facades). During the REA Reverse-Engineering Toolkit precision deepening, three files required explicit sizing governance.

---

## 1. `src/harness/services/rea_toolkit.py` (1,906 LOC)

- **Role**: Core service facade coordinating artifact detection, plugin routing across 14 categories, signature aggregation, and CLI bridge dispatch for REA.
- **Decision**: Defer decomposition; maintain single-file service facade under Rule 20 (In-Place Deepening over Tool Sprawl).
- **Split Trigger**: **2,200 LOC**.
- **Rationale**: The service provides cohesive, high-throughput routing across four sandboxed plugins (`rea_native`, `rea_managed_runtime`, `rea_mobile_firmware`, `rea_javascript`). Splitting before 2,200 LOC introduces unnecessary indirection and cross-file imports for stable routing tables and alias maps.
- **Decomposition Target**: When line count reaches 2,200 LOC, decompose into:
```text
src/harness/services/rea/routing.py    (Artifact routing tables and alias resolution)
src/harness/services/rea/detection.py  (Heuristic artifact type detection)
src/harness/services/rea/service.py    (StandardReaToolkitService facade)
```

---

## 2. `plugins/security_and_forensics/rea_managed_runtime/engine/managed_pe.py` (335 LOC)

- **Role**: Legacy Windows PE / .NET CLI metadata and header parser.
- **Decision**: Temporary sizing exemption under Rule 11.
- **Ceiling Cap**: **400 LOC**.
- **Rationale**: Pre-existing legacy PE/CLI parser ported from the TypeScript upstream. Out of scope for commit `cf0300a` / `f0460de` model artifact hardening. Deferred to a dedicated PE decomposition milestone.
- **Decomposition Target**: When modified or reaching 400 LOC, factor out CLI metadata directory parsing:
```text
engine/pe_cli.py
```

---

## 3. `plugins/security_and_forensics/rea_managed_runtime/engine/model_artifact.py` (507 LOC)

- **Role**: Zero-allocation pure-Python AI model artifact inspection engine (GGUF, Safetensors, TFLite FlatBuffers, Keras/HDF5, TensorFlow SavedModel PB, TF.js weight shards).
- **Decision**: Sizing exemption under Rule 20 (cohesive binary dispatcher deepened in-place).
- **Ceiling Cap / Re-trigger**: **600 LOC**.
- **Trajectory**: File expanded from 412 LOC to 507 LOC (+95 lines) to implement true FlatBuffer table traversal for TFLite models (`Model.subgraphs.tensors`) and TF.js sibling weight manifest parsing.
- **Decomposition Target**: If further precision parsers expand this module beyond 600 LOC, split into `engine/model_parsers/` subpackage:
```text
tflite_parser.py    (FlatBuffer traversal)
hdf5_parser.py      (Superblock and layer weight extraction)
gguf_safetensors.py (Zero-allocation tensor metadata)
protobuf_tfjs.py    (SavedModel PB and weight shard manifests)
```

---

## 4. Mechanical Enforcement

All three thresholds are enforced mechanically by `tests/test_plugin_rea_managed_runtime.py::TestReaManagedRuntimePlugin::test_engine_subpackage_line_bounds`.
Exceeding any of the above thresholds fails the unit test suite with a direct citation to this document.
