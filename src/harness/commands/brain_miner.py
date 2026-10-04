"""Brain Artifact Miner CLI Commands — Headless inspection for scratch tools, task logs, and transcripts."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
import click

from harness.services.brain_artifact_miner import (
    StandardBrainArtifactMinerService,
)

DEFAULT_BRAIN_DIR = Path(r"C:\Users\spectre\.gemini\antigravity-ide\brain")


@click.group("brain-miner")
def brain_miner_group() -> None:
    """Brain workspace archaeology, scratch tool salvage, and transcript introspection."""


@brain_miner_group.command("scan")
@click.option("--brain-dir", type=click.Path(path_type=Path), default=DEFAULT_BRAIN_DIR, help="Path to brain workspace")
@click.option("--depth", type=int, default=3, help="Maximum directory scan depth")
@click.option("--json-output", is_flag=True, help="Output results in JSON format")
def brain_miner_scan_cmd(brain_dir: Path, depth: int, json_output: bool) -> None:
    """Scan and catalog reusable Python scratch tools across conversation workspaces."""
    service = StandardBrainArtifactMinerService()
    catalog = service.scan_scratch_tools(brain_dir, max_depth=depth)

    if json_output:
        res = {
            "total_scanned": catalog.total_scanned,
            "classified_count": catalog.classified_count,
            "items_by_category": {
                cat: [
                    {
                        "category": item.category,
                        "path": item.path,
                        "functions": item.functions,
                        "imports": item.imports,
                        "docstring": item.docstring,
                    }
                    for item in items
                ]
                for cat, items in catalog.items_by_category.items()
            },
        }
        click.echo(json.dumps(res, indent=2))
        return

    click.echo("=" * 60)
    click.echo(" Brain Artifact Miner — Scratch Tool Archaeology")
    click.echo("=" * 60)
    click.echo(f" Brain Directory  : {brain_dir}")
    click.echo(f" Total Scanned    : {catalog.total_scanned}")
    click.echo(f" Classified Tools : {catalog.classified_count}")
    click.echo("-" * 60)
    for cat, items in catalog.items_by_category.items():
        click.echo(f" • {cat:<24} : {len(items):>4} scripts")


@brain_miner_group.command("triage")
@click.option("--brain-dir", type=click.Path(path_type=Path), default=DEFAULT_BRAIN_DIR, help="Path to brain workspace")
@click.option("--depth", type=int, default=4, help="Maximum directory scan depth")
@click.option("--json-output", is_flag=True, help="Output results in JSON format")
def brain_miner_triage_cmd(brain_dir: Path, depth: int, json_output: bool) -> None:
    """Triage background subprocess task logs for exit failures and deadlocks."""
    service = StandardBrainArtifactMinerService()
    report = service.triage_task_logs(brain_dir, max_depth=depth)

    if json_output:
        res = {
            "total_tasks": report.total_tasks,
            "failed_count": report.failed_count,
            "deadlock_count": report.deadlock_count,
            "samples": report.samples,
        }
        click.echo(json.dumps(res, indent=2))
        return

    click.echo("=" * 60)
    click.echo(" Brain Artifact Miner — Background Task Log Triage")
    click.echo("=" * 60)
    click.echo(f" Brain Directory  : {brain_dir}")
    click.echo(f" Total Tasks Scanned : {report.total_tasks}")
    click.echo(f" Failed Executions   : {report.failed_count}")
    click.echo(f" Pipe Deadlocks      : {report.deadlock_count}")
    if report.samples:
        click.echo("-" * 60)
        click.echo(" Recent Failure Diagnostics:")
        for sample in report.samples[:5]:
            fname = Path(sample["file"]).name
            click.echo(f"   • {fname} (exit: {sample.get('exit_code')}, deadlock: {sample.get('is_deadlock')})")


@brain_miner_group.command("step")
@click.argument("transcript_path", type=click.Path(path_type=Path))
@click.argument("step_index", type=int)
@click.option("--dereference/--no-dereference", default=True, help="Auto-dereference truncated steps against transcript_full.jsonl")
@click.option("--json-output", is_flag=True, help="Output raw JSON step payload")
def brain_miner_step_cmd(transcript_path: Path, step_index: int, dereference: bool, json_output: bool) -> None:
    """Fetch a specific step via O(1) binary seek with optional truncation dereference."""
    service = StandardBrainArtifactMinerService()
    step = service.get_step(transcript_path, step_index=step_index, dereference_truncated=dereference)

    if step is None:
        click.echo(f"Step {step_index} not found in {transcript_path}", err=True)
        return

    if json_output:
        click.echo(json.dumps(step, indent=2))
        return

    click.echo("=" * 60)
    click.echo(f" Transcript Step {step_index} ({transcript_path.name})")
    click.echo("=" * 60)
    click.echo(f" Type          : {step.get('type')}")
    click.echo(f" Source        : {step.get('source')}")
    click.echo(f" Status        : {step.get('status')}")
    click.echo(f" Is Truncated  : {step.get('is_truncated')}")
    click.echo(f" Dereferenced  : {step.get('dereferenced', False)}")
    content = str(step.get("content", ""))
    preview = content[:300] + "..." if len(content) > 300 else content
    click.echo(f" Content       :\n{preview}")


@brain_miner_group.command("brief")
@click.option("--brain-dir", type=click.Path(path_type=Path), default=DEFAULT_BRAIN_DIR, help="Path to brain workspace")
@click.option("--out", type=click.Path(path_type=Path), default=None, help="Output HTML file path")
def brain_miner_brief_cmd(brain_dir: Path, out: Path | None) -> None:
    """Generate an HTML visual brief summarizing scratch tools and background tasks."""
    service = StandardBrainArtifactMinerService()
    catalog = service.scan_scratch_tools(brain_dir, max_depth=3)
    triage = service.triage_task_logs(brain_dir, max_depth=4)

    total_dirs = len([p for p in brain_dir.iterdir() if p.is_dir()]) if brain_dir.exists() else 0
    html = service.generate_html_brief({
        "title": "Brain Artifact Miner Visual Brief",
        "total_dirs": total_dirs,
        "scratch_count": catalog.total_scanned,
        "task_count": triage.total_tasks,
        "failed_tasks": triage.failed_count,
        "categories": catalog.items_by_category,
    })

    if out is None:
        temp_dir = Path(os.environ.get("TEMP", "/tmp"))
        out = temp_dir / "brain_miner_brief.html"

    out.write_text(html, encoding="utf-8")
    click.echo(f"Visual Brief written to: {out}")
