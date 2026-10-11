"""Slotted and frozen data models for the Paperless-NGX service subsystem."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class PaperlessConfig:
    """Operational connection configuration for Paperless-NGX."""

    base_url: str = "http://localhost:8000"
    api_token: str | None = None
    timeout_seconds: float = 30.0

    def __post_init__(self) -> None:
        if not self.base_url:
            raise ValueError("base_url must not be empty")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")


@dataclass(slots=True, frozen=True)
class DocumentSummary:
    """Slotted immutable representation of a Paperless-NGX document."""

    id: int
    title: str
    correspondent: str | None = None
    document_type: str | None = None
    tags: tuple[str, ...] = ()
    created: str = ""
    archive_serial_number: int | None = None
    content_snippet: str = ""

    def __post_init__(self) -> None:
        if self.id <= 0:
            raise ValueError(f"id must be a positive integer, got {self.id}")
        if not self.title:
            raise ValueError("title must not be empty")


@dataclass(slots=True, frozen=True)
class SearchResult:
    """Slotted immutable search result set."""

    count: int
    documents: tuple[DocumentSummary, ...] = ()

    def __post_init__(self) -> None:
        if self.count < 0:
            raise ValueError("count must be non-negative")


@dataclass(slots=True, frozen=True)
class RAGAnswer:
    """Slotted immutable answer payload from paperless_ai RAG chat."""

    answer: str
    citations: tuple[int, ...] = ()

    def __post_init__(self) -> None:
        if not self.answer:
            raise ValueError("answer must not be empty")


@dataclass(slots=True, frozen=True)
class GroundedRAGAnswer:
    """Slotted immutable RAG answer payload with fully hydrated source documents."""

    answer: str
    citations: tuple[int, ...] = ()
    cited_documents: tuple[DocumentSummary, ...] = ()
    confidence: float = 1.0

    def __post_init__(self) -> None:
        if not self.answer:
            raise ValueError("answer must not be empty")
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(
                f"confidence must be in range [0.0, 1.0], got {self.confidence}"
            )


@dataclass(slots=True, frozen=True)
class TaskProgress:
    """Slotted immutable task status record."""

    task_id: str
    status: str
    task_type: str = "document_consumption"
    date_created: str = ""
    date_done: str | None = None
    result: str | None = None

    def __post_init__(self) -> None:
        if not self.task_id:
            raise ValueError("task_id must not be empty")
        if not self.status:
            raise ValueError("status must not be empty")


@dataclass(slots=True, frozen=True)
class IngestionReceipt:
    """Slotted immutable settlement receipt for an ingested and verified document."""

    document_id: int
    document: DocumentSummary
    task_id: str
    status: str
    elapsed_seconds: float
    date_created: str = ""

    def __post_init__(self) -> None:
        if self.document_id <= 0:
            raise ValueError(f"document_id must be positive, got {self.document_id}")
        if not self.task_id:
            raise ValueError("task_id must not be empty")
        if self.status != "SUCCESS":
            raise ValueError(
                f"IngestionReceipt status must be SUCCESS, got {self.status}"
            )
        if self.elapsed_seconds < 0:
            raise ValueError("elapsed_seconds must be non-negative")
