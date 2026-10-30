"""Authoritative coordinator for internal reflection and knowledge distillation."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import uuid
from datetime import datetime, timezone

import structlog

from harness.creator.reflection.distiller import EpisodicMemoryReflector
from harness.creator.reflection.extractors import MemoryPatternPipeline
from harness.creator.reflection.harvester import HarnessHistoryHarvester
from harness.creator.reflection.models import (
    DistilledHeuristic,
    ReflectionReport,
    ReflectionScope,
    ReportArtifact,
    TranscriptSession,
)
from harness.creator.reflection.visualizer import generate_reflection_html_brief
from harness.kernel.context import ServiceContext, ServiceKey
from harness.services.storage import KnowledgeItemRecord, StorageService, propose_links

logger = structlog.get_logger(__name__)


class HarnessReflectorEngine:
    """Authoritative coordinator for internal reflection and knowledge distillation."""

    def __init__(
        self,
        storage: StorageService | None = None,
        temp_dir: Path | str | None = None,
        app_data_dir: Path | str | None = None,
        pipeline: MemoryPatternPipeline | None = None,
    ) -> None:
        self.storage = storage
        self.harvester = HarnessHistoryHarvester(temp_dir=temp_dir, app_data_dir=app_data_dir)
        self.pipeline = pipeline or MemoryPatternPipeline()

    async def reflect(
        self,
        *,
        scope: ReflectionScope | None = None,
        test_report_path: Path | str | None = None,
        commit_to_vault: bool = True,
        generate_html_brief: bool = True,
        vault_dir: Path | str = ".harness/knowledge",
    ) -> ReflectionReport:
        """Execute full endogenous reflection cycle across internal memory."""
        reflection_id = f"ref_{uuid.uuid4().hex[:8]}"
        now_iso = datetime.now(timezone.utc).isoformat()

        # 1. Harvest with scope
        reports = self.harvester.harvest_temp_reports(scope=scope)
        if test_report_path:
            junit_reports = self.harvester.harvest_junit_reports(test_report_path, scope=scope)
            reports.extend(junit_reports)
        transcripts = self.harvester.harvest_transcripts(scope=scope)

        # 2. Distill through pluggable pipeline
        heuristics = self.pipeline.distill(reports, transcripts, scope=scope)

        # 3. Formulate Knowledge Items
        kis: list[KnowledgeItemRecord] = []
        for idx, h in enumerate(heuristics, start=1):
            ki = EpisodicMemoryReflector.to_knowledge_item(h, index=idx)
            kis.append(ki)

        # 4. Commit to storage vault if available (single write seam)
        if commit_to_vault and self.storage is not None:
            existing_items = await self.storage.list_knowledge_items()
            for ki in kis:
                proposed = propose_links(ki, existing_items)
                for p in proposed:
                    if not any(e.type == p.type and e.target == p.target for e in ki.edges):
                        ki.edges.append(p)
                await self.storage.save_knowledge_item(ki, vault_dir=vault_dir)

        # 5. Generate Visual Brief
        html_path: Path | None = None
        if generate_html_brief:
            html_path = self._generate_visual_brief(reflection_id, reports, transcripts, heuristics, kis)

        report = ReflectionReport(
            reflection_id=reflection_id,
            timestamp=now_iso,
            harvested_reports_count=len(reports),
            harvested_transcripts_count=len(transcripts),
            heuristics=heuristics,
            knowledge_items=kis,
            html_brief_path=html_path,
        )

        logger.info(
            "Endogenous reflection cycle completed",
            reflection_id=reflection_id,
            reports=len(reports),
            transcripts=len(transcripts),
            heuristics=len(heuristics),
        )

        return report

    def _generate_visual_brief(
        self,
        reflection_id: str,
        reports: list[ReportArtifact],
        transcripts: list[TranscriptSession],
        heuristics: list[DistilledHeuristic],
        kis: list[KnowledgeItemRecord],
    ) -> Path:
        """Generate an interactive HTML reflection brief in %TEMP%."""
        return generate_reflection_html_brief(
            output_dir=self.harvester.temp_dir,
            reflection_id=reflection_id,
            reports=reports,
            transcripts=transcripts,
            heuristics=heuristics,
            kis=kis,
        )


HARNESS_REFLECTOR_ENGINE_KEY: ServiceKey[HarnessReflectorEngine] = ServiceKey(
    "service.harness_reflector_engine"
)


def resolve_reflector_engine(
    context: ServiceContext | None = None,
    *,
    storage: StorageService | None = None,
    temp_dir: Path | str | None = None,
    app_data_dir: Path | str | None = None,
    pipeline: MemoryPatternPipeline | None = None,
) -> HarnessReflectorEngine:
    """Resolve HarnessReflectorEngine from IoC context or instantiate standalone fallback (Rule 58)."""
    if context is not None:
        service = context.optional(HARNESS_REFLECTOR_ENGINE_KEY)
        if service is not None:
            return service

    return HarnessReflectorEngine(
        storage=storage,
        temp_dir=temp_dir,
        app_data_dir=app_data_dir,
        pipeline=pipeline,
    )


__all__ = [
    "HARNESS_REFLECTOR_ENGINE_KEY",
    "HarnessReflectorEngine",
    "resolve_reflector_engine",
]
