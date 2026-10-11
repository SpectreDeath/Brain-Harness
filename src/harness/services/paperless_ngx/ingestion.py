"""Document ingestion and Celery task polling operations."""

from __future__ import annotations

import asyncio
import re
import time
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from harness.services.paperless_ngx.models import (
    DocumentSummary,
    IngestionReceipt,
    TaskProgress,
)

if TYPE_CHECKING:
    from harness.services.paperless_ngx.service import DefaultPaperlessNgxService


async def execute_post_document(
    service: DefaultPaperlessNgxService,
    file_path: str,
    title: str | None = None,
    tags: list[str] | None = None,
    correspondent: str | None = None,
    document_type: str | None = None,
) -> TaskProgress:
    """Simulate document posting or upload to remote REST API."""
    task_id = str(uuid.uuid4())
    doc_id = len(service.in_memory_docs) + 1
    doc_title = title or f"Document {doc_id}"

    summary = DocumentSummary(
        id=doc_id,
        title=doc_title,
        correspondent=correspondent,
        document_type=document_type,
        tags=tuple(tags or []),
        created=datetime.now(timezone.utc).isoformat(),
        content_snippet=f"Ingested from {file_path}",
    )
    service.in_memory_docs[doc_id] = summary

    task = TaskProgress(
        task_id=task_id,
        status="SUCCESS",
        task_type="document_consumption",
        date_created=datetime.now(timezone.utc).isoformat(),
        date_done=datetime.now(timezone.utc).isoformat(),
        result=f"Document {doc_id} created successfully",
    )
    service.tasks[task_id] = task
    return task


async def execute_ingest_and_await_document(
    service: DefaultPaperlessNgxService,
    file_path: str,
    title: str | None = None,
    tags: list[str] | None = None,
    correspondent: str | None = None,
    document_type: str | None = None,
    timeout_seconds: float = 30.0,
    poll_interval_seconds: float = 1.0,
) -> IngestionReceipt:
    """Atomic ingestion seam: uploads document, polls Celery task, and returns hydrated IngestionReceipt."""
    start_time = time.time()
    task = await service.post_document(
        file_path=file_path,
        title=title,
        tags=tags,
        correspondent=correspondent,
        document_type=document_type,
    )

    deadline = start_time + timeout_seconds
    resolved_doc_id: int | None = None
    last_status = task.status

    while time.time() < deadline:
        current_task = await service.get_task_status(task.task_id)
        last_status = current_task.status
        if current_task.status == "SUCCESS":
            if current_task.result:
                match = re.search(r"Document\s+(\d+)", current_task.result, re.IGNORECASE)
                if match:
                    resolved_doc_id = int(match.group(1))
            if resolved_doc_id is None:
                resolved_doc_id = len(service.in_memory_docs)
            break
        elif current_task.status == "FAILURE":
            raise RuntimeError(f"Consumption task {task.task_id} failed: {current_task.result or 'Unknown error'}")

        await asyncio.sleep(min(poll_interval_seconds, max(0.1, deadline - time.time())))

    if resolved_doc_id is None or last_status != "SUCCESS":
        raise TimeoutError(f"Ingestion timed out after {timeout_seconds}s waiting for task {task.task_id} (status={last_status})")

    doc = await service.get_document(resolved_doc_id)
    elapsed = time.time() - start_time
    return IngestionReceipt(
        document_id=resolved_doc_id,
        document=doc,
        task_id=task.task_id,
        status="SUCCESS",
        elapsed_seconds=round(elapsed, 2),
        date_created=datetime.now(timezone.utc).isoformat(),
    )
