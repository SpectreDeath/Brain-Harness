# AirLLM++ Super-Block Sequential Packing, Offset-Indexed Plans & Prefetch Runtime

## Provenance
- **Upstream Repository**: `https://github.com/howardleegeek/airllm-plus` (`2a9f04035d80abf43fe7579673d08947c49080f1`)
- **Surfaced By**: Ontology-Spider (`runtime` hub, `bench -> runtime` dependency) + REA `plugin.rea_managed_runtime` on `executor.pyc`, `prefetch.pyc`, `pack_blocks.pyc`

## Architectural Pattern
1. **Super-Block Packing (`pack/pack_blocks.py`, `runtime/plan.py`, `runtime/store.py`)**:
   - Consolidates fragmented `layer_*` / `model.*` shards into contiguous super-blocks (`layers_per_block=4`), writing exact `(layer, file, offset, bytes)` manifests to `index.json` so disk I/O runs as large sequential reads or $O(1)$ `seek`/`read` slices (`BlockStore.read_block_range`).
2. **Depth-Pipelined Prefetching (`runtime/prefetch.py`, `runtime/executor.py`)**:
   - `Prefetcher` decouples disk loads onto a daemon worker via bounded `submit_queue` / `result_queue` (`depth >= 2`), overlapping block `N+1..N+depth` loading with compute on block `N`.
3. **Dual-Bounded LRU Residency (`runtime/cache.py`)**:
   - `BlockCache` uses a lock-guarded `OrderedDict` evicting on either `max_blocks` or `max_size_bytes` without letting oversized blocks pollute the cache.
