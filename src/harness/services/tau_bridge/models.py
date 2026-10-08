"""Domain dataclasses and serialization DTOs for TauBridge & Pi coding harness.

Rule 12: Slotted & frozen dataclasses with __post_init__ validation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Slotted & Frozen Dataclass Domain Models (Rule 12)
# ---------------------------------------------------------------------------


@dataclass(slots=True, frozen=True)
class SessionNode:
    """Immutable session tree entry node forming the conversation DAG."""

    id: str
    parent_id: str | None = None
    type: str = "message"
    role: str = "user"
    content: str = ""
    tool_calls: tuple[dict[str, Any], ...] = ()
    tool_call_id: str | None = None
    timestamp: str = ""

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("SessionNode id cannot be empty.")
        if self.parent_id == self.id:
            raise ValueError("SessionNode parent_id cannot reference itself (cycle).")

    def to_dict(self) -> dict[str, Any]:
        """Convert immutable node to dictionary."""
        d: dict[str, Any] = {
            "id": self.id,
            "type": self.type,
            "role": self.role,
            "content": self.content,
        }
        if self.parent_id is not None:
            d["parent_id"] = self.parent_id
        if self.tool_calls:
            d["tool_calls"] = list(self.tool_calls)
        if self.tool_call_id is not None:
            d["tool_call_id"] = self.tool_call_id
        if self.timestamp:
            d["timestamp"] = self.timestamp
        return d


@dataclass(slots=True, frozen=True)
class BranchPath:
    """Resolved linear conversation ancestry from root to target entry."""

    target_id: str
    path_entries: tuple[SessionNode, ...]
    depth: int
    total_entries: int
    branch_count: int

    def __post_init__(self) -> None:
        if self.depth < 0:
            raise ValueError("BranchPath depth cannot be negative.")


@dataclass(slots=True, frozen=True)
class ToolCallRecord:
    """Normalized tool call reference."""

    call_id: str
    tool_name: str
    arguments: str = "{}"

    def __post_init__(self) -> None:
        if not self.call_id:
            raise ValueError("ToolCallRecord call_id cannot be empty.")


@dataclass(slots=True, frozen=True)
class HistoryRepairResult:
    """Immutable result of provider-safe tool history normalization."""

    repaired_messages: tuple[dict[str, Any], ...]
    dropped_count: int
    synthesized_count: int
    repairs_applied: tuple[str, ...]
    is_modified: bool

    def __post_init__(self) -> None:
        if self.dropped_count < 0 or self.synthesized_count < 0:
            raise ValueError("Drop and synthesis counts must be non-negative.")


@dataclass(slots=True, frozen=True)
class TrustScope:
    """Workspace boundary trust and security analysis."""

    project_path: str
    is_trusted: bool
    git_root: str | None
    protected_assets: tuple[str, ...]
    warnings: tuple[str, ...]
    permission_level: str

    def __post_init__(self) -> None:
        if self.permission_level not in {"TRUSTED", "RESTRICTED", "BLOCKED"}:
            raise ValueError(f"Invalid permission level: {self.permission_level}")


@dataclass(slots=True, frozen=True)
class JournalEntryRecord:
    """Immutable record of an append-only locked journal entry."""

    journal_path: str
    entry_id: str
    byte_offset: int
    timestamp: str

    def __post_init__(self) -> None:
        if self.byte_offset < 0:
            raise ValueError("byte_offset cannot be negative.")


# ---------------------------------------------------------------------------
# Pydantic DTOs for CLI / API Serialization
# ---------------------------------------------------------------------------


class SessionPathResult(BaseModel):
    """Payload representing linear ancestry traversal from root to a target branch entry."""

    target_id: str = Field(..., description="ID of the resolved target entry")
    path_entries: list[dict[str, Any]] = Field(
        default_factory=list, description="Ordered linear entries from root to target"
    )
    depth: int = Field(..., description="Number of entries in the linear ancestry path")
    total_tree_entries: int = Field(
        ..., description="Total entries present in the session graph"
    )
    branch_count: int = Field(
        ..., description="Number of branch points detected across the tree"
    )


class HistoryRepairReport(BaseModel):
    """Payload representing in-flight provider-safe tool history normalization."""

    repaired_messages: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Cleaned, provider-safe message list ready for model invocation",
    )
    dropped_count: int = Field(
        default=0, description="Number of orphan or malformed tool messages dropped"
    )
    synthesized_count: int = Field(
        default=0,
        description="Number of placeholder tool results synthesized for unresponded calls",
    )
    repairs_applied: list[str] = Field(
        default_factory=list, description="Human-readable log of specific repairs made"
    )
    is_modified: bool = Field(
        ..., description="Whether message history required modification"
    )


class ProjectTrustEvaluation(BaseModel):
    """Payload representing workspace boundary trust evaluation."""

    project_path: str = Field(..., description="Target project canonical path")
    is_trusted: bool = Field(
        ..., description="Whether target project is within trusted scope"
    )
    git_root: str | None = Field(
        default=None, description="Discovered Git root directory if present"
    )
    protected_assets: list[str] = Field(
        default_factory=list,
        description="Detected sensitive/protected files (.env, credentials, etc.)",
    )
    warnings: list[str] = Field(
        default_factory=list, description="Security and permission warnings"
    )
    permission_level: str = Field(
        ..., description="Permission tier: TRUSTED | RESTRICTED | BLOCKED"
    )


class RpcProtocolEnvelope(BaseModel):
    """Payload representing a Pi-compatible JSONL RPC response envelope."""

    jsonrpc: str = Field(default="2.0", description="RPC protocol version")
    id: str | int | None = Field(..., description="Request identifier")
    result: Any = Field(default=None, description="Success payload if applicable")
    error: dict[str, Any] | None = Field(
        default=None, description="Error payload if applicable"
    )


__all__ = [
    "BranchPath",
    "HistoryRepairReport",
    "HistoryRepairResult",
    "JournalEntryRecord",
    "ProjectTrustEvaluation",
    "RpcProtocolEnvelope",
    "SessionNode",
    "SessionPathResult",
    "ToolCallRecord",
    "TrustScope",
]
