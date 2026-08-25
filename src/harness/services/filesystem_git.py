"""Filesystem and Git Workspace Service protocol, models, and ServiceKey."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable
from pydantic import BaseModel, Field

from harness.kernel.context import ServiceKey


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


FILESYSTEM_GIT_KEY: ServiceKey[FilesystemGitService] = ServiceKey("service.filesystem_git")
