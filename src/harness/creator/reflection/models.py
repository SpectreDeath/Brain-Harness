"""Data models and scope filters for endogenous memory and reflection."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from harness.services.storage import KnowledgeItemRecord


@dataclass(slots=True)
class ReflectionScope:
    """Multi-dimensional filter scope for history harvesting and reflection."""

    since: datetime | None = None
    conversation_ids: list[str] | None = None
    categories: list[str] | None = None
    min_confidence: float = 0.80
    limit: int = 50

    def matches_date(self, iso_date_str: str) -> bool:
        """Check if an ISO date string falls at or after `since`."""
        if not self.since:
            return True
        try:
            dt = datetime.fromisoformat(iso_date_str)
            # Ensure timezone awareness comparison
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            cmp_since = self.since if self.since.tzinfo is not None else self.since.replace(tzinfo=timezone.utc)
            return dt >= cmp_since
        except Exception:
            return True

    def matches_conversation(self, conv_id: str) -> bool:
        """Check if a conversation ID matches the scope filter."""
        if not self.conversation_ids:
            return True
        return conv_id in self.conversation_ids

    def matches_category(self, category: str) -> bool:
        """Check if a heuristic category matches the scope filter."""
        if not self.categories:
            return True
        return category.lower() in [c.lower() for c in self.categories]


@dataclass(slots=True)
class ReportArtifact:
    """Parsed HTML architecture review or visual brief from temporary storage."""

    file_path: Path
    title: str
    created_at: str
    report_type: str  # "architecture_review", "compute_assessment", "domain_modeling", "custom", "test_report"
    content_text: str
    friction_points: list[str] = field(default_factory=list)
    mermaid_diagrams: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class TranscriptSession:
    """Parsed conversation transcript and step trajectory."""

    conversation_id: str
    log_path: Path
    total_steps: int
    user_requests: list[str] = field(default_factory=list)
    tools_invoked: list[str] = field(default_factory=list)
    errors_encountered: list[str] = field(default_factory=list)
    recovery_actions: list[str] = field(default_factory=list)


@dataclass(slots=True)
class DistilledHeuristic:
    """An actionable invariant, design rule, or anti-pattern distilled from memory."""

    title: str
    category: str  # "architecture", "error_recovery", "performance", "platform_quirk"
    heuristic: str
    anti_pattern: str | None = None
    confidence: float = 0.95
    source_artifacts: list[str] = field(default_factory=list)
    isnad_claims: list[dict[str, Any]] = field(default_factory=list)


@dataclass(slots=True)
class ReflectionReport:
    """Comprehensive distillation report across harvested memories."""

    reflection_id: str
    timestamp: str
    harvested_reports_count: int
    harvested_transcripts_count: int
    heuristics: list[DistilledHeuristic] = field(default_factory=list)
    knowledge_items: list[KnowledgeItemRecord] = field(default_factory=list)
    html_brief_path: Path | None = None


__all__ = [
    "DistilledHeuristic",
    "ReflectionReport",
    "ReflectionScope",
    "ReportArtifact",
    "TranscriptSession",
]
