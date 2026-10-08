"""Codebase Context Plugin — Multi-layer context architecture, budgeting, and 5-stage governance."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import structlog

# Rule 23: Windows UTF-8 Stream Codec Entrypoint Invariant
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.codebase_context import (
    CODEBASE_CONTEXT_SERVICE_KEY,
    CodebaseContextService,
    ContextGovernanceReport,
    ContextLintReport,
    DefaultCodebaseContextService,
    SyncResult,
)

logger = structlog.get_logger(__name__)


class CodebaseContextPlugin(HarnessPlugin):
    """Plugin providing in-memory codebase context architecture, linting, and governance."""

    def __init__(self, root: Path | str = ".") -> None:
        super().__init__()
        self._service = DefaultCodebaseContextService(root=root)

    @property
    def name(self) -> str:
        return "plugin.codebase_context"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return (
            "Multi-layer codebase context architecture, token budgeting, SSOT synchronization, "
            "and 5-stage context governance"
        )

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [CODEBASE_CONTEXT_SERVICE_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, context: ServiceContext) -> None:
        """Register the service into the micro-kernel IoC container (Rule 1 & Rule 2)."""
        context.provide(CODEBASE_CONTEXT_SERVICE_KEY, self._service)
        logger.info(
            "codebase_context_service_provided",
            service=str(CODEBASE_CONTEXT_SERVICE_KEY),
        )

    async def enable(self, context: ServiceContext) -> None:
        await self.on_load(context)

    async def on_disable(self) -> None:
        pass

    async def disable(self, context: Any = None) -> None:
        await self.on_disable()

    # Delegation methods
    def lint(self, root: str | Path = ".") -> ContextLintReport:
        return self._service.lint(root=root)

    def sync(self, root: str | Path = ".", source_rel: str = "AGENTS.md", dry_run: bool = False) -> SyncResult:
        return self._service.sync(root=root, source_rel=source_rel, dry_run=dry_run)

    def govern(
        self,
        root: str | Path = ".",
        target_file: str | Path | None = None,
        complexity_score: float = 0.5,
    ) -> ContextGovernanceReport:
        return self._service.govern(root=root, target_file=target_file, complexity_score=complexity_score)


# Rule 45: Export instantiated module singleton plugin instance
plugin = CodebaseContextPlugin()


# Top-level entrypoints matching plugin.json declarations
def context_lint(root: str = ".", **kwargs: Any) -> dict[str, Any]:
    """Execute 4-check context file linting."""
    report = plugin.lint(root=root)
    return report.to_dict()


def context_sync(root: str = ".", source: str = "AGENTS.md", dry_run: bool = False, **kwargs: Any) -> dict[str, Any]:
    """Synchronize downstream context files against canonical source."""
    res = plugin.sync(root=root, source_rel=source, dry_run=dry_run)
    return res.to_dict()


def context_govern(root: str = ".", complexity: float = 0.5, **kwargs: Any) -> dict[str, Any]:
    """Execute complete 5-stage context governance pipeline."""
    report = plugin.govern(root=root, complexity_score=complexity)
    return report.to_dict()
