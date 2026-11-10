"""Recursive Harness Refiner Plugin for Brain Harness.

Registers the RecursiveRefinerService into the micro-kernel IoC container (Rule 45, Rule 49),
enabling task-level Propose-Probe-Compose refinement, blind selection, and experience libraries.
Synthesized from google/harness2 (arXiv 2610.14224, Apache-2.0).
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

import structlog

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.recursive_harnessing import (
    EVIDENCE_ISOLATION_SERVICE_KEY,
    RECURSIVE_REFINER_SERVICE_KEY,
    BudgetLedger,
    CandidateSelector,
    DefaultRecursiveRefinerService,
    ExperienceLibrary,
    HarnessProposer,
    ModeResult,
    RecursiveRefinerService,
    RunView,
    SurfaceSpec,
    TaskAdapter,
    Tree,
)

logger = structlog.get_logger(__name__)


class RecursiveHarnessRefinerPlugin(HarnessPlugin, RecursiveRefinerService):
    """Plugin providing authoritative recursive agent harnessing capabilities."""

    def __init__(self) -> None:
        self._service = DefaultRecursiveRefinerService()

    @property
    def name(self) -> str:
        return "plugin.recursive_harness_refiner"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [RECURSIVE_REFINER_SERVICE_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return [EVIDENCE_ISOLATION_SERVICE_KEY]

    async def on_load(self, ctx: ServiceContext) -> None:
        logger.info("loading_plugin", plugin=self.name)
        ctx.provide(RECURSIVE_REFINER_SERVICE_KEY, self, provider=self.name)

    async def on_enable(self) -> None:
        logger.info("enabling_plugin", plugin=self.name)

    async def on_disable(self) -> None:
        logger.info("disabling_plugin", plugin=self.name)

    async def on_unload(self) -> None:
        logger.info("unloading_plugin", plugin=self.name)

    # -------------------------------------------------------------------------
    # RecursiveRefinerService Protocol Delegation
    # -------------------------------------------------------------------------

    def validate_harness(self, spec: SurfaceSpec, tree: Tree) -> dict[str, Any]:
        return self._service.validate_harness(spec, tree)

    def new_ledger(self, mode: str, task_id: str, k: int) -> BudgetLedger:
        return self._service.new_ledger(mode, task_id, k)

    def open_library(self, root: Path | str, domain: str, spec: SurfaceSpec) -> ExperienceLibrary:
        return self._service.open_library(root, domain, spec)

    def refine(
        self,
        mode: str,
        task_id: str,
        k: int,
        base: Sequence[RunView],
        *,
        adapter: TaskAdapter,
        proposer: HarnessProposer,
        work_dir: Path | str,
        run_id_of: Callable[[str], str],
        base_tree: Tree,
        library_dir: Path | None = None,
    ) -> ModeResult:
        return self._service.refine(
            mode,
            task_id,
            k,
            base,
            adapter=adapter,
            proposer=proposer,
            work_dir=work_dir,
            run_id_of=run_id_of,
            base_tree=base_tree,
            library_dir=library_dir,
        )

    def select(
        self,
        task_id: str,
        k: int,
        mode: str,
        candidates: dict[str, RunView],
        *,
        adapter: TaskAdapter,
        selector: CandidateSelector,
        work_dir: Path | str,
    ) -> Any:
        return self._service.select(task_id, k, mode, candidates, adapter=adapter, selector=selector, work_dir=work_dir)


plugin = RecursiveHarnessRefinerPlugin()
