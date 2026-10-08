"""Authoritative DefaultBrainBridgeService coordinator implementation."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any
import structlog

from .detector import clone_remote_repo, detect_brain_format, is_git_url
from .indexers import index_text_files, parse_git_commits, parse_transcripts
from .models import (
    BrainAttachResult,
    BrainDetachResult,
    BrainListResult,
    BrainQueryResult,
)
from .protocols import BrainBridgeService
from .tokenizers import compute_tf_idf_vector, tokenize_text

logger = structlog.get_logger(__name__)


class DefaultBrainBridgeService(BrainBridgeService):
    """Authoritative micro-kernel implementation of BrainBridgeService."""

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
    ) -> BrainAttachResult:
        is_remote = is_git_url(folder_path)
        if is_remote:
            default_alias = folder_path.rstrip("/").split("/")[-1].replace(".git", "").lower()
            mount_alias = alias or default_alias or "remote_repo"
            root, clone_err = clone_remote_repo(folder_path, mount_alias)
            if not root or clone_err:
                return BrainAttachResult(
                    status="error",
                    alias=mount_alias,
                    original_source=folder_path,
                    error=clone_err or "Failed to clone remote repository.",
                )
        else:
            root = Path(folder_path).resolve()
            if not root.exists() or not root.is_dir():
                return BrainAttachResult(
                    status="error",
                    alias=alias,
                    path=str(root),
                    original_source=folder_path,
                    error=f"Directory not found or does not exist: {folder_path}",
                )
            mount_alias = alias or root.name.lower() or "local_brain"

        detected_format = detect_brain_format(root)

        doc_chunks, doc_freq, detected_languages, manifests = index_text_files(root)

        transcript_chunks: list[dict[str, Any]] = []
        trajectories: list[dict[str, Any]] = []
        if read_transcripts:
            transcript_chunks, t_trajs, t_doc_freq = parse_transcripts(root)
            trajectories.extend(t_trajs)
            for term, cnt in t_doc_freq.items():
                doc_freq[term] += cnt

        git_chunks: list[dict[str, Any]] = []
        branch_name: str | None = None
        if read_commits:
            git_chunks, g_trajs, g_doc_freq, branch_name = parse_git_commits(root, max_commits=max_commits)
            trajectories.extend(g_trajs)
            for term, cnt in g_doc_freq.items():
                doc_freq[term] += cnt

        all_chunks = doc_chunks + transcript_chunks + git_chunks
        for idx, c in enumerate(all_chunks):
            c["id"] = idx

        total_docs = len(all_chunks)
        for c in all_chunks:
            c["vector"] = compute_tf_idf_vector(c["tokens"], doc_freq, total_docs)

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

        return BrainAttachResult(
            status="ok",
            alias=mount_alias,
            path=str(root),
            original_source=folder_path,
            detected_format=detected_format,
            mode=attach_mode,
            summary=summary,
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
        if not self._mounts:
            return BrainQueryResult(
                status="ok",
                query=query,
                results_count=0,
                results=[],
                note="No brains or repositories attached. Run brain_attach first.",
            )

        targets = [self._mounts[brain_alias]] if brain_alias and brain_alias in self._mounts else list(self._mounts.values())
        if brain_alias and brain_alias not in self._mounts:
            return BrainQueryResult(
                status="error",
                query=query,
                error=f"Attached brain alias '{brain_alias}' not found.",
            )

        query_tokens = tokenize_text(query)
        if not query_tokens:
            return BrainQueryResult(
                status="ok",
                query=query,
                results_count=0,
                results=[],
            )

        scored_results: list[dict[str, Any]] = []

        for mount in targets:
            q_vec = compute_tf_idf_vector(query_tokens, mount["doc_freq"], mount["total_docs"])
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

        return BrainQueryResult(
            status="ok",
            query=query,
            searched_brains=[m["alias"] for m in targets],
            results_count=len(top_results),
            results=top_results,
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
        return BrainListResult(
            status="ok",
            attached_count=len(mount_list),
            brains=mount_list,
        )

    async def list_attached_async(self) -> BrainListResult:
        return await asyncio.to_thread(self.list_attached)

    def detach(self, brain_alias: str) -> BrainDetachResult:
        if brain_alias not in self._mounts:
            return BrainDetachResult(
                status="error",
                error=f"Attached brain alias '{brain_alias}' not found.",
            )

        removed = self._mounts.pop(brain_alias)
        return BrainDetachResult(
            status="ok",
            detached_alias=brain_alias,
            path=removed["path"],
        )

    async def detach_async(self, brain_alias: str) -> BrainDetachResult:
        return await asyncio.to_thread(self.detach, brain_alias)
