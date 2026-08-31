"""Kimi Bridge Service — typed schemas, AST security nodes, transcript streaming, and MiniDb protocols."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable
import structlog

from harness.kernel.context import ServiceKey

logger = structlog.get_logger(__name__)

KIMI_BRIDGE_KEY = ServiceKey["KimiBridgeService"]("service.kimi_bridge")
KIMI_TRANSCRIPT_KEY = ServiceKey["KimiTranscriptService"]("service.kimi_transcript")
KIMI_MINIDB_KEY = ServiceKey["KimiMiniDbService"]("service.kimi_minidb")


@dataclass(slots=True, frozen=True)
class BashAstNode:
    """Slotted and frozen AST node representing parsed shell command structures."""

    node_type: str  # "command", "pipeline", "subshell", "redirect", "variable_assignment", "process_substitution", "compound"
    raw: str
    binary: str = ""
    arguments: tuple[str, ...] = ()
    operators: tuple[str, ...] = ()
    redirections: tuple[str, ...] = ()
    variables: tuple[tuple[str, str], ...] = ()
    children: tuple[BashAstNode, ...] = ()
    span: tuple[int, int] = (0, 0)
    verdict: str = "allow"  # "allow", "prompt", "deny"
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize AST node to dictionary."""
        return {
            "node_type": self.node_type,
            "raw": self.raw,
            "binary": self.binary,
            "arguments": list(self.arguments),
            "operators": list(self.operators),
            "redirections": list(self.redirections),
            "variables": [list(v) for v in self.variables],
            "children": [c.to_dict() for c in self.children],
            "span": list(self.span),
            "verdict": self.verdict,
            "reason": self.reason,
        }


@dataclass(slots=True, frozen=True)
class TranscriptFrame:
    """Slotted and frozen normalized frame in the isomorphic transcript stream."""

    frame_id: str
    turn_index: int
    granularity: str  # "off", "turn", "block", "delta"
    event_type: str
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        """Serialize transcript frame to dictionary."""
        return {
            "frame_id": self.frame_id,
            "turn_index": self.turn_index,
            "granularity": self.granularity,
            "event_type": self.event_type,
            "payload": self.payload,
            "timestamp": self.timestamp,
        }


@dataclass(slots=True, frozen=True)
class ScopeAnnotation:
    """Slotted metadata annotation representing an inspected ServiceContext scope layer."""

    context_id: str
    scope_type: str  # "app", "workspace", "session", "agent"
    parent_id: str | None = None
    depth: int = 0
    service_keys: tuple[str, ...] = ()
    active_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Serialize scope annotation to dictionary."""
        return {
            "context_id": self.context_id,
            "scope_type": self.scope_type,
            "parent_id": self.parent_id,
            "depth": self.depth,
            "service_keys": list(self.service_keys),
            "active_count": self.active_count,
        }


@dataclass(slots=True, frozen=True)
class MiniDbRecord:
    """Slotted and frozen record representing an embedded MiniDb document with WAL metadata."""

    key: str
    collection: str
    value: dict[str, Any]
    generation: int = 1
    crc32_checksum: int = 0
    wal_sequence: int = 0
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        """Serialize record to dictionary."""
        return {
            "key": self.key,
            "collection": self.collection,
            "value": self.value,
            "generation": self.generation,
            "crc32_checksum": self.crc32_checksum,
            "wal_sequence": self.wal_sequence,
            "timestamp": self.timestamp,
        }


@runtime_checkable
class KimiTranscriptService(Protocol):
    """Protocol defining transcript projection and scope inspection capabilities."""

    def project_transcript(
        self,
        frames: list[dict[str, Any]] | list[TranscriptFrame],
        granularity: str = "delta",
        cursor: int = 0,
        limit: int = 100,
    ) -> dict[str, Any]:
        """Projects transcript frames according to requested granularity level."""
        ...

    def inspect_context_hierarchy(self, context: Any) -> list[ScopeAnnotation]:
        """Walks ServiceContext parent-child chain and produces scope hierarchy annotations."""
        ...


@runtime_checkable
class KimiMiniDbService(Protocol):
    """Protocol defining in-memory KV operations with durable WAL and snapshot compaction."""

    def put(self, collection: str, key: str, value: dict[str, Any]) -> MiniDbRecord:
        """Insert or update a document, appending a CRC32 frame to WAL."""
        ...

    def get(self, collection: str, key: str) -> MiniDbRecord | None:
        """Retrieve a document by collection and key."""
        ...

    def scan(self, collection: str, filter_fn: Any | None = None) -> list[MiniDbRecord]:
        """Scan documents in a collection matching an optional filter."""
        ...

    def compact(self, target_generation: int | None = None) -> dict[str, Any]:
        """Trigger generational snapshot compaction, flushing memory state to baseline."""
        ...


@runtime_checkable
class KimiBridgeService(Protocol):
    """Unified bridge interface connecting Kimi Code architectural patterns."""

    @property
    def transcript(self) -> KimiTranscriptService:
        ...

    @property
    def minidb(self) -> KimiMiniDbService:
        ...
