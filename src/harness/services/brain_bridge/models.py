"""Data models and slotted representations for Brain Bridge service."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from pydantic import BaseModel, Field as PydanticField


# -----------------------------------------------------------------------------
# Slotted & Frozen Internal Domain Entities (AGENTS.md Rule 12 & 43)
# -----------------------------------------------------------------------------

@dataclass(slots=True, frozen=True)
class BrainMountRecord:
    """Slotted and immutable record of an attached brain mount."""

    alias: str
    path: str
    original_source: str = ""
    format: str = "raw_docs"
    mode: str = "lens"
    total_chunks: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True, frozen=True)
class IndexedChunk:
    """Slotted and immutable text or trajectory document chunk."""

    id: int
    file: str
    start_line: int
    end_line: int
    content: str
    tokens: tuple[str, ...] = ()
    chunk_type: str = "document_chunk"
    step_index: int | None = None


@dataclass(slots=True, frozen=True)
class TrajectoryEntry:
    """Slotted and immutable conversation or commit trajectory step."""

    file: str
    step_index: int
    step_type: str = "UNKNOWN"
    status: str = "OK"
    summary: str = ""
    commit_hash: str | None = None
    author: str | None = None
    date: str | None = None


@dataclass(slots=True, frozen=True)
class SearchScoreMatch:
    """Slotted and immutable scored search result chunk."""

    score: float
    brain_alias: str
    brain_format: str
    chunk_type: str
    file: str
    start_line: int
    end_line: int
    snippet: str


# -----------------------------------------------------------------------------
# Typed Pydantic Result Models (Public API / Backward Compatible)
# -----------------------------------------------------------------------------

class BrainAttachResult(BaseModel):
    """Result of attaching an external brain or repository."""

    status: str = PydanticField(default="ok", description="Status indicator (ok, error)")
    alias: str | None = PydanticField(default=None, description="Assigned mount alias")
    path: str | None = PydanticField(default=None, description="Local directory path")
    original_source: str | None = PydanticField(default=None, description="Original source or repository URL")
    detected_format: str | None = PydanticField(default=None, description="Detected brain or repository format")
    mode: str = PydanticField(default="lens", description="Attachment mode (lens, full, snapshot)")
    summary: dict[str, Any] = PydanticField(default_factory=dict, description="Index statistics and detected metadata")
    error: str | None = PydanticField(default=None, description="Error explanation if attachment failed")


class BrainQueryResult(BaseModel):
    """Result of querying across attached brains and repositories."""

    status: str = PydanticField(default="ok", description="Status indicator (ok, error)")
    query: str = PydanticField(default="", description="Queried search terms")
    searched_brains: list[str] = PydanticField(default_factory=list, description="Aliases of searched brain mounts")
    results_count: int = PydanticField(default=0, description="Total matching results returned")
    results: list[dict[str, Any]] = PydanticField(default_factory=list, description="Scored document and trajectory chunks")
    note: str | None = PydanticField(default=None, description="Informational notice")
    error: str | None = PydanticField(default=None, description="Error explanation if query failed")


class BrainListResult(BaseModel):
    """Result of enumerating all attached foreign brains and repositories."""

    status: str = PydanticField(default="ok", description="Status indicator (ok, error)")
    attached_count: int = PydanticField(default=0, description="Total active brain mounts")
    brains: list[dict[str, Any]] = PydanticField(default_factory=list, description="List of brain mount metadata objects")


class BrainDetachResult(BaseModel):
    """Result of detaching and unloading a foreign brain."""

    status: str = PydanticField(default="ok", description="Status indicator (ok, error)")
    detached_alias: str | None = PydanticField(default=None, description="Detached mount alias")
    path: str | None = PydanticField(default=None, description="Unmounted directory path")
    error: str | None = PydanticField(default=None, description="Error explanation if detachment failed")
