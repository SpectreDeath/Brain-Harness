"""ICM (Interpretable Context Methodology) CLI commands and pure programmatic entry points.

Provides headless Click CLI access to ICM workspace architecture (arXiv:2603.16021).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import click
import structlog

# Rule 23: Windows UTF-8 Stream Codec Entrypoint Invariant
if sys.platform == "win32":
    for _s in (sys.stdout, sys.stderr):
        if hasattr(_s, "reconfigure"):
            _s.reconfigure(encoding="utf-8")

from harness.services.icm_architect import (
    DefaultIcmArchitectService,
    IcmFormType,
    resolve_icm_architect_service,
)

logger = structlog.get_logger()
_DEFAULT_SERVICE = DefaultIcmArchitectService()


# --- Pure Programmatic Functions (Headless Introspection Seam — Rule 10) ---

def icm_audit_cmd(root: str = ".") -> dict[str, Any]:
    """Audit workspace against 10 ICM invariants, classifying files and tokens."""
    return _DEFAULT_SERVICE.audit_workspace(root=root).to_dict()


def icm_links_cmd(root: str = ".", skip_folders: list[str] | None = None, graph_file: str | None = None) -> dict[str, Any]:
    """Verify that relative links and contract inputs resolve without breakage."""
    return _DEFAULT_SERVICE.verify_links(root=root, skip_folders=skip_folders, graph_file=graph_file).to_dict()


def icm_quotes_cmd(root: str = ".", show_cuts: bool = False) -> dict[str, Any]:
    """Verify that quoted text appears verbatim in raw sources and enforce keep-outs."""
    return _DEFAULT_SERVICE.verify_quotes(root=root, show_cuts=show_cuts).to_dict()


def icm_index_cmd(folders: list[str], root: str = ".") -> dict[str, Any]:
    """Rebuild _index.md files across specified shelves."""
    return _DEFAULT_SERVICE.rebuild_index(folders=folders, root=root).to_dict()


def icm_scaffold_cmd(target_dir: str, form: str = "pipeline", name: str | None = None) -> dict[str, Any]:
    """Scaffold a new ICM workspace from one of 5 canonical forms."""
    return _DEFAULT_SERVICE.scaffold_form(target_dir=target_dir, form=form, name=name).to_dict()


def icm_scaffold_workspace_cmd(
    target_dir: str, template_name: str = "workspace-builder",
    name: str | None = None, variables: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Scaffold a full production workspace from canonical templates (arXiv:2603.16021)."""
    return _DEFAULT_SERVICE.scaffold_workspace(
        target_dir=target_dir, template_name=template_name, name=name, variables=variables,
    ).to_dict()


def icm_interpolate_cmd(
    template_path: str, variables: dict[str, Any] | None = None, output_path: str | None = None,
) -> dict[str, Any]:
    """Substitute {{VARIABLE}} tags and resolve conditionals per _core/placeholder-syntax.md."""
    return _DEFAULT_SERVICE.interpolate_template(
        template_path=template_path, variables=variables, output_path=output_path,
    ).to_dict()


# --- Click CLI Group & Subcommands (Rule 6 — Single-Source Consolidation) ---

@click.group("icm")
def icm_group() -> None:
    """Interpretable Context Methodology (ICM) workspace architecture & verification."""


@icm_group.command("audit")
@click.argument("root", default=".")
@click.option("--json", "as_json", is_flag=True, help="Output raw JSON results")
def icm_audit(root: str, as_json: bool) -> None:
    """Audit an ICM workspace against the 10 invariants and token limits."""
    res = icm_audit_cmd(root=root)
    if as_json:
        click.echo(json.dumps(res, indent=2))
        return

    click.echo(f"\n📂 ICM Workspace Audit: {res.get('root')}\n{'━' * 60}")
    click.echo(f"  • Form Detected:     {res.get('form_detected')}")
    click.echo(f"  • Total Files:       {res.get('total_files')}")
    click.echo(f"  • Invariants Passed: {res.get('invariants_passed')} / {res.get('invariants_total')}")

    roles = res.get("files_by_role", {})
    click.echo(f"  • Roles:             Catalog: {roles.get('catalog', 0)}, Contract: {roles.get('contract', 0)}, Factory: {roles.get('factory', 0)}, Product: {roles.get('product', 0)}")

    violations = res.get("violations", [])
    if violations:
        click.echo("\n  ⚠️ Invariant Violations:")
        for v in violations:
            icon = "❌" if v.get("severity") == "error" else "⚠️"
            click.echo(f"    {icon} Inv #{v.get('invariant_number')} ({v.get('name')}): {v.get('description')}")
    else:
        click.echo("\n  ✅ All mandatory invariants satisfied!")
    click.echo()


@icm_group.command("links")
@click.argument("root", default=".")
@click.option("--skip", "-s", multiple=True, help="Folders to skip")
@click.option("--graph", "-g", default=None, help="Output path for JSONL graph")
@click.option("--json", "as_json", is_flag=True, help="Output raw JSON results")
def icm_links(root: str, skip: tuple[str, ...], graph: str | None, as_json: bool) -> None:
    """Verify all relative links, contract inputs, and pointer lines."""
    res = icm_links_cmd(root=root, skip_folders=list(skip), graph_file=graph)
    if as_json:
        click.echo(json.dumps(res, indent=2))
        return

    click.echo(f"\n🔗 ICM Link Verification: {root}\n{'━' * 60}")
    click.echo(f"  • Total Links Scanned: {res.get('total_links')}\n  • Resolved Links:      {res.get('resolved_links')}")
    broken = res.get("broken_links", [])
    if broken:
        click.echo(f"  ❌ Broken Links ({len(broken)}):")
        for b in broken[:15]:
            click.echo(f"    - {b.get('file')}: {b.get('link')} ({b.get('type')})")
    else:
        click.echo("  ✅ All relative links and contract inputs resolve cleanly!")
    click.echo()


@icm_group.command("quotes")
@click.argument("root", default=".")
@click.option("--show-cuts", is_flag=True, help="List text dropped by cuts")
@click.option("--json", "as_json", is_flag=True, help="Output raw JSON results")
def icm_quotes(root: str, show_cuts: bool, as_json: bool) -> None:
    """Verify quote provenance against raw sources and keep-out lists."""
    res = icm_quotes_cmd(root=root, show_cuts=show_cuts)
    if as_json:
        click.echo(json.dumps(res, indent=2))
        return

    click.echo(f"\n💬 ICM Quote Verification: {root}\n{'━' * 60}")
    click.echo(f"  • Total Quotes:    {res.get('total_quotes')}\n  • Verified Quotes: {res.get('verified_quotes')}")
    broken, ko = res.get("broken_quotes", []), res.get("keep_out_violations", [])
    if broken:
        click.echo(f"  ❌ Unverified Quotes ({len(broken)}):")
        for b in broken[:10]:
            click.echo(f"    - {b.get('file')}: \"{b.get('quote')}\" ({b.get('reason')})")
    if ko:
        click.echo(f"  🛑 Keep-Out Violations ({len(ko)}):")
        for k in ko:
            click.echo(f"    - {k}")
    if not broken and not ko:
        click.echo("  ✅ All quotes verified and zero keep-out phrases detected!")
    click.echo()


@icm_group.command("index")
@click.argument("folders", nargs=-1, required=True)
@click.option("--root", default=".", help="Root workspace directory anchor")
@click.option("--json", "as_json", is_flag=True, help="Output raw JSON results")
def icm_index(folders: tuple[str, ...], root: str, as_json: bool) -> None:
    """Rebuild _index.md files across specified shelves and record folders."""
    res = icm_index_cmd(folders=list(folders), root=root)
    if as_json:
        click.echo(json.dumps(res, indent=2))
        return

    click.echo(f"\n📑 ICM Index Rebuild\n{'━' * 60}")
    click.echo(f"  • Folders Indexed:       {', '.join(res.get('folders_indexed', []))}")
    click.echo(f"  • Total Notes Cataloged: {res.get('total_notes')}")
    click.echo(f"  • Files Generated:       {', '.join(res.get('index_files_written', []))}\n")


@icm_group.command("scaffold")
@click.argument("target_dir")
@click.option("--form", default="pipeline", type=click.Choice(["pipeline", "record_library", "knowledge_bundle", "context_map", "system_map"]))
@click.option("--name", default=None, help="Workspace name or title")
@click.option("--json", "as_json", is_flag=True, help="Output raw JSON results")
def icm_scaffold(target_dir: str, form: str, name: str | None, as_json: bool) -> None:
    """Scaffold a new production-grade ICM workspace from one of the 5 canonical forms."""
    res = icm_scaffold_cmd(target_dir=target_dir, form=form, name=name)
    if as_json:
        click.echo(json.dumps(res, indent=2))
        return

    click.echo(f"\n🚀 ICM Workspace Scaffolded: {res.get('target_dir')}\n{'━' * 60}")
    click.echo(f"  • Form:   {res.get('form')}\n  • Status: {res.get('status')}\n  • Created Files:")
    for cf in res.get("created_files", []):
        click.echo(f"    + {cf}")
    click.echo()
