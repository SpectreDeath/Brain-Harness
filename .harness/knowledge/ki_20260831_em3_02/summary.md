# Zero-Copy Polyglot Memory Substrate via PyArrow IPC Streams

## Context
Multi-surface agent architectures often transfer data between numerical solvers (NumPy, PyTorch), columnar databases (DuckDB, SQLite), and high-performance native engines (Rust, Polars). Standard string/JSON serialization incurs heavy CPU overhead, precision loss on floating point values, and high memory churn.

## Distilled Learning
Adopt an Arrow-backed shared memory substrate:
1. **Polymorphic Ingestion**:
   - Allow tables to register from `pa.Table`, `pa.RecordBatch`, pandas DataFrames, lists of dicts, or objects exposing `.to_arrow()`.
2. **IPC Stream Serialization**:
   - Use `pyarrow.BufferOutputStream` and `pyarrow.ipc.new_stream` to serialize tables into zero-copy byte buffers for process boundaries.
   - Deserialize with `pyarrow.ipc.open_stream(pa.BufferReader(payload)).read_all()`.
3. **Graceful Fallback Path**:
   - If `pyarrow` is unavailable or destination surfaces are non-columnar (e.g. Prolog, Datalog), convert to standard Python dictionaries via `table.to_pydict()`.

## Triggers & Seam Choices
- **Trigger**: Inter-plugin dataset exchange, monorepo monads, or high-throughput batch transformations.
- **Seam Choice**: Register an `ArrowSubstrateService` into the kernel IoC container (`ARROW_SUBSTRATE_KEY`) accessible by all tool and storage plugins.
