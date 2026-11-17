# Google Research `etcmodel`: Extended Transformer Construction (Global-Local Attention)

## 1. Context & Provenance

- **Upstream Repository**: `https://github.com/google-research/google-research` (`etcmodel/`)
- **Snapshot Reference**: `google-research-master` (archive snapshot, non-git)
- **Publication**: *ETC: Encoding Long and Structured Inputs in Transformers* (EMNLP 2020, `https://arxiv.org/abs/2004.08483`)
- **Primary Verified Sources**:
  - `etcmodel/README.md` (`L1-L95`)
  - `etcmodel/layers/attention.py` (`L27-L290`, sha256 `4bc561f65cf206d23f4733de85193ec9c61a8c631019ecc1085b2bc917e64c91`)
  - `etcmodel/feature_utils.py` (`L30-L110`, sha256 `da7e451ee01db6fe4d43cbe5621fd7365f14d4a7ae810072eae146a51105caa9`)

## 2. Core Architectural Invariants

1. **Global-Local Fused Softmax (`FusedGlobalLocalAttention`, `attention.py#L223-L290`)**: Partitions long inputs into local token windows of `local_radius` plus compact global summary tokens, fusing `l2l + l2g` under one softmax and `g2g + g2l` under one softmax. Standard dense self-attention is recovered as a special case when `local_radius` covers the full sequence and `share_kv_projections`/`share_qkv_projections`/`share_att_output_projection` hold, enabling direct weight lifting from pre-trained dense Transformers.
2. **Clipped Relative Position IDs (`RelativePositionGenerator`, `feature_utils.py#L30-L110`)**: Encodes bounded pairwise relative offsets (`left_pad_value = 2 * max_distance` directional, or `max_distance` when `ignore_direction=True`) so arbitrary-length sequences generalize over fixed relative vocabularies.

## 3. Applicability to Brain Harness

- Architectural analogue for Brain Harness's `RepoMap` + local file-slice pattern (`Rule 9`): pair a compact global structural index (module summaries/symbols) with bounded local file windows rather than flattening full-repo tokens into flat context.
