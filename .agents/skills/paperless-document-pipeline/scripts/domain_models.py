"""Slotted domain models for Paperless-NGX document processing pipeline.

Adheres strictly to Rule 12:
- slots=True, frozen=True
- __post_init__ construction assertions
- Immutable value objects
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True, frozen=True)
class PaperlessDocument:
    """Slotted immutable representation of an ingested document."""

    id: int
    title: str
    content: str
    correspondent: str | None = None
    document_type: str | None = None
    tags: tuple[str, ...] = ()
    created: str = ""
    archive_serial_number: int | None = None
    custom_fields: tuple[tuple[str, Any], ...] = ()

    def __post_init__(self) -> None:
        if self.id <= 0:
            raise ValueError(f"id must be positive, got {self.id}")
        if not self.title.strip():
            raise ValueError("title must not be empty or whitespace")
        if self.archive_serial_number is not None and self.archive_serial_number < 0:
            raise ValueError(f"archive_serial_number must be non-negative, got {self.archive_serial_number}")


@dataclass(slots=True, frozen=True)
class ConsumeTaskStatus:
    """Slotted immutable snapshot of an asynchronous ingestion task."""

    task_id: str
    status: str
    progress: int = 0
    document_id: int | None = None
    error: str | None = None

    def __post_init__(self) -> None:
        if not self.task_id.strip():
            raise ValueError("task_id must not be empty")
        if not self.status.strip():
            raise ValueError("status must not be empty")
        if not (0 <= self.progress <= 100):
            raise ValueError(f"progress must be in range [0, 100], got {self.progress}")


@dataclass(slots=True, frozen=True)
class RAGQueryResponse:
    """Slotted immutable response from Paperless AI RAG chat."""

    answer: str
    citations: tuple[int, ...] = ()
    confidence: float = 1.0

    def __post_init__(self) -> None:
        if not self.answer.strip():
            raise ValueError("answer must not be empty")
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(f"confidence must be in range [0.0, 1.0], got {self.confidence}")
