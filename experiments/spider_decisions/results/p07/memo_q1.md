# Design Memo Q1 — Eviction & Prefetch Policy for Lazily-Staged Plugin Artifacts

**Design Question:** *"What eviction/prefetch policy should Brain Harness use for lazily-staged plugin artifacts?"*

## Recommendation

Adopt a **4-part bounded prefetch + dual-capped LRU eviction policy** for lazily-staged plugin artifacts and sub-environments:

1. **Contiguous Super-Block / Offset-Indexed Artifact Reads:** Group repeated per-plugin metadata/bytecode/shard reads into offset-indexed lookups (`f.seek(offset)` / `f.read(size)` rather than repeated full directory/manifest scans) (`ki_airllm_plus_superblock_prefetch_runtime`, Verified).
2. **Depth-Bounded Producer-Consumer Prefetch:** Overlap upcoming plugin/step staging I/O with current execution via a bounded queue (`queue.Queue(maxsize=depth)`) daemon worker so cold-start latency is masked without unbounded background spawning (`ki_airllm_plus_superblock_prefetch_runtime`, Verified).
3. **Dual Entry-Count & Byte-Size OrderedDict LRU Eviction:** Evict cached artifact handles/buffers in thread-safe `OrderedDict` LRU order enforcing **both** `max_blocks` (count limit) **and** `max_size_bytes` (memory/disk limit), cleanly skipping oversized artifacts rather than thrashing the entire cache (`ki_airllm_plus_superblock_prefetch_runtime`, Verified).
4. **Selective Demand Loading & Buffer Caps:** Stage/load only actively routed sub-components (`~16 of 896` active experts rather than full layers; `<= max_pinned_layer_bytes = 2 GiB` with pageable fallback) (`ki_airllm_layerwise_streaming_and_moe_expert_offload`, Verified), warm-load long-lived UI/worker runtimes at worker init once active (`ki_self_20260917_04`, Verified), and detect dynamic identifiers without mutating immutable prompt-cache prefixes (`ki_20261028_headroom_context_optimization`, Verified).

## Supporting Claims Cited

| KI ID | Claim Text | File / Lines | Claim Status | KI Isnad Verified |
|---|---|---|---|---|
| `ki_airllm_plus_superblock_prefetch_runtime` | "pack_blocks.py groups per-layer tensor shards (.safetensors/.bin/.pt/.onnx) into contiguous multi-layer super-blocks (default layers_per_block=4) recorded with TensorMeta byte offsets/sizes in index.json so runtime/store.py performs sequential reads or O(1) f.seek(offset)/f.read(size) range reads." | `pack/pack_blocks.py` `L1-L110` | **VERIFIED** | `True` |
| `ki_airllm_plus_superblock_prefetch_runtime` | "runtime/executor.py coordinates Plan (create_plan), BufferedBlockStore, depth-bounded producer-consumer Prefetcher (queue.Queue(maxsize=depth) daemon worker), and thread-safe OrderedDict BlockCache enforcing both max_blocks and max_size_bytes eviction." | `runtime/executor.py` `L1-L120` | **VERIFIED** | `True` |
| `ki_airllm_plus_superblock_prefetch_runtime` | "runtime/cache.py implements thread-safe OrderedDict LRU block eviction bounded simultaneously by entry count and total byte size, skipping oversized entries cleanly." | `runtime/cache.py` `L1-L95` | **VERIFIED** | `True` |
| `ki_airllm_layerwise_streaming_and_moe_expert_offload` | "AirLLMBaseModel instantiates Hugging Face models on the meta device (init_empty_weights), strips compressed-tensors model-wide ct_decompress_hook before forward, and decompresses packed MXFP4 weight_packed/weight_scale tensors on-GPU per layer after PCIe transfer (4x less PCIe traffic), while capping host pin_memory() at max_pinned_layer_bytes = 2 GiB to prevent 2-in-flight MoE layers from locking ~34 GiB RAM." | `air_llm/airllm/airllm_base.py` `L55-L535` | **VERIFIED** | `True` |
| `ki_airllm_layerwise_streaming_and_moe_expert_offload` | "AirLLMKimiK3 overrides layer_names_dict with expert_prefix (block_sparse_moe.experts) and small resident submodules so only routed sparse MoE experts (~16 of 896 per token, ~1 GB vs ~55 GB full layer) are streamed on demand." | `air_llm/airllm/airllm_kimi_k3.py` `L1-L33` | **VERIFIED** | `True` |
| `ki_self_20260917_04` | "Production AI interfaces must warm-load models and pipeline resources at module initialization rather than inside callback handlers to eliminate multi-second latency spikes and GPU VRAM exhaustion." | `(summary-derived)` | **VERIFIED** | `True` |
| `ki_20261028_headroom_context_optimization` | "The prompt cache hot zone (system prompt) must NEVER be mutated in place; dynamic UUIDs/timestamps must be surfaced via detector-only checks rather than dynamic in-place rewriting to prevent prompt cache prefix busts (PR-A2 invariant)." | `(summary-derived)` | **VERIFIED** | `True` |
| `ki_self_20260922_02` | "Kahn's topological sort dependency graphs are invariant within lifecycle epochs and can be memoized to accelerate multi-plugin cascading operations." | `(unverified claim)` | **UNVERIFIED** | `True` |

## Conflicts & Gaps

1. **[CONFLICT] Startup Warm-Loading vs. Lazy On-Demand Staging:** `ki_self_20260917_04` (verified) mandates warm-loading heavy resources at initialization to avoid per-call latency spikes, which directly conflicts with lazy staging and on-demand sparse streaming in `ki_airllm_plus_superblock_prefetch_runtime` and `ki_airllm_layerwise_streaming_and_moe_expert_offload`. Resolution: keep cold external plugin subprocesses lazy until first route match, then warm-retain active resident workers under the dual-capped LRU budget.
2. **[CONFLICT] Unverified Epoch Memoization & Memory-Map Claims:** `ki_self_20260922_02` (`verified=False` on both claims) proposes memoizing Kahn dependency graphs per lifecycle epoch, and `ki-hf-datasets-arrow-streaming` (`isnad_verified=False`, `0/4` verified claims) describes PyArrow zero-copy mmap and `xxhash` cache fingerprinting without populated claim-level line proofs. Relying on unverified KIs for disk eviction invariants is unsafe without regression benchmarks.
3. **[GAP] High Tag-Search Noise (`prefetch`/`cache`/`streaming`):** 9 of 13 matched KIs cover LLM HTTP/SSE streaming (`ki_20260918_gemini_vercel_streaming`, `ki-bot-hq-upsert-transcript`), transcript buffering (`ki_20260830_kimi_02`, `ki_20260830_grok_05`), or KV-cache mesh sharding (`ki_google_research_scaling_transformer_inference`), rather than local plugin disk-artifact eviction.
4. **[GAP] Missing Staleness / Health-Check Invalidation Rule:** None of the retrieved KIs specify TTL expiration or corrupted-venv invalidation rules for on-disk plugin artifacts.
