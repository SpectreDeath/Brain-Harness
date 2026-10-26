"""Storage data models for Isnad provenance and Knowledge Items."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class IsnadClaimStatus(str, Enum):
    """Lifecycle status of an empirical or architectural claim."""

    UNVERIFIED = "unverified"
    VERIFIED = "verified"
    CHALLENGED = "challenged"
    SUPERSEDED = "superseded"


class IsnadClaim(BaseModel):
    """Granular assertion with provenance, confidence, and lifecycle state."""

    claim_id: str | None = Field(default=None, description="Unique claim identifier")
    assertion: str = Field(..., description="Actionable architectural or empirical statement")
    status: str = Field(default=IsnadClaimStatus.VERIFIED.value, description="Lifecycle status")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence score [0.0, 1.0]")
    evidence: str | None = Field(default=None, description="Empirical evidence or test receipt")
    evidence_type: str | None = Field(default=None, description="Category of evidence")
    source: str | None = Field(default=None, description="Primary source citation")
    verified: bool = Field(default=True, description="Boolean verification flag")
    verified_by: str | None = Field(default=None, description="Test signature or verifying command")
    superseded_by: str | None = Field(default=None, description="Target claim or KI ID that supersedes this")
    challenged_reason: str | None = Field(default=None, description="Critique or contradiction notes")
    lineage: list[dict[str, Any]] = Field(default_factory=list, description="Provenance lineage nodes")


class KnowledgeEdge(BaseModel):
    """Typed directional edge connecting Knowledge Items, skills, plugins, and sources."""

    type: str = Field(..., description="became_skill, became_plugin, distilled_from, references_code, synthesizes, supersedes, contradicts, same_domain")
    target: str = Field(..., description="Target node identifier, path, URI, or skill name")
    target_kind: str = Field(default="ki", description="Entity kind: ki, skill, plugin, source, path")
    derived: bool = Field(default=False, description="Whether edge was automatically inferred")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Edge confidence score")
    description: str | None = Field(default=None, description="Optional relationship context")


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
    claims: list[dict[str, Any] | IsnadClaim] = Field(default_factory=list, description="Audited assertions and provenance nodes")
    status: str = Field(default="VERIFIED", description="Lineage status: VERIFIED, HYPOTHESIS, REJECTED, CHALLENGED")


class KnowledgeItemRecord(BaseModel):
    """Ground-truth Knowledge Item (KI) extracted from brains, repos, or audits."""

    schema_version: str = Field(default="1.0.0", description="Schema version identifier")
    id: str = Field(..., description="Unique KI identifier (e.g. ki_20260822_01)")
    title: str = Field(..., description="Actionable heuristic or pattern title")
    source_target: str = Field(default="", description="Origin folder path, Git URL, or brain URI")
    detected_format: str = Field(default="raw_docs", description="Format signature: antigravity_brain, git_repository, ide_memo, etc.")
    isnad: IsnadLineageBlock | dict[str, Any] = Field(default_factory=dict, description="Chain of custody provenance")
    tags: list[str] = Field(default_factory=list, description="Categorization tags")
    category: str = Field(default="general", description="Categorization domain")
    summary: str = Field(default="", description="Operational guideline and implementation details")
    edges: list[KnowledgeEdge] = Field(default_factory=list, description="Typed directional lineage edges")
    anchors: dict[str, Any] = Field(default_factory=dict, description="Named code and architectural anchors")
    author: str | None = Field(default=None, description="Author or synthesizing agent")
    retrieval_count: int = Field(default=0, description="Cumulative count of retrievals into agent context")
    success_count: int = Field(default=0, description="Cumulative count of successful completions")
    last_retrieved_at: str | None = Field(default=None, description="ISO timestamp of most recent retrieval")
    status: str = Field(default="ACTIVE", description="Lifecycle status: ACTIVE, PROMOTED, DEMOTED, ARCHIVED, CHALLENGED, SUPERSEDED")
    superseded_by: str | None = Field(default=None, description="Replacement KI ID if superseded")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def get_claims(self) -> list[IsnadClaim]:
        """Return typed IsnadClaim objects from isnad block."""
        claims_data = []
        if isinstance(self.isnad, IsnadLineageBlock):
            claims_data = self.isnad.claims
        elif isinstance(self.isnad, dict):
            claims_data = self.isnad.get("claims", [])

        typed: list[IsnadClaim] = []
        for c in claims_data:
            if isinstance(c, IsnadClaim):
                typed.append(c)
            elif isinstance(c, dict):
                try:
                    typed.append(IsnadClaim.model_validate(c))
                except Exception:
                    typed.append(IsnadClaim(assertion=c.get("assertion", str(c)), evidence=c.get("evidence")))
        return typed

    def add_edge(
        self,
        edge_type: str,
        target: str,
        target_kind: str = "ki",
        derived: bool = False,
        confidence: float = 1.0,
        description: str | None = None,
    ) -> KnowledgeEdge:
        """Add a typed relationship edge if not already present."""
        for e in self.edges:
            if e.type == edge_type and e.target == target:
                return e
        edge = KnowledgeEdge(
            type=edge_type,
            target=target,
            target_kind=target_kind,
            derived=derived,
            confidence=confidence,
            description=description,
        )
        self.edges.append(edge)
        return edge

    def challenge_claim(self, assertion_match: str, reason: str) -> bool:
        """Transition claim to challenged status."""
        matched = False
        claims = self.get_claims()
        for c in claims:
            if assertion_match.lower() in c.assertion.lower():
                c.status = IsnadClaimStatus.CHALLENGED.value
                c.challenged_reason = reason
                matched = True
        if matched and isinstance(self.isnad, (IsnadLineageBlock, dict)):
            dumped = [c.model_dump() for c in claims]
            if isinstance(self.isnad, IsnadLineageBlock):
                self.isnad.claims = dumped
            else:
                self.isnad["claims"] = dumped
        return matched

    def supersede_claim(self, assertion_match: str, replacement_id: str) -> bool:
        """Transition claim to superseded status."""
        matched = False
        claims = self.get_claims()
        for c in claims:
            if assertion_match.lower() in c.assertion.lower():
                c.status = IsnadClaimStatus.SUPERSEDED.value
                c.superseded_by = replacement_id
                matched = True
        if matched and isinstance(self.isnad, (IsnadLineageBlock, dict)):
            dumped = [c.model_dump() for c in claims]
            if isinstance(self.isnad, IsnadLineageBlock):
                self.isnad.claims = dumped
            else:
                self.isnad["claims"] = dumped
        return matched
