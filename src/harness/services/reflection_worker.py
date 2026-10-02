"""Scheduled Daemon Worker for Continuous Autobiographical Reflection & Knowledge Distillation.

Wires the endogenous reflection loop into a background daemon worker that continuously
or periodically distills test run trajectories, visual briefs, and execution traces into
verified, Isnad-grounded Knowledge Items.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import structlog

from harness.creator.reflection import (
    HarnessReflectorEngine,
    MemoryPatternPipeline,
    ReflectionReport,
    ReflectionScope,
)
from harness.kernel.context import ServiceKey
from harness.services.storage import SQLiteStorageService

logger = structlog.get_logger(__name__)


class ReflectionDaemonWorker:
    """Scheduled background worker running continuous endogenous reflection."""

    def __init__(
        self,
        *,
        interval_seconds: float = 300.0,
        test_report_path: Path | str | None = None,
        vault_dir: Path | str = ".harness/knowledge",
        db_path: str = ":memory:",
        commit_to_vault: bool = True,
        generate_html: bool = False,
        min_confidence: float = 0.80,
    ) -> None:
        self.interval_seconds = interval_seconds
        self.test_report_path = Path(test_report_path) if test_report_path else None
        self.vault_dir = Path(vault_dir)
        self.db_path = db_path
        self.commit_to_vault = commit_to_vault
        self.generate_html = generate_html
        self.min_confidence = min_confidence

        self._running: bool = False
        self._task: asyncio.Task[None] | None = None
        self._cycle_count: int = 0
        self._last_report: ReflectionReport | None = None

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def cycle_count(self) -> int:
        return self._cycle_count

    @property
    def last_report(self) -> ReflectionReport | None:
        return self._last_report

    async def step(self) -> ReflectionReport:
        """Execute a single reflection and distillation pass."""
        scope = ReflectionScope(
            min_confidence=self.min_confidence,
            limit=50,
        )
        storage = SQLiteStorageService(db_path=self.db_path)
        try:
            pipeline = MemoryPatternPipeline()
            engine = HarnessReflectorEngine(
                storage=storage,
                pipeline=pipeline,
            )
            report = await engine.reflect(
                scope=scope,
                test_report_path=self.test_report_path,
                commit_to_vault=self.commit_to_vault,
                generate_html_brief=self.generate_html,
                vault_dir=self.vault_dir,
            )
            self._cycle_count += 1
            self._last_report = report
            logger.info(
                "Reflection daemon cycle completed",
                cycle=self._cycle_count,
                heuristics=len(report.heuristics),
                kis=len(report.knowledge_items),
            )
            return report
        finally:
            storage.close()

    async def _loop(self) -> None:
        """Internal daemon polling loop."""
        logger.info(
            "Starting reflection daemon loop",
            interval=self.interval_seconds,
            test_report=str(self.test_report_path) if self.test_report_path else None,
        )
        while self._running:
            try:
                await self.step()
            except Exception as e:
                logger.warning("Error in reflection daemon cycle", error=str(e))

            try:
                await asyncio.sleep(self.interval_seconds)
            except asyncio.CancelledError:
                break

    def start(self) -> None:
        """Start the background daemon task."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        """Stop the background daemon task."""
        self._running = False
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("Reflection daemon stopped", total_cycles=self._cycle_count)


REFLECTION_WORKER_KEY: ServiceKey[ReflectionDaemonWorker] = ServiceKey(
    "service.reflection_worker"
)
