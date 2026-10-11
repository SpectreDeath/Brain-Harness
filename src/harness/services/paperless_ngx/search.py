"""Document search and metadata query operations for Paperless-NGX."""

from __future__ import annotations

import asyncio
import urllib.parse
from typing import TYPE_CHECKING, Any

import structlog

from harness.services.paperless_ngx.models import DocumentSummary, SearchResult, TaskProgress
from harness.services.paperless_ngx.transport import fetch_url_json

if TYPE_CHECKING:
    from harness.services.paperless_ngx.service import DefaultPaperlessNgxService

logger = structlog.get_logger(__name__)


async def execute_search_documents(
    service: DefaultPaperlessNgxService,
    query: str,
    tags: list[str] | None = None,
    correspondent: str | None = None,
    limit: int = 10,
) -> SearchResult:
    """Search documents across remote REST repository or in-memory fallback."""
    if service.is_live_configured:
        try:
            params: dict[str, str] = {"query": query}
            if correspondent:
                params["correspondent__name__iexact"] = correspondent
            url = f"{service.config.base_url.rstrip('/')}/api/documents/?{urllib.parse.urlencode(params)}"
            payload = await asyncio.to_thread(fetch_url_json, url, service.config)
            results = payload.get("results", [])
            matched_docs = [
                DocumentSummary(
                    id=item["id"],
                    title=item.get("title", f"Document {item['id']}"),
                    correspondent=str(item.get("correspondent")) if item.get("correspondent") else None,
                    document_type=str(item.get("document_type")) if item.get("document_type") else None,
                    tags=tuple(str(t) for t in item.get("tags", [])),
                    created=item.get("created", ""),
                    archive_serial_number=item.get("archive_serial_number"),
                    content_snippet=(item.get("content") or "")[:200],
                )
                for item in results[:limit]
            ]
            return SearchResult(
                count=payload.get("count", len(matched_docs)),
                documents=tuple(matched_docs),
            )
        except Exception as e:
            logger.warning("Live Paperless search failed; falling back to in-memory store", error=str(e))

    # In-memory fallback
    query_lower = query.lower()
    matched: list[DocumentSummary] = []
    for doc in service.in_memory_docs.values():
        if query_lower and (query_lower not in doc.title.lower() and query_lower not in doc.content_snippet.lower()):
            continue
        if correspondent and doc.correspondent != correspondent:
            continue
        if tags and not any(t in doc.tags for t in tags):
            continue
        matched.append(doc)

    return SearchResult(count=len(matched), documents=tuple(matched[:limit]))


async def execute_get_document(service: DefaultPaperlessNgxService, document_id: int) -> DocumentSummary:
    """Retrieve document by ID from REST API or in-memory fallback."""
    if service.is_live_configured:
        try:
            url = f"{service.config.base_url.rstrip('/')}/api/documents/{document_id}/"
            item = await asyncio.to_thread(fetch_url_json, url, service.config)
            return DocumentSummary(
                id=item["id"],
                title=item.get("title", f"Document {item['id']}"),
                correspondent=str(item.get("correspondent")) if item.get("correspondent") else None,
                document_type=str(item.get("document_type")) if item.get("document_type") else None,
                tags=tuple(str(t) for t in item.get("tags", [])),
                created=item.get("created", ""),
                archive_serial_number=item.get("archive_serial_number"),
                content_snippet=(item.get("content") or "")[:200],
            )
        except Exception as e:
            logger.warning("Live Paperless get_document failed; checking in-memory store", error=str(e), doc_id=document_id)

    if document_id in service.in_memory_docs:
        return service.in_memory_docs[document_id]
    raise KeyError(f"Document ID {document_id} not found in Paperless repository")


async def execute_get_task_status(service: DefaultPaperlessNgxService, task_id: str) -> TaskProgress:
    """Query task state from REST API or in-memory fallback."""
    if service.is_live_configured:
        try:
            url = f"{service.config.base_url.rstrip('/')}/api/tasks/?task_id={urllib.parse.quote(task_id)}"
            items = await asyncio.to_thread(fetch_url_json, url, service.config)
            if items and isinstance(items, list):
                item = items[0]
                return TaskProgress(
                    task_id=item.get("task_id", task_id),
                    status=item.get("status", "PENDING"),
                    task_type=item.get("type", "document_consumption"),
                    date_created=item.get("date_created", ""),
                    date_done=item.get("date_done"),
                    result=item.get("result"),
                )
        except Exception as e:
            logger.warning("Live Paperless get_task_status failed; checking in-memory store", error=str(e), task_id=task_id)

    if task_id in service.tasks:
        return service.tasks[task_id]
    from datetime import datetime, timezone
    return TaskProgress(task_id=task_id, status="PENDING", date_created=datetime.now(timezone.utc).isoformat())
