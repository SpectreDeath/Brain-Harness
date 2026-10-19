"""Slotted domain models for Deterministic 3-Pass Prompt Pruner (Rule 12)."""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from typing import Any

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

REF_PATTERN = re.compile(r"REF:([A-Za-z0-9_\-]+)")
DEFINE_PATTERN = re.compile(r"DEFINE:([A-Za-z0-9_\-]+)")


@dataclass(slots=True, frozen=True)
class PrunableMessage:
    """Slotted immutable representation of a message undergoing compiler-style pruning."""

    role: str
    content: str
    turn_index: int = 0
    resource_key: str | None = None
    tool_call_id: str | None = None
    defines_keys: tuple[str, ...] = field(default_factory=tuple)
    depends_on: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.role:
            raise ValueError("role must be non-empty")
        if self.turn_index < 0:
            raise ValueError("turn_index must be non-negative")

        # Auto-detect DEFINE and REF if tuples not explicitly provided
        if not self.defines_keys and self.content:
            found_defines = tuple(DEFINE_PATTERN.findall(self.content))
            if found_defines:
                object.__setattr__(self, "defines_keys", found_defines)

        if not self.depends_on and self.content:
            found_refs = tuple(REF_PATTERN.findall(self.content))
            if found_refs:
                object.__setattr__(self, "depends_on", found_refs)


@dataclass(slots=True, frozen=True)
class PruningAuditReport:
    """Auditing diagnostics detailing compiler pass reductions and fixed-point state."""

    original_message_count: int
    pruned_message_count: int
    dropped_turns: tuple[int, ...]
    restored_turns: tuple[int, ...]
    pass1_dropped: int
    pass2_dropped: int
    pass3_restored: int
    elapsed_ms: float

    def __post_init__(self) -> None:
        if self.original_message_count < 0 or self.pruned_message_count < 0:
            raise ValueError("message counts must be non-negative")
        if self.elapsed_ms < 0.0:
            raise ValueError("elapsed_ms must be non-negative")
