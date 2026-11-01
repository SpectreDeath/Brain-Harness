"""Google Mantis Autonomous Security Review & Triage CLI Commands.

Rules enforced:
- Rule 6: Single-source co-located Click group declaration.
- Rule 10: Headless CLI inspection and export seams (--json).
- Rule 23: Windows UTF-8 stream codec entrypoint invariant.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import click

# Rule 23: Windows UTF-8 stream codec entrypoint invariant
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

from harness.services.mantis_security_review import resolve_mantis_security_review


def _load_json_or_file(input_val: str) -> Any:
    p = Path(input_val)
    if p.exists() and p.is_file():
        return json.loads(p.read_text(encoding="utf-8"))
    return json.loads(input_val)


@click.group("mantis")
def mantis_group() -> None:
    """Google Mantis — Autonomous security review, AST taint audit, deduplication ladder, and risk triage."""


@mantis_group.command("history-scan")
@click.argument("repo_path", type=click.Path(path_type=Path))
@click.option("--max-commits", type=int, default=100, help="Maximum commits to scan back")
@click.option("--pattern", default="", help="Regex filter for commit subjects/files")
@click.option("--json", "json_output", is_flag=True, help="Emit raw JSON payload")
def history_scan_cmd(repo_path: Path, max_commits: int, pattern: str, json_output: bool) -> None:
    """Scan VCS history for high-churn hotspots, vulnerability fixes, and security commit signatures."""
    svc = resolve_mantis_security_review()
    res = svc.history_scan(str(repo_path), max_commits=max_commits, pattern_filter=pattern)
    if json_output:
        click.echo(json.dumps(res, indent=2))
        return

    click.secho(f"=== Mantis History Scan: {repo_path.name} ===", fg="cyan", bold=True)
    status = res.get("status", "ok")
    commits_scanned = res.get("commits_scanned", 0)
    hotspots = res.get("security_hotspots", [])
    click.echo(f"  Scanned {commits_scanned} commits (Status: {status})")
    click.echo(f"  Discovered {len(hotspots)} potential security hotspot(s):")
    for h in hotspots[:10]:
        if isinstance(h, dict):
            click.echo(f"    • {h.get('file', 'N/A')}: {h.get('reason', '')}")
        else:
            click.echo(f"    • {h}")


@mantis_group.command("dir-summary")
@click.argument("dir_path", type=click.Path(path_type=Path))
@click.option("--no-recursive", is_flag=True, help="Disable recursive directory traversal")
@click.option("--json", "json_output", is_flag=True, help="Emit raw JSON payload")
def dir_summary_cmd(dir_path: Path, no_recursive: bool, json_output: bool) -> None:
    """Generate structural security architecture summary of a directory."""
    svc = resolve_mantis_security_review()
    res = svc.directory_summary(str(dir_path), recursive=not no_recursive)
    if json_output:
        click.echo(json.dumps(res, indent=2))
        return

    click.secho(f"=== Directory Security Summary: {dir_path.name} ===", fg="cyan", bold=True)
    click.echo(f"  Total Files Analyzed : {res.get('total_files', 0)}")
    click.echo(f"  Entrypoints Detected : {len(res.get('entrypoints', []))}")
    click.echo(f"  Attack Surface Ratio : {res.get('surface_score', 'N/A')}")


@mantis_group.command("plan-review")
@click.option("--threat-model", type=str, required=True, help="Threat model JSON or path to threat model file")
@click.option("--target", "-t", "targets", multiple=True, required=True, help="Target file/directory paths under review")
@click.option("--cwe", "focus_cwes", multiple=True, help="Focus CWE identifiers (e.g. CWE-79, CWE-89)")
@click.option("--json", "json_output", is_flag=True, help="Emit raw JSON payload")
def plan_review_cmd(threat_model: str, targets: tuple[str, ...], focus_cwes: tuple[str, ...], json_output: bool) -> None:
    """Evaluate architectural review plan against threat models and CWE vectors."""
    tm_data = _load_json_or_file(threat_model)
    svc = resolve_mantis_security_review()
    res = svc.plan_review(tm_data, list(targets), list(focus_cwes) if focus_cwes else None)
    if json_output:
        click.echo(json.dumps(res, indent=2))
        return

    click.secho("=== Mantis Plan Feasibility Review ===", fg="cyan", bold=True)
    click.echo(f"  Status        : {res.get('status', 'ok')}")
    click.echo(f"  Review Plan ID: {res.get('plan_id', 'N/A')}")
    click.echo(f"  Audited Paths : {len(res.get('reviewed_paths', []))}")


@mantis_group.command("audit")
@click.argument("target_file", type=click.Path(path_type=Path))
@click.option("--cwe", "focus_cwes", multiple=True, help="Focus CWE identifiers")
@click.option("--json", "json_output", is_flag=True, help="Emit raw JSON payload")
def audit_cmd(target_file: Path, focus_cwes: tuple[str, ...], json_output: bool) -> None:
    """Execute AST taint and static analysis audit on target file."""
    if not target_file.exists():
        raise click.ClickException(f"Target file not found: {target_file}")
    content = target_file.read_text(encoding="utf-8", errors="replace")
    svc = resolve_mantis_security_review()
    res = svc.research_audit(str(target_file), content, list(focus_cwes) if focus_cwes else None)
    if json_output:
        click.echo(json.dumps(res, indent=2))
        return

    click.secho(f"=== Mantis Audit: {target_file.name} ===", fg="cyan", bold=True)
    findings = res.get("findings", [])
    click.echo(f"  Findings Discovered: {len(findings)}")
    for f in findings:
        click.echo(f"  • [{f.get('severity', 'UNKNOWN')}] {f.get('cwe', 'CWE')}: {f.get('title', '')} (line {f.get('line', '?')})")


@mantis_group.command("dedupe")
@click.argument("findings_input", type=str)
@click.option("--mode", type=click.Choice(["syntactic", "ast", "syntactic_and_ast"]), default="syntactic_and_ast", help="Deduplication mode")
@click.option("--json", "json_output", is_flag=True, help="Emit raw JSON payload")
def dedupe_cmd(findings_input: str, mode: str, json_output: bool) -> None:
    """Deduplicate findings through the Mantis deduplication ladder."""
    raw = _load_json_or_file(findings_input)
    findings = raw if isinstance(raw, list) else raw.get("findings", [])
    svc = resolve_mantis_security_review()
    res = svc.dedupe_ladder(findings, mode=mode)
    if json_output:
        click.echo(json.dumps(res, indent=2))
        return

    click.secho("=== Mantis Deduplication Ladder ===", fg="cyan", bold=True)
    click.echo(f"  Raw Findings    : {res.get('input_count', len(findings))}")
    click.echo(f"  Deduplicated    : {res.get('deduped_count', len(res.get('findings', [])))}")
    click.echo(f"  Duplicates Cut  : {res.get('duplicates_eliminated', 0)}")


@mantis_group.command("critic-filter")
@click.argument("finding_input", type=str)
@click.option("--strict/--no-strict", default=True, help="Enforce strict assertion checks")
@click.option("--json", "json_output", is_flag=True, help="Emit raw JSON payload")
def critic_filter_cmd(finding_input: str, strict: bool, json_output: bool) -> None:
    """Screen candidate finding through critic filter for false positives."""
    raw = _load_json_or_file(finding_input)
    svc = resolve_mantis_security_review()
    res = svc.critic_filter(raw, check_release_assertions=strict)
    if json_output:
        click.echo(json.dumps(res, indent=2))
        return

    passed = res.get("passed", False)
    confidence = res.get("confidence", 0.0)
    color = "green" if passed else "red"
    click.secho(f"Critic Filter Verdict: {'PASSED' if passed else 'REJECTED'} (Confidence: {confidence:.2f})", fg=color, bold=True)
    if not passed:
        click.echo(f"  Rejection Reason: {res.get('rejection_reason', 'Not provided')}")


@mantis_group.command("gate")
@click.argument("findings_input", type=str)
@click.option("--fail-on", type=click.Choice(["CRITICAL", "HIGH", "MEDIUM", "LOW"]), default="HIGH", help="Severity threshold that fails the gate")
@click.option("--source-file", type=click.Path(path_type=Path), default=None, help="Optional source code path for context verification")
@click.option("--json", "json_output", is_flag=True, help="Emit raw JSON payload")
def gate_cmd(findings_input: str, fail_on: str, source_file: Path | None, json_output: bool) -> None:
    """Evaluate review gate on findings. Exits non-zero if severity threshold is breached."""
    raw = _load_json_or_file(findings_input)
    findings = raw if isinstance(raw, list) else raw.get("findings", [raw])
    svc = resolve_mantis_security_review()

    severity_order = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
    threshold_val = severity_order[fail_on]

    violations = []
    source_content = source_file.read_text(encoding="utf-8", errors="replace") if source_file and source_file.exists() else ""

    for f in findings:
        f_sev = f.get("severity", "LOW").upper()
        if severity_order.get(f_sev, 0) >= threshold_val:
            gate_res = svc.review_gate(f, source_content, strictness="high")
            violations.append({"finding": f, "gate_result": gate_res})

    gate_passed = len(violations) == 0
    payload = {
        "status": "ok" if gate_passed else "failed",
        "gate_passed": gate_passed,
        "fail_threshold": fail_on,
        "violations_count": len(violations),
        "violations": violations,
    }

    if json_output:
        click.echo(json.dumps(payload, indent=2))
    else:
        if gate_passed:
            click.secho(f"Gate [PASS]: Zero findings reached severity threshold '{fail_on}'", fg="green", bold=True)
        else:
            click.secho(f"Gate [FAIL]: {len(violations)} finding(s) reached severity threshold '{fail_on}'", fg="red", bold=True)
            for v in violations:
                f_obj = v["finding"]
                click.echo(f"  • [{f_obj.get('severity')}] {f_obj.get('title')}: {f_obj.get('filepath')}:{f_obj.get('line')}")

    if not gate_passed:
        sys.exit(1)


@mantis_group.command("chain-exploits")
@click.argument("findings_input", type=str)
@click.option("--objective", default="", help="Target adversary objective or exploit goal")
@click.option("--json", "json_output", is_flag=True, help="Emit raw JSON payload")
def chain_exploits_cmd(findings_input: str, objective: str, json_output: bool) -> None:
    """Compose isolated findings into multi-stage exploit chains."""
    raw = _load_json_or_file(findings_input)
    findings = raw if isinstance(raw, list) else raw.get("findings", [])
    svc = resolve_mantis_security_review()
    res = svc.chain_exploits(findings, target_objective=objective)
    if json_output:
        click.echo(json.dumps(res, indent=2))
        return

    chains = res.get("exploit_chains", [])
    click.secho(f"=== Mantis Exploit Chaining: {len(chains)} Compound Chain(s) ===", fg="cyan", bold=True)
    for c in chains:
        click.echo(f"  • Chain ID: {c.get('chain_id')} | Objective: {c.get('objective')} (Severity: {c.get('compound_severity', 'critical')})")
        for s in c.get("steps", []):
            click.echo(f"      Step {s.get('step')}: [{s.get('tactic')}] on finding {s.get('finding_id')}")


@mantis_group.command("calibrate-risk")
@click.argument("findings_input", type=str)
@click.option("--criticality", type=click.Choice(["low", "medium", "high", "critical"]), default="high", help="Asset criticality")
@click.option("--json", "json_output", is_flag=True, help="Emit raw JSON payload")
def calibrate_risk_cmd(findings_input: str, criticality: str, json_output: bool) -> None:
    """Calibrate risk score based on asset exposure, environmental controls, and blast radius."""
    raw = _load_json_or_file(findings_input)
    findings = raw if isinstance(raw, list) else raw.get("findings", [])
    svc = resolve_mantis_security_review()
    res = svc.calibrate_risk(findings, asset_criticality=criticality)
    if json_output:
        click.echo(json.dumps(res, indent=2))
        return

    click.secho(f"=== Mantis Risk Calibration (Asset Criticality: {criticality}) ===", fg="cyan", bold=True)
    click.echo(f"  Composite Risk Score : {res.get('composite_risk_score', 'N/A')}")
    click.echo(f"  Risk Profile Band    : {res.get('risk_band', 'N/A')}")


@mantis_group.command("report")
@click.argument("findings_input", type=str)
@click.option("--chains", type=str, default=None, help="Optional exploit chains JSON input")
@click.option("--summary", default="", help="Optional executive summary text")
@click.option("--output", "output_path", type=click.Path(path_type=Path), default=None, help="Output destination file")
@click.option("--json", "json_output", is_flag=True, help="Emit raw JSON payload")
def report_cmd(findings_input: str, chains: str | None, summary: str, output_path: Path | None, json_output: bool) -> None:
    """Synthesize final security review audit dossier and remediation report."""
    findings_raw = _load_json_or_file(findings_input)
    findings = findings_raw if isinstance(findings_raw, list) else findings_raw.get("findings", [])
    chains_data = _load_json_or_file(chains) if chains else None
    if isinstance(chains_data, dict):
        chains_data = chains_data.get("exploit_chains", [])

    svc = resolve_mantis_security_review()
    res = svc.generate_report(findings, exploit_chains=chains_data, executive_summary=summary)

    if output_path:
        output_path.write_text(json.dumps(res, indent=2), encoding="utf-8")

    if json_output:
        click.echo(json.dumps(res, indent=2))
        return

    click.secho("=== Mantis Security Review Dossier Generated ===", fg="green", bold=True)
    click.echo(f"  Report ID   : {res.get('report_id', 'N/A')}")
    click.echo(f"  Findings    : {len(res.get('findings', []))}")
    click.echo(f"  Chains      : {len(res.get('exploit_chains', []))}")
    if output_path:
        click.echo(f"  Saved to    : {output_path}")

