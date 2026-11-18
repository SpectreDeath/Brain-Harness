# AirLLM Fused Chunked Linear Cross-Entropy

## Provenance
- **Upstream Repository**: `https://github.com/lyogavin/airllm` (`af3c212c52ebecad95f0d25eb2595e82988d0cdd`)
- **File**: `air_llm/airllm/chunked_ce.py#L1-L90` (`sha256: 0e45c9484af4a6840fe0195a14693122f682278c59cd381a5df1a5fa03190960`)
- **REA Evidence**: `ev:1f13936c4d83cd5b499418b7333c803a215101191766090739eafd09adf9787b` (extracted symbols `_compute_device`, `_ChunkedCE`, `chunked_linear_cross_entropy`)

## Mechanism
- On wide-vocabulary models (`~248k` tokens), materializing `[N, vocab]` float32 logits adds gigabytes of peak VRAM.
- `_ChunkedCE` (`torch.autograd.Function`) leaves `lm_head.weight` on CPU when needed, streams slices of `chunk_size = 4096` onto `_compute_device(hidden)`, tracks running float32 partition `logz = torch.logaddexp(logz, logits.logsumexp(dim=-1))` alongside `target_logit`, and saves only `hidden`, `labels`, `valid`, and `logz` for chunked recomputation in `backward()`.
