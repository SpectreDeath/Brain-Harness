"""RAG and grounded query operations with source provenance hydration (Rule 41)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from harness.services.paperless_ngx.models import (
    DocumentSummary,
    GroundedRAGAnswer,
    RAGAnswer,
)

if TYPE_CHECKING:
    from harness.services.paperless_ngx.service import DefaultPaperlessNgxService

logger = structlog.get_logger(__name__)


async def execute_ask_rag(
    service: DefaultPaperlessNgxService,
    query: str,
    document_ids: list[int] | None = None,
) -> RAGAnswer:
    """Simulate paperless_ai RAG chat response with citations."""
    target_docs = (
        list(service.in_memory_docs.keys()) if not document_ids else document_ids
    )
    citations = tuple(sorted(target_docs)[:3])
    return RAGAnswer(
        answer=f"Synthesized response for query '{query}' based on Paperless-NGX archive.",
        citations=citations,
    )


async def execute_ask_grounded_rag(
    service: DefaultPaperlessNgxService,
    query: str,
    document_ids: list[int] | None = None,
) -> GroundedRAGAnswer:
    """High-leverage RAG query seam: answers question and hydrates cited source documents (Rule 41)."""
    rag_answer = await service.ask_rag(query=query, document_ids=document_ids)
    hydrated_docs: list[DocumentSummary] = []
    for doc_id in rag_answer.citations:
        try:
            doc = await service.get_document(doc_id)
            hydrated_docs.append(doc)
        except KeyError:
            logger.warning("Cited document ID not found in archive", doc_id=doc_id)

    return GroundedRAGAnswer(
        answer=rag_answer.answer,
        citations=rag_answer.citations,
        cited_documents=tuple(hydrated_docs),
        confidence=1.0 if hydrated_docs else 0.8,
    )
