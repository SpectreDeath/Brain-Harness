"""Unsupervised Text Clustering and Topic Extraction protocol, models, and ServiceKey."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable
from pydantic import BaseModel, Field

from harness.kernel.context import ServiceKey


class ClusterTextResult(BaseModel):
    """Result of K-Means clustering over text documents."""

    status: str = Field(default="ok", description="Status indicator (ok, error)")
    total_documents: int = Field(default=0, description="Total input documents processed")
    clusters_count: int = Field(default=0, description="Number of clusters produced")
    clusters: list[dict[str, Any]] = Field(default_factory=list, description="Cluster groups with top keywords")
    error: str | None = Field(default=None, description="Error explanation if clustering failed")


class ClusterKeywordsResult(BaseModel):
    """Result of extracting salient topic keywords from a text group."""

    status: str = Field(default="ok", description="Status indicator (ok, error)")
    keywords: list[str] = Field(default_factory=list, description="Extracted salient keywords")
    error: str | None = Field(default=None, description="Error explanation if extraction failed")


@runtime_checkable
class EmbeddingClusterService(Protocol):
    """Protocol for unsupervised text clustering and topic extraction."""

    def cluster_text_chunks(
        self,
        texts: list[Any],
        num_clusters: int = 3,
    ) -> ClusterTextResult:
        """K-Means clustering over text documents using TF-IDF representation."""
        ...

    def extract_cluster_topic_keywords(
        self,
        cluster_texts: list[str],
        top_n: int = 5,
    ) -> ClusterKeywordsResult:
        """Extract most salient terms in a text cluster."""
        ...


EMBEDDING_CLUSTER_KEY: ServiceKey[EmbeddingClusterService] = ServiceKey("service.embedding_cluster")
