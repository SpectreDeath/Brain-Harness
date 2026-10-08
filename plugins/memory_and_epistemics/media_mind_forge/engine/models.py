"""Slotted and frozen internal data structures for Media Mind Forge engine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True, frozen=True)
class DeconstructedTranscriptResult:
    """Slotted and immutable representation of deconstructed transcript."""

    clean_text: str
    normalized_text: str
    segments: tuple[tuple[str, float, float], ...] = ()
    word_count: int = 0
    duration_s: float = 0.0
    duration_seconds: float = 0.0
    words_per_minute: float = 0.0


@dataclass(slots=True, frozen=True)
class ThematicPoints:
    """Slotted container for extracted thematic axioms and heuristics."""

    first_principles: tuple[str, ...] = ()
    heuristics: tuple[str, ...] = ()
    anti_patterns: tuple[str, ...] = ()


@dataclass(slots=True, frozen=True)
class IsnadClaimNode:
    """Slotted and immutable epistemic chain-of-custody claim node."""

    claim: str
    speaker: str = "Subject Matter Expert"
    source: str = ""
    timestamp_s: float = 0.0
    status: str = "VERIFIED"


@dataclass(slots=True, frozen=True)
class SkillPackageResult:
    """Slotted result container for synthesized skill directory package."""

    skill_name: str
    skill_dir: str
    skill_file: str
    card_file: str
