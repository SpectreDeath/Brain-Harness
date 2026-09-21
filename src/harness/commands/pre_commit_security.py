"""Headless Click CLI commands for Pre-Commit Security Guard.

Rule 6: Single-source co-located Click group declaration.
Rule 10: Headless CLI inspection and export seams.
Rule 23: Windows UTF-8 stream codec entrypoint invariant.
"""

from __future__ import annotations

import json as _json
import sys
from pathlib import Path

import click

# Rule 23: Windows UTF-8 Stream Codec Entrypoint Invariant
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

from harness.services.pre_commit_security_guard import (
    DualGateCheckData,
    PreCommitSecurityGuardService,
    SarifExportData,
    ScanReportData,
    SmokeReportData,
    SuppressionReportData,
)


def get_pre_commit_security_service() -> PreCommitSecurityGuardService:
    """Retrieve or bootstrap the PreCommitSecurityGuard service singleton."""
    try:
        from plugins.security_and_forensics.pre_commit_security_guard.main import plugin

        return plugin
    except Exception:
        from plugins.security_and_forensics.pre_commit_security_guard.main import (
            PreCommitSecurityGuardPlugin,
        )

        return PreCommitSecurityGuardPlugin()


@click.group("pre-commit-security")
def pre_commit_security_group() -> None:
    """Pre-Commit Security Guard CLI — Shift-left SAST, secret interception & CI defense."""


@pre_commit_security_group.command("scan")
@click.argument("files", nargs=-1, type=str)
@click.option("--json-output", is_flag=True, help="Emit raw JSON output")
@click.option("--sarif-output", type=str, default=None, help="Path to write SARIF v2.1.0 report")
def scan_cmd(files: tuple[str, ...], json_output: bool, sarif_output: str | None) -> None:
    """Scan staged files or paths for SAST vulnerabilities and secret leaks."""
    svc = get_pre_commit_security_service()
    report: ScanReportData = svc.scan_staged_files(list(files) if files else None)

    if sarif_output:
        sarif_data: SarifExportData = svc.export_sarif(report)
        out_p = Path(sarif_output)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(_json.dumps(sarif_data.sarif_dict, indent=2), encoding="utf-8")
        click.echo(f"SARIF report written to {sarif_output}")

    if json_output:
        click.echo(_json.dumps(report.model_dump(), indent=2))
    else:
        status_str = click.style("PASSED", fg="green", bold=True) if report.passed else click.style("FAILED", fg="red", bold=True)
        click.echo(f"Security Scan Status: {status_str}")
        click.echo(f"Files Scanned: {report.total_files_scanned}")
        click.echo(f"Duration: {report.duration_ms:.2f} ms")
        click.echo(f"Total Findings: {len(report.findings)}")

        for finding in report.findings:
            color = "red" if finding.severity in ("critical", "high") else "yellow"
            sev_badge = click.style(f"[{finding.severity.upper()}]", fg=color, bold=True)
            click.echo(f"  {sev_badge} {finding.file_path}:{finding.line_number or 1} - {finding.name} ({finding.rule_id})")
            if finding.message:
                click.echo(f"    Message: {finding.message}")
            if finding.remediation:
                click.echo(f"    Remediation: {finding.remediation}")

    if not report.passed:
        sys.exit(1)


@pre_commit_security_group.command("smoke-test")
@click.option("--json-output", is_flag=True, help="Emit raw JSON output")
def smoke_test_cmd(json_output: bool) -> None:
    """Execute deliberate synthetic failure tests verifying commit-blocking gates."""
    svc = get_pre_commit_security_service()
    report: SmokeReportData = svc.run_synthetic_smoke_tests()

    if json_output:
        click.echo(_json.dumps(report.model_dump(), indent=2))
    else:
        status_str = click.style("PASSED", fg="green", bold=True) if report.passed else click.style("FAILED", fg="red", bold=True)
        click.echo(f"Deliberate Synthetic Smoke Gate: {status_str}")
        click.echo(f"Fixtures Tested: {report.fixtures_tested}")
        click.echo(f"Duration: {report.duration_ms:.2f} ms")

        for c in report.checks:
            res_color = "green" if c.passed else "red"
            res_text = click.style("BLOCKED (Exit 1)", fg=res_color) if c.passed else click.style("FAILED TO BLOCK", fg="red")
            click.echo(f"  - {c.fixture_name} ({c.hazard_type}): {res_text} [Rule: {c.matched_rule}]")

    if not report.passed:
        sys.exit(1)


@pre_commit_security_group.command("audit-suppressions")
@click.option("--root", "root_dir", type=str, default=".", help="Root directory to inspect")
@click.option("--json-output", is_flag=True, help="Emit raw JSON output")
def audit_suppressions_cmd(root_dir: str, json_output: bool) -> None:
    """Audit repository for unjustified comment suppressions and blanket directory exclusions."""
    svc = get_pre_commit_security_service()
    report: SuppressionReportData = svc.audit_suppression_hygiene(root_dir=root_dir)

    if json_output:
        click.echo(_json.dumps(report.model_dump(), indent=2))
    else:
        status_str = click.style("PASSED", fg="green", bold=True) if report.passed else click.style("FAILED", fg="red", bold=True)
        click.echo(f"Suppression Hygiene Status: {status_str}")
        click.echo(f"Total Suppressions: {report.total_suppressions}")
        click.echo(f"Valid Suppressions: {report.valid_suppressions}")
        click.echo(f"Unjustified Suppressions: {report.unjustified_suppressions}")
        click.echo(f"Blanket Folder Exclusions: {report.blanket_exclusions}")
        click.echo(f"Summary: {report.message}")

    if not report.passed:
        sys.exit(1)


@pre_commit_security_group.command("audit-ci")
@click.option("--workflow", "workflow_path", type=str, default=".github/workflows/security.yml", help="Path to CI workflow YAML")
@click.option("--json-output", is_flag=True, help="Emit raw JSON output")
def audit_ci_cmd(workflow_path: str, json_output: bool) -> None:
    """Audit remote CI workflow for dual-gate parity (fetch-depth: 0, SARIF upload)."""
    svc = get_pre_commit_security_service()
    report: DualGateCheckData = svc.audit_dual_gate_ci(workflow_path=workflow_path)

    if json_output:
        click.echo(_json.dumps(report.model_dump(), indent=2))
    else:
        status_str = click.style("PASSED", fg="green", bold=True) if report.passed else click.style("FAILED", fg="red", bold=True)
        click.echo(f"Dual-Gate CI Parity: {status_str}")
        click.echo(f"Target Workflow: {report.target_workflow}")
        click.echo(f"  - Full History Depth (fetch-depth: 0): {'Yes' if report.has_fetch_depth_zero else 'NO'}")
        click.echo(f"  - Remote SAST Linter: {'Yes' if report.has_sast_scanner else 'NO'}")
        click.echo(f"  - Remote Secret Scanner: {'Yes' if report.has_secret_scanner else 'NO'}")
        click.echo(f"  - SARIF Upload to GitHub Security: {'Yes' if report.has_sarif_upload else 'NO'}")

        if report.reasons:
            click.echo("Gaps Detected:")
            for reason in report.reasons:
                click.echo(f"  - {reason}")

    if not report.passed:
        sys.exit(1)


@pre_commit_security_group.command("brief")
@click.option("--output", "output_path", type=str, default=None, help="Destination HTML file path")
def brief_cmd(output_path: str | None) -> None:
    """Generate interactive HTML visual brief with Mermaid diagrams."""
    svc = get_pre_commit_security_service()
    path = svc.generate_visual_brief(output_path=output_path)
    click.echo(f"Interactive Visual Brief generated at: {path}")
