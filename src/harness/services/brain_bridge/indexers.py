"""Text, transcript, and git commit indexers for Brain Bridge."""

from __future__ import annotations

from collections import defaultdict
import json
import os
from pathlib import Path
import shutil
import subprocess
from typing import Any

from .tokenizers import DEFAULT_CODE_EXTS, SPECIAL_FILENAMES, tokenize_text


def index_text_files(
    root: Path,
    target_exts: set[str] | None = None,
    chunk_lines: int = 30,
) -> tuple[list[dict[str, Any]], dict[str, int], list[str], list[str]]:
    """Scan and chunk text and code files, returning chunks, doc_freq, detected languages, and manifests."""
    if target_exts is None:
        target_exts = DEFAULT_CODE_EXTS

    chunks: list[dict[str, Any]] = []
    doc_freq: dict[str, int] = defaultdict(int)
    languages_seen: set[str] = set()
    manifests_found: list[str] = []

    manifest_names = {
        "pyproject.toml", "package.json", "cargo.toml", "go.mod", "pom.xml",
        "build.gradle", "cmakelists.txt", "requirements.txt", "setup.py",
        "gemfile", "dockerfile", "agents.md", "claude.md",
    }

    for current_root, dirs, files in os.walk(root):
        dirs[:] = [
            d for d in dirs
            if not d.startswith(".") and d not in ("__pycache__", "venv", ".venv", "node_modules", "target", "dist", "build", ".git")
        ]
        for file_name in files:
            file_path = Path(current_root) / file_name
            ext = file_path.suffix.lower()
            lower_name = file_name.lower()

            if lower_name in manifest_names:
                manifests_found.append(str(file_path.relative_to(root)))

            is_valid_ext = ext in target_exts
            is_special = lower_name in SPECIAL_FILENAMES

            if not (is_valid_ext or is_special):
                continue

            if ext:
                languages_seen.add(ext.lstrip("."))

            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
            except (OSError, UnicodeDecodeError):
                continue

            lines = content.splitlines()
            if not lines:
                continue

            step = max(10, chunk_lines - 5)
            for i in range(0, len(lines), step):
                chunk_slice = lines[i : i + chunk_lines]
                if not chunk_slice:
                    continue
                chunk_text = "\n".join(chunk_slice)
                tokens = tokenize_text(chunk_text)
                if not tokens:
                    continue

                chunk_obj = {
                    "id": len(chunks),
                    "file": str(file_path.relative_to(root)),
                    "start_line": i + 1,
                    "end_line": min(len(lines), i + len(chunk_slice)),
                    "content": chunk_text,
                    "tokens": tokens,
                    "type": "document_chunk",
                }
                chunks.append(chunk_obj)
                for term in set(tokens):
                    doc_freq[term] += 1

    return chunks, doc_freq, sorted(languages_seen), sorted(manifests_found)


def parse_transcripts(root: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, int]]:
    """Parse transcript JSONL files for conversational and trajectory memory."""
    transcript_files: list[Path] = []
    if (root / "transcript.jsonl").exists():
        transcript_files.append(root / "transcript.jsonl")
    transcript_files.extend(root.glob("**/.system_generated/logs/transcript*.jsonl"))
    transcript_files.extend(root.glob("**/transcript*.jsonl"))

    unique_paths = list({p.resolve(): p for p in transcript_files}.values())
    chunks: list[dict[str, Any]] = []
    trajectories: list[dict[str, Any]] = []
    doc_freq: dict[str, int] = defaultdict(int)

    for tf in unique_paths:
        try:
            with tf.open("r", encoding="utf-8", errors="ignore") as f:
                for line_idx, line in enumerate(f):
                    line_str = line.strip()
                    if not line_str:
                        continue
                    try:
                        record = json.loads(line_str)
                    except json.JSONDecodeError:
                        continue

                    step_type = record.get("type", "UNKNOWN")
                    content = record.get("content", "")
                    tool_calls = record.get("tool_calls", [])

                    traj_entry = {
                        "file": str(tf.relative_to(root) if tf.is_relative_to(root) else tf.name),
                        "step_index": record.get("step_index", line_idx),
                        "type": step_type,
                        "status": record.get("status", "OK"),
                        "summary": str(content)[:200] if content else "",
                    }
                    trajectories.append(traj_entry)

                    text_blob = f"Type: {step_type}\nContent: {content}\nTools: {json.dumps(tool_calls)}"
                    tokens = tokenize_text(text_blob)
                    if tokens:
                        chunk_obj = {
                            "id": len(chunks),
                            "file": traj_entry["file"],
                            "start_line": line_idx + 1,
                            "end_line": line_idx + 1,
                            "content": text_blob[:800],
                            "tokens": tokens,
                            "type": "transcript_step",
                            "step_index": traj_entry["step_index"],
                        }
                        chunks.append(chunk_obj)
                        for term in set(tokens):
                            doc_freq[term] += 1
        except (OSError, UnicodeDecodeError):
            continue

    return chunks, trajectories, doc_freq


def parse_git_commits(
    root: Path, max_commits: int = 100
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, int], str | None]:
    """Parse git commit log into historical trajectory chunks."""
    chunks: list[dict[str, Any]] = []
    trajectories: list[dict[str, Any]] = []
    doc_freq: dict[str, int] = defaultdict(int)
    branch_name: str | None = None

    git_dir = root / ".git"
    if not git_dir.exists():
        return chunks, trajectories, doc_freq, branch_name

    if not shutil.which("git"):
        return chunks, trajectories, doc_freq, branch_name

    try:
        branch_proc = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        )
        if branch_proc.returncode == 0:
            branch_name = branch_proc.stdout.strip()

        delimiter = "---GIT_COMMIT_RECORD_DELIMITER---"
        log_proc = subprocess.run(
            [
                "git",
                "-C",
                str(root),
                "log",
                f"-n{max_commits}",
                f"--pretty=format:{delimiter}%n%H%n%an%n%ad%n%s%n%b",
                "--stat",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if log_proc.returncode != 0 or not log_proc.stdout:
            return chunks, trajectories, doc_freq, branch_name

        raw_commits = log_proc.stdout.split(delimiter)
        for commit_idx, block in enumerate(raw_commits):
            block = block.strip()
            if not block:
                continue

            lines = block.splitlines()
            if len(lines) < 4:
                continue

            commit_hash = lines[0].strip()
            author = lines[1].strip()
            date = lines[2].strip()
            subject = lines[3].strip()
            body_and_stat = "\n".join(lines[4:]).strip()

            short_hash = commit_hash[:8]
            traj_entry = {
                "file": f"git:commit:{short_hash}",
                "step_index": commit_idx,
                "type": "GIT_COMMIT",
                "status": "COMMITTED",
                "commit_hash": commit_hash,
                "author": author,
                "date": date,
                "summary": subject,
            }
            trajectories.append(traj_entry)

            content_text = (
                f"Commit: {short_hash} ({commit_hash})\n"
                f"Author: {author}\n"
                f"Date: {date}\n"
                f"Subject: {subject}\n"
                f"{body_and_stat}"
            )
            tokens = tokenize_text(content_text)
            if tokens:
                chunk_obj = {
                    "id": len(chunks),
                    "file": f"git:commit:{short_hash}",
                    "start_line": 1,
                    "end_line": len(lines),
                    "content": content_text[:1200],
                    "tokens": tokens,
                    "type": "git_commit",
                    "commit_hash": commit_hash,
                    "author": author,
                    "date": date,
                    "subject": subject,
                }
                chunks.append(chunk_obj)
                for term in set(tokens):
                    doc_freq[term] += 1

    except Exception:
        pass

    return chunks, trajectories, doc_freq, branch_name
