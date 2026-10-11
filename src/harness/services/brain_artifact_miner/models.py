"""Slotted and frozen domain models for Brain Artifact Miner (Rule 12 & Rule 43)."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Any

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


@dataclass(slots=True, frozen=True)
class ScratchCatalogItem:
    """Slotted and frozen representation of a classified scratch script (Rule 12)."""

    category: str
    path: str
    functions: list[str]
    imports: list[str]
    docstring: str


@dataclass(slots=True, frozen=True)
class ScratchCatalog:
    """Slotted and frozen catalog of classified scratch tools (Rule 12)."""

    total_scanned: int
    classified_count: int
    items_by_category: dict[str, list[ScratchCatalogItem]]


@dataclass(slots=True, frozen=True)
class TaskTriageReport:
    """Slotted and frozen summary of background task executions (Rule 12, Rule 53)."""

    total_tasks: int
    failed_count: int
    deadlock_count: int
    samples: list[dict[str, Any]]


@dataclass(slots=True, frozen=True)
class ByteOffsetEntry:
    """Slotted and frozen byte offset record for O(1) binary seeks (Rule 12, Rule 48)."""

    step_index: int
    byte_offset: int
    byte_length: int


@dataclass(slots=True, frozen=True)
class DualTranscriptStep:
    """Slotted and frozen representation of a dual-transcript step (Rule 12, Rule 22)."""

    step_index: int
    source: str
    step_type: str
    status: str
    content: str
    is_truncated: bool
    tool_calls: list[dict[str, Any]]
    dereferenced: bool


@dataclass(slots=True, frozen=True)
class ArtifactLifecycleEntry:
    """Slotted and frozen representation of an artifact version lifecycle (Rule 12)."""

    conversation_id: str
    artifact_name: str
    has_plan: bool
    has_walkthrough: bool
    has_task: bool
    mtime: float


__all__ = [
    "ArtifactLifecycleEntry",
    "ByteOffsetEntry",
    "DualTranscriptStep",
    "ScratchCatalog",
    "ScratchCatalogItem",
    "TaskTriageReport",
]
