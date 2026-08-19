"""Tests for Domain 3: Embedding Cluster plugin."""

from __future__ import annotations

import pytest

from plugins.memory_and_epistemics.embedding_cluster.main import (
    cluster_text_chunks,
    extract_cluster_topic_keywords,
)


@pytest.mark.unit
class TestEmbeddingClusterPlugin:
    def test_cluster_text_chunks(self) -> None:
        docs = [
            "Kubernetes container cluster docker deployment pod node",
            "Docker containerized pod deployment service cluster",
            "PostgreSQL database SQL query relational schema table",
            "SQLite database table index SQL relational records",
            "Neuro-symbolic logic solver Z3 theorem prover deduction",
            "Prolog horn clause resolution theorem logic inference",
        ]
        res = cluster_text_chunks(docs, num_clusters=3)
        assert res["status"] == "ok"
        assert res["total_documents"] == 6
        assert res["clusters_count"] == 3

    def test_extract_cluster_topic_keywords(self) -> None:
        texts = [
            "authentication security access token oauth",
            "security password encryption credential access",
        ]
        res = extract_cluster_topic_keywords(texts, top_n=3)
        assert res["status"] == "ok"
        assert "security" in res["keywords"] or "access" in res["keywords"]
