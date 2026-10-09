"""Service protocol, typed service key, and standard service implementation."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from harness.kernel.context import ServiceKey

from .bifurcation import bifurcate_distillation, export_knowledge_item
from .friction import compile_friction_scorecard, mine_failure_clusters
from .models import (
    CognitiveBifurcationReport,
    ConversationManifest,
    FailureCluster,
    FrictionScorecard,
)
from .sqlite_reader import connect_ro, inspect_conversation, scan_corpus


@runtime_checkable
class ConversationTrajectoryMinerService(Protocol):
    """Protocol for autobiographical trajectory mining, friction archaeology, and cognitive bifurcation."""

    def connect_ro(self, db_path: Path | str) -> sqlite3.Connection:
        """Establish proactor-safe read-only SQLite URI connection (Rule 22)."""
        ...

    def inspect_conversation(self, db_path: Path) -> ConversationManifest | None:
        """Inspect a single conversation database and extract metadata safely."""
        ...

    def scan_corpus(
        self, corpus_dir: Path | str, max_dbs: int | None = None
    ) -> list[ConversationManifest]:
        """Scan corpus directory and compile manifests for SQLite conversation databases."""
        ...

    def compile_friction_scorecard(
        self, manifests: list[ConversationManifest]
    ) -> FrictionScorecard:
        """Compile aggregate friction and step distribution scorecard."""
        ...

    def mine_failure_clusters(
        self, corpus_dir: Path | str, max_dbs: int | None = None
    ) -> list[FailureCluster]:
        """Analyze step execution errors across databases and cluster recurring failure modes."""
        ...

    def bifurcate_distillation(
        self,
        cid: str,
        db_path: Path,
        output_vault_dir: Path,
        output_skills_dir: Path | None = None,
    ) -> CognitiveBifurcationReport:
        """Bifurcate session learning into Knowledge Vault item and procedural skill rules (Rule 41)."""
        ...

    def export_knowledge_item(
        self,
        output_dir: Path,
        ki_id: str,
        title: str,
        category: str,
        summary: str,
        claims: list[dict[str, Any]],
    ) -> tuple[Path, Path]:
        """Export canonical Knowledge Vault dual-file format (metadata.json + summary.md, Rule 40)."""
        ...


CONVERSATION_TRAJECTORY_MINER_KEY = ServiceKey[ConversationTrajectoryMinerService](
    "conversation_trajectory_miner_service"
)


class StandardConversationTrajectoryMinerService(ConversationTrajectoryMinerService):
    """Authoritative domain implementation of ConversationTrajectoryMinerService."""

    def connect_ro(self, db_path: Path | str) -> sqlite3.Connection:
        return connect_ro(db_path)

    def inspect_conversation(self, db_path: Path) -> ConversationManifest | None:
        return inspect_conversation(db_path)

    def scan_corpus(
        self, corpus_dir: Path | str, max_dbs: int | None = None
    ) -> list[ConversationManifest]:
        return scan_corpus(corpus_dir, max_dbs=max_dbs)

    def compile_friction_scorecard(
        self, manifests: list[ConversationManifest]
    ) -> FrictionScorecard:
        return compile_friction_scorecard(manifests)

    def mine_failure_clusters(
        self, corpus_dir: Path | str, max_dbs: int | None = None
    ) -> list[FailureCluster]:
        return mine_failure_clusters(corpus_dir, max_dbs=max_dbs)

    def bifurcate_distillation(
        self,
        cid: str,
        db_path: Path,
        output_vault_dir: Path,
        output_skills_dir: Path | None = None,
    ) -> CognitiveBifurcationReport:
        return bifurcate_distillation(
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
        return export_knowledge_item(
            output_dir=output_dir,
            ki_id=ki_id,
            title=title,
            category=category,
            summary=summary,
            claims=claims,
        )


__all__ = [
    "CONVERSATION_TRAJECTORY_MINER_KEY",
    "ConversationTrajectoryMinerService",
    "StandardConversationTrajectoryMinerService",
]
