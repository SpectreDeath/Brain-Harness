"""Local semantic vector index and retrieval plugin for Brain Harness."""

from __future__ import annotations

import math
import os
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

# Global in-memory index state
_CHUNKS: list[dict[str, Any]] = []
_DOC_FREQ: dict[str, int] = defaultdict(int)
_TOTAL_DOCS: int = 0


def _tokenize(text: str) -> list[str]:
    """Tokenize text into lowercase alphanumeric words and subwords."""
    # Split camelCase and snake_case
    words = re.findall(r"[A-Z]?[a-z0-9]+|[A-Z]+(?=[A-Z][a-z]|\d|\W|$)|\w+", text)
    tokens: list[str] = []
    for w in words:
        low = w.lower()
        if len(low) > 1:
            tokens.append(low)
    return tokens


def _compute_vector(tokens: list[str]) -> dict[str, float]:
    """Compute normalized TF-IDF vector for tokens."""
    tf = Counter(tokens)
    vec: dict[str, float] = {}
    norm_sq = 0.0

    for term, count in tf.items():
        # Sublinear TF scaling
        tf_weight = 1.0 + math.log(count)
        idf_weight = math.log((_TOTAL_DOCS + 1.0) / (_DOC_FREQ.get(term, 0) + 1.0)) + 1.0
        weight = tf_weight * idf_weight
        vec[term] = weight
        norm_sq += weight * weight

    # L2 normalize
    norm = math.sqrt(norm_sq) if norm_sq > 0 else 1.0
    for term in vec:
        vec[term] /= norm

    return vec


def vector_index_directory(
    path: str = ".",
    extensions: list[str] | None = None,
    chunk_lines: int = 30,
) -> dict[str, Any]:
    """Scan and index documents in a directory for semantic search."""
    global _CHUNKS, _DOC_FREQ, _TOTAL_DOCS

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

            # Chunk into overlapping windows
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

                # Track document frequency for unique tokens in this chunk
                for term in set(tokens):
                    doc_freq[term] += 1

    _CHUNKS = chunks_built
    _DOC_FREQ = doc_freq
    _TOTAL_DOCS = len(chunks_built)

    # Precompute vectors for all chunks
    for chunk in _CHUNKS:
        chunk["vector"] = _compute_vector(chunk["tokens"])

    return {
        "status": "ok",
        "root": str(root),
        "indexed_chunks": len(_CHUNKS),
        "unique_terms": len(_DOC_FREQ),
    }


def vector_search_semantic(query: str, top_k: int = 5) -> dict[str, Any]:
    """Perform natural language cosine similarity search."""
    if not _CHUNKS:
        return {"status": "ok", "query": query, "results_count": 0, "results": [], "note": "Index is empty. Run vector_index_directory first."}

    query_tokens = _tokenize(query)
    if not query_tokens:
        return {"status": "ok", "query": query, "results_count": 0, "results": []}

    q_vec = _compute_vector(query_tokens)

    scored: list[tuple[float, dict[str, Any]]] = []
    for chunk in _CHUNKS:
        # Cosine dot product of normalized vectors
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


def vector_search_hybrid(
    query: str,
    keyword: str | None = None,
    top_k: int = 5,
) -> dict[str, Any]:
    """Perform hybrid search combining semantic score with exact keyword boosting."""
    base_res = vector_search_semantic(query, top_k=top_k * 2)
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
