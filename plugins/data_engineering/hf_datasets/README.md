# domain.hf_datasets (v1.0.0)

Hugging Face Datasets engine plugin providing PyArrow zero-copy memory mapping, lazy streaming iterators, lakehouse format conversion, and automated schema profiling.

## Architecture

| Field | Specification |
|---|---|
| **Plugin Directory** | `plugins/data_engineering/hf_datasets` |
| **Service Key** | `service.hf_datasets` (`HF_DATASETS_SERVICE_KEY`) |
| **Isolation Mode** | `in_process` (with fallback subprocess isolation) |
| **Provides** | `HfDatasetsService` |

## Exported Tools

- `hf_inspect_dataset`: Inspect dataset splits, features, row counts, and metadata without full data pull.
- `hf_stream_sample`: Lazily sample N records from a streaming dataset iterator without downloading full dataset.
- `hf_profile_schema`: Extract detailed column schemas, Arrow types, nullability, and sample values.
- `hf_convert_format`: Convert dataset file between CSV, JSON, Arrow, and Parquet lakehouse formats.

## Python Usage

```python
from harness.kernel.context import ServiceContext
from harness.services.hf_datasets import HF_DATASETS_SERVICE_KEY

# Resolve from IoC context
service = context.require(HF_DATASETS_SERVICE_KEY)
meta = service.inspect_dataset("data/train.jsonl")
print(meta.name, meta.num_rows, meta.features)
```


---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `hf_inspect_dataset` | `(path_or_name, split)` | Inspect dataset splits, features, row counts, and metadata without full data pull |
| `hf_evaluate_storage_strategy` | `(path_or_name, split, auto_stream_threshold_mb)` | Evaluate dataset footprint and select between memory-mapped Arrow and streaming iterators |
| `hf_stream_sample` | `(path_or_name, split, max_samples)` | Lazily sample N records from a streaming dataset iterator without downloading full dataset |
| `hf_profile_schema` | `(path_or_name)` | Extract detailed column schemas, Arrow types, nullability, and sample values |
| `hf_transform_dataset` | `(input_path, output_path, filter_field, filter_op, filter_value, select_columns, batch_size)` | Execute lazy filtering, column projection, and batch transformation |
| `hf_convert_format` | `(input_path, output_path, target_format)` | Convert dataset file between CSV, JSON, Arrow, and Parquet lakehouse formats |
| `hf_commit_to_vault` | `(dataset_name, input_path, split, vault_root)` | Commit dataset catalog and schema provenance to Knowledge Vault (Rule 40) |
