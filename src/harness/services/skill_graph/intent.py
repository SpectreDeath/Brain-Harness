"""Semantic intent routing, trigram matching, and candidate score ranking (Rule 55)."""

from __future__ import annotations

import re
from typing import Any

from harness.services.skill_graph.models import SkillCardDefinition


def _trigram_overlap(s1: str, s2: str) -> float:
    """Calculate character trigram Jaccard similarity between two strings."""
    if len(s1) < 3 or len(s2) < 3:
        return 0.0
    tri1 = {s1[i : i + 3] for i in range(len(s1) - 2)}
    tri2 = {s2[i : i + 3] for i in range(len(s2) - 2)}
    if not tri1 or not tri2:
        return 0.0
    return len(tri1 & tri2) / len(tri1 | tri2)


def route_skill_intent(
    intent: str,
    skills_cache: dict[str, SkillCardDefinition],
    idf_table: dict[str, float],
    chain_fn: Any,
    top_k: int = 3,
    min_confidence: float = 0.20,
) -> dict[str, Any]:
    """Route natural language task intent to candidate skills with confidence scores (Rule 55)."""
    intent_lower = intent.lower().strip()
    intent_tokens = set(re.findall(r"\w+", intent_lower))

    avg_tokens = 8.0
    n_tokens = max(1.0, float(len(intent_tokens)))
    len_norm = 0.75 + 0.25 * min(2.5, n_tokens / avg_tokens)

    matches: list[dict[str, Any]] = []

    for skill in skills_cache.values():
        score = 0.0
        matched_triggers: list[str] = []

        # Exact or partial name match
        if skill.name in intent_lower:
            score += 2.5
            matched_triggers.append(skill.name)

        # Slash command invocation match
        if skill.invocation and skill.invocation.lower() in intent_lower:
            score += 3.0
            matched_triggers.append(skill.invocation)

        # Trigger phrase match
        covered_trig_tokens: set[str] = set()
        for trigger in skill.triggers:
            trig_lower = trigger.lower()
            if trig_lower in intent_lower:
                score += 2.0
                matched_triggers.append(trigger)
                covered_trig_tokens.update(re.findall(r"\w+", trig_lower))
            else:
                trig_tokens = set(re.findall(r"\w+", trig_lower))
                overlap = intent_tokens.intersection(trig_tokens)
                new_overlap = overlap - covered_trig_tokens
                if new_overlap:
                    idf_trigger_score = sum(idf_table.get(t, 1.0) for t in new_overlap)
                    precision = len(overlap) / max(1.0, float(len(trig_tokens)))
                    score += 0.5 * idf_trigger_score * (0.5 + 0.5 * precision)
                    covered_trig_tokens.update(new_overlap)
                    matched_triggers.extend(list(new_overlap)[:2])

        # Description / target token overlap
        text_corpus = f"{skill.target} {skill.category}".lower()
        text_tokens = set(re.findall(r"\w+", text_corpus))
        text_overlap = intent_tokens.intersection(text_tokens)
        if text_overlap:
            idf_score = sum(idf_table.get(t, 1.0) for t in text_overlap)
            score += 0.3 * idf_score

        # Character trigram overlap
        tri_score = _trigram_overlap(intent_lower, text_corpus)
        if tri_score > 0.15:
            score += 1.2 * tri_score

        # Knowledge Item cross-link boost
        if skill.knowledge_items:
            for ki in skill.knowledge_items:
                if (
                    ki.lower() in intent_lower
                    or ki.lower().replace("-", " ") in intent_lower
                ):
                    score += 1.5
                    matched_triggers.append(ki)

        if score > 0.0:
            norm_score = score / (1.5 * len_norm + 1.0)
            confidence = min(0.98, max(0.20, norm_score / 2.2 + 0.25))
            if confidence >= min_confidence:
                matches.append(
                    {
                        "skill_name": skill.name,
                        "category": skill.category,
                        "confidence": round(confidence, 3),
                        "raw_score": round(score, 4),
                        "target": skill.target,
                        "matched_triggers": list(dict.fromkeys(matched_triggers))[:4],
                    }
                )

    matches.sort(
        key=lambda m: (float(m["confidence"]), float(m.get("raw_score", 0.0))),
        reverse=True,
    )
    top_matches = matches[:top_k]

    recommended_chain: list[str] = []
    if len(top_matches) >= 2:
        s1, s2 = top_matches[0]["skill_name"], top_matches[1]["skill_name"]
        chain_res = chain_fn(s1, s2, fallback_direct=False)
        if getattr(chain_res, "status", "") == "ok" and getattr(chain_res, "chain", None):
            recommended_chain = list(chain_res.chain)
        else:
            chain_rev = chain_fn(s2, s1, fallback_direct=False)
            if getattr(chain_rev, "status", "") == "ok" and getattr(chain_rev, "chain", None):
                recommended_chain = list(chain_rev.chain)
            elif (
                abs(
                    float(top_matches[0]["confidence"])
                    - float(top_matches[1]["confidence"])
                )
                < 0.02
            ):
                recommended_chain = []
            else:
                recommended_chain = [s1]
    elif top_matches:
        recommended_chain = [top_matches[0]["skill_name"]]

    return {
        "status": "ok",
        "intent": intent,
        "matches": top_matches,
        "recommended_chain": recommended_chain,
        "total_indexed": len(skills_cache),
    }


__all__ = [
    "_trigram_overlap",
    "route_skill_intent",
]
