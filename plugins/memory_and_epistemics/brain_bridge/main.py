"""Federated Brain Bridge & Repository Attachment Plugin for Brain Harness."""

from __future__ import annotations

import asyncio
import json
import math
import os
import re
import shutil
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
import structlog

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.brain_bridge import (
    BRAIN_BRIDGE_KEY,
    BrainAttachResult,
    BrainBridgeService,
    BrainDetachResult,
    BrainListResult,
    BrainQueryResult,
)

logger = structlog.get_logger(__name__)

DEFAULT_CODE_EXTS: set[str] = {
    # Source languages
    ".py", ".ts", ".tsx", ".js", ".jsx", ".rs", ".go", ".java", ".cpp", ".c", ".h", ".hpp",
    ".cs", ".rb", ".php", ".swift", ".kt", ".kts", ".scala", ".sh", ".bash", ".ps1", ".bat",
    ".sql", ".graphql", ".gql", ".proto", ".lua", ".r", ".dart", ".zig", ".nim",
    # Manifests and configs
    ".yaml", ".yml", ".json", ".toml", ".ini", ".cfg", ".xml", ".env.example",
    # Documentation & specs
    ".md", ".rst", ".txt", ".adoc", ".tex"
}

SPECIAL_FILENAMES: set[str] = {
    "dockerfile", "makefile", "containerfile", "procfile", "gemfile", "rakefile", "license"
}


def _tokenize(text: str) -> list[str]:
    """Tokenize text into lowercase alphanumeric words and subwords."""
    words = re.findall(r"[A-Z]?[a-z0-9]+|[A-Z]+(?=[A-Z][a-z]|\d|\W|$)|\w+", text)
    tokens: list[str] = []
    for w in words:
        low = w.lower()
        if len(low) > 1:
            tokens.append(low)
    return tokens


def _compute_vector(tokens: list[str], doc_freq: dict[str, int], total_docs: int) -> dict[str, float]:
    """Compute normalized TF-IDF vector for tokens."""
    tf = Counter(tokens)
    vec: dict[str, float] = {}
    norm_sq = 0.0

    for term, count in tf.items():
        tf_weight = 1.0 + math.log(count)
        idf_weight = math.log((total_docs + 1.0) / (doc_freq.get(term, 0) + 1.0)) + 1.0
        weight = tf_weight * idf_weight
        vec[term] = weight
        norm_sq += weight * weight

    norm = math.sqrt(norm_sq) if norm_sq > 0 else 1.0
    for term in vec:
        vec[term] /= norm

    return vec


def _is_git_url(path_or_url: str) -> bool:
    """Check if the given string is a remote Git repository URL."""
    low = path_or_url.strip().lower()
    if low.startswith(("http://", "https://", "git@", "git://", "ssh://")):
        return True
    if low.endswith(".git"):
        return True
    return False


def _detect_brain_format(root: Path) -> str:
    """Detect format of the external brain, repository, or knowledge store."""
    if (root / ".system_generated" / "logs").exists() or (root / "transcript.jsonl").exists():
        return "antigravity_brain"
    if any(root.glob("**/transcript.jsonl")):
        return "antigravity_brain"
    if (root / ".harness").exists() or (root / "src" / "harness").exists():
        return "harness_instance"
    if (root / ".claude").exists() or (root / ".cursor").exists() or (root / ".cursorrules").exists():
        return "ide_memo"
    if (root / ".obsidian").exists():
        return "obsidian_vault"
    # Check for git repository
    if (root / ".git").exists():
        return "git_repository"
    # Check for markdown density with wikilinks
    md_files = list(root.glob("*.md"))[:10]
    for md in md_files:
        try:
            content = md.read_text(encoding="utf-8", errors="ignore")
            if "[[" in content and "]]" in content:
                return "obsidian_vault"
        except (OSError, UnicodeDecodeError):
            pass
    # Check for code repository manifest files
    manifest_markers = ["pyproject.toml", "package.json", "Cargo.toml", "go.mod", "pom.xml", "build.gradle", "CMakeLists.txt"]
    if any((root / marker).exists() for marker in manifest_markers):
        return "git_repository"
    return "raw_docs"


def _index_text_files(
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
        "gemfile", "dockerfile", "agents.md", "claude.md"
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
                tokens = _tokenize(chunk_text)
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


def _parse_transcripts(root: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, int]]:
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
                        "status": record.get("status", "DONE"),
                        "tool_names": [tc.get("name") if isinstance(tc, dict) else str(tc) for tc in tool_calls] if tool_calls else [],
                        "summary": str(content)[:200] if content else "",
                    }
                    trajectories.append(traj_entry)

                    text_blob = f"Type: {step_type}\nContent: {content}\nTools: {json.dumps(tool_calls)}"
                    tokens = _tokenize(text_blob)
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


def _parse_git_commits(
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
            tokens = _tokenize(content_text)
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


def _clone_remote_repo(url: str, alias: str) -> tuple[Path | None, str | None]:
    """Clone a remote git repository into the local cache directory."""
    if not shutil.which("git"):
        return None, "git executable not found in PATH"

    cache_dir = Path.home() / ".harness" / "cache" / "repos" / alias
    cache_dir.parent.mkdir(parents=True, exist_ok=True)

    if cache_dir.exists():
        try:
            pull_res = subprocess.run(
                ["git", "-C", str(cache_dir), "pull"],
                capture_output=True,
                text=True,
                check=False,
            )
            if pull_res.returncode == 0:
                return cache_dir, None
        except Exception:
            pass

    if cache_dir.exists():
        try:
            shutil.rmtree(cache_dir, ignore_errors=True)
        except Exception:
            pass

    try:
        clone_proc = subprocess.run(
            ["git", "clone", "--depth", "50", url, str(cache_dir)],
            capture_output=True,
            text=True,
            check=False,
        )
        if clone_proc.returncode != 0:
            return None, f"Git clone failed: {clone_proc.stderr.strip()}"
        return cache_dir, None
    except Exception as exc:
        return None, f"Failed to clone repository: {exc}"


class BrainBridgeEngine:
    """Encapsulated engine managing external brain and repository attachments."""

    def __init__(self) -> None:
        self._mounts: dict[str, dict[str, Any]] = {}

    def attach(
        self,
        folder_path: str,
        alias: str | None = None,
        read_transcripts: bool = True,
        read_commits: bool = True,
        max_commits: int = 100,
        attach_mode: str = "lens",
    ) -> dict[str, Any]:
        is_remote = _is_git_url(folder_path)
        if is_remote:
            default_alias = folder_path.rstrip("/").split("/")[-1].replace(".git", "").lower()
            mount_alias = alias or default_alias or "remote_repo"
            root, clone_err = _clone_remote_repo(folder_path, mount_alias)
            if not root or clone_err:
                return {"status": "error", "error": f"Failed to attach remote repository: {clone_err}"}
        else:
            root = Path(folder_path).resolve()
            if not root.exists() or not root.is_dir():
                return {"status": "error", "error": f"Directory not found: {folder_path}"}
            mount_alias = alias or root.name.lower().replace(" ", "_").replace("-", "_")

        detected_format = _detect_brain_format(root)
        doc_chunks, doc_freq, detected_languages, manifests = _index_text_files(root)

        transcript_chunks: list[dict[str, Any]] = []
        trajectories: list[dict[str, Any]] = []
        if read_transcripts:
            transcript_chunks, t_trajs, t_doc_freq = _parse_transcripts(root)
            trajectories.extend(t_trajs)
            for term, cnt in t_doc_freq.items():
                doc_freq[term] += cnt

        git_chunks: list[dict[str, Any]] = []
        branch_name: str | None = None
        if read_commits:
            git_chunks, g_trajs, g_doc_freq, branch_name = _parse_git_commits(root, max_commits=max_commits)
            trajectories.extend(g_trajs)
            for term, cnt in g_doc_freq.items():
                doc_freq[term] += cnt

        all_chunks = doc_chunks + transcript_chunks + git_chunks
        for idx, c in enumerate(all_chunks):
            c["id"] = idx

        total_docs = len(all_chunks)
        for c in all_chunks:
            c["vector"] = _compute_vector(c["tokens"], doc_freq, total_docs)

        summary = {
            "format": detected_format,
            "mode": attach_mode,
            "total_chunks": len(all_chunks),
            "document_chunks": len(doc_chunks),
            "transcript_chunks": len(transcript_chunks),
            "git_commit_chunks": len(git_chunks),
            "trajectories_recorded": len(trajectories),
            "unique_terms": len(doc_freq),
            "detected_languages": detected_languages,
            "manifest_files": manifests,
            "branch": branch_name,
            "is_remote": is_remote,
        }

        self._mounts[mount_alias] = {
            "alias": mount_alias,
            "path": str(root),
            "original_source": folder_path,
            "format": detected_format,
            "mode": attach_mode,
            "chunks": all_chunks,
            "doc_freq": doc_freq,
            "total_docs": total_docs,
            "trajectories": trajectories,
            "summary": summary,
        }

        return {
            "status": "ok",
            "alias": mount_alias,
            "path": str(root),
            "original_source": folder_path,
            "detected_format": detected_format,
            "mode": attach_mode,
            "summary": summary,
        }

    def query(
        self,
        query: str,
        brain_alias: str | None = None,
        include_trajectories: bool = True,
        top_k: int = 5,
    ) -> dict[str, Any]:
        if not self._mounts:
            return {"status": "ok", "query": query, "results_count": 0, "results": [], "note": "No brains or repositories attached. Run brain_attach first."}

        targets = [self._mounts[brain_alias]] if brain_alias and brain_alias in self._mounts else list(self._mounts.values())
        if brain_alias and brain_alias not in self._mounts:
            return {"status": "error", "error": f"Attached brain alias '{brain_alias}' not found."}

        query_tokens = _tokenize(query)
        if not query_tokens:
            return {"status": "ok", "query": query, "results_count": 0, "results": []}

        scored_results: list[dict[str, Any]] = []

        for mount in targets:
            q_vec = _compute_vector(query_tokens, mount["doc_freq"], mount["total_docs"])
            for chunk in mount["chunks"]:
                chunk_type = chunk.get("type", "document_chunk")
                if not include_trajectories and chunk_type in ("transcript_step", "git_commit"):
                    continue

                score = sum(q_weight * chunk["vector"].get(term, 0.0) for term, q_weight in q_vec.items())
                if score > 0.01:
                    scored_results.append({
                        "score": round(score, 4),
                        "brain_alias": mount["alias"],
                        "brain_format": mount["format"],
                        "type": chunk_type,
                        "file": chunk["file"],
                        "start_line": chunk["start_line"],
                        "end_line": chunk["end_line"],
                        "snippet": chunk["content"][:350] + ("..." if len(chunk["content"]) > 350 else ""),
                    })

        scored_results.sort(key=lambda x: x["score"], reverse=True)
        top_results = scored_results[:top_k]

        return {
            "status": "ok",
            "query": query,
            "searched_brains": [m["alias"] for m in targets],
            "results_count": len(top_results),
            "results": top_results,
        }

    def list_attached(self) -> dict[str, Any]:
        mount_list = [
            {
                "alias": m["alias"],
                "path": m["path"],
                "original_source": m.get("original_source", m["path"]),
                "format": m["format"],
                "mode": m["mode"],
                "summary": m["summary"],
            }
            for m in self._mounts.values()
        ]
        return {
            "status": "ok",
            "attached_count": len(mount_list),
            "brains": mount_list,
        }

    def detach(self, brain_alias: str) -> dict[str, Any]:
        if brain_alias not in self._mounts:
            return {"status": "error", "error": f"Attached brain alias '{brain_alias}' not found."}

        removed = self._mounts.pop(brain_alias)
        return {
            "status": "ok",
            "detached_alias": brain_alias,
            "path": removed["path"],
        }


# Global default engine for direct module functions
_GLOBAL_ENGINE = BrainBridgeEngine()


def brain_attach(
    folder_path: str,
    alias: str | None = None,
    read_transcripts: bool = True,
    read_commits: bool = True,
    max_commits: int = 100,
    attach_mode: str = "lens",
) -> dict[str, Any]:
    """Inspect and mount an external brain, repository, IDE state, or knowledge directory."""
    return _GLOBAL_ENGINE.attach(
        folder_path=folder_path,
        alias=alias,
        read_transcripts=read_transcripts,
        read_commits=read_commits,
        max_commits=max_commits,
        attach_mode=attach_mode,
    )


def brain_query(
    query: str,
    brain_alias: str | None = None,
    include_trajectories: bool = True,
    top_k: int = 5,
) -> dict[str, Any]:
    """Query across one or all mounted external brains/repos for knowledge, code, solutions, or trajectories."""
    return _GLOBAL_ENGINE.query(
        query=query,
        brain_alias=brain_alias,
        include_trajectories=include_trajectories,
        top_k=top_k,
    )


def brain_list_attached() -> dict[str, Any]:
    """List all currently mounted external brains/repositories, their detected formats, and index statistics."""
    return _GLOBAL_ENGINE.list_attached()


def brain_detach(brain_alias: str) -> dict[str, Any]:
    """Unmount a foreign brain or repository and release its memory indexes."""
    return _GLOBAL_ENGINE.detach(brain_alias=brain_alias)


class BrainBridgePlugin(HarnessPlugin, BrainBridgeService):
    """Harness Plugin providing federated external brain and Git repository attachment services."""

    name = "plugin.brain_bridge"
    version = "1.0.0"
    description = "Federated brain bridge, multi-repository attachment, and cross-codebase knowledge indexer"
    trusted = True

    def __init__(self, engine: BrainBridgeEngine | None = None) -> None:
        self._engine = engine or _GLOBAL_ENGINE

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [BRAIN_BRIDGE_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, ctx: ServiceContext) -> None:
        logger.info("loading_plugin", plugin=self.name)
        ctx.provide(BRAIN_BRIDGE_KEY, self, provider=self.name)

    async def on_enable(self) -> None:
        logger.info("enabling_plugin", plugin=self.name)

    async def on_disable(self) -> None:
        logger.info("disabling_plugin", plugin=self.name)

    async def on_unload(self) -> None:
        logger.info("unloading_plugin", plugin=self.name)

    # -------------------------------------------------------------------------
    # BrainBridgeService Protocol Implementation
    # -------------------------------------------------------------------------

    def attach(
        self,
        folder_path: str,
        alias: str | None = None,
        read_transcripts: bool = True,
        read_commits: bool = True,
        max_commits: int = 100,
        attach_mode: str = "lens",
    ) -> BrainAttachResult:
        res = self._engine.attach(
            folder_path=folder_path,
            alias=alias,
            read_transcripts=read_transcripts,
            read_commits=read_commits,
            max_commits=max_commits,
            attach_mode=attach_mode,
        )
        return BrainAttachResult(
            status=res["status"],
            alias=res.get("alias"),
            path=res.get("path"),
            original_source=res.get("original_source"),
            detected_format=res.get("detected_format"),
            mode=res.get("mode", attach_mode),
            summary=res.get("summary", {}),
            error=res.get("error"),
        )

    async def attach_async(
        self,
        folder_path: str,
        alias: str | None = None,
        read_transcripts: bool = True,
        read_commits: bool = True,
        max_commits: int = 100,
        attach_mode: str = "lens",
    ) -> BrainAttachResult:
        return await asyncio.to_thread(
            self.attach, folder_path, alias, read_transcripts, read_commits, max_commits, attach_mode
        )

    def query(
        self,
        query: str,
        brain_alias: str | None = None,
        include_trajectories: bool = True,
        top_k: int = 5,
    ) -> BrainQueryResult:
        res = self._engine.query(
            query=query,
            brain_alias=brain_alias,
            include_trajectories=include_trajectories,
            top_k=top_k,
        )
        return BrainQueryResult(
            status=res["status"],
            query=res.get("query", query),
            searched_brains=res.get("searched_brains", []),
            results_count=res.get("results_count", 0),
            results=res.get("results", []),
            note=res.get("note"),
            error=res.get("error"),
        )

    async def query_async(
        self,
        query: str,
        brain_alias: str | None = None,
        include_trajectories: bool = True,
        top_k: int = 5,
    ) -> BrainQueryResult:
        return await asyncio.to_thread(
            self.query, query, brain_alias, include_trajectories, top_k
        )

    def list_attached(self) -> BrainListResult:
        res = self._engine.list_attached()
        return BrainListResult(
            status=res["status"],
            attached_count=res.get("attached_count", 0),
            brains=res.get("brains", []),
        )

    def detach(self, brain_alias: str) -> BrainDetachResult:
        res = self._engine.detach(brain_alias=brain_alias)
        return BrainDetachResult(
            status=res["status"],
            detached_alias=res.get("detached_alias"),
            path=res.get("path"),
            error=res.get("error"),
        )
