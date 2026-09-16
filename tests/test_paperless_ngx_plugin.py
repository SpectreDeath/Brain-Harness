"""Tests for Paperless-NGX Data Engineering Plugin, slotted domain models, and service registration."""

from __future__ import annotations

from pathlib import Path

import pytest

from harness.creator.validator import PluginValidator
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
)
from plugins.data_engineering.paperless_ngx.main import (
    PaperlessNgxPlugin,
    paperless_ask_grounded_rag,
    paperless_get_document,
    paperless_get_task_status,
    paperless_ingest_and_await,
    paperless_post_document,
    paperless_search_documents,
)


@pytest.mark.unit
def test_paperless_ngx_plugin_metadata() -> None:
    """Verify plugin identity, description, and service key contracts."""
    p = PaperlessNgxPlugin()
    assert p.name == "plugin.paperless_ngx"
    assert p.version == "1.0.0"
    assert "Paperless-NGX" in p.description
    assert PAPERLESS_NGX_SERVICE_KEY in p.provides
    assert isinstance(p, PaperlessNgxService)


@pytest.mark.unit
def test_paperless_ngx_ioc_lifecycle() -> None:
    """Verify registration and resolution inside ServiceContext container."""
    context = ServiceContext()
    p = PaperlessNgxPlugin()

    p.on_load(context)
    resolved = context.require(PAPERLESS_NGX_SERVICE_KEY)
    assert resolved is p
    assert isinstance(resolved, PaperlessNgxService)

    p.on_unload(context)


@pytest.mark.unit
def test_paperless_slotted_frozen_dataclasses() -> None:
    """Verify slotted and frozen dataclass invariants per Rule 12 and Rule 43."""
    doc = DocumentSummary(
        id=1,
        title="Tax Return 2025",
        correspondent="IRS",
        document_type="Tax Form",
        tags=("tax", "financial"),
    )
    receipt = IngestionReceipt(
        document_id=1,
        document=doc,
        task_id="task-12345",
        status="SUCCESS",
        elapsed_seconds=1.25,
    )
    assert receipt.document_id == 1
    assert receipt.document.title == "Tax Return 2025"
    assert receipt.status == "SUCCESS"

    # Rule 43: Immutability assertion via direct attribute assignment
    with pytest.raises((AttributeError, TypeError)):
        receipt.status = "FAILED"  # type: ignore[misc]

    rag = GroundedRAGAnswer(
        answer="Total tax liability is $4,200.",
        citations=(1,),
        cited_documents=(doc,),
        confidence=0.98,
    )
    assert rag.citations == (1,)
    assert len(rag.cited_documents) == 1
    assert rag.confidence == 0.98

    with pytest.raises((AttributeError, TypeError)):
        rag.answer = "Modified"  # type: ignore[misc]

    # Construction assertion validation
    with pytest.raises(ValueError):
        IngestionReceipt(
            document_id=0,
            document=doc,
            task_id="task-123",
            status="SUCCESS",
            elapsed_seconds=1.0,
        )

    with pytest.raises(ValueError):
        GroundedRAGAnswer(
            answer="",
            citations=(1,),
            cited_documents=(doc,),
        )


@pytest.mark.asyncio
async def test_paperless_service_operations() -> None:
    """Verify asynchronous service operations against DefaultPaperlessNgxService."""
    service = DefaultPaperlessNgxService(PaperlessConfig())

    # 1. Post document
    task = await service.post_document(
        file_path="sample_invoice.pdf",
        title="Sample Invoice #101",
        tags=["invoice", "finance"],
        correspondent="Vendor Corp",
        document_type="Invoice",
    )
    assert isinstance(task, TaskProgress)
    assert task.status == "SUCCESS"
    assert "Document 1" in (task.result or "")

    # 2. Check task status
    task_status = await service.get_task_status(task.task_id)
    assert task_status.task_id == task.task_id
    assert task_status.status == "SUCCESS"

    # 3. Get document
    doc = await service.get_document(1)
    assert isinstance(doc, DocumentSummary)
    assert doc.id == 1
    assert doc.title == "Sample Invoice #101"
    assert "invoice" in doc.tags
    assert doc.correspondent == "Vendor Corp"

    # 4. Search documents
    search_res = await service.search_documents(query="invoice", tags=["finance"])
    assert isinstance(search_res, SearchResult)
    assert search_res.count >= 1
    assert search_res.documents[0].id == 1

    # 5. Ask RAG
    rag_ans = await service.ask_rag("What is the invoice amount?", document_ids=[1])
    assert isinstance(rag_ans, RAGAnswer)
    assert 1 in rag_ans.citations
    assert "invoice" in rag_ans.answer.lower()


@pytest.mark.asyncio
async def test_paperless_ingest_and_await_seam() -> None:
    """Verify high-leverage atomic ingestion seam with polling and hydration."""
    service = DefaultPaperlessNgxService(PaperlessConfig())

    receipt = await service.ingest_and_await_document(
        file_path="contracts/master_services.pdf",
        title="Master Services Agreement 2026",
        tags=["legal", "contracts"],
        correspondent="Acme Legal",
        document_type="Contract",
        timeout_seconds=5.0,
    )

    assert isinstance(receipt, IngestionReceipt)
    assert receipt.status == "SUCCESS"
    assert receipt.document_id >= 1
    assert receipt.document.title == "Master Services Agreement 2026"
    assert "contracts" in receipt.document.tags
    assert receipt.document.correspondent == "Acme Legal"
    assert receipt.elapsed_seconds >= 0.0


@pytest.mark.asyncio
async def test_paperless_grounded_rag_seam() -> None:
    """Verify grounded RAG query seam with cited document hydration."""
    service = DefaultPaperlessNgxService(PaperlessConfig())

    # Ingest document first
    await service.post_document(
        file_path="handbook.pdf",
        title="Employee Handbook",
        tags=["hr"],
        correspondent="People Ops",
    )

    grounded = await service.ask_grounded_rag(
        query="What is the remote work policy?",
        document_ids=[1],
    )
    assert isinstance(grounded, GroundedRAGAnswer)
    assert len(grounded.citations) > 0
    assert len(grounded.cited_documents) > 0
    assert grounded.cited_documents[0].id == 1
    assert grounded.cited_documents[0].title == "Employee Handbook"
    assert grounded.confidence >= 0.8


@pytest.mark.unit
def test_module_tool_wrappers() -> None:
    """Verify synchronous tool wrappers exported by the plugin module."""
    # 1. Ingest and await
    ingest_res = paperless_ingest_and_await(
        file_path="receipt.png",
        title="Dinner Receipt",
        tags=["expenses"],
        correspondent="Bistro",
    )
    assert ingest_res["status"] == "ok"
    assert ingest_res["task_status"] == "SUCCESS"
    assert ingest_res["document"]["title"] == "Dinner Receipt"
    doc_id = ingest_res["document_id"]

    # 2. Get document
    doc_res = paperless_get_document(doc_id)
    assert doc_res["status"] == "ok"
    assert doc_res["document"]["id"] == doc_id

    # 3. Search documents
    search_res = paperless_search_documents(query="Dinner")
    assert search_res["status"] == "ok"
    assert search_res["count"] >= 1

    # 4. Ask Grounded RAG
    rag_res = paperless_ask_grounded_rag(
        query="What was the restaurant name?", document_ids=[doc_id]
    )
    assert rag_res["status"] == "ok"
    assert len(rag_res["citations"]) > 0
    assert len(rag_res["cited_documents"]) > 0
    assert rag_res["cited_documents"][0]["id"] == doc_id

    # 5. Legacy post document & task status
    post_res = paperless_post_document(
        file_path="statement.pdf", title="Bank Statement"
    )
    assert post_res["status"] == "ok"
    status_res = paperless_get_task_status(post_res["task_id"])
    assert status_res["status"] == "ok"


@pytest.mark.asyncio
async def test_safe_run_in_active_event_loop() -> None:
    """Verify _safe_run successfully dispatches tool wrappers from inside an active asyncio loop."""
    # Calling paperless_search_documents inside an async coroutine would raise
    # RuntimeError: asyncio.run() cannot be called from a running event loop
    # unless _safe_run delegates to worker thread.
    res = paperless_search_documents(query="Dinner")
    assert res["status"] == "ok"

    ingest_res = paperless_ingest_and_await(
        file_path="async_test.pdf", title="Async Test Document"
    )
    assert ingest_res["status"] == "ok"
    assert ingest_res["document"]["title"] == "Async Test Document"


@pytest.mark.unit
def test_plugin_validator_compliance() -> None:
    """Validate plugin.json and directory layout using PluginValidator per Rule 38."""
    plugin_dir = Path("plugins/data_engineering/paperless_ngx").resolve()
    report = PluginValidator.validate_sync(plugin_dir)
    assert report.valid is True
    for check in report.checks:
        assert check.passed is True, (
            f"Plugin check '{check.rule}' failed: {check.message}"
        )
