"""Tests for Domain 3: Embedding Cluster plugin."""

from __future__ import annotations

import pytest

from harness.kernel.context import ServiceContext
from harness.services.embedding_cluster import (
    EMBEDDING_CLUSTER_KEY,
    ClusterKeywordsResult,
    ClusterTextResult,
    EmbeddingClusterService,
)
from plugins.memory_and_epistemics.embedding_cluster.main import (
    EmbeddingClusterPlugin,
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

    @pytest.mark.asyncio
    async def test_embedding_cluster_plugin_ioc_lifecycle(self) -> None:
        plugin = EmbeddingClusterPlugin()
        assert plugin.name == "plugin.embedding_cluster"
        assert EMBEDDING_CLUSTER_KEY in plugin.provides

        ctx = ServiceContext()
        await plugin.on_load(ctx)
        await plugin.on_enable()

        service = ctx.require(EMBEDDING_CLUSTER_KEY)
        assert isinstance(service, EmbeddingClusterService)

        docs = [
            "graphiti memory graph temporal edges nodes",
            "memgraphrag vector hybrid retrieval graph",
        ]
        cluster_res = service.cluster_text_chunks(docs, num_clusters=2)
        assert isinstance(cluster_res, ClusterTextResult)
        assert cluster_res.status == "ok"
        assert cluster_res.total_documents == 2

        kw_res = service.extract_cluster_topic_keywords(docs, top_n=2)
        assert isinstance(kw_res, ClusterKeywordsResult)
        assert kw_res.status == "ok"
        assert len(kw_res.keywords) >= 1

        await plugin.on_disable()
        await plugin.on_unload()
