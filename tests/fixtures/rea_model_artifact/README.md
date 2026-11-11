# REA Model Artifact Test Fixtures

Minimal binary model fixtures providing deterministic, dependency-free test signal in CI environments without external repo clones (Track 0.2 / Rule 13).

## Fixtures Overview

| File | Size | Format | Provenance & Specification |
|---|---|---|---|
| `minimal_speech.tflite` | 592 B | `tflite_v3` | Synthesized to match FlatBuffer table structure of `google-research-master/.../model1_wfrontend.tflite`. Contains Model root table, SubGraph, and 7 exact Tensor tables (`audio_samples`, 5 intermediate slices/matmul, and `Identity`). Also embeds raw byte fragments (`p/T`, `l/8`, `_/N`) in padding to catch regression to naive regex parsing. |
| `minimal_keras.h5` | 118 B | `hdf5_v0` | Synthesized to match HDF5 v0 superblock and Keras layer weights of `google-research-master/.../model.h5`. Contains `\x89HDF\r\n\x1a\n\x00` magic, `model_config` header, and 4 exact weight datasets (`dense/kernel:0`, `dense/bias:0`, `lstm_cell/kernel:0`, `lstm_cell/bias:0`). |

## Tensor Specifications

### `minimal_speech.tflite` (7 tensors)
1. `audio_samples` `[1, 32000]`
2. `model_10/tf.__operators__.getitem_14/strided_slice/stack` `[2]`
3. `model_10/tf.__operators__.getitem_14/strided_slice/stack_1` `[2]`
4. `model_10/tf.__operators__.getitem_14/strided_slice/stack_2` `[2]`
5. `model_10/dense_10/MatMul` `[2048, 10]`
6. `model_10/tf.__operators__.getitem_14/strided_slice` `[1, 10]`
7. `Identity` `[1, 2048]`

### `minimal_keras.h5` (4 tensors)
1. `dense/kernel:0`
2. `dense/bias:0`
3. `lstm_cell/kernel:0`
4. `lstm_cell/bias:0`
