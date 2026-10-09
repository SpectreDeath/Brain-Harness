"""Natural Language Processing, tokenization, TF-IDF vectors, and triple extraction heuristics."""

from __future__ import annotations

import math
import re
from collections import Counter


def _tokenize(text: str) -> list[str]:
    """Tokenize text into lowercase alphanumeric words."""
    words = re.findall(r"[A-Z]?[a-z0-9]+|[A-Z]+(?=[A-Z][a-z]|\d|\W|$)|\w+", text)
    return [w.lower() for w in words if len(w) > 1]


def _compute_tf_idf_vector(tokens: list[str], doc_freq: dict[str, int], total_docs: int) -> dict[str, float]:
    """Compute normalized TF-IDF vector."""
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


def _cosine_similarity(vec1: dict[str, float], vec2: dict[str, float]) -> float:
    """Compute cosine similarity between two sparse vector dicts."""
    if not vec1 or not vec2:
        return 0.0
    if len(vec1) > len(vec2):
        vec1, vec2 = vec2, vec1
    score = sum(val * vec2.get(k, 0.0) for k, val in vec1.items())
    return max(0.0, min(1.0, score))


def _infer_entity_type(entity: str) -> str:
    """Infer ontology entity type from lexical patterns."""
    ent = entity.strip()
    if re.match(r"^\d+(\.\d+)?%?$", ent) or any(c.isdigit() for c in ent):
        return "Quantity"
    if any(w in ent.lower() for w in ["system", "engine", "model", "algorithm", "rag", "framework", "software"]):
        return "Technology"
    if any(w in ent.lower() for w in ["university", "corp", "inc", "group", "lab", "team", "organization"]):
        return "Organization"
    if any(w in ent.lower() for w in ["dr", "prof", "wu", "tang", "zhang", "smith", "lovelace", "turing", "user"]):
        return "Person"
    if any(w in ent.lower() for w in ["accuracy", "latency", "f1", "precision", "recall", "score", "rate"]):
        return "Metric"
    if any(w in ent.lower() for w in ["memory", "fact", "passage", "schema", "triple", "graph", "dataset"]):
        return "KnowledgeStructure"
    return "Concept"


def _extract_triples_heuristic(text: str) -> list[tuple[str, str, str]]:
    """Lightweight relational triple extractor with rule-based heuristics."""
    triples: list[tuple[str, str, str]] = []
    sentences = re.split(r"[.!?\n]+", text)
    relation_patterns = [
        r"^(.*?)\s+(is a|is an|is|was|are|were)\s+(.*)$",
        r"^(.*?)\s+(organizes|manages|stores|contains|uses|implements|supports|extracts|resolves|builds)\s+(.*)$",
        r"^(.*?)\s+(developed by|founded by|authored by|created by)\s+(.*)$",
        r"^(.*?)\s+(consists of|connects to|combines with|enhances)\s+(.*)$",
    ]

    for s in sentences:
        s_clean = s.strip()
        if not s_clean or len(s_clean) < 8:
            continue

        matched = False
        for pat in relation_patterns:
            m = re.match(pat, s_clean, re.IGNORECASE)
            if m:
                head = m.group(1).strip()
                rel = m.group(2).strip().lower()
                tail = m.group(3).strip()
                if 1 < len(head) < 80 and 1 < len(tail) < 100:
                    triples.append((head, rel, tail))
                    matched = True
                    break

        if not matched and "," in s_clean:
            parts = [p.strip() for p in s_clean.split(",") if p.strip()]
            if len(parts) >= 2 and len(parts[0]) < 50 and len(parts[1]) < 60:
                triples.append((parts[0], "related_to", parts[1]))

    # Deduplicate while preserving order
    unique_triples: list[tuple[str, str, str]] = []
    seen = set()
    for t in triples:
        k = (t[0].lower(), t[1].lower(), t[2].lower())
        if k not in seen:
            seen.add(k)
            unique_triples.append(t)

    return unique_triples
