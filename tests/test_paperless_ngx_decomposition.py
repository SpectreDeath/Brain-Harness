"""Contract verification tests for Cycle 51: Paperless-NGX Integration Service decomposition.

Verifies:
- Direct imports from decomposed submodules and package facade re-exports
- Protocol conformance and typed ServiceKey registration
- Slotted and frozen immutability assertions (Rule 12 & 43)
- Single-seam resolver behavior with and without context (Rule 58)
- Grounded RAG document hydration seam and ingestion flow
"""

from __future__ import annotations

import pytest

from harness.kernel.context import ServiceContext
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
    resolve_paperless_ngx_service,
)
from harness.services.paperless_ngx.ingestion import (
    execute_ingest_and_await_document,
    execute_post_document,
)
from harness.services.paperless_ngx.models import (
    DocumentSummary as DirectDocSummary,
    IngestionReceipt as DirectReceipt,
    PaperlessConfig as DirectConfig,
)
from harness.services.paperless_ngx.protocols import (
    PAPERLESS_NGX_SERVICE_KEY as DirectKey,
    PaperlessNgxService as DirectProtocol,
)
from harness.services.paperless_ngx.rag import (
    execute_ask_grounded_rag,
    execute_ask_rag,
)
from harness.services.paperless_ngx.resolvers import (
    resolve_paperless_ngx_service as direct_resolve,
)
from harness.services.paperless_ngx.search import (
    execute_get_document,
    execute_get_task_status,
    execute_search_documents,
)


@pytest.mark.unit
def test_paperless_ngx_imports_and_exports() -> None:
    """Verify subpackage symbols match direct module imports."""
    assert DirectDocSummary is DocumentSummary
    assert DirectReceipt is IngestionReceipt
    assert DirectConfig is PaperlessConfig
    assert DirectKey is PAPERLESS_NGX_SERVICE_KEY
    assert DirectProtocol is PaperlessNgxService
    assert direct_resolve is resolve_paperless_ngx_service


@pytest.mark.unit
def test_paperless_ngx_protocol_conformance() -> None:
    """Verify DefaultPaperlessNgxService implements runtime checkable PaperlessNgxService protocol."""
    service = DefaultPaperlessNgxService()
    assert isinstance(service, PaperlessNgxService)
    assert PAPERLESS_NGX_SERVICE_KEY.name == "data_engineering.paperless_ngx"


@pytest.mark.unit
def test_paperless_ngx_slotted_frozen_immutability() -> None:
    """Verify slotted and frozen dataclass architecture per Rule 12 and Rule 43."""
    doc = DocumentSummary(
        id=42,
        title="Quarterly Financial Audit",
        correspondent="KPMG",
        document_type="Audit Report",
        tags=("audit", "finance", "2026"),
        content_snippet="Net income reflects 14% growth...",
    )
    assert doc.id == 42
    assert doc.title == "Quarterly Financial Audit"
    assert doc.tags == ("audit", "finance", "2026")

    # Immutability assertion per Rule 43
    with pytest.raises((AttributeError, TypeError)):
        doc.title = "Altered Title"  # type: ignore[misc]

    receipt = IngestionReceipt(
        document_id=42,
        document=doc,
        task_id="task-999",
        status="SUCCESS",
        elapsed_seconds=0.45,
    )
    with pytest.raises((AttributeError, TypeError)):
        receipt.status = "PENDING"  # type: ignore[misc]

    # Construction validations
    with pytest.raises(ValueError, match="id must be a positive integer"):
        DocumentSummary(id=0, title="Invalid")

    with pytest.raises(ValueError, match="title must not be empty"):
        DocumentSummary(id=1, title="")

    with pytest.raises(ValueError, match="status must be SUCCESS"):
        IngestionReceipt(
            document_id=1,
            document=doc,
            task_id="t-1",
            status="FAILED",
            elapsed_seconds=1.0,
        )


@pytest.mark.unit
def test_paperless_ngx_single_seam_resolver() -> None:
    """Verify resolve_paperless_ngx_service single-seam IoC resolver per Rule 58."""
    # 1. Fallback to default instance when context is None
    default_svc = resolve_paperless_ngx_service(None)
    assert isinstance(default_svc, PaperlessNgxService)

    # 2. Fallback when context has no provider
    empty_context = ServiceContext()
    fallback_svc = resolve_paperless_ngx_service(empty_context)
    assert isinstance(fallback_svc, PaperlessNgxService)
    assert fallback_svc is default_svc

    # 3. Resolution when custom service is provided
    custom_context = ServiceContext()
    custom_svc = DefaultPaperlessNgxService(PaperlessConfig(base_url="http://paperless.internal:8000"))
    custom_context.provide(PAPERLESS_NGX_SERVICE_KEY, custom_svc)

    resolved_svc = resolve_paperless_ngx_service(custom_context)
    assert resolved_svc is custom_svc
    assert resolved_svc.config.base_url == "http://paperless.internal:8000"


@pytest.mark.asyncio
async def test_paperless_ngx_grounded_rag_and_ingestion_decomposed() -> None:
    """Verify execution routines in decomposed modules operate cohesively."""
    service = DefaultPaperlessNgxService()

    # Ingest document
    receipt = await execute_ingest_and_await_document(
        service=service,
        file_path="records/q3_report.pdf",
        title="Q3 Consolidated Performance",
        tags=["q3", "earnings"],
        correspondent="Treasury",
        document_type="Financial Report",
        timeout_seconds=5.0,
    )
    assert receipt.document_id == 1
    assert receipt.document.title == "Q3 Consolidated Performance"
    assert receipt.status == "SUCCESS"

    # Search document
    search_res = await execute_search_documents(service=service, query="performance")
    assert search_res.count == 1
    assert search_res.documents[0].id == 1

    # Grounded RAG with source hydration
    grounded = await execute_ask_grounded_rag(
        service=service,
        query="What is the Q3 performance summary?",
        document_ids=[1],
    )
    assert grounded.citations == (1,)
    assert len(grounded.cited_documents) == 1
    assert grounded.cited_documents[0].title == "Q3 Consolidated Performance"
    assert grounded.confidence == 1.0
