# Paperless-NGX Document Lifecycle Architecture & Dual-Store Ingestion Engine

## Epistemic Introspection & Overview

Paperless-NGX (v3.1.3, 12,135 commits) is a production document management system that transforms physical paper and heterogeneous electronic documents (PDF, TIFF, Office, Images, Emails) into a searchable, structured, and vectorized knowledge archive.

The core architecture decouples continuous background consumption from foreground user interaction via a distributed Celery task queue, Redis broker, and Django REST Framework API.

---

## The 9-Stage Document Consumer Pipeline

At the heart of Paperless-NGX is `documents/consumer.py`, orchestrated by `Consumer.run()`. Every document ingested via filesystem watchers, IMAP mail fetchers (`paperless_mail`), or REST uploads (`/api/documents/post_document/`) passes through 9 deterministic stages:

1. **Pre-Check File Existence & Access**: Validates permissions and file readability in temporary ingestion directories.
2. **Duplicate Detection Check**: Computes MD5 checksums of the raw input file and queries `Document.objects.filter(checksum=checksum)` to reject or archive duplicates without reprocessing.
3. **Archive Serial Number (ASN) Pre-Check**: Verifies target ASN uniqueness against existing records.
4. **Pre-Consume Script Hook**: Executes user-configured hook scripts (`PAPERLESS_PRE_CONSUME_SCRIPT`) with environment parameters (`DOCUMENT_SOURCE_PATH`, `TASK_ID`).
5. **Pluggable Parser Selection & OCR**:
   - Queries `documents.parsers.get_parser_class()` matching file MIME type.
   - Executes OCR pipeline (via `ocrmypdf` or `tika-client` / `gotenberg-client`).
   - Extracts full text content, page boundaries, and thumbnail previews.
6. **Machine Learning & AI Classification**:
   - Runs `documents.classifier.load_classifier()` (Scikit-Learn Naive Bayes model trained on historical corpus).
   - Evaluates auto-matching rules for Correspondents, Document Types, Storage Paths, and Tags.
   - Falls back to `paperless_ai.ai_classifier.AIClassifier` when LLM structured classification is enabled.
7. **Unique Filename & Storage Path Generation**:
   - Formats destination paths using Jinja2 / placeholder formatting templates (`{correspondent}/{created_year}/{title}`).
   - Writes document file to managed storage directory under atomic file locking (`FileLock`).
8. **Post-Consume Script Hook**:
   - Invokes `PAPERLESS_POST_CONSUME_SCRIPT` passing the newly created document ID.
9. **Workflow Automation & Index Enqueue**:
   - Evaluates `documents.workflows` triggers (`WorkflowTrigger` $\rightarrow$ `WorkflowAction`).
   - Enqueues Tantivy lexical index update and SQLite-Vec vector store chunking tasks.

---

## Concurrency Guarantees & File Locking Invariants

- **Storage Invariants**: Multi-worker Celery consumers write to shared media roots safely through `filelock.FileLock` instances targeting `.lock` files per document ID.
- **Index Concurrency**: Updating Tantivy and SQLite-Vec indices uses `filelock.ReadWriteLock` to allow parallel readers while serializing batch updates.
- **Transaction Rollback**: Failures during parsing or classification trigger `Consumer._fail()`, cleaning up temporary working directories and recording diagnostic error messages to `PaperlessTask`.

---

## Telemetry & WebSocket Progress Seam

- **Task Tracking**: Every Celery task registers a `PaperlessTask` model with states: `PENDING`, `STARTED`, `SUCCESS`, `FAILURE`.
- **Real-Time Stream**: The ASGI layer mounts `StatusConsumer` at `ws/status/`, broadcasting JSON progress updates to the Angular frontend or external agent bridges.
