"""Evidence Isolation Guard Plugin for Brain Harness.

Registers the EvidenceIsolationService into the micro-kernel IoC container (Rule 45, Rule 49),
enforcing answer-key isolation, grader verdict detection, and trial identity tracking.
Synthesized from google/harness2 (arXiv 2610.14224, Apache-2.0).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import structlog

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.recursive_harnessing import (
    EVIDENCE_ISOLATION_SERVICE_KEY,
    DefaultEvidenceIsolationService,
    EvidenceIsolationService,
)

logger = structlog.get_logger(__name__)


class EvidenceIsolationGuardPlugin(HarnessPlugin, EvidenceIsolationService):
    """Plugin providing authoritative evidence isolation and trial identity services."""

    def __init__(self) -> None:
        self._service = DefaultEvidenceIsolationService()

    @property
    def name(self) -> str:
        return "plugin.evidence_isolation_guard"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [EVIDENCE_ISOLATION_SERVICE_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, ctx: ServiceContext) -> None:
        logger.info("loading_plugin", plugin=self.name)
        ctx.provide(EVIDENCE_ISOLATION_SERVICE_KEY, self, provider=self.name)

    async def on_enable(self) -> None:
        logger.info("enabling_plugin", plugin=self.name)

    async def on_disable(self) -> None:
        logger.info("disabling_plugin", plugin=self.name)

    async def on_unload(self) -> None:
        logger.info("unloading_plugin", plugin=self.name)

    # -------------------------------------------------------------------------
    # EvidenceIsolationService Protocol Delegation
    # -------------------------------------------------------------------------

    def assert_no_leak_paths(self, root: Path | str, patterns: Sequence[str]) -> None:
        self._service.assert_no_leak_paths(root, patterns)

    def assert_no_verdicts(self, root: Path | str) -> None:
        self._service.assert_no_verdicts(root)

    def assert_tree_clean(self, tree: Mapping[str, str]) -> None:
        self._service.assert_tree_clean(tree)

    def scrub_env(self, base_env: Mapping[str, str] | None = None, *, keep: Sequence[str] = ()) -> dict[str, str]:
        return self._service.scrub_env(base_env, keep=keep)

    def fingerprint_dir(self, harness_dir: Path | str | None) -> str:
        return self._service.fingerprint_dir(harness_dir)

    def fingerprint_tree(self, tree: Mapping[str, str]) -> str:
        return self._service.fingerprint_tree(tree)

    def mark_complete(
        self,
        where: Path | str,
        *,
        run_id: str,
        harness_dir: Path | str | None = None,
        inputs: str | None = None,
    ) -> Path:
        return self._service.mark_complete(where, run_id=run_id, harness_dir=harness_dir, inputs=inputs)

    def is_complete(
        self,
        where: Path | str,
        *,
        harness_dir: Path | str | None = None,
        match_harness: bool = True,
        inputs: str | None = None,
    ) -> bool:
        return self._service.is_complete(where, harness_dir=harness_dir, match_harness=match_harness, inputs=inputs)


plugin = EvidenceIsolationGuardPlugin()
