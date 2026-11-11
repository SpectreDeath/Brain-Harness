# Semantic Signatures: model1_wfrontend.tflite (ai_model)

**Knowledge Item ID:** `ki-rea-sig-model1_wfrontend-9a4d5b7c`  
**Evidence Record:** `ev:7859c872d76cf5384dcc81ea7ce07942d86c686a2232fbd4dfb3464e30110fb2`  
**Artifact SHA-256:** `0ac5866ae7f30ddd8380c6047b4ba9071d6e2c21a9a8ce0721a98e145a4d5bb4`  
**Detected Kind:** `ai_model`  
**Provider:** `plugin.rea_managed_runtime`  

## Facet Availability Audit

| Facet | State | Availability Notes |
|---|---|---|
| `model_headers` | `AVAILABLE` | `Observed` |

## Extracted Semantic Signatures (8 total)

| Signature Kind | Identifier / Symbol | Structural Metadata |
|---|---|---|
| `model_format` | `tflite_v3` | `{"tensors_count": 7, "metadata": {"flatbuffer_identifier": "TFL3", "root_table_offset": 28, "size_bytes": 83144}}` |
| `model_tensor` | `audio_samples` | `{"dtype": "tflite_tensor", "shape": [1, 32000]}` |
| `model_tensor` | `model_10/tf.__operators__.getitem_14/strided_slice/stack` | `{"dtype": "tflite_tensor", "shape": [2]}` |
| `model_tensor` | `model_10/tf.__operators__.getitem_14/strided_slice/stack_1` | `{"dtype": "tflite_tensor", "shape": [2]}` |
| `model_tensor` | `model_10/tf.__operators__.getitem_14/strided_slice/stack_2` | `{"dtype": "tflite_tensor", "shape": [2]}` |
| `model_tensor` | `model_10/dense_10/MatMul` | `{"dtype": "tflite_tensor", "shape": [2048, 10]}` |
| `model_tensor` | `model_10/tf.__operators__.getitem_14/strided_slice` | `{"dtype": "tflite_tensor", "shape": [1, 10]}` |
| `model_tensor` | `Identity` | `{"dtype": "tflite_tensor", "shape": [1, 2048]}` |

## Isnad Lineage Chain
- Grounded in empirical observation `ev:7859c872d76cf5384dcc81ea7ce07942d86c686a2232fbd4dfb3464e30110fb2` produced by `plugin.rea_managed_runtime`.
- Regenerated 2026-11-11 following parser precision correction (FlatBuffer tensor-table traversal). Striking binary noise false positives (`p/T`, `l/8`, `_/N`) and recovering complete tensor graph (`audio_samples`, `Identity`).
- All unobserved facets strictly quarantined as `UNKNOWN` rather than conflated with zero.
