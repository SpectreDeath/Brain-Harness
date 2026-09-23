# PyArrow Zero-Copy Execution, Streaming Iterators & Deterministic Caching

## Epistemic Introspection & Overview

Hugging Face `datasets` (v5.0.2.dev0) is the industry-standard data access, streaming, and lakehouse transformation library for modern machine learning. Rather than eagerly loading tabular data into Python dictionaries or Pandas dataframes, it decouples the physical storage representation from high-level Python access through Apache Arrow C++ memory mapping.

The system is architected around two complementary execution engines:
1. **The In-Memory / Memory-Mapped Arrow Engine (`Dataset`)**: Operates over immutable Arrow RecordBatches and Tables memory-mapped from disk. Slicing rows or projecting columns takes sub-millisecond $O(1)$ time with zero RAM allocation.
2. **The Lazy Generator Streaming Engine (`IterableDataset`)**: Evaluates unbounded or remote datasets row-by-row or batch-by-batch via composable Python generator streams, bypassing local disk storage entirely.

---

## The Dual Execution Engines

### 1. Arrow Table Memory Mapping (`src/datasets/arrow_dataset.py`)
- `Dataset(DatasetInfoMixin, IndexableMixin, TensorflowDatasetMixin)` encapsulates a `pyarrow.Table`.
- File buffers (`.arrow` or `.parquet`) are memory-mapped (`pa.memory_map`). The operating system kernel pages chunks into physical RAM on-demand.
- Transformations (`.map()`, `.filter()`, `.select()`) operate in vectorized batches (`batch_size=1000`) and stream new columns directly into memory-mapped temporary Arrow tables.

### 2. Lazy Generator Streaming (`src/datasets/iterable_dataset.py`)
- `IterableDataset` encapsulates a `_BaseExamplesIterable` generator pipeline.
- Supports sharded parallel downloading, dynamic chunk prefetching, and windowed reservoir shuffling (`.shuffle(buffer_size=10000)`).
- `interleave_datasets([d1, d2], probabilities=[0.8, 0.2])` interleaves multiple heterogeneous streams without materializing either in memory.

---

## Deterministic Cache Fingerprinting (`src/datasets/fingerprint.py`)

- Every dataset state possesses an immutable SHA-like cache fingerprint computed by `Hasher`.
- The fingerprint hashes:
  1. The parent dataset's fingerprint.
  2. The transformation function's bytecode and closure variables (via `dill`).
  3. Transformation parameters (`batch_size`, `remove_columns`).
- If an operation with matching fingerprint was previously computed, `datasets` instantly reloads the cached Arrow table from disk without re-executing model inferences or string parsers.

---

## Packaged Format Catalog & Scientific Features

Hugging Face `datasets` provides 30+ built-in packaged modules:
- **Columnar & Lakehouse**: Parquet, Arrow, Lance, Iceberg, Vortex, DuckDB/SQL, Spark.
- **Multimodal**: AudioFolder, ImageFolder, VideoFolder, MeshFolder, PDFFolder, NIfTIFolder.
- **Biological Structures**: `BioStructure` (`mmcif.py`, `pdb.py`) for macromolecular protein crystallography, and `BioSequence` (`fasta.py`, `fastq.py`, `genbank.py`) for genomic sequencing.

---

## Core Invariants & Anti-Patterns

1. **Avoid Eager Materialization on Large Corpora**: Calling `list(iterable_dataset)` or `dataset.to_pandas()` on multi-gigabyte datasets blows out physical RAM. Always use streaming generator iteration or memory-mapped batched Arrow slices.
2. **Deterministic Hash Invariance**: Dynamic non-reproducible lambdas (e.g. `lambda x: x + time.time()`) break cache fingerprint stability and force redundant table writes.
3. **Multi-Node Sharding Invariant**: In distributed swarms or worker pools, always shard streaming datasets by rank (`dataset.shard(num_shards=N, index=rank)`) to guarantee mutually exclusive non-overlapping partitions.
