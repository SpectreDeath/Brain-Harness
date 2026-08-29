"""Filesystem and Git Workspace Service protocol, models, and ServiceKey."""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, Field
import structlog

from harness.kernel.context import ServiceKey

logger = structlog.get_logger()


class FileReadResult(BaseModel):
    """Result of reading file content."""

    status: str = Field(default="ok", description="Status indicator")
    path: str = Field(default="", description="Resolved file path")
    total_lines: int = Field(default=0, description="Total line count in file")
    start_line: int = Field(default=0, description="Start line of sliced window")
    end_line: int = Field(default=0, description="End line of sliced window")
    content: str = Field(default="", description="Sliced text content")
    error: str | None = Field(default=None, description="Error details if read failed")


class FileWriteResult(BaseModel):
    """Result of writing file content."""

    status: str = Field(default="ok", description="Status indicator")
    path: str = Field(default="", description="Target file path")
    bytes_written: int = Field(default=0, description="Count of bytes written")
    error: str | None = Field(default=None, description="Error details if write failed")


class DirListResult(BaseModel):
    """Result of directory listing."""

    status: str = Field(default="ok", description="Status indicator")
    root: str = Field(default="", description="Root directory path")
    count: int = Field(default=0, description="Count of discovered file/dir entries")
    entries: list[dict[str, Any]] = Field(default_factory=list, description="List of directory entries")
    error: str | None = Field(default=None, description="Error details if listing failed")


class SearchResult(BaseModel):
    """Result of pattern searching across text files."""

    status: str = Field(default="ok", description="Status indicator")
    pattern: str = Field(default="", description="Queried search regex pattern")
    match_count: int = Field(default=0, description="Total matching lines found")
    matches: list[dict[str, Any]] = Field(default_factory=list, description="Matching line entries with file and line numbers")
    error: str | None = Field(default=None, description="Error details if search failed")


class GitStatusResult(BaseModel):
    """Result of querying git status."""

    status: str = Field(default="ok", description="Status indicator")
    branch: str = Field(default="", description="Current active branch name")
    dirty: bool = Field(default=False, description="True if uncommitted changes exist")
    changed_files_count: int = Field(default=0, description="Count of changed files")
    changes: list[str] = Field(default_factory=list, description="List of changed file paths")
    error: str | None = Field(default=None, description="Error details if command failed")


class GitDiffResult(BaseModel):
    """Result of querying git diff."""

    status: str = Field(default="ok", description="Status indicator")
    diff: str = Field(default="", description="Unified diff output")
    error: str | None = Field(default=None, description="Error details if command failed")


class GitLogResult(BaseModel):
    """Result of querying git log history."""

    status: str = Field(default="ok", description="Status indicator")
    count: int = Field(default=0, description="Count of retrieved commits")
    commits: list[dict[str, str]] = Field(default_factory=list, description="Commit records with hash, author, date, subject")
    error: str | None = Field(default=None, description="Error details if command failed")


class GitCommitResult(BaseModel):
    """Result of committing a transactional workspace change."""

    status: str = Field(default="ok", description="Status indicator (ok, error, clean)")
    commit_hash: str | None = Field(default=None, description="Created commit hash if committed")
    message: str = Field(default="", description="Commit message used")
    files_committed: int = Field(default=0, description="Number of changed files committed")
    error: str | None = Field(default=None, description="Error details if commit failed")


class GitRollbackResult(BaseModel):
    """Result of rolling back uncommitted or failed workspace changes."""

    status: str = Field(default="ok", description="Status indicator")
    files_reverted: list[str] = Field(default_factory=list, description="Reverted file paths")
    target_hash: str | None = Field(default=None, description="Target hash reset to if specified")
    error: str | None = Field(default=None, description="Error details if rollback failed")


@runtime_checkable
class FilesystemGitService(Protocol):
    """Protocol for filesystem operations and Git version control."""

    def read_file(
        self,
        path: str,
        start_line: int | None = None,
        end_line: int | None = None,
    ) -> FileReadResult:
        """Read file content with optional line-slice."""
        ...

    def write_file(
        self,
        path: str,
        content: str,
        overwrite: bool = False,
    ) -> FileWriteResult:
        """Write or overwrite text content to a file."""
        ...

    def list_dir(
        self,
        path: str = ".",
        max_depth: int = 2,
    ) -> DirListResult:
        """List directory contents recursively up to max_depth."""
        ...

    def search_text(
        self,
        pattern: str,
        search_path: str = ".",
        case_sensitive: bool = False,
    ) -> SearchResult:
        """Search for pattern across text files."""
        ...

    def git_status(self, repo_path: str = ".") -> GitStatusResult:
        """Get status of the git repository."""
        ...

    def git_diff(self, repo_path: str = ".", target: str | None = None) -> GitDiffResult:
        """Get git diff."""
        ...

    def git_log(self, repo_path: str = ".", max_commits: int = 10) -> GitLogResult:
        """Get git commit history."""
        ...

    def commit_transaction(
        self,
        message: str,
        repo_path: str = ".",
        author: str = "Harness Agent <agent@harness.local>",
    ) -> GitCommitResult:
        """Stage all modified tracked/untracked workspace files and commit with message."""
        ...

    def rollback_transaction(
        self,
        repo_path: str = ".",
        target_hash: str | None = None,
    ) -> GitRollbackResult:
        """Discard uncommitted modifications and restore clean workspace state."""
        ...

    def get_uncommitted_diff(self, repo_path: str = ".") -> GitDiffResult:
        """Retrieve unified diff of all uncommitted workspace changes."""
        ...


FILESYSTEM_GIT_KEY: ServiceKey[FilesystemGitService] = ServiceKey("service.filesystem_git")


class DefaultFilesystemGitService:
    """Default standard implementation of FilesystemGitService."""

    def read_file(
        self,
        path: str,
        start_line: int | None = None,
        end_line: int | None = None,
    ) -> FileReadResult:
        p = Path(path)
        if not p.exists() or not p.is_file():
            return FileReadResult(status="error", path=path, error=f"File not found: {path}")
        try:
            lines = p.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
            total = len(lines)
            s = max(1, start_line or 1)
            e = min(total, end_line or total)
            content = "".join(lines[s - 1 : e])
            return FileReadResult(status="ok", path=str(p), total_lines=total, start_line=s, end_line=e, content=content)
        except Exception as err:
            return FileReadResult(status="error", path=path, error=str(err))

    def write_file(
        self,
        path: str,
        content: str,
        overwrite: bool = False,
    ) -> FileWriteResult:
        p = Path(path)
        if p.exists() and not overwrite:
            return FileWriteResult(status="error", path=path, error="File exists and overwrite is False")
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            bytes_written = p.write_text(content, encoding="utf-8")
            return FileWriteResult(status="ok", path=str(p), bytes_written=bytes_written)
        except Exception as err:
            return FileWriteResult(status="error", path=path, error=str(err))

    def list_dir(self, path: str = ".", max_depth: int = 2) -> DirListResult:
        p = Path(path)
        if not p.exists() or not p.is_dir():
            return DirListResult(status="error", root=path, error=f"Directory not found: {path}")
        try:
            entries: list[dict[str, Any]] = []
            for root, dirs, files in os.walk(path):
                rel = os.path.relpath(root, path)
                depth = 0 if rel == "." else rel.count(os.sep) + 1
                if depth > max_depth:
                    dirs.clear()
                    continue
                for d in dirs:
                    entries.append({"name": d, "type": "directory", "rel_path": os.path.join(rel, d)})
                for f in files:
                    entries.append({"name": f, "type": "file", "rel_path": os.path.join(rel, f)})
            return DirListResult(status="ok", root=str(p), count=len(entries), entries=entries)
        except Exception as err:
            return DirListResult(status="error", root=path, error=str(err))

    def search_text(self, pattern: str, search_path: str = ".", case_sensitive: bool = False) -> SearchResult:
        flags = 0 if case_sensitive else re.IGNORECASE
        try:
            compiled = re.compile(pattern, flags)
            matches: list[dict[str, Any]] = []
            for root, _, files in os.walk(search_path):
                for f in files:
                    full = os.path.join(root, f)
                    try:
                        with open(full, "r", encoding="utf-8", errors="ignore") as fp:
                            for idx, line in enumerate(fp, start=1):
                                if compiled.search(line):
                                    matches.append({"file": full, "line": idx, "content": line.strip()})
                    except Exception:
                        pass
            return SearchResult(status="ok", pattern=pattern, match_count=len(matches), matches=matches)
        except Exception as err:
            return SearchResult(status="error", pattern=pattern, error=str(err))

    def _run_git(self, args: list[str], repo_path: str = ".") -> tuple[int, str, str]:
        res = subprocess.run(["git", *args], cwd=repo_path, capture_output=True, text=True, check=False)
        return res.returncode, res.stdout, res.stderr

    def git_status(self, repo_path: str = ".") -> GitStatusResult:
        code, out, err = self._run_git(["status", "--porcelain", "-b"], repo_path)
        if code != 0:
            return GitStatusResult(status="error", error=err or "git status failed")
        lines = out.strip().splitlines()
        branch = lines[0].replace("##", "").strip() if lines else "unknown"
        changes = [line[3:].strip() for line in lines[1:] if len(line) > 3]
        return GitStatusResult(status="ok", branch=branch, dirty=len(changes) > 0, changed_files_count=len(changes), changes=changes)

    def git_diff(self, repo_path: str = ".", target: str | None = None) -> GitDiffResult:
        args = ["diff"]
        if target:
            args.append(target)
        code, out, err = self._run_git(args, repo_path)
        if code != 0:
            return GitDiffResult(status="error", error=err or "git diff failed")
        return GitDiffResult(status="ok", diff=out)

    def git_log(self, repo_path: str = ".", max_commits: int = 10) -> GitLogResult:
        code, out, err = self._run_git(["log", f"-n{max_commits}", "--pretty=format:%H|%an|%ad|%s"], repo_path)
        if code != 0:
            return GitLogResult(status="error", error=err or "git log failed")
        commits: list[dict[str, str]] = []
        for line in out.strip().splitlines():
            parts = line.split("|", 3)
            if len(parts) == 4:
                commits.append({"hash": parts[0], "author": parts[1], "date": parts[2], "subject": parts[3]})
        return GitLogResult(status="ok", count=len(commits), commits=commits)

    def commit_transaction(
        self,
        message: str,
        repo_path: str = ".",
        author: str = "Harness Agent <agent@harness.local>",
    ) -> GitCommitResult:
        # Check if dirty
        status = self.git_status(repo_path)
        if status.status != "ok":
            return GitCommitResult(status="error", error=status.error)
        if not status.dirty:
            return GitCommitResult(status="clean", message=message, files_committed=0)

        # Stage and commit
        add_code, _, add_err = self._run_git(["add", "-A"], repo_path)
        if add_code != 0:
            return GitCommitResult(status="error", error=f"git add failed: {add_err}")

        commit_code, commit_out, commit_err = self._run_git(
            ["commit", f"--author={author}", "-m", message],
            repo_path,
        )
        if commit_code != 0:
            return GitCommitResult(status="error", error=f"git commit failed: {commit_err}")

        # Get latest commit hash
        hash_code, hash_out, _ = self._run_git(["rev-parse", "HEAD"], repo_path)
        commit_hash = hash_out.strip() if hash_code == 0 else None

        return GitCommitResult(
            status="ok",
            commit_hash=commit_hash,
            message=message,
            files_committed=status.changed_files_count,
        )

    def rollback_transaction(
        self,
        repo_path: str = ".",
        target_hash: str | None = None,
    ) -> GitRollbackResult:
        # Revert uncommitted changes
        status = self.git_status(repo_path)
        reverted_files = status.changes if status.status == "ok" else []

        if target_hash:
            code, _, err = self._run_git(["reset", "--hard", target_hash], repo_path)
            if code != 0:
                return GitRollbackResult(status="error", error=f"git reset failed: {err}")
        else:
            self._run_git(["restore", "--staged", "."], repo_path)
            self._run_git(["restore", "."], repo_path)
            self._run_git(["clean", "-fd"], repo_path)

        return GitRollbackResult(status="ok", files_reverted=reverted_files, target_hash=target_hash)

    def get_uncommitted_diff(self, repo_path: str = ".") -> GitDiffResult:
        return self.git_diff(repo_path)


__all__ = [
    "DefaultFilesystemGitService",
    "DirListResult",
    "FILESYSTEM_GIT_KEY",
    "FileReadResult",
    "FileWriteResult",
    "FilesystemGitService",
    "GitCommitResult",
    "GitDiffResult",
    "GitLogResult",
    "GitRollbackResult",
    "GitStatusResult",
    "SearchResult",
]
