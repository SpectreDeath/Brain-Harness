"""CLI and service commands for endogenous reflection and memory distillation."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import structlog

from harness.creator.reflection import (
    HarnessReflectorEngine,
    MemoryPatternPipeline,
    ReflectionReport,
    ReflectionScope,
)
from harness.services.storage import SQLiteStorageService

logger = structlog.get_logger(__name__)


async def run_reflection_cmd(
    *,
    db_path: str = ":memory:",
    scope: ReflectionScope | None = None,
    since_iso: str | None = None,
    conv_id: str | None = None,
    category: str | None = None,
    min_confidence: float = 0.80,
    limit: int = 50,
    commit_to_vault: bool = True,
    generate_html: bool = True,
    vault_dir: Path | str = ".harness/knowledge",
    temp_dir: Path | str | None = None,
    app_data_dir: Path | str | None = None,
    pipeline: MemoryPatternPipeline | None = None,
) -> ReflectionReport:
    """Run an endogenous memory reflection loop and distill knowledge items."""
    # Build or adapt scope
    if scope is None:
        since_dt = None
        if since_iso:
            try:
                since_dt = datetime.fromisoformat(since_iso)
            except Exception as e:
                logger.warning("Invalid since_iso timestamp, ignoring", since=since_iso, error=str(e))

        conv_list = [conv_id] if conv_id else None
        cat_list = [category] if category else None

        scope = ReflectionScope(
            since=since_dt,
            conversation_ids=conv_list,
            categories=cat_list,
            min_confidence=min_confidence,
            limit=limit,
        )

    storage = SQLiteStorageService(db_path=db_path)
    try:
        engine = HarnessReflectorEngine(
            storage=storage,
            temp_dir=temp_dir,
            app_data_dir=app_data_dir,
            pipeline=pipeline,
        )
        report = await engine.reflect(
            scope=scope,
            commit_to_vault=commit_to_vault,
            generate_html_brief=generate_html,
            vault_dir=vault_dir,
        )
        return report
    finally:
        storage.close()
