"""VCS history mining and directory structure overview."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any
import structlog

logger = structlog.get_logger(__name__)


def history_scan(
    repo_path: str, max_commits: int = 100, pattern_filter: str = ""
) -> dict[str, Any]:
    """Mine VCS repository history for historical vulnerabilities and security fixes."""
    target = Path(repo_path)
    if not target.exists():
        return {
            "status": "error",
            "error": f"Repository path '{repo_path}' does not exist.",
        }

    keywords = [
        "fix", "cve", "vuln", "security", "patch", "overflow", "sanitize", "bypass", "exploit",
    ]
    if pattern_filter:
        keywords.append(pattern_filter.lower())

    commits: list[dict[str, Any]] = []
    try:
        cmd = [
            "git", "-C", str(target), "log", f"-n{max_commits}",
            "--pretty=format:%H|%an|%ad|%s", "--date=short",
        ]
        res = subprocess.run(
            cmd, capture_output=True, text=True, encoding="utf-8", errors="replace"
        )
        if res.returncode == 0:
            for line in res.stdout.strip().splitlines():
                if "|" in line:
                    parts = line.split("|", 3)
                    commit_hash = parts[0]
                    author = parts[1]
                    date = parts[2]
                    msg = parts[3] if len(parts) > 3 else ""
                    msg_lower = msg.lower()
                    matched_keys = [k for k in keywords if k in msg_lower]
                    if matched_keys:
                        commits.append({
                            "hash": commit_hash,
                            "author": author,
                            "date": date,
                            "subject": msg,
                            "matched_keywords": matched_keys,
                        })
    except Exception as e:
        logger.warning("git_history_scan_error", error=str(e))
        return {"status": "error", "error": f"Git inspection failed: {e!s}"}

    return {
        "status": "ok",
        "repo_path": str(target),
        "total_commits_scanned": max_commits,
        "security_commits_found": len(commits),
        "historical_learnings": commits,
    }


def directory_summary(dir_path: str, recursive: bool = True) -> dict[str, Any]:
    """Generate hierarchical security directory map."""
    p = Path(dir_path)
    if not p.exists():
        return {"status": "error", "error": f"Path '{dir_path}' does not exist."}

    code_exts = {".py", ".c", ".cpp", ".h", ".hpp", ".go", ".rs", ".js", ".ts", ".java"}
    config_exts = {".json", ".yaml", ".yml", ".toml", ".ini", ".xml"}

    code_files: list[str] = []
    config_files: list[str] = []
    doc_files: list[str] = []
    total_lines = 0

    pattern = "**/*" if recursive else "*"
    for item in p.glob(pattern):
        if item.is_file() and not any(part.startswith(".") for part in item.parts):
            ext = item.suffix.lower()
            rel = item.relative_to(p).as_posix()
            if ext in code_exts:
                code_files.append(rel)
            elif ext in config_exts:
                config_files.append(rel)
            elif ext in {".md", ".rst", ".txt"}:
                doc_files.append(rel)

            try:
                total_lines += len(
                    item.read_text(encoding="utf-8", errors="ignore").splitlines()
                )
            except Exception:
                pass

    return {
        "status": "ok",
        "root_directory": str(p),
        "code_files_count": len(code_files),
        "config_files_count": len(config_files),
        "doc_files_count": len(doc_files),
        "total_estimated_lines": total_lines,
        "code_files": code_files[:100],
        "config_files": config_files[:50],
    }
