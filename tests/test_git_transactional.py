"""Unit tests for transactional Git workspace operations."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
import pytest

from harness.services.filesystem_git import (
    FILESYSTEM_GIT_KEY,
    DefaultFilesystemGitService,
    FilesystemGitService,
)


@pytest.mark.unit
def test_filesystem_git_service_key() -> None:
    """Verify ServiceKey registration."""
    assert FILESYSTEM_GIT_KEY.name == "service.filesystem_git"


@pytest.mark.unit
def test_git_transaction_commit_and_rollback() -> None:
    """Test git commit and rollback workflows in isolated temp repo."""
    svc = DefaultFilesystemGitService()

    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)

        # Initialize git repo
        subprocess.run(["git", "init"], cwd=str(root), capture_output=True, check=True)
        subprocess.run(["git", "config", "user.name", "Test Agent"], cwd=str(root), capture_output=True, check=True)
        subprocess.run(["git", "config", "user.email", "test@agent.local"], cwd=str(root), capture_output=True, check=True)

        # Initial commit
        (root / "README.md").write_text("# Initial\n", encoding="utf-8")
        subprocess.run(["git", "add", "README.md"], cwd=str(root), capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "initial commit"], cwd=str(root), capture_output=True, check=True)

        # Write new file via service
        svc.write_file(str(root / "feature.py"), "def feature(): pass\n")

        # Check status is dirty
        status = svc.git_status(str(root))
        assert status.status == "ok"
        assert status.dirty is True
        assert status.changed_files_count == 1

        # Commit transaction
        commit_res = svc.commit_transaction("feat: add feature module", repo_path=str(root))
        assert commit_res.status == "ok"
        assert commit_res.commit_hash is not None
        assert commit_res.files_committed == 1

        # Check status clean
        status2 = svc.git_status(str(root))
        assert status2.dirty is False

        # Make bad change and rollback
        svc.write_file(str(root / "broken.py"), "bad syntax!!!\n")
        assert svc.git_status(str(root)).dirty is True

        rollback_res = svc.rollback_transaction(repo_path=str(root))
        assert rollback_res.status == "ok"
        assert (root / "broken.py").exists() is False
        assert svc.git_status(str(root)).dirty is False
