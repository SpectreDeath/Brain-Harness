"""Headless Click CLI commands for Network Forensics & Diagnostics.

Rule 6: Single-source co-located Click group declaration.
Rule 10: Headless CLI inspection and export seams.
Rule 23: Windows UTF-8 stream codec entrypoint invariant.
Rule 26: Machine-parsed stream piping with --json-output.
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

from harness.services.network_forensics import (
    NetworkForensicsService,
)


def get_network_forensics_service() -> NetworkForensicsService:
    """Retrieve or bootstrap the NetworkForensics service singleton."""
    try:
        from plugins.security_and_forensics.network_forensics.main import plugin

        return plugin
    except Exception:
        from plugins.security_and_forensics.network_forensics.main import (
            NetworkForensicsPlugin,
        )

        return NetworkForensicsPlugin()


@click.group("network-forensics")
def network_forensics_group() -> None:
    """Network Forensics CLI — Protocol reconnaissance, tri-state recon & 7-layer fault isolation."""


@network_forensics_group.command("traceroute")
@click.argument("target_or_file", type=str)
@click.option("--json-output", is_flag=True, help="Emit raw JSON output")
def traceroute_cmd(target_or_file: str, json_output: bool) -> None:
    """Parse traceroute output from file path or raw text string."""
    path = Path(target_or_file)
    if path.exists() and path.is_file():
        raw_output = path.read_text(encoding="utf-8")
    else:
        raw_output = target_or_file

    svc = get_network_forensics_service()
    res = svc.analyze_traceroute_hops(raw_output)
    data = res.model_dump() if hasattr(res, "model_dump") else res

    if json_output:
        click.echo(_json.dumps(data, indent=2))
        return

    click.secho(
        f"Traceroute Target: {data.get('target', 'unknown')}",
        fg="cyan",
        bold=True,
    )
    click.echo(
        f"Total Hops: {data.get('total_hops', 0)} | Reached Target: {data.get('reached_target', False)}"
    )
    for h in data.get("hops", []):
        hop_num = h.get("hop_number")
        ip = h.get("ip_address")
        rtt = h.get("rtt_ms")
        status = h.get("status")
        click.echo(f"  Hop {hop_num:2d}: {ip:20s} {rtt:6.1f} ms [{status}]")
    if data.get("anomalies"):
        click.secho("\nAnomalies Detected:", fg="yellow", bold=True)
        for a in data["anomalies"]:
            click.secho(
                f"  - Hop {a.get('hop')}: {a.get('type')} ({a.get('detail')})",
                fg="yellow",
            )


@network_forensics_group.command("scan-ports")
@click.option(
    "--ports",
    type=str,
    required=True,
    help="Comma-separated list of ports or scan JSON",
)
@click.option("--json-output", is_flag=True, help="Emit raw JSON output")
def scan_ports_cmd(ports: str, json_output: bool) -> None:
    """Evaluate port reachability into tri-state classification (open/closed/filtered)."""
    svc = get_network_forensics_service()
    if ports.strip().startswith("["):
        scan_records = _json.loads(ports)
    else:
        scan_records = []
        for p_str in ports.split(","):
            p_clean = p_str.strip()
            if not p_clean:
                continue
            if ":" in p_clean:
                p_num, p_resp = p_clean.split(":", 1)
                scan_records.append({"port": int(p_num), "response": p_resp})
            else:
                scan_records.append({"port": int(p_clean), "response": "SYN/ACK"})

    res = svc.evaluate_port_states(scan_records)
    data = res.model_dump() if hasattr(res, "model_dump") else res

    if json_output:
        click.echo(_json.dumps(data, indent=2))
        return

    click.secho("Port Reconnaissance Evaluation:", fg="cyan", bold=True)
    click.echo(f"  Total Ports Evaluated: {data.get('total_ports', 0)}")
    click.secho(f"  Open Ports (SYN/ACK):     {data.get('open_ports', [])}", fg="green")
    click.secho(f"  Closed Ports (RST):       {data.get('closed_ports', [])}", fg="red")
    click.secho(
        f"  Filtered Ports (Blocked): {data.get('filtered_ports', [])}",
        fg="yellow",
    )


@network_forensics_group.command("decode-flags")
@click.argument("flags_hex", type=str)
@click.option("--json-output", is_flag=True, help="Emit raw JSON output")
def decode_flags_cmd(flags_hex: str, json_output: bool) -> None:
    """Decode hexadecimal TCP flags and detect evasion patterns (Null, Xmas, SYN-FIN)."""
    svc = get_network_forensics_service()
    res = svc.decode_tcp_flags(flags_hex)
    data = res.model_dump() if hasattr(res, "model_dump") else res

    if json_output:
        click.echo(_json.dumps(data, indent=2))
        return

    click.secho(f"TCP Flag Analysis ({flags_hex}):", fg="cyan", bold=True)
    click.echo(f"  Asserted Flags: {', '.join(data.get('flags_set', [])) or 'NONE'}")
    click.echo(
        f"  SYN: {data.get('is_syn')} | ACK: {data.get('is_ack')} | FIN: {data.get('is_fin')} | RST: {data.get('is_rst')}"
    )
    if data.get("anomalous"):
        click.secho(
            f"  [!] ANOMALOUS SCAN EVASION: {data.get('evasion_type')}",
            fg="red",
            bold=True,
        )
    else:
        click.secho("  Standard Flag Combination", fg="green")


@network_forensics_group.command("cleartext")
@click.option(
    "--proto",
    type=str,
    required=True,
    help="Protocol name (e.g. HTTP, FTP, Telnet)",
)
@click.option(
    "--port",
    type=int,
    required=True,
    help="Port number (e.g. 80, 21, 23, 443)",
)
@click.option("--json-output", is_flag=True, help="Emit raw JSON output")
def cleartext_cmd(proto: str, port: int, json_output: bool) -> None:
    """Evaluate cleartext protocol exposure risk and unencrypted credential vulnerabilities."""
    svc = get_network_forensics_service()
    res = svc.classify_cleartext_exposure(proto, port)
    data = res.model_dump() if hasattr(res, "model_dump") else res

    if json_output:
        click.echo(_json.dumps(data, indent=2))
        return

    click.secho(
        f"Cleartext Protocol Assessment ({proto}:{port}):", fg="cyan", bold=True
    )
    if data.get("is_cleartext"):
        click.secho(
            f"  [!] CLEARTEXT EXPOSURE DETECTED - Severity: {data.get('severity', '').upper()}",
            fg="red",
            bold=True,
        )
        click.echo(f"  Risk: {data.get('credential_harvest_risk')}")
        click.secho(f"  Mitigation: {data.get('recommendation')}", fg="yellow")
    else:
        click.secho("  Encrypted / Protected Transport", fg="green")


@network_forensics_group.command("diagnose-7layer")
@click.argument("target", type=str)
@click.option("--port", type=int, default=80, help="Target port (defaults to 80)")
@click.option("--json-output", is_flag=True, help="Emit raw JSON output")
def diagnose_7layer_cmd(target: str, port: int, json_output: bool) -> None:
    """Execute systematic 7-layer fault isolation chain against a target."""
    svc = get_network_forensics_service()
    res = svc.run_7layer_diagnostic_chain(target, port)
    data = res.model_dump() if hasattr(res, "model_dump") else res

    if json_output:
        click.echo(_json.dumps(data, indent=2))
        return

    click.secho(f"7-Layer Diagnostic Chain: {target}:{port}", fg="cyan", bold=True)
    for r in data.get("results", []):
        layer_num = r.get("layer")
        name = r.get("layer_name")
        passed = r.get("passed")
        details = r.get("details")
        badge = (
            click.style("[PASS]", fg="green", bold=True)
            if passed
            else click.style("[FAIL]", fg="red", bold=True)
        )
        click.echo(f"  Layer {layer_num} ({name}): {badge} {details}")
    if data.get("earliest_failing_layer"):
        click.secho(
            f"\nRoot Cause: Earliest Failure at Layer {data.get('earliest_failing_layer')}",
            fg="red",
            bold=True,
        )
        for rem in data.get("remediations", []):
            click.secho(f"  Remediation: {rem}", fg="yellow")
    else:
        click.secho(
            "\nAll Layers Operational. Zero Network Regressions.",
            fg="green",
            bold=True,
        )


@network_forensics_group.command("subnet")
@click.argument("cidr", type=str)
@click.option("--json-output", is_flag=True, help="Emit raw JSON output")
def subnet_cmd(cidr: str, json_output: bool) -> None:
    """Compute network address, broadcast address, and host capacity for an IPv4 CIDR prefix."""
    svc = get_network_forensics_service()
    res = svc.calculate_subnet_geometry(cidr)
    data = res.model_dump() if hasattr(res, "model_dump") else res

    if json_output:
        click.echo(_json.dumps(data, indent=2))
        return

    click.secho(f"Subnet Bitwise Geometry ({cidr}):", fg="cyan", bold=True)
    click.echo(f"  Network Address:   {data.get('network_address')}")
    click.echo(f"  Broadcast Address: {data.get('broadcast_address')}")
    click.echo(
        f"  Subnet Mask:       {data.get('netmask')} (/{data.get('prefix_length')})"
    )
    click.echo(f"  Total Addresses:   {data.get('total_addresses')}")
    click.echo(f"  Usable Hosts:      {data.get('usable_hosts')}")
    click.echo(f"  Usable Host Range: {data.get('usable_host_range')}")


@network_forensics_group.command("brief")
@click.option("--output-path", type=str, default=None, help="Target HTML file path")
def brief_cmd(output_path: str | None) -> None:
    """Generate interactive HTML visual brief with Mermaid diagrams in %TEMP%."""
    svc = get_network_forensics_service()
    out = svc.generate_visual_brief(output_path)
    click.secho(f"Visual Brief generated: {out}", fg="green", bold=True)
