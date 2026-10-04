"""Brain Artifact Miner Plugin for Brain Harness (Rule 1, Rule 2, Rule 45, Rule 49).

Registers the BrainArtifactMinerService into the micro-kernel IoC container.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from collections.abc import Iterator

import structlog

from harness.kernel.context import ServiceContext
from harness.plugins.base import HarnessPlugin
from harness.services.brain_artifact_miner import (
    BRAIN_ARTIFACT_MINER_KEY,
    BrainArtifactMinerService,
    ScratchCatalog,
    StandardBrainArtifactMinerService,
    TaskTriageReport,
)

logger = structlog.get_logger(__name__)


class BrainArtifactMinerPlugin(HarnessPlugin):
    """Domain-partitioned plugin for brain artifact mining and scratch tool archaeology."""

    name = "plugin.brain_artifact_miner"
    version = "0.1.0"
    description = "Filesystem-native brain workspace archaeology and scratch tool salvage"
    author = "Brain Harness Forge Engine"

    def __init__(self) -> None:
        super().__init__()
        self._service = StandardBrainArtifactMinerService()

    @property
    def provides(self) -> list[Any]:
        return [BRAIN_ARTIFACT_MINER_KEY]

    @property
    def requires(self) -> list[Any]:
        return []

    async def on_load(self, ctx: ServiceContext) -> None:
        logger.info("loading_plugin", plugin=self.name)
        ctx.provide(BRAIN_ARTIFACT_MINER_KEY, self._service, provider=self.name)

    async def on_enable(self) -> None:
        logger.info("enabling_plugin", plugin=self.name)

    async def on_disable(self) -> None:
        logger.info("disabling_plugin", plugin=self.name)

    async def on_unload(self) -> None:
        logger.info("unloading_plugin", plugin=self.name)

    # -------------------------------------------------------------------------
    # Delegation Seams
    # -------------------------------------------------------------------------

    def build_offset_index(self, path: Path) -> dict[int, tuple[int, int]]:
        return self._service.build_offset_index(path)

    def get_step(
        self,
        transcript_path: Path,
        step_index: int,
        dereference_truncated: bool = True,
    ) -> dict[str, Any] | None:
        return self._service.get_step(
            transcript_path=transcript_path,
            step_index=step_index,
            dereference_truncated=dereference_truncated,
        )

    def stream_steps(
        self,
        transcript_path: Path,
        dereference_truncated: bool = True,
    ) -> Iterator[dict[str, Any]]:
        return self._service.stream_steps(
            transcript_path=transcript_path,
            dereference_truncated=dereference_truncated,
        )

    def scan_scratch_tools(self, brain_dir: Path, max_depth: int = 3) -> ScratchCatalog:
        return self._service.scan_scratch_tools(brain_dir, max_depth=max_depth)

    def triage_task_logs(self, brain_dir: Path, max_depth: int = 4) -> TaskTriageReport:
        return self._service.triage_task_logs(brain_dir, max_depth=max_depth)

    def generate_html_brief(self, data: dict[str, Any]) -> str:
        return self._service.generate_html_brief(data)

    def export_knowledge_item(
        self,
        output_dir: Path,
        ki_id: str,
        title: str,
        category: str,
        summary: str,
        claims: list[dict[str, Any]],
    ) -> tuple[Path, Path]:
        return self._service.export_knowledge_item(
            output_dir=output_dir,
            ki_id=ki_id,
            title=title,
            category=category,
            summary=summary,
            claims=claims,
        )


# Module-level singleton (Rule 45)
plugin = BrainArtifactMinerPlugin()
