"""Paperless-NGX Data Engineering Plugin for Brain Harness.

Provides document ingestion, full-text search, OCR retrieval, and
RAG chat integration with the Paperless-NGX ecosystem.
"""

from __future__ import annotations

import asyncio
import concurrent.futures
from typing import Any

import structlog

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.paperless_ngx import (
    PAPERLESS_NGX_SERVICE_KEY,
    DefaultPaperlessNgxService,
    DocumentSummary,
    GroundedRAGAnswer,
    IngestionReceipt,
    PaperlessConfig,
    PaperlessNgxService,
    RAGAnswer,
    SearchResult,
    TaskProgress,
)

logger = structlog.get_logger(__name__)


def _safe_run(coro: Any) -> Any:
    """Safely execute an async coroutine even if called from an active event loop."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(asyncio.run, coro).result()
    else:
        return asyncio.run(coro)


class PaperlessNgxPlugin(HarnessPlugin, PaperlessNgxService):
    """Harness Plugin implementing Paperless-NGX integration."""

    name = "plugin.paperless_ngx"
    version = "1.0.0"
    description = (
        "Paperless-NGX document ingestion, hybrid search, and RAG integration bridge"
    )
    trusted = True

    def __init__(self, config: PaperlessConfig | None = None) -> None:
        super().__init__()
        self._engine = DefaultPaperlessNgxService(config or PaperlessConfig())

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [PAPERLESS_NGX_SERVICE_KEY]

    def on_load(self, context: ServiceContext) -> None:
        context.provide(PAPERLESS_NGX_SERVICE_KEY, self, provider=self.name)
        logger.info("PaperlessNgxPlugin registered into IoC container")

    def on_unload(self, context: ServiceContext) -> None:
        logger.info("PaperlessNgxPlugin unloaded")

    async def search_documents(
        self,
        query: str,
        tags: list[str] | None = None,
        correspondent: str | None = None,
        limit: int = 10,
    ) -> SearchResult:
        """Search documents across Paperless-NGX repository."""
        return await self._engine.search_documents(
            query=query,
            tags=tags,
            correspondent=correspondent,
            limit=limit,
        )

    async def get_document(self, document_id: int) -> DocumentSummary:
        """Retrieve details and metadata for a specific document ID."""
        return await self._engine.get_document(document_id=document_id)

    async def post_document(
        self,
        file_path: str,
        title: str | None = None,
        tags: list[str] | None = None,
        correspondent: str | None = None,
        document_type: str | None = None,
    ) -> TaskProgress:
        """Upload and enqueue a document for consumption."""
        return await self._engine.post_document(
            file_path=file_path,
            title=title,
            tags=tags,
            correspondent=correspondent,
            document_type=document_type,
        )

    async def ask_rag(
        self,
        query: str,
        document_ids: list[int] | None = None,
    ) -> RAGAnswer:
        """Query paperless_ai RAG chat endpoint with document citations."""
        return await self._engine.ask_rag(query=query, document_ids=document_ids)

    async def get_task_status(self, task_id: str) -> TaskProgress:
        """Inspect the current execution state of an asynchronous consumption task."""
        return await self._engine.get_task_status(task_id=task_id)

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
        return await self._engine.ingest_and_await_document(
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
        return await self._engine.ask_grounded_rag(
            query=query, document_ids=document_ids
        )


# Module-level tool wrappers for direct tool dispatch
def paperless_ingest_and_await(
    file_path: str,
    title: str | None = None,
    tags: list[str] | None = None,
    correspondent: str | None = None,
    document_type: str | None = None,
    timeout_seconds: float = 30.0,
) -> dict[str, Any]:
    """Upload document, await background consumption, and return verified IngestionReceipt."""
    receipt: IngestionReceipt = _safe_run(
        plugin.ingest_and_await_document(
            file_path=file_path,
            title=title,
            tags=tags,
            correspondent=correspondent,
            document_type=document_type,
            timeout_seconds=timeout_seconds,
        )
    )
    return {
        "status": "ok",
        "document_id": receipt.document_id,
        "task_id": receipt.task_id,
        "task_status": receipt.status,
        "elapsed_seconds": receipt.elapsed_seconds,
        "document": {
            "id": receipt.document.id,
            "title": receipt.document.title,
            "correspondent": receipt.document.correspondent,
            "document_type": receipt.document.document_type,
            "tags": list(receipt.document.tags),
            "created": receipt.document.created,
            "content_snippet": receipt.document.content_snippet,
        },
    }


def paperless_ask_grounded_rag(
    query: str,
    document_ids: list[int] | None = None,
) -> dict[str, Any]:
    """Query RAG chat endpoint and return answer with fully hydrated cited document records."""
    ans: GroundedRAGAnswer = _safe_run(
        plugin.ask_grounded_rag(query=query, document_ids=document_ids)
    )
    return {
        "status": "ok",
        "answer": ans.answer,
        "citations": list(ans.citations),
        "confidence": ans.confidence,
        "cited_documents": [
            {
                "id": doc.id,
                "title": doc.title,
                "correspondent": doc.correspondent,
                "document_type": doc.document_type,
                "tags": list(doc.tags),
                "created": doc.created,
                "content_snippet": doc.content_snippet,
            }
            for doc in ans.cited_documents
        ],
    }


def paperless_search_documents(
    query: str,
    tags: list[str] | None = None,
    correspondent: str | None = None,
    limit: int = 10,
) -> dict[str, Any]:
    """Search documents across Paperless-NGX repository."""
    result: SearchResult = _safe_run(
        plugin.search_documents(
            query=query, tags=tags, correspondent=correspondent, limit=limit
        )
    )
    return {
        "status": "ok",
        "count": result.count,
        "documents": [
            {
                "id": doc.id,
                "title": doc.title,
                "correspondent": doc.correspondent,
                "document_type": doc.document_type,
                "tags": list(doc.tags),
                "created": doc.created,
                "content_snippet": doc.content_snippet,
            }
            for doc in result.documents
        ],
    }


def paperless_get_document(document_id: int) -> dict[str, Any]:
    """Retrieve details and metadata for a document ID."""
    try:
        doc: DocumentSummary = _safe_run(plugin.get_document(document_id=document_id))
        return {
            "status": "ok",
            "document": {
                "id": doc.id,
                "title": doc.title,
                "correspondent": doc.correspondent,
                "document_type": doc.document_type,
                "tags": list(doc.tags),
                "created": doc.created,
                "content_snippet": doc.content_snippet,
            },
        }
    except KeyError as e:
        return {"status": "error", "error": str(e)}


def paperless_post_document(
    file_path: str,
    title: str | None = None,
    tags: list[str] | None = None,
    correspondent: str | None = None,
    document_type: str | None = None,
) -> dict[str, Any]:
    """Upload and enqueue a document for consumption."""
    task: TaskProgress = _safe_run(
        plugin.post_document(
            file_path=file_path,
            title=title,
            tags=tags,
            correspondent=correspondent,
            document_type=document_type,
        )
    )
    return {
        "status": "ok",
        "task_id": task.task_id,
        "task_status": task.status,
        "result": task.result,
    }


def paperless_ask_rag(
    query: str,
    document_ids: list[int] | None = None,
) -> dict[str, Any]:
    """Query paperless_ai RAG chat endpoint with citations."""
    ans: RAGAnswer = _safe_run(plugin.ask_rag(query=query, document_ids=document_ids))
    return {
        "status": "ok",
        "answer": ans.answer,
        "citations": list(ans.citations),
    }


def paperless_get_task_status(task_id: str) -> dict[str, Any]:
    """Inspect the current execution state of an asynchronous consumption task."""
    task: TaskProgress = _safe_run(plugin.get_task_status(task_id=task_id))
    return {
        "status": "ok",
        "task_id": task.task_id,
        "task_status": task.status,
        "result": task.result,
        "date_done": task.date_done,
    }


# Export authoritative module-level singleton (Rule 45)
plugin = PaperlessNgxPlugin()
