"""DocSynchronizer Plugin — Repository documentation audit, drift check, and Diataxis scaffolding."""

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

# Dynamically ensure skill scripts directory is on sys.path
_PLUGIN_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _PLUGIN_DIR.parents[2]
_SKILL_SCRIPTS = _REPO_ROOT / ".agents" / "skills" / "repo-doc-synchronizer" / "scripts"
_HARNESS_SRC = _REPO_ROOT / "src"

for _p in [_SKILL_SCRIPTS, _HARNESS_SRC]:
    if _p.exists() and str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from doc_synchronizer import DocSynchronizerEngine

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.doc_synchronizer import (
    DOC_SYNCHRONIZER_SERVICE_KEY,
    BrokenLinkData,
    DocCoverageReportData,
    DocDriftReportData,
    DocSynchronizerService,
    ModuleDocStatusData,
    StaleSymbolData,
)

logger = structlog.get_logger(__name__)


class DocSynchronizerPlugin(HarnessPlugin, DocSynchronizerService):
    """Plugin providing in-memory documentation synchronization and drift verification."""

    def __init__(self, root_dir: Path | str | None = None) -> None:
        super().__init__()
        self._root = Path(root_dir or _REPO_ROOT).resolve()
        self._engine = DocSynchronizerEngine(root_dir=self._root)

    @property
    def name(self) -> str:
        return "plugin.doc_synchronizer"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return (
            "Repository documentation coverage auditing, AST code-to-doc symbol drift verification, "
            "Diataxis scaffolding, and interactive visual brief generation"
        )

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [DOC_SYNCHRONIZER_SERVICE_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, context: ServiceContext) -> None:
        """Register self as the DocSynchronizerService into the IoC container."""
        context.provide(DOC_SYNCHRONIZER_SERVICE_KEY, self)
        logger.info(
            "doc_synchronizer_service_provided",
            service=str(DOC_SYNCHRONIZER_SERVICE_KEY),
        )

    async def enable(self, context: ServiceContext) -> None:
        await self.on_load(context)

    async def on_disable(self) -> None:
        pass

    async def disable(self, context: Any = None) -> None:
        await self.on_disable()

    # --- DocSynchronizerService Implementation ---

    def audit(
        self,
        target_dir: str | Path | None = None,
        min_coverage: float = 80.0,
        exclude_patterns: list[str] | None = None,
    ) -> DocCoverageReportData:
        """Audit Python codebase and calculate documentation coverage metrics."""
        report = self._engine.audit(
            target_dir=target_dir,
            min_coverage=min_coverage,
            exclude_patterns=exclude_patterns,
        )
        return DocCoverageReportData(
            scanned_root=report.scanned_root,
            total_modules=report.total_modules,
            modules_with_docstring=report.modules_with_docstring,
            total_symbols=report.total_symbols,
            documented_symbols=report.documented_symbols,
            overall_coverage_pct=report.overall_coverage_pct,
            min_passing_score=report.min_passing_score,
            passed=report.passed,
            missing_docs=list(report.missing_docs),
            modules=[
                ModuleDocStatusData(
                    module_path=m.module_path,
                    module_name=m.module_name,
                    has_module_docstring=m.has_module_docstring,
                    total_symbols=m.total_symbols,
                    documented_symbols=m.documented_symbols,
                    dedicated_doc_path=m.dedicated_doc_path,
                    coverage_pct=m.coverage_pct,
                )
                for m in report.modules
            ],
        )

    def drift_check(
        self,
        docs_dir: str | Path | None = None,
        check_symbols: bool = True,
    ) -> DocDriftReportData:
        """Inspect markdown documents for broken relative links and stale AST symbol references."""
        report = self._engine.drift_check(
            docs_dir=docs_dir, check_symbols=check_symbols
        )
        return DocDriftReportData(
            scanned_docs_count=report.scanned_docs_count,
            broken_links=[
                BrokenLinkData(
                    source_file=b.source_file,
                    target_link=b.target_link,
                    line_number=b.line_number,
                    reason=b.reason,
                )
                for b in report.broken_links
            ],
            stale_symbols=[
                StaleSymbolData(
                    source_file=s.source_file,
                    symbol_name=s.symbol_name,
                    line_number=s.line_number,
                    reason=s.reason,
                )
                for s in report.stale_symbols
            ],
            has_drift=report.has_drift,
        )

    def scaffold(
        self,
        module_path: str | Path,
        doc_type: str = "api",
        output_path: str | Path | None = None,
    ) -> Path:
        """Scaffold standardized Diataxis documentation for a Python module."""
        return self._engine.scaffold(
            module_path=module_path,
            doc_type=doc_type,
            output_path=output_path,
        )

    def visual_brief(
        self,
        target_dir: str | Path | None = None,
        output_path: str | Path | None = None,
    ) -> Path:
        """Render interactive HTML visual brief with Mermaid topology and coverage metrics."""
        return self._engine.visual_brief(
            target_dir=target_dir,
            output_path=output_path,
        )

    def get_cache_stats(self) -> dict[str, int]:
        """Return AST parsing cache statistics."""
        return self._engine.cache_stats


# Rule 45: Export module singleton plugin instance
plugin = DocSynchronizerPlugin()


# Top-level entrypoints matching plugin.json tool declarations
def doc_audit(
    target: str | None = None,
    min_coverage: float = 80.0,
    **kwargs: Any,
) -> dict[str, Any]:
    """Top-level entrypoint for doc_audit tool invocation."""
    report = plugin.audit(target_dir=target, min_coverage=min_coverage)
    return report.model_dump()


def doc_drift_check(
    docs_dir: str | None = None,
    check_symbols: bool = True,
    **kwargs: Any,
) -> dict[str, Any]:
    """Top-level entrypoint for doc_drift_check tool invocation."""
    report = plugin.drift_check(docs_dir=docs_dir, check_symbols=check_symbols)
    return report.model_dump()


def doc_scaffold(
    module_path: str,
    doc_type: str = "api",
    output_path: str | None = None,
    **kwargs: Any,
) -> str:
    """Top-level entrypoint for doc_scaffold tool invocation."""
    res = plugin.scaffold(
        module_path=module_path, doc_type=doc_type, output_path=output_path
    )
    return str(res)


def doc_visual_brief(
    target_dir: str | None = None,
    output_path: str | None = None,
    **kwargs: Any,
) -> str:
    """Top-level entrypoint for doc_visual_brief tool invocation."""
    res = plugin.visual_brief(target_dir=target_dir, output_path=output_path)
    return str(res)
