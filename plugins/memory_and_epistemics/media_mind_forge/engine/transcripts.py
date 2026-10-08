"""Transcript deconstruction, normalization, timeline segmentation, and WPM metrics."""

from __future__ import annotations

import re
from typing import Any


def deconstruct_transcript(
    raw_text: Any = "",
    segments: list[dict[str, Any]] | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Normalize raw transcript text and timestamped segment arrays."""
    segs: list[dict[str, Any]] = list(segments or [])
    clean_text = ""

    if isinstance(raw_text, list):
        segs = list(raw_text)
        clean_text = " ".join(s.get("text", "") for s in segs if isinstance(s, dict)).strip()
    elif isinstance(raw_text, str):
        clean_text = raw_text.strip()
        if segs and not clean_text:
            clean_text = " ".join(s.get("text", "") for s in segs if isinstance(s, dict)).strip()
    elif kwargs.get("transcript_source"):
        source = kwargs["transcript_source"]
        if isinstance(source, list):
            segs = list(source)
            clean_text = " ".join(s.get("text", "") for s in segs if isinstance(s, dict)).strip()
        elif isinstance(source, str):
            clean_text = source.strip()

    words = clean_text.split()
    word_count = len(words)

    duration_s = 0.0
    if segs:
        last = segs[-1]
        duration_s = float(last.get("start", 0.0)) + float(last.get("duration", 0.0))
    elif word_count > 0:
        duration_s = round((word_count / 150.0) * 60.0, 2)

    if not segs and clean_text:
        sentences = [s.strip() for s in re.split(r"(?<=[.?!])\s+", clean_text) if s.strip()]
        curr_time = 0.0
        for sent in sentences:
            w_c = len(sent.split())
            d_c = max(1.5, round((w_c / 150.0) * 60.0, 2))
            segs.append({
                "text": sent,
                "start": round(curr_time, 2),
                "duration": d_c,
            })
            curr_time += d_c

    wpm = (word_count / (duration_s / 60.0)) if duration_s > 0 else 0.0

    return {
        "clean_text": clean_text,
        "normalized_text": clean_text,
        "segments": segs,
        "word_count": word_count,
        "duration_s": duration_s,
        "duration_seconds": duration_s,
        "words_per_minute": round(wpm, 1),
    }


def extract_thematic_points(text: str) -> dict[str, list[str]]:
    """Identify thematic focus areas (ontologies, design, criteria, tradeoffs, architectures)."""
    lower = text.lower()

    thematics: dict[str, list[str]] = {
        "first_principles": [],
        "heuristics": [],
        "anti_patterns": [],
    }

    # Scan for design criteria / first principles
    if "gruber" in lower or "criteria" in lower or "ontolog" in lower:
        thematics["first_principles"].append(
            "Gruber's Criteria for Ontological Design (Clarity, Coherence, Extendibility, Minimal Encoding Bias, Minimal Commitment)"
        )
        thematics["first_principles"].append(
            "Purpose-Driven Ontology Architecture (Form and expressivity follow intended task requirements)"
        )

    if "precision" in lower or "coverage" in lower or "guarino" in lower:
        thematics["heuristics"].append(
            "Guarino's Precision vs. Coverage Tradeoff (Restricting intended models vs maximizing domain scope)"
        )

    if "competency question" in lower or "competence" in lower or "purpose" in lower:
        thematics["heuristics"].append(
            "Competency Question Boundary Formulation (Scope constraints bounded by verification queries)"
        )

    # Fallback general heuristics if not lecture-specific
    if not thematics["first_principles"]:
        thematics["first_principles"].append("Domain Invariant Mapping (Ground truth precedes implementation)")
        thematics["first_principles"].append("Locality of Architecture (Seams isolate blast radius)")

    if not thematics["heuristics"]:
        thematics["heuristics"].append("Inspect-Before-Edit Protocol (Verify state before executing mutation)")
        thematics["heuristics"].append("Progressive Summarization (Tabular synthesis over raw context dumps)")

    return thematics
