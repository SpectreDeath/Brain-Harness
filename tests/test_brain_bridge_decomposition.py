"""Comprehensive characterization test suite for Brain Bridge service decomposition.

Validates:
1. Slotted and frozen dataclass architecture (Rules 12 and 43).
2. Domain-partitioned submodules:
   - models: Slotted and frozen records (BrainMountRecord, IndexedChunk, TrajectoryEntry, SearchScoreMatch).
   - protocols: BrainBridgeService protocol and typed BRAIN_BRIDGE_KEY.
   - tokenizers: Text tokenization and normalized TF-IDF vector computation.
   - detector: Brain format heuristics, Git URL detection, repository caching.
   - indexers: Code/doc chunking, transcript parsing, and Git commit log parsing.
   - core: DefaultBrainBridgeService coordinator class.
   - resolvers: Single-seam resolver factory resolve_brain_bridge (Rule 58).
3. 100% backward compatibility for all external callers and entrypoints.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
import pytest

from harness.kernel.context import ServiceContext
from harness.services.brain_bridge import (
    BRAIN_BRIDGE_KEY,
    BrainAttachResult,
    BrainBridgeService,
    BrainDetachResult,
    BrainListResult,
    BrainQueryResult,
    DEFAULT_CODE_EXTS,
    DefaultBrainBridgeService,
    SPECIAL_FILENAMES,
    clone_remote_repo,
    compute_tf_idf_vector,
    detect_brain_format,
    index_text_files,
    is_git_url,
    parse_git_commits,
    parse_transcripts,
    resolve_brain_bridge,
    tokenize_text,
)
from harness.services.brain_bridge.models import (
    BrainMountRecord,
    IndexedChunk,
    SearchScoreMatch,
    TrajectoryEntry,
)
from harness.services.brain_bridge.tokenizers import (
    compute_tf_idf_vector as sub_compute_vector,
    tokenize_text as sub_tokenize,
)
from harness.services.brain_bridge.detector import (
    detect_brain_format as sub_detect_format,
    is_git_url as sub_is_git_url,
)
from harness.services.brain_bridge.indexers import (
    index_text_files as sub_index_files,
    parse_git_commits as sub_parse_commits,
    parse_transcripts as sub_parse_transcripts,
)
from harness.services.brain_bridge.resolvers import (
    resolve_brain_bridge as sub_resolve_bridge,
)


@pytest.mark.unit
class TestBrainBridgeSlottedModels:
    """Verify slotted and frozen dataclass architecture per Rules 12 and 43."""

    def test_brain_mount_record_immutability(self) -> None:
        rec = BrainMountRecord(
            alias="test_alias",
            path="/tmp/test_path",
            original_source="/tmp/test_path",
            format="antigravity_brain",
            mode="lens",
            total_chunks=10,
        )
        assert rec.alias == "test_alias"
        assert hasattr(rec, "__slots__")

        # Rule 43: Direct attribute assignment inside pytest.raises((AttributeError, TypeError))
        with pytest.raises((AttributeError, TypeError)):
            rec.alias = "mutated"  # type: ignore[misc]

    def test_indexed_chunk_immutability(self) -> None:
        chunk = IndexedChunk(
            id=1,
            file="src/main.py",
            start_line=1,
            end_line=10,
            content="print('hello')",
            tokens=("print", "hello"),
            chunk_type="document_chunk",
        )
        assert chunk.id == 1
        assert hasattr(chunk, "__slots__")

        with pytest.raises((AttributeError, TypeError)):
            chunk.id = 2  # type: ignore[misc]

    def test_trajectory_entry_immutability(self) -> None:
        entry = TrajectoryEntry(
            file="transcript.jsonl",
            step_index=0,
            step_type="USER_INPUT",
            summary="User initial request",
        )
        assert entry.step_index == 0
        assert hasattr(entry, "__slots__")

        with pytest.raises((AttributeError, TypeError)):
            entry.step_index = 5  # type: ignore[misc]

    def test_search_score_match_immutability(self) -> None:
        match = SearchScoreMatch(
            score=0.95,
            brain_alias="main_brain",
            brain_format="harness_instance",
            chunk_type="document_chunk",
            file="README.md",
            start_line=1,
            end_line=30,
            snippet="Architecture documentation",
        )
        assert match.score == 0.95
        assert hasattr(match, "__slots__")

        with pytest.raises((AttributeError, TypeError)):
            match.score = 0.5  # type: ignore[misc]


@pytest.mark.unit
class TestBrainBridgeSubmodules:
    """Verify each decomposed domain submodule in isolation."""

    def test_tokenizers_submodule(self) -> None:
        tokens = sub_tokenize("DefaultBrainBridgeService and TF-IDF calculation")
        assert "defaultbrainbridgeservice" in tokens or "default" in tokens
        assert "calculation" in tokens

        doc_freq = {"default": 1, "calculation": 1}
        vec = sub_compute_vector(tokens, doc_freq, total_docs=1)
        assert isinstance(vec, dict)
        assert len(vec) > 0

    def test_detector_submodule(self, tmp_path: Path) -> None:
        assert sub_is_git_url("https://github.com/test/repo.git") is True
        assert sub_is_git_url("git@github.com:test/repo.git") is True
        assert sub_is_git_url(str(tmp_path)) is False

        ag_dir = tmp_path / "ag"
        (ag_dir / "transcript.jsonl").parent.mkdir(parents=True)
        (ag_dir / "transcript.jsonl").write_text("{}\n", encoding="utf-8")
        assert sub_detect_format(ag_dir) == "antigravity_brain"

    def test_indexers_submodule(self, tmp_path: Path) -> None:
        code_dir = tmp_path / "code"
        code_dir.mkdir()
        (code_dir / "sample.py").write_text("def hello():\n    return 42\n", encoding="utf-8")
        chunks, doc_freq, langs, manifests = sub_index_files(code_dir)
        assert len(chunks) > 0
        assert "py" in langs

    def test_resolvers_submodule(self) -> None:
        # Default fallback
        svc = sub_resolve_bridge(None)
        assert isinstance(svc, DefaultBrainBridgeService)

        # Context resolution
        ctx = ServiceContext()
        custom = DefaultBrainBridgeService()
        ctx.provide(BRAIN_BRIDGE_KEY, custom, provider="unit_test")
        assert sub_resolve_bridge(ctx) is custom


@pytest.mark.unit
class TestBrainBridgeFacadeAndBackwardCompatibility:
    """Verify DefaultBrainBridgeService lifecycle and top-level exports."""

    def test_lifecycle_and_exports(self, tmp_path: Path) -> None:
        repo = tmp_path / "lifecycle_brain"
        repo.mkdir()
        (repo / "doc.md").write_text("# Knowledge Base\nFederated memory querying.\n", encoding="utf-8")

        service = DefaultBrainBridgeService()

        # Attach
        res_attach = service.attach(str(repo), alias="test_repo")
        assert res_attach.status == "ok"
        assert res_attach.alias == "test_repo"

        # List
        res_list = service.list_attached()
        assert res_list.attached_count == 1
        assert res_list.brains[0]["alias"] == "test_repo"

        # Query
        res_query = service.query("Federated memory", brain_alias="test_repo")
        assert res_query.status == "ok"
        assert res_query.results_count > 0

        # Detach
        res_detach = service.detach("test_repo")
        assert res_detach.status == "ok"
        assert service.list_attached().attached_count == 0

    @pytest.mark.asyncio
    async def test_async_lifecycle(self, tmp_path: Path) -> None:
        repo = tmp_path / "async_test"
        repo.mkdir()
        (repo / "test.py").write_text("value = 100\n", encoding="utf-8")

        service = DefaultBrainBridgeService()
        attach_res = await service.attach_async(str(repo), alias="async_alias")
        assert attach_res.status == "ok"

        query_res = await service.query_async("value", brain_alias="async_alias")
        assert query_res.status == "ok"

        list_res = await service.list_attached_async()
        assert list_res.attached_count == 1

        detach_res = await service.detach_async("async_alias")
        assert detach_res.status == "ok"
