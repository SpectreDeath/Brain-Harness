"""Differential Facet Verifier Plugin for Brain Harness.

Registers DifferentialFacetService into the micro-kernel IoC container,
enabling multi-provider evidence dossier comparisons, facet availability semantics,
absence claimability evaluation, and 3-valued differential outcome synthesis.
"""

from __future__ import annotations

from typing import Any
import structlog

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.differential_facet import (
    CoverageDeclaration,
    DIFFERENTIAL_FACET_SERVICE_KEY,
    DifferentialFacetService,
    DifferentialReport,
    StandardDifferentialFacetService,
)

logger = structlog.get_logger(__name__)


class DifferentialFacetPlugin(HarnessPlugin, DifferentialFacetService):
    """Plugin providing authoritative differential facet verification capabilities."""

    def __init__(self) -> None:
        self._service = StandardDifferentialFacetService()

    @property
    def name(self) -> str:
        return "plugin.differential_facet_verifier"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [DIFFERENTIAL_FACET_SERVICE_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, ctx: ServiceContext) -> None:
        logger.info("loading_plugin", plugin=self.name)
        ctx.provide(DIFFERENTIAL_FACET_SERVICE_KEY, self, provider=self.name)

    async def on_enable(self) -> None:
        logger.info("enabling_plugin", plugin=self.name)

    async def on_disable(self) -> None:
        logger.info("disabling_plugin", plugin=self.name)

    async def on_unload(self) -> None:
        logger.info("unloading_plugin", plugin=self.name)

    # -------------------------------------------------------------------------
    # DifferentialFacetService Protocol Implementation
    # -------------------------------------------------------------------------

    def validate_absence_claim(self, coverage: CoverageDeclaration) -> bool:
        return self._service.validate_absence_claim(coverage)

    def evaluate_facet_limitations(self, snapshot: dict[str, Any], dimension: str) -> list[str]:
        return self._service.evaluate_facet_limitations(snapshot, dimension)

    def compare_observations(
        self,
        left: dict[str, Any],
        right: dict[str, Any],
        providers_differ: bool = False,
    ) -> DifferentialReport:
        return self._service.compare_observations(left, right, providers_differ=providers_differ)

    def export_report(self, report: DifferentialReport) -> dict[str, Any]:
        return self._service.export_report(report)


plugin = DifferentialFacetPlugin()
