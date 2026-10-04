"""Conversation Trajectory Miner CLI Commands — Headless inspection for autobiographical trajectories and friction."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import click

from harness.services.conversation_trajectory_miner import (
    StandardConversationTrajectoryMinerService,
)

DEFAULT_CONVERSATIONS_DIR = Path(
    os.environ.get(
        "HARNESS_CONVERSATIONS_DIR",
        r"C:\Users\spectre\.gemini\antigravity-ide\conversations",
    )
)
DEFAULT_VAULT_DIR = Path(".harness/knowledge")


@click.group("trajectory")
def trajectory_group() -> None:
    """Autobiographical execution trajectory archaeology, friction metrics, and cognitive bifurcation."""


@trajectory_group.command("scan")
@click.option(
    "--corpus-dir",
    type=click.Path(path_type=Path),
    default=DEFAULT_CONVERSATIONS_DIR,
    help="Path to conversations directory containing SQLite WAL databases.",
)
@click.option("--max-dbs", type=int, default=50, help="Maximum conversation databases to scan.")
@click.option("--json-output", is_flag=True, help="Output results in JSON format.")
def trajectory_scan_cmd(corpus_dir: Path, max_dbs: int, json_output: bool) -> None:
    """Scan and catalog conversation database manifests across session stores."""
    service = StandardConversationTrajectoryMinerService()
    manifests = service.scan_corpus(corpus_dir, max_dbs=max_dbs)

    if json_output:
        res = [
            {
                "cid": m.cid,
                "db_path": m.db_path,
                "file_size_bytes": m.file_size_bytes,
                "step_count": m.step_count,
                "has_wal": m.has_wal,
                "step_types": m.step_types,
                "errors_detected": m.errors_detected,
                "first_prompt_snippet": m.first_prompt_snippet,
                "retry_count": m.retry_count,
            }
            for m in manifests
        ]
        click.echo(json.dumps(res, indent=2))
        return

    click.echo("=" * 65)
    click.echo(" Conversation Trajectory Miner — Corpus Scan")
    click.echo("=" * 65)
    click.echo(f" Corpus Directory : {corpus_dir}")
    click.echo(f" Databases Scanned: {len(manifests)}")
    click.echo("-" * 65)
    for m in manifests[:15]:
        wal_flag = " [WAL]" if m.has_wal else ""
        click.echo(
            f" - {m.cid[:16]}... | {m.step_count:>4} steps | {m.errors_detected:>2} errs | {m.retry_count:>2} retries | {m.file_size_bytes / 1024:>6.1f} KB{wal_flag}"
        )
        if m.first_prompt_snippet:
            click.echo(f"   Prompt: {m.first_prompt_snippet[:80]}...")


@trajectory_group.command("friction")
@click.option(
    "--corpus-dir",
    type=click.Path(path_type=Path),
    default=DEFAULT_CONVERSATIONS_DIR,
    help="Path to conversations directory.",
)
@click.option("--max-dbs", type=int, default=50, help="Maximum databases to analyze.")
@click.option("--json-output", is_flag=True, help="Output results in JSON format.")
def trajectory_friction_cmd(corpus_dir: Path, max_dbs: int, json_output: bool) -> None:
    """Compile aggregate friction scorecard and failure mode clusters."""
    service = StandardConversationTrajectoryMinerService()
    manifests = service.scan_corpus(corpus_dir, max_dbs=max_dbs)
    scorecard = service.compile_friction_scorecard(manifests)

    if json_output:
        res = {
            "total_conversations": scorecard.total_conversations,
            "total_steps": scorecard.total_steps,
            "total_bytes_mb": scorecard.total_bytes_mb,
            "total_errors": scorecard.total_errors,
            "error_rate": scorecard.error_rate,
            "step_type_distribution": scorecard.step_type_distribution,
            "high_friction_sessions": scorecard.high_friction_sessions,
            "failure_clusters": [
                {
                    "error_type": fc.error_type,
                    "count": fc.count,
                    "sample_cids": list(fc.sample_cids),
                    "tool_names": list(fc.tool_names),
                    "sample_messages": list(fc.sample_messages),
                }
                for fc in scorecard.failure_clusters
            ],
        }
        click.echo(json.dumps(res, indent=2))
        return

    click.echo("=" * 65)
    click.echo(" Trajectory Friction & Failure Cluster Scorecard")
    click.echo("=" * 65)
    click.echo(f" Total Sessions    : {scorecard.total_conversations}")
    click.echo(f" Total Steps       : {scorecard.total_steps}")
    click.echo(f" Total Size        : {scorecard.total_bytes_mb} MB")
    click.echo(
        f" Total Errors      : {scorecard.total_errors} (rate: {scorecard.error_rate * 100:.2f}%)"
    )
    click.echo(f" High-Friction CIDs: {len(scorecard.high_friction_sessions)}")
    click.echo("-" * 65)
    click.echo(" Failure Clusters:")
    for fc in scorecard.failure_clusters:
        click.echo(f"   * {fc.error_type:<32} count: {fc.count:>3} | tools: {', '.join(fc.tool_names[:3]) or 'none'}")


@trajectory_group.command("inspect")
@click.argument("cid", type=str)
@click.option(
    "--corpus-dir",
    type=click.Path(path_type=Path),
    default=DEFAULT_CONVERSATIONS_DIR,
    help="Path to conversations directory.",
)
@click.option("--json-output", is_flag=True, help="Output results in JSON format.")
def trajectory_inspect_cmd(cid: str, corpus_dir: Path, json_output: bool) -> None:
    """Deep inspect a specific conversation ID."""
    service = StandardConversationTrajectoryMinerService()
    cid_path = Path(cid)
    if cid_path.exists() and cid_path.is_file():
        db_file = cid_path
        actual_cid = cid_path.stem
    else:
        clean_cid = cid[:-3] if cid.endswith(".db") else cid
        db_file = corpus_dir / f"{clean_cid}.db"
        actual_cid = clean_cid

    if not db_file.exists():
        click.echo(f"Error: Conversation database not found: {db_file}", err=True)
        return

    manifest = service.inspect_conversation(db_file)
    if not manifest:
        click.echo(f"Error: Could not inspect conversation: {actual_cid}", err=True)
        return

    if json_output:
        click.echo(json.dumps({
            "cid": manifest.cid,
            "db_path": manifest.db_path,
            "step_count": manifest.step_count,
            "file_size_bytes": manifest.file_size_bytes,
            "errors_detected": manifest.errors_detected,
            "retry_count": manifest.retry_count,
            "step_types": manifest.step_types,
            "first_prompt_snippet": manifest.first_prompt_snippet,
        }, indent=2))
        return

    click.echo("=" * 65)
    click.echo(f" Conversation Inspection: {manifest.cid}")
    click.echo("=" * 65)
    click.echo(f" DB Path       : {manifest.db_path}")
    click.echo(f" Step Count    : {manifest.step_count}")
    click.echo(f" File Size     : {manifest.file_size_bytes / 1024:.1f} KB")
    click.echo(f" Errors        : {manifest.errors_detected}")
    click.echo(f" Retries       : {manifest.retry_count}")
    click.echo(f" Step Breakdown: {manifest.step_types}")
    click.echo(f" First Prompt  : {manifest.first_prompt_snippet}")


@trajectory_group.command("bifurcate")
@click.argument("cid", type=str)
@click.option(
    "--corpus-dir",
    type=click.Path(path_type=Path),
    default=DEFAULT_CONVERSATIONS_DIR,
    help="Path to conversations directory.",
)
@click.option(
    "--vault-dir",
    type=click.Path(path_type=Path),
    default=DEFAULT_VAULT_DIR,
    help="Output directory for canonical Knowledge Vault item.",
)
@click.option(
    "--skills-dir",
    type=click.Path(path_type=Path),
    default=None,
    help="Optional output directory for learned skill scaffold.",
)
@click.option("--json-output", is_flag=True, help="Output results in JSON format.")
def trajectory_bifurcate_cmd(
    cid: str, corpus_dir: Path, vault_dir: Path, skills_dir: Path | None, json_output: bool
) -> None:
    """Bifurcate session learning into Knowledge Vault items and procedural skill rules (Rule 41)."""
    service = StandardConversationTrajectoryMinerService()
    cid_path = Path(cid)
    if cid_path.exists() and cid_path.is_file():
        db_file = cid_path
        actual_cid = cid_path.stem
    else:
        clean_cid = cid[:-3] if cid.endswith(".db") else cid
        db_file = corpus_dir / f"{clean_cid}.db"
        actual_cid = clean_cid

    if not db_file.exists():
        click.echo(f"Error: Conversation database not found: {db_file}", err=True)
        return

    report = service.bifurcate_distillation(
        cid=actual_cid,
        db_path=db_file,
        output_vault_dir=vault_dir,
        output_skills_dir=skills_dir,
    )

    if json_output:
        click.echo(json.dumps({
            "cid": report.cid,
            "knowledge_vault_path": report.knowledge_vault_path,
            "skill_scaffold_path": report.skill_scaffold_path,
            "extracted_invariants": list(report.extracted_invariants),
            "procedural_rules": list(report.procedural_rules),
        }, indent=2))
        return

    click.echo("=" * 65)
    click.echo(f" Dual-Lens Cognitive Bifurcation: {report.cid}")
    click.echo("=" * 65)
    click.echo(f" Knowledge Vault Item : {report.knowledge_vault_path}")
    if report.skill_scaffold_path:
        click.echo(f" Skill Scaffold       : {report.skill_scaffold_path}")
    click.echo(f" Invariants Extracted : {len(report.extracted_invariants)}")
    for inv in report.extracted_invariants:
        click.echo(f"   - {inv}")
    click.echo(f" Procedural Rules     : {len(report.procedural_rules)}")
    for rule in report.procedural_rules:
        click.echo(f"   * {rule}")
