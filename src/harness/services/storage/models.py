"""Storage data models for Isnad provenance and Knowledge Items."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class IsnadLineageNode(BaseModel):
    """Lineage node representing a primary source, test receipt, or manifest."""

    node_type: str = Field(..., description="Node category: primary_code, verification_test, manifest, tool_event")
    uri: str = Field(..., description="File path, URL, or identifier with line slice (e.g. file:///...#L10-L20)")
    sha256_hash: str | None = Field(default=None, description="SHA-256 hash of node content")
    verified: bool = Field(default=False, description="Whether node has been verified against ground truth")


class IsnadLineageBlock(BaseModel):
    """Complete Isnad chain-of-custody block verifying architectural claims."""

    decision_id: str = Field(..., description="Unique decision or learning identifier")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat(), description="ISO timestamp")
    claims: list[dict[str, Any]] = Field(default_factory=list, description="Audited assertions and provenance nodes")
    status: str = Field(default="VERIFIED", description="Lineage status: VERIFIED, HYPOTHESIS, REJECTED")


class KnowledgeItemRecord(BaseModel):
    """Ground-truth Knowledge Item (KI) extracted from brains, repos, or audits."""

    id: str = Field(..., description="Unique KI identifier (e.g. ki_20260822_01)")
    title: str = Field(..., description="Actionable heuristic or pattern title")
    source_target: str = Field(..., description="Origin folder path, Git URL, or brain URI")
    detected_format: str = Field(..., description="Format signature: antigravity_brain, git_repository, ide_memo, etc.")
    isnad: IsnadLineageBlock | dict[str, Any] = Field(default_factory=dict, description="Chain of custody provenance")
    tags: list[str] = Field(default_factory=list, description="Categorization tags")
    category: str = Field(default="general", description="Categorization domain")
    summary: str = Field(default="", description="Operational guideline and implementation details")
    retrieval_count: int = Field(default=0, description="Cumulative count of retrievals into agent context")
    success_count: int = Field(default=0, description="Cumulative count of successful completions")
    last_retrieved_at: str | None = Field(default=None, description="ISO timestamp of most recent retrieval")
    status: str = Field(default="ACTIVE", description="Lifecycle status: ACTIVE, PROMOTED, DEMOTED, ARCHIVED")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
