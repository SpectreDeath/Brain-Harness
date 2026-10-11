"""Paperless-NGX Integration Service — modular subpackage facade."""

from __future__ import annotations

from harness.services.paperless_ngx.ingestion import (
    execute_ingest_and_await_document,
    execute_post_document,
)
from harness.services.paperless_ngx.models import (
    DocumentSummary,
    GroundedRAGAnswer,
    IngestionReceipt,
    PaperlessConfig,
    RAGAnswer,
    SearchResult,
    TaskProgress,
)
from harness.services.paperless_ngx.protocols import (
    PAPERLESS_NGX_SERVICE_KEY,
    PaperlessNgxService,
)
from harness.services.paperless_ngx.rag import execute_ask_grounded_rag, execute_ask_rag
from harness.services.paperless_ngx.resolvers import resolve_paperless_ngx_service
from harness.services.paperless_ngx.search import (
    execute_get_document,
    execute_get_task_status,
    execute_search_documents,
)
from harness.services.paperless_ngx.service import DefaultPaperlessNgxService
from harness.services.paperless_ngx.transport import fetch_url_json, get_auth_headers

__all__ = [
    "DefaultPaperlessNgxService",
    "DocumentSummary",
    "GroundedRAGAnswer",
    "IngestionReceipt",
    "PAPERLESS_NGX_SERVICE_KEY",
    "PaperlessConfig",
    "PaperlessNgxService",
    "RAGAnswer",
    "SearchResult",
    "TaskProgress",
    "execute_ask_grounded_rag",
    "execute_ask_rag",
    "execute_get_document",
    "execute_get_task_status",
    "execute_ingest_and_await_document",
    "execute_post_document",
    "execute_search_documents",
    "fetch_url_json",
    "get_auth_headers",
    "resolve_paperless_ngx_service",
]
