# Google Research `scaling_transformer_inference_efficiency`: Partitioned Low-Latency Decoding

## 1. Context & Provenance

- **Upstream Repository**: `https://github.com/google-research/google-research` (`scaling_transformer_inference_efficiency/`)
- **Snapshot Reference**: `google-research-master` (archive snapshot, non-git)
- **Publication**: *Efficiently Scaling Transformer Inference* (`http://arxiv.org/abs/2211.05102`)
- **Primary Verified Sources**:
  - `scaling_transformer_inference_efficiency/README.md` (`L1-L37`)
  - `scaling_transformer_inference_efficiency/partitioning.py` (`L42-L173`, sha256 `d478358ffbf77fe918ae57cfd17e4b317b40ab24b2844a55b0a47c0a7c548c05`)
  - `scaling_transformer_inference_efficiency/inference.py` (`L60-L109`, sha256 `3f4130f2fa61748df9dcd5323cdf4fdd01efc74e0d1d714e268b82552d4b53fa`)

## 2. Core Architectural Invariants

1. **Logical-to-Physical Partitioning Rules (`partitioning.py`)**: Rather than hardcoding shard specs at every call site, `make_rules_two_d`, `make_rules_one_d`, and `make_rules_weight_gathered` bind logical tensor axis names (`residual_embed`, `heads`, `vocab`, `attn_batch`, etc.) to physical 3D mesh axes `(x, y, z)` under a thread-local `PartitioningRules` context stack, switching weight-stationary vs weight-gathered regimes via `AttnAllToAll`.
2. **Prefix-Shared Multi-Sample Decoding (`inference.py`)**: `infer()` enforces `batch % prefix_batch == 0`, slicing shared RoPE `sin`/`cos` tables once per prefix using `attention.prefix_lengths(kv_caches)` + `jax.vmap(lax.dynamic_slice_in_dim)` and writing static-shape KV slices via `lax.dynamic_update_index_in_dim` to eliminate dynamic reallocation during decode.

## 3. Applicability to Brain Harness

- Directly complements **prefix-cache-stable context engineering** (`Rule 9`) and **multi-trace sampling (`cisc`)**: grouping multiple verification/reasoning rollouts over an identical prompt prefix avoids recomputing KV prefixes across traces.
