"""Local semantic vector index and retrieval plugin for Brain Harness."""

from __future__ import annotations

import asyncio
import math
import os
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
import structlog

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.vector_index import (
    VECTOR_INDEX_KEY,
    VectorHybridSearchResult,
    VectorIndexResult,
    VectorIndexService,
    VectorSearchResult,
)

logger = structlog.get_logger(__name__)


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


class VectorIndexEngine:
    """Encapsulated engine managing local vector indexing and semantic retrieval."""

    def __init__(self) -> None:
        self._chunks: list[dict[str, Any]] = []
        self._doc_freq: dict[str, int] = defaultdict(int)
        self._total_docs: int = 0
        self._root: str | None = None

    def index_directory(
        self,
        path: str = ".",
        extensions: list[str] | None = None,
        chunk_lines: int = 30,
    ) -> dict[str, Any]:
        target_exts = set(extensions) if extensions else {".py", ".md", ".json", ".txt", ".rst"}
        root = Path(path).resolve()
        if not root.exists() or not root.is_dir():
            return {"status": "error", "error": f"Directory not found: {path}"}

        chunks_built: list[dict[str, Any]] = []
        doc_freq: dict[str, int] = defaultdict(int)

        for current_root, dirs, files in os.walk(root):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("__pycache__", "venv", ".venv", "node_modules")]

            for file_name in files:
                file_path = Path(current_root) / file_name
                if file_path.suffix.lower() not in target_exts:
                    continue

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
                        "id": len(chunks_built),
                        "file": str(file_path.relative_to(root)),
                        "start_line": i + 1,
                        "end_line": min(len(lines), i + len(chunk_slice)),
                        "content": chunk_text,
                        "tokens": tokens,
                    }
                    chunks_built.append(chunk_obj)

                    for term in set(tokens):
                        doc_freq[term] += 1

        self._chunks = chunks_built
        self._doc_freq = doc_freq
        self._total_docs = len(chunks_built)
        self._root = str(root)

        for chunk in self._chunks:
            chunk["vector"] = _compute_vector(chunk["tokens"], self._doc_freq, self._total_docs)

        return {
            "status": "ok",
            "root": str(root),
            "indexed_chunks": len(self._chunks),
            "unique_terms": len(self._doc_freq),
        }

    def search_semantic(self, query: str, top_k: int = 5) -> dict[str, Any]:
        if not self._chunks:
            return {"status": "ok", "query": query, "results_count": 0, "results": [], "note": "Index is empty. Run vector_index_directory first."}

        query_tokens = _tokenize(query)
        if not query_tokens:
            return {"status": "ok", "query": query, "results_count": 0, "results": []}

        q_vec = _compute_vector(query_tokens, self._doc_freq, self._total_docs)

        scored: list[tuple[float, dict[str, Any]]] = []
        for chunk in self._chunks:
            score = sum(q_weight * chunk["vector"].get(term, 0.0) for term, q_weight in q_vec.items())
            if score > 0.01:
                scored.append((score, chunk))

        scored.sort(key=lambda x: x[0], reverse=True)
        top_results = [
            {
                "score": round(score, 4),
                "file": chunk["file"],
                "start_line": chunk["start_line"],
                "end_line": chunk["end_line"],
                "snippet": chunk["content"][:300] + ("..." if len(chunk["content"]) > 300 else ""),
            }
            for score, chunk in scored[:top_k]
        ]

        return {
            "status": "ok",
            "query": query,
            "results_count": len(top_results),
            "results": top_results,
        }

    def search_hybrid(
        self,
        query: str,
        keyword: str | None = None,
        top_k: int = 5,
    ) -> dict[str, Any]:
        base_res = self.search_semantic(query, top_k=top_k * 2)
        results = base_res.get("results", [])

        if keyword:
            kw_lower = keyword.lower()
            for item in results:
                if kw_lower in item["snippet"].lower():
                    item["score"] = round(item["score"] * 1.5, 4)
                    item["keyword_match"] = True
                else:
                    item["keyword_match"] = False
            results.sort(key=lambda x: x["score"], reverse=True)

        return {
            "status": "ok",
            "query": query,
            "keyword": keyword,
            "results_count": min(top_k, len(results)),
            "results": results[:top_k],
        }


# Global default engine for module-level functions
_GLOBAL_ENGINE = VectorIndexEngine()


def vector_index_directory(
    path: str = ".",
    extensions: list[str] | None = None,
    chunk_lines: int = 30,
) -> dict[str, Any]:
    """Scan and index documents in a directory for semantic search."""
    return _GLOBAL_ENGINE.index_directory(path=path, extensions=extensions, chunk_lines=chunk_lines)


def vector_search_semantic(query: str, top_k: int = 5) -> dict[str, Any]:
    """Perform natural language cosine similarity search."""
    return _GLOBAL_ENGINE.search_semantic(query=query, top_k=top_k)


def vector_search_hybrid(
    query: str,
    keyword: str | None = None,
    top_k: int = 5,
) -> dict[str, Any]:
    """Perform hybrid search combining semantic score with exact keyword boosting."""
    return _GLOBAL_ENGINE.search_hybrid(query=query, keyword=keyword, top_k=top_k)


class VectorIndexPlugin(HarnessPlugin, VectorIndexService):
    """Harness Plugin providing local document vector indexing, semantic search, and hybrid retrieval."""

    name = "plugin.vector_index"
    version = "1.0.0"
    description = "Local TF-IDF vector index, semantic similarity search, and hybrid keyword boosting"
    trusted = True

    def __init__(self, engine: VectorIndexEngine | None = None) -> None:
        self._engine = engine or _GLOBAL_ENGINE

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [VECTOR_INDEX_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, ctx: ServiceContext) -> None:
        logger.info("loading_plugin", plugin=self.name)
        ctx.provide(VECTOR_INDEX_KEY, self, provider=self.name)

    async def on_enable(self) -> None:
        logger.info("enabling_plugin", plugin=self.name)

    async def on_disable(self) -> None:
        logger.info("disabling_plugin", plugin=self.name)

    async def on_unload(self) -> None:
        logger.info("unloading_plugin", plugin=self.name)

    # -------------------------------------------------------------------------
    # VectorIndexService Protocol Implementation
    # -------------------------------------------------------------------------

    def index_directory(
        self,
        path: str = ".",
        extensions: list[str] | None = None,
        chunk_lines: int = 30,
    ) -> VectorIndexResult:
        res = self._engine.index_directory(path=path, extensions=extensions, chunk_lines=chunk_lines)
        return VectorIndexResult(
            status=res["status"],
            root=res.get("root"),
            indexed_chunks=res.get("indexed_chunks", 0),
            unique_terms=res.get("unique_terms", 0),
            error=res.get("error"),
        )

    async def index_directory_async(
        self,
        path: str = ".",
        extensions: list[str] | None = None,
        chunk_lines: int = 30,
    ) -> VectorIndexResult:
        return await asyncio.to_thread(self.index_directory, path, extensions, chunk_lines)

    def search_semantic(
        self,
        query: str,
        top_k: int = 5,
    ) -> VectorSearchResult:
        res = self._engine.search_semantic(query=query, top_k=top_k)
        return VectorSearchResult(
            status=res["status"],
            query=res.get("query", query),
            results_count=res.get("results_count", 0),
            results=res.get("results", []),
            note=res.get("note"),
            error=res.get("error"),
        )

    async def search_semantic_async(
        self,
        query: str,
        top_k: int = 5,
    ) -> VectorSearchResult:
        return await asyncio.to_thread(self.search_semantic, query, top_k)

    def search_hybrid(
        self,
        query: str,
        keyword: str | None = None,
        top_k: int = 5,
    ) -> VectorHybridSearchResult:
        res = self._engine.search_hybrid(query=query, keyword=keyword, top_k=top_k)
        return VectorHybridSearchResult(
            status=res["status"],
            query=res.get("query", query),
            keyword=res.get("keyword"),
            results_count=res.get("results_count", 0),
            results=res.get("results", []),
            error=res.get("error"),
        )

    async def search_hybrid_async(
        self,
        query: str,
        keyword: str | None = None,
        top_k: int = 5,
    ) -> VectorHybridSearchResult:
        return await asyncio.to_thread(self.search_hybrid, query, keyword, top_k)
