"""Tests for Domain: Hermes State FTS5 plugin."""

from __future__ import annotations

import pytest

from plugins.memory_and_epistemics.hermes_state_fts5.main import (
    fts5_search_messages,
    fork_session_tree,
    compress_session_slice,
    query_session_provenance,
)


@pytest.mark.unit
class TestHermesStateFts5:
    def test_fts5_search_messages(self) -> None:
        res = fts5_search_messages("micro-kernel")
        assert res["status"] == "ok"
        assert res["total_matches"] >= 1
        assert any("micro-kernel" in r["content"].lower() for r in res["results"])

    def test_fork_session_tree(self) -> None:
        res = fork_session_tree("session_demo_001", "Summary of conversation turns 1-10")
        assert res["status"] == "ok"
        assert res["parent_session_id"] == "session_demo_001"
        assert res["child_session_id"].startswith("session_child_")

    def test_compress_session_slice(self) -> None:
        res = compress_session_slice("session_demo_001", window_size=5)
        assert res["status"] == "ok"
        assert res["saved_tokens_pct"] > 50

    def test_query_session_provenance(self) -> None:
        res = query_session_provenance("msg_001")
        assert res["status"] == "ok"
        assert res["provenance"]["session_id"] == "session_demo_001"
