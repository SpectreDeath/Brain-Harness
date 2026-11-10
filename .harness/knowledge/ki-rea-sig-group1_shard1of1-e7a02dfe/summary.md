# Semantic Signatures: group1-shard1of1.bin (ai_model)

**Knowledge Item ID:** `ki-rea-sig-group1_shard1of1-e7a02dfe`  
**Evidence Record:** `ev:92401778d591846ecebe44449462c2a5eb8b0607630c09304ed47bc9db7889c1`  
**Artifact SHA-256:** `445a582808b7d9a0868f8163eaf18cdea375736476b3c6b50152984dba070a0c`  
**Detected Kind:** `ai_model`  
**Provider:** `plugin.rea_managed_runtime`  

## Facet Availability Audit

| Facet | State | Availability Notes |
|---|---|---|
| `model_headers` | `AVAILABLE` | `Observed` |

## Extracted Semantic Signatures (6 total)

| Signature Kind | Identifier / Symbol | Structural Metadata |
|---|---|---|
| `model_format` | `tfjs_weight_shard` | `{"tensors_count": 5, "metadata": {"shard_name": "group1-shard1of1.bin", "size_bytes": 92680, "float32_elements": 23170, "format": "layers-model", "generated_by": "keras v2.3.0-tf", "converted_by": "TensorFlow.js Converter v2.0.1.post1"}}` |
| `model_tensor` | `dense/kernel` | `{"dtype": "float32", "shape": [64, 2]}` |
| `model_tensor` | `dense/bias` | `{"dtype": "float32", "shape": [2]}` |
| `model_tensor` | `lstm/lstm_cell/kernel` | `{"dtype": "float32", "shape": [25, 256]}` |
| `model_tensor` | `lstm/lstm_cell/recurrent_kernel` | `{"dtype": "float32", "shape": [64, 256]}` |
| `model_tensor` | `lstm/lstm_cell/bias` | `{"dtype": "float32", "shape": [256]}` |

## Isnad Lineage Chain
- Grounded in empirical observation `ev:92401778d591846ecebe44449462c2a5eb8b0607630c09304ed47bc9db7889c1` produced by `plugin.rea_managed_runtime`.
- All unobserved facets strictly quarantined as `UNKNOWN` rather than conflated with zero.
