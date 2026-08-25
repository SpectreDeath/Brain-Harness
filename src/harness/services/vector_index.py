"""Local Vector Index and Retrieval service protocol, typed models, and ServiceKey."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable
from pydantic import BaseModel, Field

from harness.kernel.context import ServiceKey


class VectorIndexResult(BaseModel):
    """Result of directory vector indexing."""

    status: str = Field(default="ok", description="Status indicator (ok, error)")
    root: str | None = Field(default=None, description="Indexed root directory path")
    indexed_chunks: int = Field(default=0, description="Total document chunks indexed")
    unique_terms: int = Field(default=0, description="Unique vocabulary terms in vocabulary")
    error: str | None = Field(default=None, description="Error explanation if indexing failed")


class VectorSearchResult(BaseModel):
    """Result of semantic cosine similarity search."""

    status: str = Field(default="ok", description="Status indicator (ok, error)")
    query: str = Field(default="", description="Queried search expression")
    results_count: int = Field(default=0, description="Count of retrieved matching chunks")
    results: list[dict[str, Any]] = Field(default_factory=list, description="Scored result chunks with snippets")
    note: str | None = Field(default=None, description="Notice if index is unpopulated")
    error: str | None = Field(default=None, description="Error explanation if search failed")


class VectorHybridSearchResult(BaseModel):
    """Result of hybrid semantic + exact keyword boosted search."""

    status: str = Field(default="ok", description="Status indicator (ok, error)")
    query: str = Field(default="", description="Queried semantic expression")
    keyword: str | None = Field(default=None, description="Exact boost keyword")
    results_count: int = Field(default=0, description="Count of retrieved chunks")
    results: list[dict[str, Any]] = Field(default_factory=list, description="Scored result chunks with boost status")
    error: str | None = Field(default=None, description="Error explanation if search failed")


@runtime_checkable
class VectorIndexService(Protocol):
    """Protocol for local vector indexing, semantic search, and hybrid keyword boosting."""

    def index_directory(
        self,
        path: str = ".",
        extensions: list[str] | None = None,
        chunk_lines: int = 30,
    ) -> VectorIndexResult:
        """Scan and index documents in a directory synchronously."""
        ...

    async def index_directory_async(
        self,
        path: str = ".",
        extensions: list[str] | None = None,
        chunk_lines: int = 30,
    ) -> VectorIndexResult:
        """Scan and index documents in a directory asynchronously without blocking event loops."""
        ...

    def search_semantic(
        self,
        query: str,
        top_k: int = 5,
    ) -> VectorSearchResult:
        """Perform natural language cosine similarity search synchronously."""
        ...

    async def search_semantic_async(
        self,
        query: str,
        top_k: int = 5,
    ) -> VectorSearchResult:
        """Perform natural language cosine similarity search asynchronously."""
        ...

    def search_hybrid(
        self,
        query: str,
        keyword: str | None = None,
        top_k: int = 5,
    ) -> VectorHybridSearchResult:
        """Perform hybrid search combining semantic score with exact keyword boosting."""
        ...

    async def search_hybrid_async(
        self,
        query: str,
        keyword: str | None = None,
        top_k: int = 5,
    ) -> VectorHybridSearchResult:
        """Perform hybrid search combining semantic score with exact keyword boosting asynchronously."""
        ...


VECTOR_INDEX_KEY: ServiceKey[VectorIndexService] = ServiceKey("service.vector_index")
