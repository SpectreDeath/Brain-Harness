"""Tests for vector_index plugin."""

from __future__ import annotations

from pathlib import Path
import pytest

from harness.kernel.context import ServiceContext
from harness.services.vector_index import (
    VECTOR_INDEX_KEY,
    VectorHybridSearchResult,
    VectorIndexResult,
    VectorIndexService,
    VectorSearchResult,
)
from plugins.memory_and_epistemics.vector_index.main import (
    VectorIndexPlugin,
    vector_index_directory,
    vector_search_hybrid,
    vector_search_semantic,
)


@pytest.mark.unit
class TestVectorIndexPlugin:
    def test_indexing_and_semantic_search(self, tmp_path: Path) -> None:
        (tmp_path / "auth.py").write_text(
            "def authenticate_user(username: str, token: str) -> bool:\n"
            "    \"\"\"Validate user credentials and security token.\"\"\"\n"
            "    return True\n"
        )
        (tmp_path / "storage.py").write_text(
            "class DatabaseStorage:\n"
            "    \"\"\"Persist key value records in sqlite database.\"\"\"\n"
            "    def save(self, key: str, val: str): pass\n"
        )

        res_idx = vector_index_directory(str(tmp_path), chunk_lines=20)
        assert res_idx["status"] == "ok"
        assert res_idx["indexed_chunks"] >= 2
        assert res_idx["unique_terms"] > 5

        # Query semantic match for authentication
        res_search = vector_search_semantic("user login credentials token security", top_k=2)
        assert res_search["status"] == "ok"
        assert res_search["results_count"] >= 1
        assert "auth.py" in res_search["results"][0]["file"]
        assert res_search["results"][0]["score"] > 0.1

        # Query semantic match for storage
        res_search_db = vector_search_semantic("database persistence sqlite", top_k=2)
        assert res_search_db["status"] == "ok"
        assert res_search_db["results_count"] >= 1
        assert "storage.py" in res_search_db["results"][0]["file"]

    def test_hybrid_search(self, tmp_path: Path) -> None:
        (tmp_path / "doc.md").write_text(
            "# Architecture Guide\n"
            "Brain Harness provides IoC micro-kernel architecture with typed ServiceKeys.\n"
        )
        vector_index_directory(str(tmp_path))

        res_hyb = vector_search_hybrid("micro-kernel architecture", keyword="ServiceKeys")
        assert res_hyb["status"] == "ok"
        assert res_hyb["results_count"] >= 1
        assert res_hyb["results"][0]["keyword_match"] is True

    @pytest.mark.asyncio
    async def test_vector_index_plugin_ioc_lifecycle(self, tmp_path: Path) -> None:
        plugin = VectorIndexPlugin()
        assert plugin.name == "plugin.vector_index"
        assert VECTOR_INDEX_KEY in plugin.provides

        ctx = ServiceContext()
        await plugin.on_load(ctx)
        await plugin.on_enable()

        service = ctx.require(VECTOR_INDEX_KEY)
        assert isinstance(service, VectorIndexService)

        (tmp_path / "ioc_doc.py").write_text(
            "def resolve_service():\n    \"\"\"Resolves typed ServiceKey[T] from container.\"\"\"\n    pass\n"
        )

        idx_res = await service.index_directory_async(str(tmp_path))
        assert isinstance(idx_res, VectorIndexResult)
        assert idx_res.status == "ok"
        assert idx_res.indexed_chunks >= 1

        search_res = await service.search_semantic_async("resolve typed service container")
        assert isinstance(search_res, VectorSearchResult)
        assert search_res.status == "ok"
        assert search_res.results_count >= 1

        hybrid_res = await service.search_hybrid_async("service container", keyword="ServiceKey")
        assert isinstance(hybrid_res, VectorHybridSearchResult)
        assert hybrid_res.status == "ok"

        await plugin.on_disable()
        await plugin.on_unload()
