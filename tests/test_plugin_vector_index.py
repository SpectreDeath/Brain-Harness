"""Tests for vector_index plugin."""

from __future__ import annotations

from pathlib import Path

import pytest

from plugins.memory_and_epistemics.vector_index.main import (
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
