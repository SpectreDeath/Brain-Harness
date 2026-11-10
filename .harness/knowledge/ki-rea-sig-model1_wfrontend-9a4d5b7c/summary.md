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

## Extracted Semantic Signatures (9 total)

| Signature Kind | Identifier / Symbol | Structural Metadata |
|---|---|---|
| `model_format` | `tflite_v3` | `{"tensors_count": 8, "metadata": {"flatbuffer_identifier": "TFL3", "root_table_offset": 28, "size_bytes": 83144}}` |
| `model_tensor` | `model_10/tf.__operators__.getitem_14/strided_slice` | `{"dtype": "tflite_tensor", "shape": []}` |
| `model_tensor` | `p/T` | `{"dtype": "tflite_tensor", "shape": []}` |
| `model_tensor` | `l/8` | `{"dtype": "tflite_tensor", "shape": []}` |
| `model_tensor` | `_/N` | `{"dtype": "tflite_tensor", "shape": []}` |
| `model_tensor` | `model_10/dense_10/MatMul` | `{"dtype": "tflite_tensor", "shape": []}` |
| `model_tensor` | `model_10/tf.__operators__.getitem_14/strided_slice/stack_2` | `{"dtype": "tflite_tensor", "shape": []}` |
| `model_tensor` | `model_10/tf.__operators__.getitem_14/strided_slice/stack_1` | `{"dtype": "tflite_tensor", "shape": []}` |
| `model_tensor` | `model_10/tf.__operators__.getitem_14/strided_slice/stack` | `{"dtype": "tflite_tensor", "shape": []}` |

## Isnad Lineage Chain
- Grounded in empirical observation `ev:7859c872d76cf5384dcc81ea7ce07942d86c686a2232fbd4dfb3464e30110fb2` produced by `plugin.rea_managed_runtime`.
- All unobserved facets strictly quarantined as `UNKNOWN` rather than conflated with zero.
