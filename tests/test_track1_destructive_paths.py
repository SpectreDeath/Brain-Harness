"""Tests for Track 1 — Destructive paths (data-loss class)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from harness.agent.session.models import AgentSession
from harness.agent.session.store import CorruptSessionError, StorageBackedSessionStore
from harness.services.dock import DefaultDockService, DockError
from harness.services.filesystem_git import DefaultFilesystemGitService


@pytest.mark.unit
class TestFilesystemGitScopedTransactions:
    def test_commit_and_rollback_transaction_scoped_paths(self) -> None:
        svc = DefaultFilesystemGitService()
        with patch.object(svc, "_run_git", return_value=(0, "ok", "")) as mock_git:
            with patch.object(
                svc,
                "git_status",
                return_value=MagicMock(status="ok", dirty=True, changed_files_count=1),
            ):
                # Commit with scoped path
                res_commit = svc.commit_transaction("test commit", paths=["src/file.py"])
                assert res_commit.status == "ok"
                # Check git add was called with -- src/file.py, not -A
                add_call = [c for c in mock_git.call_args_list if c[0][0][0] == "add"][0]
                assert add_call[0][0] == ["add", "--", "src/file.py"]

                # Rollback with scoped path
                mock_git.reset_mock()
                res_rollback = svc.rollback_transaction(paths=["src/file.py"])
                assert res_rollback.status == "ok"
                calls = [c[0][0] for c in mock_git.call_args_list]
                assert ["restore", "--staged", "--", "src/file.py"] in calls
                assert ["restore", "--", "src/file.py"] in calls
                assert ["clean", "-f", "--", "src/file.py"] in calls
                # Assert unscoped git clean -fd was NOT called across the repo!
                assert ["clean", "-fd"] not in calls


@pytest.mark.unit
class TestDockCorruptFileQuarantine:
    def test_corrupt_docks_json_quarantined_and_not_overwritten(self, tmp_path: Path) -> None:
        docks_file = tmp_path / "docks.json"
        docks_file.write_text("{ this is corrupt json !!!")

        service = DefaultDockService(workspace_root=tmp_path)
        service._state_file = docks_file

        with pytest.raises(DockError, match="corrupted and quarantined"):
            service._load_records()

        # Verify quarantine backup file was created
        corrupt_backups = list(tmp_path.glob("docks.json.corrupt-*"))
        assert len(corrupt_backups) == 1
        assert corrupt_backups[0].read_text() == "{ this is corrupt json !!!"


@pytest.mark.unit
class TestKnowledgeDismissAction:
    @pytest.mark.asyncio
    async def test_dismiss_action_persists_edge(self) -> None:
        from harness.ui.server.routes.knowledge import (
            ResolveContradictionRequest,
            resolve_knowledge_contradiction_endpoint,
        )

        mock_storage = AsyncMock()
        mock_storage.close = MagicMock()
        item_a = MagicMock(id="ki_a", status="ACTIVE")
        item_b = MagicMock(id="ki_b", status="ACTIVE")
        mock_storage.get_knowledge_item.side_effect = lambda ki_id: item_a if ki_id == "ki_a" else item_b

        with patch("harness.ui.server.routes.knowledge.SQLiteStorageService", return_value=mock_storage):
            req = ResolveContradictionRequest(
                ki_a="ki_a",
                ki_b="ki_b",
                action="dismiss",
                reason="Not conflicting in practice",
            )
            res = await resolve_knowledge_contradiction_endpoint(req)
            assert res["status"] == "ok"
            assert res["action"] == "dismiss"

            # Check dismissed_contradiction edge was added to both items
            item_a.add_edge.assert_called_with(
                "dismissed_contradiction",
                "ki_b",
                target_kind="ki",
                derived=False,
                confidence=1.0,
                description="Not conflicting in practice",
            )
            item_b.add_edge.assert_called_with(
                "dismissed_contradiction",
                "ki_a",
                target_kind="ki",
                derived=False,
                confidence=1.0,
                description="Not conflicting in practice",
            )
            assert mock_storage.save_knowledge_item.call_count == 2
            assert mock_storage.export_single_item.call_count == 2


@pytest.mark.unit
class TestSessionStoreCorruptHandling:
    @pytest.mark.asyncio
    async def test_get_distinguishes_missing_from_corrupt(self) -> None:
        mock_kv = AsyncMock()
        store = StorageBackedSessionStore(mock_kv)

        # Missing session
        mock_kv.get.return_value = None
        assert await store.get("missing_sess") is None

        # Corrupt JSON string
        mock_kv.get.return_value = "{ invalid json"
        with pytest.raises(CorruptSessionError):
            await store.get("corrupt_sess")

        # Corrupt dict schema (missing required fields for from_dict)
        mock_kv.get.return_value = {"not_a_valid_session": 123}
        with pytest.raises(CorruptSessionError):
            await store.get("corrupt_dict_sess")

    @pytest.mark.asyncio
    async def test_list_surfaces_corrupt_sessions(self) -> None:
        mock_kv = AsyncMock()
        store = StorageBackedSessionStore(mock_kv)

        mock_kv.list_keys.return_value = ["session:valid1", "session:corrupt2"]

        valid_sess = AgentSession(session_id="valid1", task="valid task")
        mock_kv.get.side_effect = lambda k: (
            valid_sess.to_dict() if "valid1" in k else "{ corrupted json"
        )

        sessions = await store.list()
        assert len(sessions) == 2
        valid = [s for s in sessions if s.session_id == "valid1"][0]
        corrupt = [s for s in sessions if s.session_id == "corrupt2"][0]
        assert valid.status == "running"
        assert corrupt.status == "corrupt"
        assert "[CORRUPT SESSION" in corrupt.task
