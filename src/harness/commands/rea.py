"""REA Reverse-Engineering Toolkit CLI Commands.

Provides headless Click CLI inspection, artifact routing, decompiler orchestration,
semantic signature extraction, multi-provider differential comparison,
and endogenous Knowledge Vault learning for software reverse engineering.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

import click

from harness.services.rea_toolkit import (
    ARTIFACT_KIND_TOOLS,
    REA_TOOL_ALIASES,
    ReaDissectionBudgets,
    StandardReaToolkitService,
    resolve_rea_toolkit,
)


def _format_badge(state: str) -> str:
    s = state.lower()
    if s == "available":
        return "[AVAILABLE] "
    if s == "absent":
        return "[ABSENT]    "
    return "[UNKNOWN]   "


@click.group("rea")
def rea_group() -> None:
    """REA — Reverse-engineering toolkit, multi-provider dissection, and signature learning."""
    if sys.platform == "win32":
        try:
            if hasattr(sys.stdout, "reconfigure"):
                sys.stdout.reconfigure(encoding="utf-8")
            if hasattr(sys.stderr, "reconfigure"):
                sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass


@rea_group.command("inspect")
@click.argument("artifact_path", type=click.Path(path_type=Path))
@click.option("--artifact-type", "-t", default=None, help="Explicit artifact kind override (e.g. elf, pe_managed, apk, wasm, har)")
@click.option("--json", "json_output", is_flag=True, help="Emit raw JSON DissectionEnvelope")
def rea_inspect_cmd(artifact_path: Path, artifact_type: str | None, json_output: bool) -> None:
    """Inspect and dissect an artifact into unified facets with availability semantics."""
    if not artifact_path.exists() and not str(artifact_path).startswith("0x"):
        raise click.ClickException(f"Target artifact does not exist: {artifact_path}")

    service = StandardReaToolkitService()
    try:
        envelope = service.dissect(str(artifact_path), artifact_type=artifact_type)
    except Exception as exc:
        raise click.ClickException(f"Dissection failed: {exc}")

    if json_output:
        click.echo(json.dumps(envelope.to_dict(), indent=2, ensure_ascii=False))
        return

    # Human-formatted rich table output
    click.echo("=" * 76)
    click.echo(f" REA DISSECTION ENVELOPE: {envelope.evidence_id}")
    click.echo("=" * 76)
    click.echo(f" Artifact Path    : {envelope.artifact.path}")
    click.echo(f" Detected Kind    : {envelope.artifact.detected_kind} ({envelope.artifact.magic_summary})")
    click.echo(f" SHA-256 Digest   : {envelope.artifact.sha256}")
    click.echo(f" File Size        : {envelope.artifact.size_bytes:,} bytes")
    click.echo(f" Primary Provider : {envelope.provider.plugin} [{envelope.provider.tool}]")
    if envelope.artifact.polyglot_warnings:
        click.echo(" Polyglot Alerts  :")
        for w in envelope.artifact.polyglot_warnings:
            click.echo(f"   [!] {w}")
    click.echo("-" * 76)
    click.echo(" FACET OBSERVABILITY MATRIX (3-Valued Availability Semantics):")
    click.echo("-" * 76)
    for name, facet in sorted(envelope.facets.items()):
        badge = _format_badge(facet.state)
        reason_note = f" (Reason: {facet.availability.reason})" if facet.availability.reason and facet.state == "unknown" else ""
        click.echo(f"  {badge} {name:<20} scope={facet.coverage.scope:<18} claimable={facet.coverage.absence_claimable}{reason_note}")
    click.echo("-" * 76)
    click.echo(f" SEMANTIC SIGNATURES EXTRACTED ({len(envelope.signatures)} total):")
    click.echo("-" * 76)
    if not envelope.signatures:
        click.echo("  (Zero semantic signatures observed)")
    else:
        for s in envelope.signatures[:25]:
            detail_str = f" | {json.dumps(s.details, ensure_ascii=False)}" if s.details else ""
            click.echo(f"  [{s.kind:<18}] {s.name}{detail_str}")
        if len(envelope.signatures) > 25:
            click.echo(f"  ... and {len(envelope.signatures) - 25} more (use --json for complete dossier)")
    click.echo("=" * 76)


@rea_group.command("list")
@click.option("--artifact-type", "-t", default=None, help="Filter tool list by artifact kind")
@click.option("--json", "json_output", is_flag=True, help="Emit tool catalog as JSON")
def rea_list_cmd(artifact_type: str | None, json_output: bool) -> None:
    """List REA tools grouped by artifact kind."""
    filter_kind = artifact_type.lower() if artifact_type else None
    matched_kinds = {k: v for k, v in ARTIFACT_KIND_TOOLS.items() if not filter_kind or k == filter_kind}

    if json_output:
        catalog = []
        for kind, tools in matched_kinds.items():
            for alias, target, desc in tools:
                catalog.append({
                    "artifact_kind": kind,
                    "alias": alias,
                    "target_tool": target,
                    "description": desc,
                })
        click.echo(json.dumps(catalog, indent=2, ensure_ascii=False))
        return

    click.echo("\nREA Reverse-Engineering Toolkit — Tools Grouped by Artifact Kind\n" + "═" * 78)
    for kind, tools in sorted(matched_kinds.items()):
        click.echo(f"\n Artifact Kind: {kind.upper()} ({len(tools)} tools)")
        click.echo("─" * 78)
        for alias, target, desc in tools:
            click.echo(f"  • {alias:<30} -> {target}")
            click.echo(f"    {desc}")
    click.echo("\nTotal registered canonical aliases: 28\n")


@rea_group.command("providers")
@click.option("--json", "json_output", is_flag=True, help="Emit providers status as JSON")
def rea_providers_cmd(json_output: bool) -> None:
    """Report external reverse-engineering binary availability, paths, and versions."""
    service = StandardReaToolkitService()
    prov_map = service.providers()

    if json_output:
        click.echo(json.dumps({k: v.to_dict() for k, v in prov_map.items()}, indent=2, ensure_ascii=False))
        return

    click.echo("=" * 76)
    click.echo(" REA EXTERNAL PROVIDERS & REVERSE-ENGINEERING BINARIES STATUS")
    click.echo("=" * 76)
    click.echo(f"{'Binary / Engine':<18} | {'Status':<16} | {'Plugin':<28} | {'Resolved Path'}")
    click.echo("-" * 76)
    for name, p in sorted(prov_map.items()):
        mode_str = p.execution_mode.upper()
        status_badge = "[OK] INSTALLED" if p.binary_path else f"[{mode_str}]"
        path_str = p.binary_path if p.binary_path else "(not found in PATH)"
        click.echo(f"{name:<18} | {status_badge:<16} | {p.plugin:<28} | {path_str}")
    click.echo("=" * 76)


@rea_group.command("decompile")
@click.argument("artifact_path", type=click.Path(path_type=Path))
@click.option("--symbols", "-s", required=True, help="Comma-separated list of symbols to decompile")
@click.option("--provider", "-p", default="ghidra", type=click.Choice(["ghidra", "hopper", "ida"]), help="Decompiler provider")
@click.option("--json", "json_output", is_flag=True, help="Emit result as JSON")
def rea_decompile_cmd(artifact_path: Path, symbols: str, provider: str, json_output: bool) -> None:
    """Decompile procedure symbols concurrently via headless decompiler."""
    sym_list = [s.strip() for s in symbols.split(",") if s.strip()]
    service = StandardReaToolkitService()
    envelope = service.dissect(str(artifact_path), symbols=sym_list, provider=provider)

    decomp_facet = envelope.facets.get("decompilation")
    if json_output:
        click.echo(json.dumps(envelope.to_dict(), indent=2, ensure_ascii=False))
        return

    click.echo("=" * 76)
    click.echo(f" REA DECOMPILATION: {artifact_path} [Provider: {provider}]")
    click.echo("=" * 76)
    if not decomp_facet or decomp_facet.state == "unknown":
        reason = decomp_facet.availability.reason if decomp_facet else "No decompilation facet"
        click.echo(f" [UNKNOWN] Decompilation unavailable: {reason}")
        return

    procs = decomp_facet.data or []
    for proc in procs:
        p_dict = proc if isinstance(proc, dict) else (proc.model_dump() if hasattr(proc, "model_dump") else {})
        click.echo(f"\n--- Symbol: {p_dict.get('symbol')} (Address: {p_dict.get('address', 'N/A')}) ---")
        click.echo(p_dict.get("pseudocode") or "(No pseudocode emitted)")
    click.echo("\n" + "=" * 76)


@rea_group.command("callgraph")
@click.argument("artifact_path", type=click.Path(path_type=Path))
@click.option("--entry", "-e", required=True, help="Procedure entrypoint symbol")
@click.option("--depth", "-d", default=3, type=int, help="Traversal depth (default: 3)")
@click.option("--direction", default="callee", type=click.Choice(["callee", "caller"]), help="Direction of traversal")
@click.option("--json", "json_output", is_flag=True, help="Emit result as JSON")
def rea_callgraph_cmd(artifact_path: Path, entry: str, depth: int, direction: str, json_output: bool) -> None:
    """Traverse caller or callee call-graph relationships from an entrypoint."""
    service = StandardReaToolkitService()
    res = service.adapter.call_native("call_graph", target_path=str(artifact_path), entry_symbol=entry, depth=depth, direction=direction)

    if json_output:
        click.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    click.echo(f"\nCall Graph Traversal for '{entry}' [direction: {direction}, depth: {depth}]:")
    click.echo("─" * 70)
    edges = res.get("edges") or []
    if not edges:
        click.echo("  (Zero edges observed)")
    for edge in edges:
        e_dict = edge if isinstance(edge, dict) else (edge.model_dump() if hasattr(edge, "model_dump") else {})
        click.echo(f"  {e_dict.get('caller')} ──[{e_dict.get('call_type', 'direct')}]──> {e_dict.get('callee')}")
    click.echo()


@rea_group.command("signatures")
@click.argument("artifact_path", type=click.Path(path_type=Path))
@click.option("--kind", "-k", default=None, help="Filter signature kind (e.g. evm_selector, pinvoke, ipc_channel, export, import)")
@click.option("--json", "json_output", is_flag=True, help="Emit signatures as JSON")
def rea_signatures_cmd(artifact_path: Path, kind: str | None, json_output: bool) -> None:
    """Extract and deduplicate semantic signatures from an artifact."""
    service = StandardReaToolkitService()
    sigs = service.signatures(str(artifact_path), kind=kind)

    if json_output:
        click.echo(json.dumps([s.to_dict() for s in sigs], indent=2, ensure_ascii=False))
        return

    click.echo(f"\nSemantic Signatures extracted from {artifact_path} ({len(sigs)} matches):\n" + "─" * 76)
    for s in sigs:
        det = f" | {s.details}" if s.details else ""
        click.echo(f"  • [{s.kind:<18}] {s.name:<32}{det}")
    click.echo()


@rea_group.command("devices")
@click.option("--packages", "target_serial", default=None, help="Device serial to query installed packages from")
@click.option("--json", "json_output", is_flag=True, help="Emit output as JSON")
def rea_devices_cmd(target_serial: str | None, json_output: bool) -> None:
    """Enumerate attached ADB devices, emulators, and device package trees."""
    service = StandardReaToolkitService()
    client_res = service.adapter.call_mobile("adb_inspect_client")
    devices_res = service.adapter.call_mobile("adb_list_devices")

    payload: dict[str, Any] = {
        "client": client_res,
        "devices": devices_res.get("devices", []),
    }

    if target_serial:
        pkg_res = service.adapter.call_mobile("adb_list_packages", device_serial=target_serial)
        payload["packages"] = pkg_res.get("packages", [])

    if json_output:
        click.echo(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    adb_path = client_res.get("adb_path") or "(not found)"
    click.echo("=" * 70)
    click.echo(f" ADB CLIENT & ATTACHED DEVICE SURFACE")
    click.echo("=" * 70)
    click.echo(f" ADB Binary Path  : {adb_path}")
    click.echo(f" ADB Client Status: {'READY' if client_res.get('installed') else 'NOT INSTALLED'}")
    click.echo("-" * 70)
    devices = devices_res.get("devices") or []
    click.echo(f" Attached Devices ({len(devices)} total):")
    if not devices:
        click.echo("  (Zero devices or emulators attached)")
    for dev in devices:
        d_dict = dev if isinstance(dev, dict) else (dev.model_dump() if hasattr(dev, "model_dump") else {})
        click.echo(f"  • {d_dict.get('serial'):<20} state={d_dict.get('state')} model={d_dict.get('model', 'unknown')}")
    if target_serial and "packages" in payload:
        pkgs = payload["packages"]
        click.echo(f"\n Packages installed on device '{target_serial}' ({len(pkgs)} total):")
        for p_item in pkgs[:30]:
            p_dict = p_item if isinstance(p_item, dict) else (p_item.model_dump() if hasattr(p_item, "model_dump") else {})
            click.echo(f"    - {p_dict.get('package_name')}")
    click.echo("=" * 70)


@rea_group.command("diff")
@click.argument("artifact_path", type=click.Path(path_type=Path))
@click.option("--providers", "-p", default="ghidra,hopper", help="Two comma-separated providers to compare (default: ghidra,hopper)")
@click.option("--symbols", "-s", default="main", help="Symbols to compare (default: main)")
@click.option("--json", "json_output", is_flag=True, help="Emit DifferentialReport JSON")
def rea_diff_cmd(artifact_path: Path, providers: str, symbols: str, json_output: bool) -> None:
    """Compare two providers on an artifact and emit a 3-valued DifferentialReport."""
    prov_list = [p.strip() for p in providers.split(",") if p.strip()]
    if len(prov_list) != 2:
        raise click.ClickException("Must specify exactly two providers separated by a comma (e.g. --providers ghidra,hopper)")

    sym_list = [s.strip() for s in symbols.split(",") if s.strip()]
    service = StandardReaToolkitService()
    report = service.diff(str(artifact_path), providers=(prov_list[0], prov_list[1]), symbols=sym_list)
    exported = service.differential_service.export_report(report)

    if json_output:
        click.echo(json.dumps(exported, indent=2, ensure_ascii=False))
        return

    click.echo("=" * 76)
    click.echo(f" REA MULTI-PROVIDER DIFFERENTIAL REPORT: {report.report_id}")
    click.echo(f" Providers: {prov_list[0]} vs {prov_list[1]} | Overall: {report.overall_status.upper()}")
    click.echo("-" * 76)
    click.echo(f"{'Dimension':<18} | {'Status':<10} | {'Conclusion':<22} | {'Counts (L/R)'}")
    click.echo("-" * 76)
    for dim in report.dimensions:
        l_cnt = str(dim.left_count) if dim.left_count is not None else "null"
        r_cnt = str(dim.right_count) if dim.right_count is not None else "null"
        counts = f"{l_cnt} / {r_cnt}"
        click.echo(f"{dim.dimension:<18} | {dim.status:<10} | {dim.conclusion_kind:<22} | {counts}")
        for limit in dim.limitations:
            click.echo(f"  └─ limitation: {limit}")
    click.echo("=" * 76)


@rea_group.command("learn")
@click.argument("artifact_path", type=click.Path(path_type=Path))
@click.option("--dry-run", is_flag=True, help="Preview learned signatures without writing to vault")
@click.option("--vault", default=".harness/knowledge", help="Path to Knowledge Vault root")
@click.option("--ledger", default=".harness/reconstruction_ledger.json", help="Path to ROL ledger state file")
@click.option("--domain", default="security_and_forensics", help="Domain category for the Knowledge Item")
@click.option("--tag", "-t", "tags", multiple=True, help="Optional tags for the Knowledge Item")
@click.option("--json", "json_output", is_flag=True, help="Emit learning report as JSON")
def rea_learn_cmd(artifact_path: Path, dry_run: bool, vault: str, ledger: str, domain: str, tags: tuple[str, ...], json_output: bool) -> None:
    """Dissect artifact and distill semantic signatures into the Knowledge Vault and ROL ledger."""
    service = StandardReaToolkitService()
    res = service.learn(str(artifact_path), vault_dir=vault, ledger_path=ledger, dry_run=dry_run, domain=domain, tags=list(tags))

    if json_output:
        click.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    dry_prefix = "[DRY-RUN] " if dry_run else ""
    click.echo("=" * 72)
    click.echo(f" {dry_prefix}REA KNOWLEDGE DISTILLATION COMPLETE")
    click.echo("=" * 72)
    click.echo(f" Knowledge Item ID  : {res['ki_id']}")
    click.echo(f" Title              : {res['title']}")
    click.echo(f" Evidence Record    : {res['evidence_id']}")
    click.echo(f" Signatures Sealed  : {res['signatures_count']}")
    click.echo(f" Vault Location     : {res['vault_dir']}")
    click.echo("=" * 72)


@rea_group.command("learned")
@click.option("--query", "-q", default=None, help="Filter by keyword")
@click.option("--vault", default=".harness/knowledge", help="Path to Knowledge Vault root")
@click.option("--json", "json_output", is_flag=True, help="Emit results as JSON")
def rea_learned_cmd(query: str | None, vault: str, json_output: bool) -> None:
    """List distilled REA knowledge items stored in the Knowledge Vault."""
    v_root = Path(vault)
    items: list[dict[str, Any]] = []

    if v_root.exists():
        for d in sorted(v_root.glob("ki-rea-sig-*")):
            meta_file = d / "metadata.json"
            if meta_file.exists():
                try:
                    data = json.loads(meta_file.read_text(encoding="utf-8"))
                    if not query or query.lower() in json.dumps(data).lower():
                        items.append(data)
                except Exception:
                    pass

    if json_output:
        click.echo(json.dumps(items, indent=2, ensure_ascii=False))
        return

    click.echo(f"\nDistilled REA Knowledge Items ({len(items)} found):\n" + "─" * 70)
    for item in items:
        ki_id = item.get("id", "")
        title = item.get("title", "")
        sigs = item.get("signatures_count", 0)
        click.echo(f"  • {ki_id:<32} {sigs:>3} sigs  {title}")
    click.echo()
