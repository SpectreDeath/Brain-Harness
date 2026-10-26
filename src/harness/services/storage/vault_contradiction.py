"""Contradiction and antinomy detection for Knowledge Items and Isnad claims."""

from __future__ import annotations

import re
from typing import Sequence
from pydantic import BaseModel, Field

from harness.services.storage.models import KnowledgeItemRecord
from harness.services.storage.vault_taxonomy import get_taxonomy_domain


class ContradictionReviewItem(BaseModel):
    """Flagged contradiction or supersession candidate for human or agent review."""

    ki_a: str = Field(..., description="First Knowledge Item ID")
    ki_b: str = Field(..., description="Second Knowledge Item ID")
    title_a: str = Field(..., description="First KI title")
    title_b: str = Field(..., description="Second KI title")
    assertion_a: str = Field(..., description="Assertion from KI A")
    assertion_b: str = Field(..., description="Assertion from KI B")
    conflict_type: str = Field(..., description="direct_antinomy, supersession_candidate, polarity_mismatch, anchor_conflict")
    confidence: float = Field(default=0.85, ge=0.0, le=1.0)
    suggested_edge: str = Field(default="contradicts", description="Suggested typed edge: contradicts, supersedes")
    reason: str = Field(..., description="Diagnostic explanation of conflicting assertions")


# Opposing modality keywords indicating conflicting advice
OPPOSING_MODALITIES: list[tuple[str, str]] = [
    ("always", "never"),
    ("require", "forbid"),
    ("required", "forbidden"),
    ("allowed", "disallowed"),
    ("in-process", "subprocess"),
    ("in_process", "subprocess"),
    ("deprecated", "recommended"),
    ("synchronous", "asynchronous"),
    ("sync", "async"),
    ("blocking", "non-blocking"),
    ("trusted", "untrusted"),
    ("permit", "prohibit"),
]


class ContradictionDetector:
    """Scans knowledge items for contradictory assertions, outdated heuristics, and supersessions."""

    def detect_contradictions(
        self,
        items: Sequence[KnowledgeItemRecord],
    ) -> list[ContradictionReviewItem]:
        """Audit pairwise assertions across KIs in the same domain and surface a review queue."""
        conflicts: list[ContradictionReviewItem] = []
        n = len(items)

        for i in range(n):
            a = items[i]
            claims_a = a.get_claims()
            domain_a = get_taxonomy_domain(a.category)

            for j in range(i + 1, n):
                b = items[j]
                claims_b = b.get_claims()
                domain_b = get_taxonomy_domain(b.category)

                # 1. Explicit supersession link check
                if a.superseded_by == b.id or b.superseded_by == a.id:
                    conflicts.append(
                        ContradictionReviewItem(
                            ki_a=a.id,
                            ki_b=b.id,
                            title_a=a.title,
                            title_b=b.title,
                            assertion_a=claims_a[0].assertion if claims_a else a.title,
                            assertion_b=claims_b[0].assertion if claims_b else b.title,
                            conflict_type="supersession_candidate",
                            confidence=0.95,
                            suggested_edge="supersedes",
                            reason=f"Explicit supersession record between {a.id} and {b.id}",
                        )
                    )
                    continue

                # 2. Check if already linked via contradicts or supersedes
                existing_edge = False
                for edge in a.edges:
                    if edge.target == b.id and edge.type in ("contradicts", "supersedes"):
                        existing_edge = True
                        break
                if existing_edge:
                    continue

                # Must share domain, anchors, or significant tag overlap to compare claims
                shared_tags = set(a.tags).intersection(set(b.tags))
                shared_anchors = bool(a.anchors and b.anchors and any(
                    a.anchors.get(k) == b.anchors.get(k) for k in a.anchors if k in b.anchors
                ))
                same_domain = domain_a == domain_b and domain_a != "general"

                if not (same_domain or len(shared_tags) >= 2 or shared_anchors):
                    continue

                # Compare pairwise assertions
                conflict = self._compare_claims(a, b, claims_a, claims_b, shared_anchors)
                if conflict:
                    conflicts.append(conflict)

        return conflicts

    def _compare_claims(
        self,
        a: KnowledgeItemRecord,
        b: KnowledgeItemRecord,
        claims_a: list,
        claims_b: list,
        shared_anchors: bool,
    ) -> ContradictionReviewItem | None:
        """Evaluate whether any claim in A contradicts any claim in B."""
        for ca in claims_a:
            text_a = ca.assertion.lower()
            words_a = set(re.findall(r"\w+", text_a))

            for cb in claims_b:
                text_b = cb.assertion.lower()
                words_b = set(re.findall(r"\w+", text_b))

                # Shared topic words (excluding common stop words)
                topic_words = (words_a & words_b) - {
                    "the", "a", "an", "is", "are", "must", "should", "not", "to", "for", "with", "in", "on", "by", "of"
                }
                if len(topic_words) < 2 and not shared_anchors:
                    continue

                for pos, neg in OPPOSING_MODALITIES:
                    has_pos_a = pos in text_a
                    has_neg_b = neg in text_b
                    has_neg_a = neg in text_a
                    has_pos_b = pos in text_b

                    if (has_pos_a and has_neg_b) or (has_neg_a and has_pos_b):
                        return ContradictionReviewItem(
                            ki_a=a.id,
                            ki_b=b.id,
                            title_a=a.title,
                            title_b=b.title,
                            assertion_a=ca.assertion,
                            assertion_b=cb.assertion,
                            conflict_type="direct_antinomy",
                            confidence=0.88,
                            suggested_edge="contradicts",
                            reason=f"Opposing modalities ('{pos}' vs '{neg}') on shared topics: {', '.join(sorted(topic_words)[:4])}",
                        )
        return None
