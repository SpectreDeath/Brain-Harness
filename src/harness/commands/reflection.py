"""CLI and service commands for endogenous reflection and memory distillation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import structlog

from harness.creator.reflection import HarnessReflectorEngine, ReflectionReport
from harness.services.storage import SQLiteStorageService

logger = structlog.get_logger(__name__)


async def run_reflection_cmd(
    *,
    db_path: str = ":memory:",
    commit_to_vault: bool = True,
    generate_html: bool = True,
    vault_dir: Path | str = ".harness/knowledge",
    temp_dir: Path | str | None = None,
    app_data_dir: Path | str | None = None,
) -> ReflectionReport:
    """Run an endogenous memory reflection loop and distill knowledge items."""
    storage = SQLiteStorageService(db_path=db_path)
    try:
        engine = HarnessReflectorEngine(
            storage=storage,
            temp_dir=temp_dir,
            app_data_dir=app_data_dir,
        )
        report = await engine.reflect(
            commit_to_vault=commit_to_vault,
            generate_html_brief=generate_html,
            vault_dir=vault_dir,
        )
        return report
    finally:
        storage.close()
