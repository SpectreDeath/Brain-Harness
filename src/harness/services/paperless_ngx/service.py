"""Paperless-NGX reference service implementation coordinating decomposed operations."""

from __future__ import annotations

import os
from typing import Any

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
from harness.services.paperless_ngx.rag import execute_ask_grounded_rag, execute_ask_rag
from harness.services.paperless_ngx.search import (
    execute_get_document,
    execute_get_task_status,
    execute_search_documents,
)


class DefaultPaperlessNgxService:
    """Reference implementation of PaperlessNgxService with fallback mock capabilities and REST transport."""

    def __init__(self, config: PaperlessConfig | None = None) -> None:
        self._config = config or PaperlessConfig()
        self._in_memory_docs: dict[int, DocumentSummary] = {}
        self._tasks: dict[str, TaskProgress] = {}

    @property
    def config(self) -> PaperlessConfig:
        return self._config

    @property
    def in_memory_docs(self) -> dict[int, DocumentSummary]:
        return self._in_memory_docs

    @property
    def tasks(self) -> dict[str, TaskProgress]:
        return self._tasks

    @property
    def is_live_configured(self) -> bool:
        """Return True if an API token is provided for live REST communication."""
        token = self._config.api_token or os.environ.get("PAPERLESS_API_TOKEN")
        return bool(token)

    async def search_documents(
        self,
        query: str,
        tags: list[str] | None = None,
        correspondent: str | None = None,
        limit: int = 10,
    ) -> SearchResult:
        """Search documents across remote REST repository or in-memory fallback."""
        return await execute_search_documents(self, query, tags=tags, correspondent=correspondent, limit=limit)

    async def get_document(self, document_id: int) -> DocumentSummary:
        """Retrieve document by ID from REST API or in-memory fallback."""
        return await execute_get_document(self, document_id)

    async def post_document(
        self,
        file_path: str,
        title: str | None = None,
        tags: list[str] | None = None,
        correspondent: str | None = None,
        document_type: str | None = None,
    ) -> TaskProgress:
        """Simulate document posting or upload to remote REST API."""
        return await execute_post_document(self, file_path, title=title, tags=tags, correspondent=correspondent, document_type=document_type)

    async def ask_rag(
        self,
        query: str,
        document_ids: list[int] | None = None,
    ) -> RAGAnswer:
        """Simulate paperless_ai RAG chat response with citations."""
        return await execute_ask_rag(self, query, document_ids=document_ids)

    async def get_task_status(self, task_id: str) -> TaskProgress:
        """Query task state from REST API or in-memory fallback."""
        return await execute_get_task_status(self, task_id)

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
        return await execute_ingest_and_await_document(
            self,
            file_path=file_path,
            title=title,
            tags=tags,
            correspondent=correspondent,
            document_type=document_type,
            timeout_seconds=timeout_seconds,
            poll_interval_seconds=poll_interval_seconds,
        )

    async def ask_grounded_rag(
        self,
        query: str,
        document_ids: list[int] | None = None,
    ) -> GroundedRAGAnswer:
        """High-leverage RAG query seam: answers question and hydrates cited source documents (Rule 41)."""
        return await execute_ask_grounded_rag(self, query, document_ids=document_ids)
