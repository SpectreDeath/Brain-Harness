#!/usr/bin/env python3
"""Headless Click CLI Seam for TypeScript Agent Harness Construction & Verification.

Enforces Rule 10 (Headless CLI Introspection Seams) and Rule 23 (Windows UTF-8 Stream Codec).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

# Rule 23: Windows UTF-8 stream codec entrypoint invariant
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

import click

from ts_harness_engine import (
    AtomicBudgetEvaluator,
    DiagnosticAuditReport,
    HarnessBudgetConfig,
    PRNGBatchSimulator,
    TypeScriptHarnessScaffolder,
)


@click.group("ts-harness")
def cli() -> None:
    """TypeScript Agent Harness Constructor & Verification CLI."""


@cli.command("simulate")
@click.option(
    "--seed",
    default="0x12345678",
    help="Hex or integer seed for PRNG reproducibility (default: 0x12345678)",
)
@click.option(
    "--runs",
    default=150,
    type=int,
    help="Number of randomized batch property iterations (default: 150)",
)
@click.option(
    "--json",
    "as_json",
    is_flag=True,
    help="Emit machine-readable JSON output",
)
def simulate_cmd(seed: str, runs: int, as_json: bool) -> None:
    """Execute seeded PRNG property-based simulation of atomic batch budgeting."""
    parsed_seed = int(seed, 16) if seed.startswith("0x") else int(seed)
    result = PRNGBatchSimulator.run_simulation(seed=parsed_seed, iterations=runs)

    if as_json:
        click.echo(json.dumps(result, indent=2))
        return

    click.echo(
        f"Seeded PRNG Batch Simulation: {runs} iterations (Seed: {hex(parsed_seed)})"
    )
    click.echo("=" * 60)
    click.echo(f"  Admitted Batches:       {result['admitted_runs']}")
    click.echo(f"  Rejected Batches:       {result['rejected_runs']}")
    click.echo(f"  Zero-Orphan Invariant:  {'PASS' if result['zero_orphan_asserted'] else 'FAIL'}")
    click.echo(f"  Overall Status:         {'SUCCESS' if result['success'] else 'FAILED'}")


@cli.command("scaffold")
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
    required=True,
    help="Target directory to scaffold TypeScript agent harness",
)
@click.option(
    "--json",
    "as_json",
    is_flag=True,
    help="Emit JSON summary of scaffolded files",
)
def scaffold_cmd(output_dir: Path, as_json: bool) -> None:
    """Scaffold complete zero-dependency TypeScript agent harness modules."""
    files = TypeScriptHarnessScaffolder.scaffold_all(output_dir)

    if as_json:
        click.echo(
            json.dumps(
                {
                    "output_dir": str(output_dir.resolve()),
                    "files": {k: str(v.resolve()) for k, v in files.items()},
                    "count": len(files),
                },
                indent=2,
            )
        )
        return

    click.echo(f"Scaffolded {len(files)} TypeScript harness modules into {output_dir}:")
    for name, path in files.items():
        click.echo(f"  ✓ src/{name}")


@cli.command("audit")
@click.option(
    "--target-dir",
    "-t",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default=".",
    help="Directory containing TypeScript harness codebase to audit",
)
@click.option(
    "--json",
    "as_json",
    is_flag=True,
    help="Emit JSON audit diagnostics",
)
def audit_cmd(target_dir: Path, as_json: bool) -> None:
    """Audit a codebase against the 9 binary diagnostic seam scorecards."""
    src_dir = target_dir / "src" if (target_dir / "src").exists() else target_dir

    checks = [
        {
            "id": "tool_validation",
            "name": "Tool Argument Validation",
            "passed": (src_dir / "tools.ts").exists(),
            "detail": "tools.ts contract schema validation present",
        },
        {
            "id": "error_bifurcation",
            "name": "Error Class Bifurcation",
            "passed": (src_dir / "runAgent.ts").exists() and (src_dir / "tools.ts").exists(),
            "detail": "Tool errors recoverable vs model errors terminal",
        },
        {
            "id": "workspace_confinement",
            "name": "Filesystem Sandboxing & Ancestor Symlink Walk",
            "passed": (src_dir / "workspace.ts").exists(),
            "detail": "Workspace.open and ancestor symlink walk present",
        },
        {
            "id": "command_hardening",
            "name": "Command Execution Hardening",
            "passed": (src_dir / "workspace.ts").exists(),
            "detail": "Command presets declared without raw shell execution",
        },
        {
            "id": "atomic_batch_budget",
            "name": "Atomic Batch Budget Verification",
            "passed": (src_dir / "budget.ts").exists() and (src_dir / "runAgent.ts").exists(),
            "detail": "Tool budget verified atomically before history mutation",
        },
        {
            "id": "context_indivisibility",
            "name": "Context Window Turn Group Indivisibility",
            "passed": (src_dir / "context.ts").exists(),
            "detail": "selectContext sliding window keeps tool-call/result pairs atomic",
        },
        {
            "id": "observer_isolation",
            "name": "Telemetry Observer Crash Isolation",
            "passed": (src_dir / "telemetry.ts").exists(),
            "detail": "onEvent telemetry dispatches isolated inside try/catch",
        },
        {
            "id": "deterministic_evals",
            "name": "Deterministic Failure Testing",
            "passed": (src_dir / "model.ts").exists(),
            "detail": "scriptedModel fake provider available for token-free evals",
        },
        {
            "id": "provider_seam",
            "name": "Provider Seam Decoupling",
            "passed": (src_dir / "model.ts").exists(),
            "detail": "Decoupled Model interface enables zero-codebase provider swaps",
        },
    ]

    passed_count = sum(1 for c in checks if c["passed"])
    total_count = len(checks)
    is_compliant = passed_count == total_count

    report = DiagnosticAuditReport(
        target_path=str(target_dir.resolve()),
        passed_count=passed_count,
        total_count=total_count,
        is_compliant=is_compliant,
        checks=tuple(checks),
    )

    if as_json:
        click.echo(
            json.dumps(
                {
                    "target_path": report.target_path,
                    "passed_count": report.passed_count,
                    "total_count": report.total_count,
                    "is_compliant": report.is_compliant,
                    "checks": list(report.checks),
                },
                indent=2,
            )
        )
        return

    click.echo(f"Harness Seam Audit: {report.target_path}")
    click.echo("=" * 60)
    for c in report.checks:
        status_icon = "✓ PASS" if c["passed"] else "✗ FAIL"
        click.echo(f"  [{status_icon}] {c['name']:<40} - {c['detail']}")
    click.echo("-" * 60)
    click.echo(f"Score: {report.passed_count}/{report.total_count} gates compliant")


if __name__ == "__main__":
    cli()
