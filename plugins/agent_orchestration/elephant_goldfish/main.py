"""Elephant-Goldfish Plugin entrypoint for Brain Harness."""

from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

import structlog

# Ensure Harness core src is on sys.path
_HARNESS_SRC = Path(__file__).resolve().parents[3] / "src"
if _HARNESS_SRC.exists() and str(_HARNESS_SRC) not in sys.path:
    sys.path.insert(0, str(_HARNESS_SRC))

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.elephant_goldfish import (
    ELEPHANT_GOLDFISH_SERVICE_KEY,
    DriftReportData,
    ElephantGoldfishService,
    GoldfishReviewReportData,
    SemanticBoundaryData,
)

try:
    from plugins.agent_orchestration.elephant_goldfish.service import (
        ElephantGoldfishServiceImpl,
    )
except ImportError:
    from service import ElephantGoldfishServiceImpl  # type: ignore

logger = structlog.get_logger(__name__)


class ElephantGoldfishPlugin(HarnessPlugin, ElephantGoldfishService):
    """Brain Harness Plugin providing Elephant-Goldfish Model governance."""

    name = "plugin.elephant_goldfish"
    version = "1.0.0"
    description = "Authoritative Elephant-Goldfish Model plugin: bifurcated cognitive context spec drafting, 5-stage zero-context review, and AST codebase drift detection"
    trusted = False

    def __init__(self) -> None:
        super().__init__()
        self._impl = ElephantGoldfishServiceImpl()

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [ELEPHANT_GOLDFISH_SERVICE_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, ctx: ServiceContext) -> None:
        logger.info("loading_plugin", plugin=self.name)
        ctx.provide(ELEPHANT_GOLDFISH_SERVICE_KEY, self, provider=self.name)

    async def on_unload(self, ctx: ServiceContext) -> None:
        logger.info("unloading_plugin", plugin=self.name)

    def extract_boundaries(self, content: str) -> SemanticBoundaryData:
        """Extract line ranges for FeatureRange and DetailedRange from spec markdown."""
        return self._impl.extract_boundaries(content)

    def review_spec(
        self, target_file: str, stage: str = "all"
    ) -> GoldfishReviewReportData:
        """Execute Goldfish review on target specification and return consolidated report."""
        return self._impl.review_spec(target_file, stage)

    def detect_drift(
        self, spec_content: str, source_root: str
    ) -> DriftReportData:
        """Analyze living spec content against codebase to detect implementation drift."""
        return self._impl.detect_drift(spec_content, source_root)


# Rule 45: Module-level singleton instance for loader discovery
plugin = ElephantGoldfishPlugin()


# Top-level tool entrypoints
def egm_extract_boundaries(content: str) -> dict[str, Any]:
    """Extract semantic altitude ranges (FeatureRange vs DetailedRange) from spec document."""
    res = plugin.extract_boundaries(content)
    return res.model_dump()


def egm_review_spec(target_file: str, stage: str = "all") -> dict[str, Any]:
    """Execute Goldfish multi-stage zero-context review and return consolidated report."""
    res = plugin.review_spec(target_file, stage)
    return res.model_dump()


def egm_detect_drift(spec_content: str, source_root: str) -> dict[str, Any]:
    """Detect implementation drift between living specification and live codebase files."""
    res = plugin.detect_drift(spec_content, source_root)
    return res.model_dump()

