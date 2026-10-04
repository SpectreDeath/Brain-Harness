"""Temp Artifact Miner CLI Commands — Headless inspection for visual briefs, pytest sandboxes, and logs."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import click

from harness.services.temp_artifact_miner import (
    StandardTempArtifactMinerService,
)

DEFAULT_TEMP_DIR = Path(
    os.environ.get("TEMP") or os.environ.get("TMP") or r"C:\Users\spectre\AppData\Local\Temp"
)
DEFAULT_VAULT_DIR = Path(".harness/knowledge")
DEFAULT_DOCS_DIR = Path("docs/architecture")


@click.group("temp")
def temp_miner_group() -> None:
    """Ephemeral workspace archaeology, HTML visual brief extraction, and sandbox triage."""


@temp_miner_group.command("scan")
@click.option(
    "--temp-dir",
    type=click.Path(path_type=Path),
    default=DEFAULT_TEMP_DIR,
    help="Path to temporary directory containing visual HTML briefs.",
)
@click.option("--depth", type=int, default=2, help="Maximum directory scan depth.")
@click.option("--heavy-threshold", type=int, default=100000, help="Byte threshold for heavy topologies.")
@click.option("--json-output", is_flag=True, help="Output results in JSON format.")
def temp_miner_scan_cmd(
    temp_dir: Path,
    depth: int,
    heavy_threshold: int,
    json_output: bool,
) -> None:
    """Scan and catalog HTML visual briefs across temporary directories."""
    service = StandardTempArtifactMinerService(default_temp_dir=temp_dir)
    catalog = service.scan_briefs(temp_dir=temp_dir, max_depth=depth, heavy_threshold=heavy_threshold)

    if json_output:
        res = {
            "total_scanned": catalog.total_scanned,
            "brief_count": catalog.brief_count,
            "total_bytes": catalog.total_bytes,
            "heavy_count": catalog.heavy_count,
            "categories": {
                cat: [
                    {
                        "name": item.name,
                        "path": item.path,
                        "category": item.category,
                        "title": item.title,
                        "size_bytes": item.size_bytes,
                        "mtime": item.mtime,
                        "has_mermaid": item.has_mermaid,
                        "has_scorecard": item.has_scorecard,
                        "has_antipatterns": item.has_antipatterns,
                        "is_heavy_topology": item.is_heavy_topology,
                        "mermaid_dags": list(item.mermaid_dags),
                        "sha256": item.sha256,
                    }
                    for item in items
                ]
                for cat, items in catalog.items_by_category.items()
            },
        }
        click.echo(json.dumps(res, indent=2))
        return

    click.echo("=" * 65)
    click.echo(" Temp Artifact Miner — Visual Brief Catalog")
    click.echo("=" * 65)
    click.echo(f" Temp Directory   : {temp_dir}")
    click.echo(f" Total Scanned    : {catalog.total_scanned}")
    click.echo(f" Briefs Identified: {catalog.brief_count}")
    click.echo(f" Heavy Topologies : {catalog.heavy_count} (bounded)")
    click.echo(f" Total Payload    : {catalog.total_bytes / (1024 * 1024):.2f} MB")
    click.echo("-" * 65)
    for cat, items in sorted(catalog.items_by_category.items(), key=lambda x: len(x[1]), reverse=True):
        mermaid_count = sum(1 for i in items if i.has_mermaid)
        click.echo(f" • {cat:<26} : {len(items):>3} briefs ({mermaid_count:>2} with Mermaid DAGs)")


@temp_miner_group.command("sandbox")
@click.option(
    "--temp-dir",
    type=click.Path(path_type=Path),
    default=DEFAULT_TEMP_DIR,
    help="Path to temporary directory containing pytest sandboxes.",
)
@click.option("--depth", type=int, default=3, help="Maximum directory scan depth.")
@click.option("--json-output", is_flag=True, help="Output results in JSON format.")
def temp_miner_sandbox_cmd(
    temp_dir: Path,
    depth: int,
    json_output: bool,
) -> None:
    """Triage ephemeral pytest test sandbox environments and mock fixtures."""
    service = StandardTempArtifactMinerService(default_temp_dir=temp_dir)
    report = service.triage_sandbox(pytest_dir=temp_dir, max_depth=depth)

    if json_output:
        res = {
            "total_runs": report.total_runs,
            "sandbox_path": report.sandbox_path,
            "runs": [
                {
                    "name": r.name,
                    "path": r.path,
                    "fixture_count": r.fixture_count,
                    "mock_skills": list(r.mock_skills),
                }
                for r in report.runs
            ],
            "error_snippets": list(report.error_snippets),
        }
        click.echo(json.dumps(res, indent=2))
        return

    click.echo("=" * 65)
    click.echo(" Temp Artifact Miner — Pytest Sandbox Triage")
    click.echo("=" * 65)
    click.echo(f" Sandbox Path     : {report.sandbox_path}")
    click.echo(f" Total Runs Found : {report.total_runs}")
    click.echo("-" * 65)
    for r in report.runs[:10]:
        skills_str = f"({', '.join(r.mock_skills)})" if r.mock_skills else ""
        click.echo(f" • {r.name:<24} : {r.fixture_count:>3} fixtures {skills_str}")


@temp_miner_group.command("tail")
@click.argument("log_path", type=click.Path(path_type=Path))
@click.option("--lines", type=int, default=50, help="Maximum trailing lines to read.")
def temp_miner_tail_cmd(log_path: Path, lines: int) -> None:
    """Stream trailing lines from an ephemeral diagnostic log into a bounded ring buffer."""
    service = StandardTempArtifactMinerService()
    trailing_lines = service.tail_diagnostic_log(log_path, max_lines=lines)

    if not trailing_lines:
        click.echo(f"No log output found or file does not exist: {log_path}", err=True)
        return

    click.echo("=" * 65)
    click.echo(f" Diagnostic Log Tail ({len(trailing_lines)} lines) — {log_path.name}")
    click.echo("=" * 65)
    for line in trailing_lines:
        click.echo(line)


@temp_miner_group.command("salvage")
@click.option(
    "--temp-dir",
    type=click.Path(path_type=Path),
    default=DEFAULT_TEMP_DIR,
    help="Path to temporary directory.",
)
@click.option("--out", type=click.Path(path_type=Path), default=None, help="Output markdown file path.")
def temp_miner_salvage_cmd(temp_dir: Path, out: Path | None) -> None:
    """Synthesize high-density Markdown salvage index of visual briefs and sandboxes."""
    service = StandardTempArtifactMinerService(default_temp_dir=temp_dir)
    catalog = service.scan_briefs(temp_dir=temp_dir)
    sandbox = service.triage_sandbox(pytest_dir=temp_dir)
    md = service.generate_salvage_markdown(catalog, sandbox=sandbox)

    if out is not None:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(md, encoding="utf-8")
        click.echo(f"Salvage report written to: {out}")
    else:
        click.echo(md)


@temp_miner_group.command("bifurcate")
@click.argument("brief_path", type=click.Path(path_type=Path))
@click.option(
    "--vault-dir",
    type=click.Path(path_type=Path),
    default=DEFAULT_VAULT_DIR,
    help="Target Knowledge Vault directory.",
)
@click.option(
    "--docs-dir",
    type=click.Path(path_type=Path),
    default=DEFAULT_DOCS_DIR,
    help="Target repository documentation directory.",
)
@click.option("--json-output", is_flag=True, help="Output results in JSON format.")
def temp_miner_bifurcate_cmd(
    brief_path: Path,
    vault_dir: Path,
    docs_dir: Path,
    json_output: bool,
) -> None:
    """Execute dual-lens cognitive bifurcation: Knowledge Vault dual-files + permanent docs."""
    service = StandardTempArtifactMinerService()
    try:
        report = service.bifurcate_brief(
            brief_path=brief_path,
            target_vault_dir=vault_dir,
            target_docs_dir=docs_dir,
        )
    except Exception as e:
        click.echo(f"Error during bifurcation: {e}", err=True)
        return

    if json_output:
        res = {
            "source_name": report.source_name,
            "knowledge_vault_path": report.knowledge_vault_path,
            "salvaged_doc_path": report.salvaged_doc_path,
            "extracted_heuristics": list(report.extracted_heuristics),
            "procedural_rules": list(report.procedural_rules),
        }
        click.echo(json.dumps(res, indent=2))
        return

    click.echo("=" * 65)
    click.echo(" Dual-Lens Cognitive Bifurcation Completed")
    click.echo("=" * 65)
    click.echo(f" Source Brief       : {report.source_name}")
    click.echo(f" Knowledge Vault KI : {report.knowledge_vault_path}")
    click.echo(f" Permanent Doc File : {report.salvaged_doc_path}")
    click.echo("-" * 65)
    click.echo(f" Heuristics Extracted : {len(report.extracted_heuristics)}")
    click.echo(f" Procedural Rules     : {len(report.procedural_rules)}")


__all__ = [
    "temp_miner_group",
]
