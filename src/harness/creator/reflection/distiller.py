"""Episodic memory reflection and Knowledge Item synthesis."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

from harness.creator.reflection.extractors import MemoryPatternPipeline
from harness.creator.reflection.models import (
    DistilledHeuristic,
    ReflectionScope,
    ReportArtifact,
    TranscriptSession,
)
from harness.services.storage import (
    IsnadLineageBlock,
    KnowledgeItemRecord,
)


class EpisodicMemoryReflector:
    """Helper for converting heuristics into ground-truth KnowledgeItemRecords."""

    @classmethod
    def distill(
        cls,
        reports: Sequence[ReportArtifact],
        transcripts: Sequence[TranscriptSession],
        scope: ReflectionScope | None = None,
    ) -> list[DistilledHeuristic]:
        """Delegate distillation to default MemoryPatternPipeline."""
        pipeline = MemoryPatternPipeline()
        return pipeline.distill(reports, transcripts, scope=scope)

    @classmethod
    def to_knowledge_item(cls, heuristic: DistilledHeuristic, index: int = 1) -> KnowledgeItemRecord:
        """Convert a distilled heuristic into a canonical KnowledgeItemRecord."""
        date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        ki_id = f"ki_self_{date_str}_{index:02d}"

        isnad_block = IsnadLineageBlock(
            decision_id=f"decision_{ki_id}",
            timestamp=datetime.now(timezone.utc).isoformat(),
            claims=heuristic.isnad_claims,
            status="VERIFIED",
        )

        tags = [heuristic.category, "endogenous_memory", "self_reflection"]

        summary = (
            f"### Distilled Heuristic\n{heuristic.heuristic}\n\n"
            f"### Named Anti-Pattern\n{heuristic.anti_pattern or 'None recorded.'}\n\n"
            f"### Empirical Evidence & Provenance\n"
            f"- **Sources**: {', '.join(Path(s).name for s in heuristic.source_artifacts)}\n"
            f"- **Confidence**: {heuristic.confidence * 100:.0f}%\n"
        )

        return KnowledgeItemRecord(
            id=ki_id,
            title=heuristic.title,
            source_target="internal://harness/history",
            detected_format="endogenous_reflection",
            isnad=isnad_block,
            tags=tags,
            summary=summary,
        )


__all__ = [
    "EpisodicMemoryReflector",
]
