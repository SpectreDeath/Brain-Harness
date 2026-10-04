"""Conversation Trajectory Miner Plugin for Brain Harness (Rule 1, Rule 2, Rule 45, Rule 49).

Registers the ConversationTrajectoryMinerService into the micro-kernel IoC container.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

import structlog

from harness.kernel.context import ServiceContext
from harness.plugins.base import HarnessPlugin
from harness.services.conversation_trajectory_miner import (
    CONVERSATION_TRAJECTORY_MINER_KEY,
    CognitiveBifurcationReport,
    ConversationManifest,
    ConversationTrajectoryMinerService,
    FailureCluster,
    FrictionScorecard,
    StandardConversationTrajectoryMinerService,
)

logger = structlog.get_logger(__name__)


class ConversationTrajectoryMinerPlugin(HarnessPlugin):
    """Domain-partitioned plugin for autobiographical trajectory mining and friction analysis."""

    name = "plugin.conversation_trajectory_miner"
    version = "0.1.0"
    description = "Autobiographical trajectory archaeology and dual-lens cognitive bifurcation"
    author = "Brain Harness Forge Engine"

    def __init__(self) -> None:
        super().__init__()
        self._service = StandardConversationTrajectoryMinerService()

    @property
    def provides(self) -> list[Any]:
        return [CONVERSATION_TRAJECTORY_MINER_KEY]

    @property
    def requires(self) -> list[Any]:
        return []

    async def on_load(self, ctx: ServiceContext) -> None:
        logger.info("loading_plugin", plugin=self.name)
        ctx.provide(CONVERSATION_TRAJECTORY_MINER_KEY, self._service, provider=self.name)

    async def on_enable(self) -> None:
        logger.info("enabling_plugin", plugin=self.name)

    async def on_disable(self) -> None:
        logger.info("disabling_plugin", plugin=self.name)

    async def on_unload(self) -> None:
        logger.info("unloading_plugin", plugin=self.name)

    # -------------------------------------------------------------------------
    # Delegation Seams
    # -------------------------------------------------------------------------

    def connect_ro(self, db_path: Path | str) -> sqlite3.Connection:
        return self._service.connect_ro(db_path)

    def inspect_conversation(self, db_path: Path) -> ConversationManifest | None:
        return self._service.inspect_conversation(db_path)

    def scan_corpus(
        self, corpus_dir: Path | str, max_dbs: int | None = None
    ) -> list[ConversationManifest]:
        return self._service.scan_corpus(corpus_dir, max_dbs=max_dbs)

    def compile_friction_scorecard(
        self, manifests: list[ConversationManifest]
    ) -> FrictionScorecard:
        return self._service.compile_friction_scorecard(manifests)

    def mine_failure_clusters(
        self, corpus_dir: Path | str, max_dbs: int | None = None
    ) -> list[FailureCluster]:
        return self._service.mine_failure_clusters(corpus_dir, max_dbs=max_dbs)

    def bifurcate_distillation(
        self,
        cid: str,
        db_path: Path,
        output_vault_dir: Path,
        output_skills_dir: Path | None = None,
    ) -> CognitiveBifurcationReport:
        return self._service.bifurcate_distillation(
            cid=cid,
            db_path=db_path,
            output_vault_dir=output_vault_dir,
            output_skills_dir=output_skills_dir,
        )

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
plugin = ConversationTrajectoryMinerPlugin()
