# AirLLM Layer-Wise Disk Offloading, Per-Expert MoE Streaming & On-GPU Packed Decompression

## Provenance
- **Upstream Repository**: `https://github.com/lyogavin/airllm` (`af3c212c52ebecad95f0d25eb2595e82988d0cdd`)
- **Surfaced By**: Ontology-Spider (`air_llm` unlearned tested `nlp_and_llm_project`) + REA `plugin.rea_managed_runtime` (`cpython_pyc` signature extraction `ev:653cd6965569ee6db6a850c0d0fdc9b3ffe73d8c2c4cc14c6a660e48fa07aaee`)

## Key Mechanisms
1. **Meta-Device Instantiation & Runtime Mixin (`air_llm/airllm/airllm_base.py`)**:
   - Instantiates `*ForCausalLM` on `meta` via `accelerate.init_empty_weights()`, materializes small buffers (`inv_freq`), re-exports relocated `transformers` symbols, and patches `device`/`dtype` properties + `GenerationMixin` when absent in `transformers >= 4.50`.
2. **Per-Layer On-GPU Packed Decompression & Bounded Pinning**:
   - Removes `ct_decompress_hook` before inference so `compressed-tensors` never pre-expands all layers; transfers packed weights across PCIe (`4x` bandwidth savings for MXFP4) and calls `compressor.decompress()` on-GPU inside `_decompress_state_dict`.
   - Enforces `max_pinned_layer_bytes = 2 * 1024**3` before calling `.pin_memory()`, falling back cleanly to pageable memory on `RuntimeError`.
3. **Granular MoE Expert Streaming (`air_llm/airllm/airllm_kimi_k3.py`)**:
   - Configures `expert_prefix: 'block_sparse_moe.experts'` and keeps only compact routing/projection towers in `'resident'`, cutting loaded bytes per token on `896`-expert layers from `~55 GB` down to `~1 GB`.
