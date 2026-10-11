"""Protocols and typed ServiceKey definitions for Paperless-NGX."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from harness.kernel.context import ServiceKey
from harness.services.paperless_ngx.models import (
    DocumentSummary,
    GroundedRAGAnswer,
    IngestionReceipt,
    RAGAnswer,
    SearchResult,
    TaskProgress,
)


@runtime_checkable
class PaperlessNgxService(Protocol):
    """Authoritative service protocol for Paperless-NGX document management."""

    async def search_documents(
        self,
        query: str,
        tags: list[str] | None = None,
        correspondent: str | None = None,
        limit: int = 10,
    ) -> SearchResult:
        """Search documents using Tantivy full-text search with metadata filters."""
        ...

    async def get_document(self, document_id: int) -> DocumentSummary:
        """Retrieve full details and metadata for a specific document."""
        ...

    async def post_document(
        self,
        file_path: str,
        title: str | None = None,
        tags: list[str] | None = None,
        correspondent: str | None = None,
        document_type: str | None = None,
    ) -> TaskProgress:
        """Upload and enqueue a document for consumption."""
        ...

    async def ask_rag(
        self,
        query: str,
        document_ids: list[int] | None = None,
    ) -> RAGAnswer:
        """Query the paperless_ai RAG chat endpoint to answer questions with citations."""
        ...

    async def get_task_status(self, task_id: str) -> TaskProgress:
        """Inspect the current execution state of an asynchronous consumption task."""
        ...

    async def ingest_and_await_document(
        self,
        file_path: str,
        title: str | None = None,
        tags: list[str] | None = None,
        correspondent: str | None = None,
        document_type: str | None = None,
        timeout_seconds: float = 30.0,
        poll_interval_seconds: float = 1.0,
    ) -> IngestionReceipt:
        """Atomic ingestion seam: uploads document, polls Celery task, and returns hydrated IngestionReceipt."""
        ...

    async def ask_grounded_rag(
        self,
        query: str,
        document_ids: list[int] | None = None,
    ) -> GroundedRAGAnswer:
        """High-leverage RAG query seam: answers question and hydrates cited source documents (Rule 41)."""
        ...


PAPERLESS_NGX_SERVICE_KEY = ServiceKey[PaperlessNgxService](
    "data_engineering.paperless_ngx"
)
