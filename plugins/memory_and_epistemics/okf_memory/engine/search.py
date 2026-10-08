"""OKF BM25 lexical ranking and path-scoped governance evaluation engine."""

from __future__ import annotations

import math
from collections import Counter
from pathlib import Path
from typing import Any

from .utils import _normalize_path, _tokenize


def execute_search(
    concepts: dict[str, tuple[dict[str, Any], str, Path]],
    root: Path,
    query: str = "",
    for_path: str | None = None,
    limit: int = 3,
) -> dict[str, Any]:
    """Execute BM25 lexical search or for-path governance evaluation."""
    scored: list[dict[str, Any]] = []

    # 1. Path-scoped governance scoping (Rule 1 / SearchForPath)
    if for_path:
        norm_target = _normalize_path(for_path)
        for cid, (data, _body, file_path) in concepts.items():
            code_refs = [
                _normalize_path(r) for r in (data.get("code_refs") or []) if isinstance(r, str)
            ]
            matched_refs = []
            for ref in code_refs:
                if ref == norm_target or norm_target.startswith(ref + "/") or ref.startswith(norm_target + "/"):
                    matched_refs.append(ref)

            if matched_refs:
                score = 100.0 + len(matched_refs) * 10.0
                gov_rules = data.get("governance") or []
                scored.append({
                    "id": cid,
                    "title": data.get("title", ""),
                    "type": data.get("type", "concept"),
                    "description": data.get("description", ""),
                    "score": round(score, 2),
                    "governance": gov_rules,
                    "code_refs": code_refs,
                    "matched_refs": matched_refs,
                    "path": _normalize_path(file_path.relative_to(root)),
                })

        scored.sort(key=lambda x: x["score"], reverse=True)
        results = scored[: max(1, limit)]
        return {
            "status": "ok",
            "query": query,
            "for_path": for_path,
            "results_count": len(results),
            "results": results,
        }

    # 2. BM25 Lexical search (Rule 2 / Search)
    q_tokens = _tokenize(query)
    if not q_tokens:
        # Empty query: return most recent or alphabetically first concepts
        for cid, (data, _body, file_path) in list(concepts.items())[:limit]:
            scored.append({
                "id": cid,
                "title": data.get("title", ""),
                "type": data.get("type", "concept"),
                "description": data.get("description", ""),
                "score": 1.0,
                "governance": data.get("governance") or [],
                "code_refs": data.get("code_refs") or [],
                "path": _normalize_path(file_path.relative_to(root)),
            })
        return {
            "status": "ok",
            "query": query,
            "for_path": None,
            "results_count": len(scored),
            "results": scored,
        }

    # Document tokenization & corpus stats
    doc_tokens: dict[str, list[str]] = {}
    doc_gov_tokens: dict[str, set[str]] = {}
    df = Counter()
    total_docs = len(concepts)

    for cid, (data, body, _) in concepts.items():
        title_toks = _tokenize(data.get("title", "")) * 3
        desc_toks = _tokenize(data.get("description", "")) * 2
        id_toks = _tokenize(cid) * 2
        gov_texts = [str(g) for g in (data.get("governance") or [])]
        gov_toks = _tokenize(" ".join(gov_texts)) * 3
        body_toks = _tokenize(body)

        all_toks = title_toks + desc_toks + id_toks + gov_toks + body_toks
        doc_tokens[cid] = all_toks
        doc_gov_tokens[cid] = set(gov_toks)

        unique_terms = set(all_toks)
        for t in unique_terms:
            df[t] += 1

    avg_dl = sum(len(toks) for toks in doc_tokens.values()) / max(1, total_docs)
    k1 = 1.2
    b = 0.75

    # Calculate BM25 scores
    for cid, (data, _body, file_path) in concepts.items():
        tokens = doc_tokens[cid]
        doc_len = len(tokens)
        term_counts = Counter(tokens)
        score = 0.0

        for qt in q_tokens:
            if qt not in term_counts:
                continue
            tf = term_counts[qt]
            doc_freq = df.get(qt, 0)
            idf = math.log(1.0 + (total_docs - doc_freq + 0.5) / (doc_freq + 0.5))
            numerator = tf * (k1 + 1.0)
            denominator = tf + k1 * (1.0 - b + b * (doc_len / avg_dl))
            score += idf * (numerator / denominator)

        # Governance boost bonus
        gov_matches = sum(1 for qt in q_tokens if qt in doc_gov_tokens[cid])
        if gov_matches > 0:
            score += gov_matches * 1.5

        if score > 0.0:
            scored.append({
                "id": cid,
                "title": data.get("title", ""),
                "type": data.get("type", "concept"),
                "description": data.get("description", ""),
                "score": round(score, 4),
                "governance": data.get("governance") or [],
                "code_refs": data.get("code_refs") or [],
                "path": _normalize_path(file_path.relative_to(root)),
            })

    scored.sort(key=lambda x: x["score"], reverse=True)
    results = scored[: max(1, limit)]
    return {
        "status": "ok",
        "query": query,
        "for_path": None,
        "results_count": len(results),
        "results": results,
    }
