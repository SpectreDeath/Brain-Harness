"""BM25 tokenization, corpus IDF weight calculation, and catalog indexing for skills."""

from __future__ import annotations

import collections
import math
import re
from typing import Any

from harness.services.skill_graph.models import SkillCardDefinition


class SkillCatalogIndexer:
    """Tokenizer, corpus IDF weight calculator, and catalog retrieval indexer."""

    @staticmethod
    def tokenize(text: str) -> list[str]:
        """Extract lowercase word tokens from text."""
        return re.findall(r"\w+", text.lower())

    @classmethod
    def build_idf_table(cls, corpus: dict[str, str]) -> dict[str, float]:
        """Compute smoothed inverse document frequency weights across document corpus."""
        corpus_df: dict[str, int] = collections.Counter()
        for doc_text in corpus.values():
            tokens = set(cls.tokenize(doc_text))
            corpus_df.update(tokens)
        n_docs = max(1, len(corpus))
        return {
            t: math.log((n_docs + 1) / (df + 1)) for t, df in corpus_df.items()
        }

    @classmethod
    def score_overlap(
        cls,
        query_tokens: set[str],
        doc_tokens: set[str],
        idf_table: dict[str, float],
        weight: float = 1.0,
    ) -> float:
        """Compute IDF-weighted overlap score between query tokens and document tokens."""
        overlap = query_tokens.intersection(doc_tokens)
        if not overlap:
            return 0.0
        return weight * sum(idf_table.get(t, 1.0) for t in overlap)

    @classmethod
    def query(
        cls,
        query: str,
        skills: dict[str, SkillCardDefinition],
        top_k: int = 5,
        idf_table: dict[str, float] | None = None,
    ) -> list[dict[str, Any]]:
        """Query skill catalog by matching name, triggers, target description, and category."""
        if not skills:
            return []
        query_lower = query.lower().strip()
        query_tokens = set(cls.tokenize(query_lower))
        if idf_table is None:
            corpus = {
                k: f"{s.name} {s.target} {s.category} {' '.join(s.triggers)}"
                for k, s in skills.items()
            }
            idf_table = cls.build_idf_table(corpus)

        results: list[dict[str, Any]] = []
        for name, skill in skills.items():
            score = 0.0
            matched_terms: list[str] = []
            if skill.name in query_lower:
                score += 3.0
                matched_terms.append(skill.name)

            for trig in skill.triggers:
                trig_lower = trig.lower()
                if trig_lower in query_lower:
                    score += 2.0
                    matched_terms.append(trig)
                else:
                    trig_tokens = set(cls.tokenize(trig_lower))
                    overlap = query_tokens.intersection(trig_tokens)
                    if overlap:
                        score += 0.5 * sum(idf_table.get(t, 1.0) for t in overlap)
                        matched_terms.extend(list(overlap)[:2])

            doc_text = f"{skill.target} {skill.category}".lower()
            doc_tokens = set(cls.tokenize(doc_text))
            text_score = cls.score_overlap(query_tokens, doc_tokens, idf_table, weight=0.3)
            score += text_score

            if score > 0.0:
                results.append(
                    {
                        "skill_name": skill.name,
                        "score": round(score, 4),
                        "category": skill.category,
                        "matched_terms": list(dict.fromkeys(matched_terms))[:4],
                    }
                )

        results.sort(key=lambda r: float(r["score"]), reverse=True)
        return results[:top_k]


__all__ = ["SkillCatalogIndexer"]
