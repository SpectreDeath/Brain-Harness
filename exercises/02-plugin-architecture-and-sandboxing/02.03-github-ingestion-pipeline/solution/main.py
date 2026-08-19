"""Exercise 02.03: GitHub Ingestion Pipeline (Solution)."""

from __future__ import annotations

from pathlib import Path

from harness.ingestion import PluginIngestionPipeline
from harness.plugins.sandboxed import SandboxedPlugin


async def ingest_local_repo(repo_dir: Path) -> SandboxedPlugin:
    pipeline = PluginIngestionPipeline()
    return await pipeline.ingest(repo_dir)
