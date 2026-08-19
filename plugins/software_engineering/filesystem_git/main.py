"""Filesystem & Git tools for Brain Harness autonomous agents."""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from typing import Any


def fs_read_file(path: str, start_line: int | None = None, end_line: int | None = None) -> dict[str, Any]:
    """Read file content with optional line-slice."""
    try:
        p = Path(path).resolve()
        if not p.exists():
            return {"status": "error", "error": f"File not found: {path}"}
        if not p.is_file():
            return {"status": "error", "error": f"Path is not a file: {path}"}

        lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
        total_lines = len(lines)

        s_idx = max(0, (start_line - 1)) if start_line is not None else 0
        e_idx = min(total_lines, end_line) if end_line is not None else total_lines

        sliced_content = "\n".join(lines[s_idx:e_idx])
        return {
            "status": "ok",
            "path": str(p),
            "total_lines": total_lines,
            "start_line": s_idx + 1 if total_lines > 0 else 0,
            "end_line": e_idx,
            "content": sliced_content,
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


def fs_write_file(path: str, content: str, overwrite: bool = False) -> dict[str, Any]:
    """Write or overwrite text content to a file."""
    try:
        p = Path(path).resolve()
        if p.exists() and not overwrite:
            return {
                "status": "error",
                "error": f"File already exists: {path}. Set overwrite=true to replace.",
            }

        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return {
            "status": "ok",
            "path": str(p),
            "bytes_written": len(content.encode("utf-8")),
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


def fs_list_dir(path: str = ".", max_depth: int = 2) -> dict[str, Any]:
    """List directory contents recursively up to max_depth."""
    try:
        root = Path(path).resolve()
        if not root.exists():
            return {"status": "error", "error": f"Directory not found: {path}"}
        if not root.is_dir():
            return {"status": "error", "error": f"Path is not a directory: {path}"}

        entries: list[dict[str, Any]] = []

        def _scan(current: Path, depth: int) -> None:
            if depth > max_depth:
                return
            for item in sorted(current.iterdir()):
                # skip hidden dot folders like .git, .venv
                if item.name.startswith(".") and item.name in (".git", ".venv", ".pytest_cache", ".ruff_cache", ".mypy_cache"):
                    continue
                is_directory = item.is_dir()
                entry: dict[str, Any] = {
                    "name": item.name,
                    "rel_path": str(item.relative_to(root)),
                    "is_dir": is_directory,
                }
                if is_directory:
                    try:
                        entry["children_count"] = len(list(item.iterdir()))
                    except Exception:
                        entry["children_count"] = 0
                    entries.append(entry)
                    _scan(item, depth + 1)
                else:
                    try:
                        entry["size_bytes"] = item.stat().st_size
                    except Exception:
                        entry["size_bytes"] = 0
                    entries.append(entry)

        _scan(root, 1)
        return {"status": "ok", "root": str(root), "count": len(entries), "entries": entries}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def fs_search_text(pattern: str, search_path: str = ".", case_sensitive: bool = False) -> dict[str, Any]:
    """Search for pattern across text files."""
    try:
        root = Path(search_path).resolve()
        if not root.exists():
            return {"status": "error", "error": f"Search path not found: {search_path}"}

        flags = 0 if case_sensitive else re.IGNORECASE
        regex = re.compile(pattern, flags)
        matches: list[dict[str, Any]] = []

        for current_root, dirs, files in os.walk(root):
            # prune ignored directories
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("__pycache__", "node_modules", "venv", ".venv")]

            for file_name in files:
                file_path = Path(current_root) / file_name
                try:
                    text = file_path.read_text(encoding="utf-8", errors="ignore")
                except (OSError, UnicodeDecodeError):
                    continue

                for line_no, line in enumerate(text.splitlines(), start=1):
                    if regex.search(line):
                        matches.append({
                            "file": str(file_path.relative_to(root)),
                            "line_number": line_no,
                            "line_content": line.strip()[:200],
                        })
                        if len(matches) >= 50:
                            break
                if len(matches) >= 50:
                    break

        return {"status": "ok", "pattern": pattern, "match_count": len(matches), "matches": matches}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def git_status(repo_path: str = ".") -> dict[str, Any]:
    """Get status of the git repository."""
    try:
        res = subprocess.run(
            ["git", "status", "--porcelain=v1", "-b"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode != 0:
            return {"status": "error", "error": res.stderr.strip() or "Git command failed"}

        lines = res.stdout.splitlines()
        branch_line = lines[0] if lines else "## unknown"
        modified_files = [line.strip() for line in lines[1:] if line.strip()]

        return {
            "status": "ok",
            "branch": branch_line.lstrip("# ").strip(),
            "dirty": len(modified_files) > 0,
            "changed_files_count": len(modified_files),
            "changes": modified_files,
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


def git_diff(repo_path: str = ".", target: str | None = None) -> dict[str, Any]:
    """Get git diff."""
    try:
        cmd = ["git", "diff"]
        if target:
            cmd.append(target)

        res = subprocess.run(
            cmd,
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode != 0:
            return {"status": "error", "error": res.stderr.strip() or "Git diff failed"}

        return {"status": "ok", "diff": res.stdout}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def git_log(repo_path: str = ".", max_commits: int = 10) -> dict[str, Any]:
    """Get git commit history."""
    try:
        res = subprocess.run(
            ["git", "log", f"-n{max_commits}", "--pretty=format:%H|%an|%ad|%s", "--date=short"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode != 0:
            return {"status": "error", "error": res.stderr.strip() or "Git log failed"}

        commits: list[dict[str, str]] = []
        for line in res.stdout.splitlines():
            parts = line.split("|", 3)
            if len(parts) == 4:
                commits.append({
                    "hash": parts[0],
                    "author": parts[1],
                    "date": parts[2],
                    "subject": parts[3],
                })

        return {"status": "ok", "count": len(commits), "commits": commits}
    except Exception as e:
        return {"status": "error", "error": str(e)}
