---
name: paperless-document-pipeline
description: Ingest, classify, parse, and query documents across the Paperless-NGX ecosystem using hybrid Tantivy lexical and SQLite-Vec semantic search. Do not use for generic file manipulation or non-document SQL databases.
---

# Paperless Document Pipeline: Ingestion, Hybrid Search & RAG Architecture

`paperless-document-pipeline` is the production agent skill for interacting with Paperless-NGX (v3.1.3). It operationalizes the 9-stage document consumption lifecycle, Tantivy BM25 full-text indexing, and `paperless_ai` in-database vector RAG (`sqlite-vec`) into an autonomous, verified agent workflow.

See [CARD.md](CARD.md) for the companion summary card, 5-stage progression matrix, and invariants checklist.
Consult [config.default.yaml](config.default.yaml) for baseline operational parameters and zero-fork configuration.

---

## The 5-Stage Operational Pipeline

```
[1. Intake & Invariants] ──► [2. Ingestion & Pre-Flight] ──► [3. Consumer Polling]
                                                                    │
                                                                    ▼
[5. RAG Verification & Citing] ◄── [4. Hybrid Search & Retrieval] ◄─┘
```

---

## 1. Intake & Invariant Checks

Before submitting documents to Paperless-NGX, validate file readiness and metadata invariants:

1. **Verify Physical File Integrity**:
   - Check file existence, readability, and non-zero byte size.
   - Restrict files to supported extensions (`.pdf`, `.png`, `.jpg`, `.jpeg`, `.tiff`, `.txt`, `.docx`, `.eml`).
2. **Execute Pre-Flight Validator**:
   ```bash
   python scripts/validate_pipeline.py <path-to-document>
   ```
3. **Assert ASN & Metadata Formatting**:
   - If an Archive Serial Number (ASN) is specified, assert that it is a positive integer.
   - Enforce ISO 8601 formatting on date overrides (`YYYY-MM-DD`).

> **Completion criterion**: Target file passes `validate_pipeline.py` with `valid: true` and zero format violations.

---

## 2. Ingestion & Asynchronous Task Dispatch

Submit the validated document to the Paperless-NGX consumption pipeline:

1. **Invoke Ingestion Seam**:
   - Call the `paperless_post_document` tool or execute `scripts/paperless_client.py post`:
     ```bash
     python scripts/paperless_client.py post /path/to/invoice.pdf --title "Invoice #104" --tags "finance" "receipts" --correspondent "Acme Corp"
     ```
2. **Capture Asynchronous Task UUID**:
   - Record the returned Celery task UUID (`task_id`).
   - Instantiate a slotted `ConsumeTaskStatus` object (`scripts/domain_models.py`).

> **Completion criterion**: Celery task UUID returned and initial task status confirmed as `PENDING` or `STARTED`.

---

## 3. Consumer Task Polling & Telemetry

Monitor the background processing pipeline through asynchronous status checks:

1. **Poll Task Queue State**:
   - Query `/api/tasks/` via `paperless_get_task_status` or `scripts/paperless_client.py task <task_id>`.
   - Adhere to polling budgets: query every 2 seconds up to a maximum of 15 attempts (30s timeout).
2. **Inspect Consumption Stages**:
   - Verify that the consumer executes duplicate checking, OCR parsing (`ocrmypdf`), ML classification, and storage writing.
   - On task status `FAILURE`, capture error diagnostic message and halt.
3. **Resolve Ingested Document ID**:
   - Extract the generated document ID upon task status `SUCCESS`.

> **Completion criterion**: Task completes with status `SUCCESS` and assigned document ID is resolved.

---

## 4. Hybrid Search & Document Retrieval

Query the document repository combining Tantivy lexical tokenization with metadata filters:

1. **Execute Search Query**:
   - Call `paperless_search_documents` or run:
     ```bash
     python scripts/paperless_client.py search "tax return 2025" --tags "finance" --limit 5
     ```
2. **Hydrate Slotted Document Records**:
   - Instantiate immutable `PaperlessDocument` entities (`scripts/domain_models.py`) with title, correspondent, tags, and OCR snippets.
3. **Retrieve Full Metadata & Content**:
   - When deeper context is needed, query specific documents via `paperless_get_document(document_id)`.

> **Completion criterion**: Non-empty search results returned and parsed into `PaperlessDocument` value objects.

---

## 5. RAG Verification & Citation Citing

Query the `paperless_ai` vector RAG engine to answer complex domain questions grounded in the archived corpus:

1. **Submit Semantic Query**:
   - Call `paperless_ask_rag` or run:
     ```bash
     python scripts/paperless_client.py ask "What was the total expenditure for Q3?" --doc-ids 12 15
     ```
2. **Execute Local String Salvage (Rule 42)**:
   - On unformatted model or API output, run `salvage_json` in `scripts/paperless_client.py` to strip markdown fences and extract structured fields.
3. **Verify Grounded Citations**:
   - Assert that `RAGQueryResponse` contains at least one primary source document citation ID.
   - Link final agent recommendations directly to cited document IDs.

> **Completion criterion**: RAG answer synthesized with non-empty citation list verified against repository document IDs.

---

## Axis 3 Coaching Rubric & Diagnostic Scorecard

| Dimension | Evaluation Question | Passing Gate |
|---|---|---|
| **Trigger Precision** | Does the skill router distinguish Paperless queries from generic SQL queries? | Action verbs front-loaded with explicit negative boundary in description. |
| **Data Immutability** | Are document and task records protected from in-flight mutation? | Slotted and frozen dataclasses (`@dataclass(slots=True, frozen=True)`). |
| **Configuration** | Can operational endpoints be customized without code changes? | 3-tier zero-fork configuration (`config.default.yaml`) supported. |
| **Error Resilience** | Does the client recover from malformed JSON or OCR outputs? | Local multi-pass string salvage operational before token reprompts. |
| **Execution Safety** | Are all execution scripts safe for automated subprocess execution? | Zero `input()` calls, relocatable paths, explicit UTF-8 streams. |

---

## Anti-Patterns

- **Unbounded Task Polling** — Polling the Celery task queue in an infinite loop without bounded timeout thresholds.
- **Unverified Ingestion** — Assuming a document is ingested and indexed immediately after POST upload without verifying task completion status.
- **Uncited RAG Claims** — Presenting synthesized facts from the RAG chat engine without attributing claims to concrete document IDs.
- **Mutable Document State** — Modifying document attributes in-place instead of creating new immutable slotted value objects.
- **Interactive Script Hang** — Introducing blocking console prompts in bundled client scripts that cause subprocess transports to freeze.
