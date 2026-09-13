"""Documentation commands — headless CLI and IoC service seams for doc synchronization.

Provides CLI inspection for repository documentation coverage audits,
AST symbol drift checks, Diataxis documentation scaffolding, and visual briefs.
"""

from __future__ import annotations

import json as _json
import sys
from pathlib import Path

import click
import structlog

from harness.kernel.context import ServiceContext
from harness.services.doc_synchronizer import (
    DOC_SYNCHRONIZER_SERVICE_KEY,
    DocCoverageReportData,
    DocDriftReportData,
    DocSynchronizerService,
)

logger = structlog.get_logger(__name__)


def get_doc_service(context: ServiceContext | None = None) -> DocSynchronizerService:
    """Resolve DocSynchronizerService from context or fall back to plugin singleton."""
    if context is not None:
        svc = context.optional(DOC_SYNCHRONIZER_SERVICE_KEY)
        if svc is not None:
            return svc

    # Lazy fallback to plugin singleton
    _ws_root = Path.cwd()
    if str(_ws_root) not in sys.path:
        sys.path.insert(0, str(_ws_root))
    if str(_ws_root / "src") not in sys.path:
        sys.path.insert(0, str(_ws_root / "src"))

    try:
        from plugins.developer_tooling.doc_synchronizer.main import plugin as doc_plugin

        return doc_plugin
    except Exception as exc:
        logger.warning("doc_plugin_fallback_failed", error=str(exc))
        # Direct fallback to DocSynchronizerEngine
        skill_scripts = (
            _ws_root / ".agents" / "skills" / "repo-doc-synchronizer" / "scripts"
        )
        if str(skill_scripts) not in sys.path:
            sys.path.insert(0, str(skill_scripts))
        from doc_synchronizer import DocSynchronizerEngine  # type: ignore

        class _EngineAdapter(DocSynchronizerService):
            def __init__(self) -> None:
                self._eng = DocSynchronizerEngine(root_dir=_ws_root)

            def audit(
                self,
                target_dir: str | Path | None = None,
                min_coverage: float = 80.0,
                exclude_patterns: list[str] | None = None,
            ) -> DocCoverageReportData:
                rep = self._eng.audit(
                    target_dir=target_dir,
                    min_coverage=min_coverage,
                    exclude_patterns=exclude_patterns,
                )
                return DocCoverageReportData(
                    scanned_root=rep.scanned_root,
                    total_modules=rep.total_modules,
                    modules_with_docstring=rep.modules_with_docstring,
                    total_symbols=rep.total_symbols,
                    documented_symbols=rep.documented_symbols,
                    overall_coverage_pct=rep.overall_coverage_pct,
                    min_passing_score=rep.min_passing_score,
                    passed=rep.passed,
                    missing_docs=list(rep.missing_docs),
                    modules=[],
                )

            def drift_check(
                self,
                docs_dir: str | Path | None = None,
                check_symbols: bool = True,
            ) -> DocDriftReportData:
                rep = self._eng.drift_check(
                    docs_dir=docs_dir, check_symbols=check_symbols
                )
                return DocDriftReportData(
                    scanned_docs_count=rep.scanned_docs_count,
                    broken_links=[],
                    stale_symbols=[],
                    has_drift=rep.has_drift,
                )

            def scaffold(
                self,
                module_path: str | Path,
                doc_type: str = "api",
                output_path: str | Path | None = None,
            ) -> Path:
                return self._eng.scaffold(
                    module_path=module_path,
                    doc_type=doc_type,
                    output_path=output_path,
                )

            def visual_brief(
                self,
                target_dir: str | Path | None = None,
                output_path: str | Path | None = None,
            ) -> Path:
                return self._eng.visual_brief(
                    target_dir=target_dir, output_path=output_path
                )

            def get_cache_stats(self) -> dict[str, int]:
                return self._eng.cache_stats

        return _EngineAdapter()


@click.group("doc")
def doc_group() -> None:
    """Repository documentation auditing, AST symbol drift verification, and scaffolding."""


@doc_group.command("audit")
@click.option(
    "--target",
    "-t",
    default=None,
    help="Target directory to audit (defaults to workspace root)",
)
@click.option(
    "--min-coverage",
    "-m",
    default=80.0,
    type=float,
    help="Minimum acceptable documentation coverage percentage",
)
@click.option(
    "--exclude",
    "-e",
    multiple=True,
    help="Patterns to exclude from scanning",
)
@click.option(
    "--json",
    "as_json",
    is_flag=True,
    help="Output report as structured JSON",
)
def doc_audit_cli(
    target: str | None,
    min_coverage: float,
    exclude: tuple[str, ...],
    as_json: bool,
) -> None:
    """Audit Python codebase and calculate documentation coverage metrics."""
    service = get_doc_service()
    exclude_list = list(exclude) if exclude else None
    report = service.audit(
        target_dir=target,
        min_coverage=min_coverage,
        exclude_patterns=exclude_list,
    )

    if as_json:
        dump_data = (
            report.model_dump() if hasattr(report, "model_dump") else report.__dict__
        )
        click.echo(_json.dumps(dump_data, indent=2))
        sys.exit(0 if report.passed else 1)

    click.echo(f"\nDocumentation Coverage Audit: {report.scanned_root}")
    click.echo("━" * 60)
    click.echo(f"Total Modules Inspected:     {report.total_modules}")
    click.echo(f"Modules with Docstring:      {report.modules_with_docstring}")
    click.echo(f"Total Public Symbols:        {report.total_symbols}")
    click.echo(f"Documented Symbols:          {report.documented_symbols}")
    click.echo(f"Overall Coverage:            {report.overall_coverage_pct:.1f}%")
    click.echo(f"Minimum Passing Threshold:   {report.min_passing_score:.1f}%")
    click.echo(
        f"Result:                      {'[PASS] PASSED' if report.passed else '[FAIL] FAILED'}"
    )

    if report.missing_docs:
        click.echo(f"\nMissing Documentation ({len(report.missing_docs)} items):")
        for item in report.missing_docs[:10]:
            click.echo(f"  - {item}")
        if len(report.missing_docs) > 10:
            click.echo(f"  ... and {len(report.missing_docs) - 10} more")

    click.echo()
    sys.exit(0 if report.passed else 1)


@doc_group.command("drift")
@click.option(
    "--docs-dir",
    "-d",
    default=None,
    help="Markdown docs directory to verify (defaults to workspace docs/ and READMEs)",
)
@click.option(
    "--no-symbols",
    is_flag=True,
    default=False,
    help="Disable AST code symbol drift checking",
)
@click.option(
    "--json",
    "as_json",
    is_flag=True,
    help="Output report as structured JSON",
)
def doc_drift_cli(
    docs_dir: str | None,
    no_symbols: bool,
    as_json: bool,
) -> None:
    """Inspect markdown documents for broken relative links and stale AST symbol references."""
    service = get_doc_service()
    report = service.drift_check(docs_dir=docs_dir, check_symbols=not no_symbols)

    if as_json:
        dump_data = (
            report.model_dump() if hasattr(report, "model_dump") else report.__dict__
        )
        click.echo(_json.dumps(dump_data, indent=2))
        sys.exit(1 if report.has_drift else 0)

    click.echo("\nDocumentation Drift Verification:")
    click.echo("━" * 60)
    click.echo(f"Documents Scanned:           {report.scanned_docs_count}")
    click.echo(f"Broken Relative Links:       {len(report.broken_links)}")
    click.echo(f"Stale Code Symbols:          {len(report.stale_symbols)}")
    click.echo(
        f"Drift Status:                {'[FAIL] DRIFT DETECTED' if report.has_drift else '[PASS] IN SYNC'}"
    )

    if report.broken_links:
        click.echo(f"\nBroken Links ({len(report.broken_links)} items):")
        for b in report.broken_links[:10]:
            click.echo(
                f"  - {b.source_file}:{b.line_number} -> {b.target_link} ({b.reason})"
            )
        if len(report.broken_links) > 10:
            click.echo(f"  ... and {len(report.broken_links) - 10} more")

    if report.stale_symbols:
        click.echo(f"\nStale Symbols ({len(report.stale_symbols)} items):")
        for s in report.stale_symbols[:10]:
            click.echo(
                f"  - {s.source_file}:{s.line_number} -> {s.symbol_name} ({s.reason})"
            )
        if len(report.stale_symbols) > 10:
            click.echo(f"  ... and {len(report.stale_symbols) - 10} more")

    click.echo()
    sys.exit(1 if report.has_drift else 0)


@doc_group.command("scaffold")
@click.argument("module_path")
@click.option(
    "--type",
    "doc_type",
    type=click.Choice(["api", "tutorial", "how-to", "explanation"]),
    default="api",
    help="Diataxis documentation archetype",
)
@click.option(
    "--output",
    "-o",
    default=None,
    help="Destination markdown output path",
)
def doc_scaffold_cli(
    module_path: str,
    doc_type: str,
    output: str | None,
) -> None:
    """Scaffold standardized Diataxis documentation for a Python module."""
    service = get_doc_service()
    out_file = service.scaffold(
        module_path=module_path,
        doc_type=doc_type,
        output_path=output,
    )
    click.echo(f"[OK] Scaffolded {doc_type} documentation: {out_file}")


@doc_group.command("brief")
@click.option(
    "--target",
    "-t",
    default=None,
    help="Target directory to inspect",
)
@click.option(
    "--output",
    "-o",
    default=None,
    help="Destination HTML visual brief path",
)
def doc_brief_cli(
    target: str | None,
    output: str | None,
) -> None:
    """Render interactive HTML visual brief with Mermaid topology and coverage metrics."""
    service = get_doc_service()
    brief_file = service.visual_brief(target_dir=target, output_path=output)
    click.echo(f"[OK] Generated interactive HTML visual brief: {brief_file}")


@doc_group.command("stats")
@click.option(
    "--json",
    "as_json",
    is_flag=True,
    help="Output cache statistics as JSON",
)
def doc_stats_cli(as_json: bool) -> None:
    """Inspect AST parsing cache performance statistics."""
    service = get_doc_service()
    stats = service.get_cache_stats()
    if as_json:
        click.echo(_json.dumps(stats, indent=2))
        return

    click.echo("\nAST Parsing Cache Statistics:")
    click.echo("━" * 40)
    for k, v in stats.items():
        click.echo(f"{k.replace('_', ' ').title():<25}: {v}")
    click.echo()


__all__ = [
    "doc_audit_cli",
    "doc_brief_cli",
    "doc_drift_cli",
    "doc_group",
    "doc_scaffold_cli",
    "doc_stats_cli",
    "get_doc_service",
]
