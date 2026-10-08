"""Architecture Linter plugin — circular imports, module coupling, and layer boundary enforcement."""

from __future__ import annotations

from typing import Any
import structlog

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.arch_linter import (
    ARCH_LINTER_KEY,
    ArchLinterService,
    BoundaryCheckResult,
    CircularImportResult,
    DefaultArchLinterService,
    FileLintResult,
    ModuleCouplingResult,
)

logger = structlog.get_logger(__name__)


def detect_circular_imports(root_path: str = "src") -> dict[str, Any]:
    """Detect cyclic import loops across Python modules."""
    svc = DefaultArchLinterService()
    res = svc.detect_circular_imports(root_path=root_path)
    return res.model_dump()


def compute_module_coupling(root_path: str = "src") -> dict[str, Any]:
    """Compute afferent (Ca), efferent (Ce), and Instability (I = Ce / (Ca + Ce))."""
    svc = DefaultArchLinterService()
    res = svc.compute_module_coupling(root_path=root_path)
    return res.model_dump()


def verify_clean_boundaries(
    root_path: str = "src",
    layer_hierarchy: list[str] | None = None,
) -> dict[str, Any]:
    """Verify inward dependency rule (inner layers must not import outer layers)."""
    svc = DefaultArchLinterService()
    res = svc.verify_clean_boundaries(root_path=root_path, layer_hierarchy=layer_hierarchy)
    return res.model_dump()


class ArchLinterPlugin(DefaultArchLinterService, HarnessPlugin):
    """Harness Plugin providing codebase coupling, cohesion, and boundary linting."""

    name = "plugin.arch_linter"
    version = "1.0.0"
    description = "Codebase coupling/cohesion analyzer, circular import detector, and clean architecture boundary verifier"
    trusted = True

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [ARCH_LINTER_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, ctx: ServiceContext) -> None:
        logger.info("loading_plugin", plugin=self.name)
        ctx.provide(ARCH_LINTER_KEY, self, provider=self.name)

    async def on_enable(self) -> None:
        logger.info("enabling_plugin", plugin=self.name)

    async def on_disable(self) -> None:
        logger.info("disabling_plugin", plugin=self.name)

    async def on_unload(self) -> None:
        logger.info("unloading_plugin", plugin=self.name)


plugin = ArchLinterPlugin()

__all__ = [
    "ArchLinterPlugin",
    "compute_module_coupling",
    "detect_circular_imports",
    "plugin",
    "verify_clean_boundaries",
]
