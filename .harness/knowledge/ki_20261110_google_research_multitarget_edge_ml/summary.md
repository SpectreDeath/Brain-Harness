# Multi-Target Edge ML Serialization & Streaming Delay-Line Architecture

## Context & Provenance
Distilled from deep inspection of the **Google Research** monorepo (`google-research-master`, 760 projects, 19,618 sampled files) using `StandardReaToolkitService`, `ReaManagedRuntimeService`, and `MemGraphRAGService`.

## Core Architectural Invariants
1. **Frontend-Decoupled TFLite Graph Partitioning**:
   Audio and speech benchmarks (`non_semantic_speech_benchmark`, `kws_streaming`) export paired FlatBuffer (`TFL3`) artifacts: `model1_wfrontend.tflite` (83,144 B, embedding spectrogram/mel-filterbank ops in-graph) and `model1_woutfrontend.tflite` (271,188 B, accepting pre-computed features). Streaming layers wrap standard Keras/TF layers with explicit state ring buffers so non-streaming training graphs compile cleanly into stateful microcontroller inference graphs.
2. **Dual-Runtime Keras HDF5 to TensorFlow.js Sharding**:
   Real-time interactive pipelines (`sign_language_detection`) maintain synchronized weight representations across Python (`models/py/model.h5`, HDF5 superblock v0, 109,264 B) and browser runtimes (`models/js/model.json` + `group1-shard1of1.bin`, 92,680 B). REA dissection of the binary shard alongside its sibling manifest recovers all 5 constituent tensors (`dense/kernel` `[64, 2]`, `dense/bias` `[2]`, `lstm/lstm_cell/kernel` `[25, 256]`, `lstm/lstm_cell/recurrent_kernel` `[64, 256]`, `lstm/lstm_cell/bias` `[256]`).
3. **Declarative Configuration Graphs**:
   Across 760 subprojects, 321 `.gin` configuration files and `absl.flags` modules (`args.py`) isolate experimental hyperparameter sweeps from core neural architecture definitions.
