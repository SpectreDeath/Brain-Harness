"""Temp Artifact Miner Plugin for Brain Harness (Rule 1, Rule 2, Rule 45, Rule 49).

Registers the TempArtifactMinerService into the micro-kernel IoC container.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import structlog

from harness.kernel.context import ServiceContext
from harness.plugins.base import HarnessPlugin
from harness.services.temp_artifact_miner import (
    TEMP_ARTIFACT_MINER_KEY,
    BriefCatalog,
    BriefCatalogItem,
    CognitiveBifurcationReport,
    SandboxReport,
    StandardTempArtifactMinerService,
    TempArtifactMinerService,
    VisualSalvageReport,
)

logger = structlog.get_logger(__name__)


class TempArtifactMinerPlugin(HarnessPlugin):
    """Domain-partitioned plugin for ephemeral artifact mining, visual brief extraction, and sandbox triage."""

    name = "plugin.temp_artifact_miner"
    version = "0.1.0"
    description = "Ephemeral workspace archaeology and dual-lens cognitive bifurcation"
    author = "Brain Harness Forge Engine"

    def __init__(self) -> None:
        super().__init__()
        self._service = StandardTempArtifactMinerService()

    @property
    def provides(self) -> list[Any]:
        return [TEMP_ARTIFACT_MINER_KEY]

    @property
    def requires(self) -> list[Any]:
        return []

    async def on_load(self, ctx: ServiceContext) -> None:
        logger.info("loading_plugin", plugin=self.name)
        ctx.provide(TEMP_ARTIFACT_MINER_KEY, self._service, provider=self.name)

    async def on_enable(self) -> None:
        logger.info("enabling_plugin", plugin=self.name)

    async def on_disable(self) -> None:
        logger.info("disabling_plugin", plugin=self.name)

    async def on_unload(self) -> None:
        logger.info("unloading_plugin", plugin=self.name)

    # -------------------------------------------------------------------------
    # Delegation Seams
    # -------------------------------------------------------------------------

    def scan_briefs(
        self,
        temp_dir: Path | str | None = None,
        max_depth: int = 2,
        heavy_threshold: int = 100000,
    ) -> BriefCatalog:
        return self._service.scan_briefs(
            temp_dir=temp_dir,
            max_depth=max_depth,
            heavy_threshold=heavy_threshold,
        )

    def triage_sandbox(
        self,
        pytest_dir: Path | str | None = None,
        max_depth: int = 3,
    ) -> SandboxReport:
        return self._service.triage_sandbox(pytest_dir=pytest_dir, max_depth=max_depth)

    def tail_diagnostic_log(
        self,
        log_path: Path | str,
        max_lines: int = 50,
    ) -> tuple[str, ...]:
        return self._service.tail_diagnostic_log(log_path=log_path, max_lines=max_lines)

    def generate_salvage_markdown(
        self,
        catalog: BriefCatalog,
        sandbox: SandboxReport | None = None,
    ) -> str:
        return self._service.generate_salvage_markdown(catalog=catalog, sandbox=sandbox)

    def bifurcate_brief(
        self,
        brief_path: Path | str,
        target_vault_dir: Path | str | None = None,
        target_docs_dir: Path | str | None = None,
    ) -> CognitiveBifurcationReport:
        return self._service.bifurcate_brief(
            brief_path=brief_path,
            target_vault_dir=target_vault_dir,
            target_docs_dir=target_docs_dir,
        )

    def salvage_diagrams(
        self,
        brief_path: Path | str,
        target_docs_dir: Path | str | None = None,
    ) -> VisualSalvageReport:
        return self._service.salvage_diagrams(
            brief_path=brief_path,
            target_docs_dir=target_docs_dir,
        )

    def parse_html_brief(
        self,
        file_path: Path,
        heavy_threshold: int = 100000,
    ) -> BriefCatalogItem:
        return self._service.parse_html_brief(
            file_path=file_path,
            heavy_threshold=heavy_threshold,
        )


# Module-level singleton (Rule 45)
plugin = TempArtifactMinerPlugin()
