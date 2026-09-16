# Skill Summary Card: `paperless-document-pipeline`

```
┌────────────────────────────────────────────────────────┐
│               SKILL SUMMARY CARD                       │
├────────────────────────────────────────────────────────┤
│ SKILL:        paperless-document-pipeline              │
│ Category:    data_engineering / documents / rag        │
│ Invocation:  /paperless-document-pipeline              │
│ Trigger:     "ingest document", "search paperless",    │
│              "query paperless rag", "document ocr"     │
│ Version:     1.0.0                                     │
│ Requires:    "harness.services.paperless_ngx"          │
│ Provides:    "paperless_document_lifecycle"            │
├────────────────────────────────────────────────────────┤
│ Target:      Ingest, parse, classify, and query        │
│              heterogeneous documents across the        │
│              Paperless-NGX enterprise ecosystem.       │
└────────────────────────────────────────────────────────┘
```

---

## The 5-Stage Pipeline Progression

| Stage | Objective | Primary Artifact / Output | Completion Gate |
|---|---|---|---|
| **1. Intake & Invariants** | Validate file existence, MIME type, and ASN format | `scripts/validate_pipeline.py` output | Valid file readiness report |
| **2. Ingestion & Pre-Flight** | Upload document and trigger asynchronous Celery task | `post_document` task UUID | Task status `PENDING` or `STARTED` |
| **3. Consumer Polling** | Monitor background consumption pipeline & OCR | `get_task_status` telemetry | Task status `SUCCESS` |
| **4. Hybrid Search** | Query document metadata and full text via Tantivy | `search_documents` result list | Non-negative result count |
| **5. RAG Citing & Verification** | Ask question and extract cited document references | `ask_rag` structured response | Answer with verified citation IDs |

---

## Invariants & Guardrails

- [ ] **Slotted Domain Models**: Enforce immutable `@dataclass(slots=True, frozen=True)` for all document and task records (Rule 12).
- [ ] **3-Tier Zero-Fork Configuration**: Read defaults from `config.default.yaml` with project override support (Rule 44).
- [ ] **Non-Interactive Execution**: Ensure bundled scripts use UTF-8 streams and zero `input()` calls (Rule 23, Rule 42, Rule 50).
- [ ] **Local String Salvage**: Apply multi-pass salvage to repair malformed model JSON before reprompting (Rule 42).
- [ ] **Verified Citation Lineage**: Every RAG answer must link to concrete document IDs.
