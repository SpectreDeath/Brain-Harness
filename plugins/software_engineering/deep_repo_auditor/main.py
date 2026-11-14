"""Deep Repo Auditor plugin adapter exposing DeepRepoAuditorService via IoC (Rules 45, 49)."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import structlog

if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

_PLUGIN_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _PLUGIN_DIR.parents[2]
_SRC_DIR = _REPO_ROOT / "src"
if _SRC_DIR.exists() and str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from harness.kernel.context import ServiceContext, ServiceKey  # noqa: E402
from harness.plugins.base import HarnessPlugin  # noqa: E402
from harness.services.deep_auditor import (  # noqa: E402
    DEEP_AUDITOR_SERVICE_KEY,
    DeepAuditReport,
    DeepRepoAuditorService,
    DefaultDeepRepoAuditorService,
    VisualBriefPaths,
)

logger = structlog.get_logger(__name__)


class DeepRepoAuditorPlugin(HarnessPlugin, DeepRepoAuditorService):
    """Micro-kernel plugin registering DEEP_AUDITOR_SERVICE_KEY into ServiceContext."""

    name = "plugin.deep_repo_auditor"
    version = "1.0.0"
    description = "4-axis repository introspection, 5D compute scoring, and visual brief generator"
    trusted = False
    provides: list[ServiceKey[Any]] = [DEEP_AUDITOR_SERVICE_KEY]
    requires: list[ServiceKey[Any]] = []

    def __init__(self) -> None:
        super().__init__()
        self._impl = DefaultDeepRepoAuditorService()

    async def on_load(self, context: ServiceContext) -> None:
        context.provide(DEEP_AUDITOR_SERVICE_KEY, self._impl, provider=self.name)
        logger.info("DeepRepoAuditorPlugin loaded", plugin=self.name)

    async def on_enable(self) -> None:
        logger.info("enabling_plugin", plugin=self.name)

    async def on_disable(self) -> None:
        logger.info("disabling_plugin", plugin=self.name)

    async def on_unload(self) -> None:
        logger.info("unloading_plugin", plugin=self.name)

    def audit_repo(self, repo_path: str | Path) -> DeepAuditReport:
        return self._impl.audit_repo(repo_path)

    def generate_briefs(
        self,
        report: DeepAuditReport,
        output_dir: str | Path | None = None,
    ) -> VisualBriefPaths:
        return self._impl.generate_briefs(report, output_dir=output_dir)

    def extract_ki_candidates(self, report: DeepAuditReport) -> list[dict[str, Any]]:
        return self._impl.extract_ki_candidates(report)

    def run_full_audit(
        self,
        repo_path: str | Path,
        output_dir: str | Path | None = None,
    ) -> dict[str, Any]:
        return self._impl.run_full_audit(repo_path, output_dir=output_dir)


# Export module-level singleton per Rule 45
plugin = DeepRepoAuditorPlugin()


def deep_audit_repo(repo_path: str, **kwargs: Any) -> dict[str, Any]:
    """Top-level plugin entrypoint for single-pass 4-axis audit."""
    return plugin.audit_repo(repo_path).to_dict()


def deep_audit_briefs(
    repo_path: str,
    output_dir: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Top-level plugin entrypoint rendering HTML visual briefs."""
    report = plugin.audit_repo(repo_path)
    return plugin.generate_briefs(report, output_dir=output_dir).to_dict()


def deep_audit_ki_candidates(repo_path: str, **kwargs: Any) -> list[dict[str, Any]]:
    """Top-level plugin entrypoint extracting KI candidates."""
    report = plugin.audit_repo(repo_path)
    return plugin.extract_ki_candidates(report)


def deep_audit_full(
    repo_path: str,
    output_dir: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Top-level plugin entrypoint orchestrating audit, briefs, and KI extraction."""
    return plugin.run_full_audit(repo_path, output_dir=output_dir)
