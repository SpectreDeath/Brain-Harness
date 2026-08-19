"""Unsupervised text clustering and topic extraction plugin for Brain Harness."""

from __future__ import annotations

import math
import random
import re
from collections import Counter, defaultdict
from typing import Any


def _tokenize(text: str) -> list[str]:
    return [w.lower() for w in re.findall(r"[a-zA-Z]{3,}", text)]


def _build_tfidf_vector(tokens: list[str], doc_freq: dict[str, int], total_docs: int) -> dict[str, float]:
    tf = Counter(tokens)
    vec: dict[str, float] = {}
    norm_sq = 0.0

    for term, cnt in tf.items():
        w = (1.0 + math.log(cnt)) * (math.log((total_docs + 1.0) / (doc_freq.get(term, 0) + 1.0)) + 1.0)
        vec[term] = w
        norm_sq += w * w

    norm = math.sqrt(norm_sq) if norm_sq > 0 else 1.0
    for term in vec:
        vec[term] /= norm
    return vec


def _cosine(v1: dict[str, float], v2: dict[str, float]) -> float:
    return sum(weight * v2.get(term, 0.0) for term, weight in v1.items())


def cluster_text_chunks(
    texts: list[Any],
    num_clusters: int = 3,
) -> dict[str, Any]:
    """K-Means clustering over text documents using TF-IDF representation."""
    clean_texts = [t.get("text", t.get("content", str(t))) if isinstance(t, dict) else str(t) for t in texts]
    if not clean_texts:
        return {"status": "ok", "clusters_count": 0, "clusters": []}

    k = min(max(1, num_clusters), len(clean_texts))
    tokenized = [_tokenize(t) for t in clean_texts]

    doc_freq: dict[str, int] = defaultdict(int)
    for toks in tokenized:
        for term in set(toks):
            doc_freq[term] += 1

    vectors = [_build_tfidf_vector(toks, doc_freq, len(clean_texts)) for toks in tokenized]

    # Initialize centroids randomly with seed
    rng = random.Random(42)
    sample_indices = rng.sample(range(len(vectors)), k)
    centroids = [dict(vectors[i]) for i in sample_indices]

    assignments = [0] * len(vectors)

    # 5 iterations of K-Means
    for _ in range(5):
        # Assign to nearest centroid
        for i, vec in enumerate(vectors):
            best_sim = -1.0
            best_c = 0
            for c_idx, cent in enumerate(centroids):
                sim = _cosine(vec, cent)
                if sim > best_sim:
                    best_sim = sim
                    best_c = c_idx
            assignments[i] = best_c

        # Recompute centroids
        for c_idx in range(k):
            members = [vectors[i] for i, a in enumerate(assignments) if a == c_idx]
            if not members:
                continue
            new_cent: dict[str, float] = defaultdict(float)
            for m in members:
                for term, val in m.items():
                    new_cent[term] += val / len(members)
            centroids[c_idx] = dict(new_cent)

    clusters: list[dict[str, Any]] = []
    for c_idx in range(k):
        member_texts = [clean_texts[i] for i, a in enumerate(assignments) if a == c_idx]
        keywords = extract_cluster_topic_keywords(member_texts, top_n=5).get("keywords", [])
        clusters.append({
            "cluster_id": c_idx,
            "size": len(member_texts),
            "top_keywords": keywords,
            "sample_snippet": member_texts[0][:150] if member_texts else "",
        })

    return {
        "status": "ok",
        "total_documents": len(clean_texts),
        "clusters_count": len(clusters),
        "clusters": clusters,
    }


def extract_cluster_topic_keywords(cluster_texts: list[str], top_n: int = 5) -> dict[str, Any]:
    """Extract most salient terms in a text cluster."""
    all_tokens: list[str] = []
    for t in cluster_texts:
        all_tokens.extend(_tokenize(t))

    counts = Counter(all_tokens)
    top = [term for term, _ in counts.most_common(top_n)]
    return {
        "status": "ok",
        "keywords": top,
    }
