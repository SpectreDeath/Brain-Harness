# REA Slotted Report Serialization & MemGraphRAG Partition Propagation Invariant

## Problem & Discovery Context
During large-scale execution of the REA Reverse-Engineering Toolkit and MemGraphRAG knowledge graphing engines against `google-research-master` (760 projects), three cross-seam friction points surfaced:
1. `ReaDomainAdapter.call_managed` checked `hasattr(res, "model_dump")` and `hasattr(res, "to_dict")` on `ReaManagedReportBase` instances. Because `ReaManagedReportBase` only implemented `__getitem__`, `get`, and `__contains__`, `call_managed` evaluated to `{}` and marked `model_headers` and `pyc_code` facets as `[UNKNOWN]`.
2. `StandardReaToolkitService.detect_artifact` and `ModelArtifactEngine` only routed `.gguf` and `.safetensors` to `ai_model`, causing `.tflite` (`TFL3`), `.h5` (`\x89HDF`), and `saved_model.pb` to fall through to `unknown` and TF.js `group1-shard1of1.bin` to misclassify as `firmware`.
3. `MemGraphRAGPlugin.retrieve()`, `query()`, and `add_passage()` omitted the `save_dir: str = "outputs/default"` parameter supported by the underlying engine, causing queries after `index(..., save_dir=custom_dir)` to inspect an unindexed default partition.

## Resolution & Invariants
- **Slotted Dataclass Serialization (`ReaManagedReportBase`)**: Implement `to_dict(self)` and `model_dump(self)` returning `dataclasses.asdict(self)` on all slotted service report base classes.
- **Multi-Format AI Model Forensics (`ModelArtifactEngine` & `StandardReaToolkitService`)**: Support zero-allocation header and manifest inspection across GGUF, Safetensors, TFLite (`TFL3`), Keras/HDF5 (`\x89HDF\r\n\x1a\n`), TensorFlow SavedModel (`.pb`), and TensorFlow.js binary weight shards (`*shard*.bin` with automatic sibling `model.json` `weightsManifest` tensor recovery), emitting structured `SemanticSignature` records for tensors, bytecode imports/functions, and JS classes/functions.
- **Partition Parameter Pass-Through (`MemGraphRAGService`)**: Expose `save_dir: str = "outputs/default"` across all `MemGraphRAGService` protocol and plugin methods (`index`, `retrieve`, `query`, `add_passage`, `get_summary`, `detect_conflicts`).
