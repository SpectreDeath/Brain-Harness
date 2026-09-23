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
