# plugin.paperless_ngx (v1.0.0)

Paperless-NGX document ingestion, hybrid search, and RAG integration bridge

---

## Overview & Metadata

| Property | Value |
|---|---|
| Plugin Directory | `plugins/data_engineering/paperless_ngx` |
| Category | `data_engineering` |
| Isolation Mode | `subprocess` |
| Services Provided | `data_engineering.paperless_ngx` |
| Dependencies Required | None |

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `paperless_ingest_and_await` | `(file_path, title, tags, correspondent, document_type, timeout_seconds)` | Upload document, await background consumption, and return verified IngestionReceipt with hydrated document metadata |
| `paperless_ask_grounded_rag` | `(query, document_ids)` | Query paperless_ai RAG chat endpoint and return answer with fully hydrated cited document records for provenance verification |
| `paperless_search_documents` | `(query, tags, correspondent, limit)` | Search documents across Paperless-NGX using Tantivy full-text search with metadata filters |
| `paperless_get_document` | `(document_id)` | Retrieve detailed metadata and OCR content snippet for a document ID |
| `paperless_post_document` | `(file_path, title, tags, correspondent, document_type)` | Upload a document file to Paperless-NGX for background asynchronous consumption |
| `paperless_ask_rag` | `(query, document_ids)` | Query paperless_ai RAG chat endpoint to answer questions with document citations |
| `paperless_get_task_status` | `(task_id)` | Check status, progress, and result of an asynchronous consumption task |

---

## Key Modules & AST Symbols

### Module [main.py](main.py)

Paperless-NGX document ingestion, hybrid search, and RAG integration bridge

#### Classes

- `class PaperlessNgxPlugin` — Harness Plugin implementing Paperless-NGX integration.
  - `def __init__(config)` — Executes the operation.
  - `def provides()` — Executes the operation.
  - `def on_load(context)` — Executes the operation.
  - `def on_unload(context)` — Executes the operation.
  - `def search_documents(query, tags, correspondent, limit)` — Search documents across Paperless-NGX repository.
  - `def get_document(document_id)` — Retrieve details and metadata for a specific document ID.
  - `def post_document(file_path, title, tags, correspondent, document_type)` — Upload and enqueue a document for consumption.
  - `def ask_rag(query, document_ids)` — Query paperless_ai RAG chat endpoint with document citations.
  - `def get_task_status(task_id)` — Inspect the current execution state of an asynchronous consumption task.
  - `def ingest_and_await_document(file_path, title, tags, correspondent, document_type, timeout_seconds, poll_interval_seconds)` — Atomic ingestion seam: uploads document, polls Celery task, and returns hydrated IngestionReceipt.
  - `def ask_grounded_rag(query, document_ids)` — High-leverage RAG query seam: answers question and hydrates cited source documents (Rule 41).

---

## Quickstart & Usage

```python
from harness.kernel.context import ServiceContext
from plugins.data_engineering.paperless_ngx.main import plugin

context = ServiceContext()
# Load plugin into service context
plugin.on_load(context)
```

---

## Architecture & Diátaxis Classification

- Diátaxis Quadrant: Reference (Track B) & How-To Guides
- Isolation: `subprocess` execution sandbox
- Invariants: Slotted dataclass architecture (Rule 12), transactional context bounds (Rule 8), and zero-fork YAML configuration (Rule 44).
