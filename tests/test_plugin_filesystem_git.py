"""Tests for filesystem_git plugin."""

from __future__ import annotations

from pathlib import Path

import pytest

from plugins.filesystem_git.main import (
    fs_list_dir,
    fs_read_file,
    fs_search_text,
    fs_write_file,
    git_diff,
    git_log,
    git_status,
)


@pytest.mark.unit
class TestFilesystemGitPlugin:
    def test_fs_write_and_read(self, tmp_path: Path) -> None:
        target = tmp_path / "hello.txt"
        res_write = fs_write_file(str(target), "line 1\nline 2\nline 3\nline 4")
        assert res_write["status"] == "ok"
        assert res_write["bytes_written"] > 0

        # Cannot overwrite without flag
        res_fail = fs_write_file(str(target), "new")
        assert res_fail["status"] == "error"

        # Overwrite with flag
        res_ovr = fs_write_file(str(target), "line 1\nline 2\nline 3\nline 4", overwrite=True)
        assert res_ovr["status"] == "ok"

        # Read slice
        res_read = fs_read_file(str(target), start_line=2, end_line=3)
        assert res_read["status"] == "ok"
        assert res_read["total_lines"] == 4
        assert res_read["content"] == "line 2\nline 3"

    def test_fs_list_dir(self, tmp_path: Path) -> None:
        (tmp_path / "a.txt").write_text("a")
        sub = tmp_path / "subdir"
        sub.mkdir()
        (sub / "b.txt").write_text("b")

        res = fs_list_dir(str(tmp_path), max_depth=2)
        assert res["status"] == "ok"
        assert res["count"] >= 2

    def test_fs_search_text(self, tmp_path: Path) -> None:
        (tmp_path / "file1.py").write_text("def my_secret_function(): pass\n")
        (tmp_path / "file2.py").write_text("other code\n")

        res = fs_search_text("secret_function", search_path=str(tmp_path))
        assert res["status"] == "ok"
        assert res["match_count"] == 1
        assert "my_secret_function" in res["matches"][0]["line_content"]

    def test_git_operations(self, tmp_path: Path) -> None:
        import subprocess

        # Initialize isolated git repo
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=tmp_path, capture_output=True, check=True)

        (tmp_path / "file.txt").write_text("initial commit")
        subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=tmp_path, capture_output=True, check=True)

        # Test git status
        st = git_status(str(tmp_path))
        assert st["status"] == "ok"
        assert "branch" in st

        # Modify file and test git diff
        (tmp_path / "file.txt").write_text("modified content")
        diff = git_diff(str(tmp_path))
        assert diff["status"] == "ok"
        assert "modified content" in diff["diff"]

        # Test git log
        log = git_log(str(tmp_path), max_commits=3)
        assert log["status"] == "ok"
        assert len(log["commits"]) >= 1
