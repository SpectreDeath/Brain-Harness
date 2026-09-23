---
name: hf-datasets-engineer
description: Architect, load, stream, slice, and transform high-scale datasets using Hugging Face Datasets with Arrow zero-copy memory mapping, lazy streaming iterators, and multi-format lakehouse pipelines. Do not use for raw SQL database administration, low-level socket programming, or model weight training.
---

# Hugging Face Datasets Engineer

`hf-datasets-engineer` is the authoritative agent skill for orchestrating datasets in Brain Harness. It leverages Apache Arrow zero-copy memory-mapped tables, lazy generator streams (`IterableDataset`), deterministic transformation caching (`xxhash`), and multi-format lakehouse converters (Parquet, Arrow, JSON, CSV, Lance, Iceberg) to handle terabyte-scale data pipelines without physical memory exhaustion.

See [CARD.md](CARD.md) for the companion summary card, stage progression table, and invariants checklist.
Consult [config.default.yaml](config.default.yaml) for baseline operational budgets and timeout thresholds.

---

## The 5-Stage Shu-Ha-Ri Pipeline Progression

```
[1. Manifest & Schema Discovery]
              │
              ▼
[2. Storage Strategy Selection (Arrow vs. Streaming)]
              │
              ▼
[3. Zero-Copy Execution & Lazy Transformation]
              │
              ▼
[4. Lakehouse Columnar Serialization (Parquet/Arrow)]
              │
              ▼
[5. Deterministic xxhash Verification & Vault Commit]
```

---

## 1. Manifest & Schema Discovery

Probe remote hub endpoints or local dataset files to determine schema and partition boundaries without pulling raw payloads:

1. **Invoke Inspection**:
   - Inspect dataset formats, splits (`train`, `test`, `validation`), and total rows using `hf_inspect_dataset(path_or_name)`.
   - If payload size $> 500\text{ MB}$ or source is an unbounded web stream, flag for streaming execution mode.
2. **Profile Column Types**:
   - Run `hf_profile_schema(path_or_name)` to determine Arrow data types (`int64`, `double`, `string`, `struct`, `list`).

> **Completion criterion**: Target dataset schema mapped, split boundaries resolved, and physical footprint evaluated.

---

## 2. Storage Strategy Selection

Select between memory-mapped tabular execution and lazy streaming iterators based on data topology:

1. **Strategy A: Memory-Mapped Arrow (`Dataset`)**:
   - Select when data fits on local NVMe storage and random access indexing or multi-pass training is required.
   - Leverages zero-copy OS virtual memory paging via PyArrow.
2. **Strategy B: Lazy Generator Streaming (`IterableDataset`)**:
   - Select when data exceeds physical disk capacity, comes from remote HTTP streams, or requires real-time shard interleaving.
   - Consumes $O(1)$ memory by evaluating items row-by-row or in bounded batches.

> **Completion criterion**: Storage paradigm chosen and operational batch size configured.

---

## 3. Zero-Copy Execution & Lazy Transformation

Apply high-throughput transformations with bounded memory utilization:

1. **Lazy Sampling**:
   - Test transformation logic on bounded records using `hf_stream_sample(path_or_name, max_samples=100)`.
2. **Batched Mapping & Projection**:
   - Execute vectorized `.map()` operations with batch sizes matching operational budgets (`config.default.yaml`).
   - Filter rows and prune unnecessary columns early to minimize Arrow buffer allocations.

> **Completion criterion**: Sample batch processed and transformation pipeline verified.

---

## 4. Lakehouse Columnar Serialization

Persist processed records into modern columnar formats:

1. **Format Conversion**:
   - Invoke `hf_convert_format(input_path, output_path, target_format="parquet")` to serialize JSON/CSV inputs into optimized columnar Parquet or Arrow tables.
2. **Partitioning & Sharding**:
   - For multi-worker distributed training, partition output into balanced shards with zero data skew.

> **Completion criterion**: Columnar dataset serialized to target path with valid header and metadata.

---

## 5. Deterministic xxhash Verification & Vault Commit

Verify transformation integrity and record epistemic provenance:

1. **Cache Fingerprinting**:
   - Compute transformation cache fingerprint to guarantee idempotency across re-runs.
2. **Knowledge Vault Logging**:
   - Record dataset metadata and transformation hashes to persistent state.

> **Completion criterion**: 100% verification checks passed; transform execution logged with valid cache fingerprint.

---

## In-File Reference & Vocabulary

- **Arrow Zero-Copy**: Accessing memory-mapped binary tabular data buffers directly without deserializing into Python object representations.
- **IterableDataset**: Generator-backed lazy dataset stream evaluated on-demand with minimal memory footprint.
- **Cache Fingerprint**: Deterministic xxhash identifying parent state, transform function bytecode, and execution arguments.

---

## Anti-Patterns

- **Eager Memory Blowout** — Calling `list(iterable_dataset)` or `to_pandas()` on multi-gigabyte datasets, causing out-of-memory kernel kills.
- **Unsharded Stream Thrashing** — Deploying multi-worker agent swarms on a single streaming dataset without calling `.shard(num_shards, rank)`.
- **Blind Cache Invalidation** — Using non-deterministic lambdas or timestamped closures inside `.map()` that continuously invalidate xxhash cache fingerprints.
- **Unchecked String Casting** — Treating numerical or biological features as untyped strings instead of declaring typed Arrow/Features schemas.
- **Monolithic Ingestion Bottlenecks** — Downloading full remote multi-gigabyte archives before inspecting schema or testing sample batches.
