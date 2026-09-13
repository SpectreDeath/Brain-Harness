"""OKF Memory CLI commands and pure programmatic entry points.

Provides headless Click CLI access to Git-native OKF agent memory bundles:
- Pre-edit governance scoping for target code paths
- BM25 lexical search with governance term boosting
- Concept inspection and Markdown retrieval
- Normative OKF v0.2 bundle schema and trust ordering validation
"""

from __future__ import annotations

import json
import sys
from typing import Any

import click
import structlog

from plugins.memory_and_epistemics.okf_memory.main import OKFMemoryEngine

logger = structlog.get_logger()
_DEFAULT_ENGINE = OKFMemoryEngine()


# -----------------------------------------------------------------------------
# Pure Programmatic Functions (MCP & Headless Introspection Seam — Rule 10)
# -----------------------------------------------------------------------------

def okf_scope_cmd(target_path: str, bundle_dir: str | None = None) -> dict[str, Any]:
    """Evaluate pre-edit governance scoping for a target code path."""
    engine = OKFMemoryEngine(default_root=bundle_dir) if bundle_dir else _DEFAULT_ENGINE
    return engine.search(for_path=target_path, bundle_dir=bundle_dir)


def okf_search_cmd(query: str, limit: int = 3, bundle_dir: str | None = None) -> dict[str, Any]:
    """Execute BM25 lexical search over knowledge bundle."""
    engine = OKFMemoryEngine(default_root=bundle_dir) if bundle_dir else _DEFAULT_ENGINE
    return engine.search(query=query, limit=limit, bundle_dir=bundle_dir)


def okf_show_cmd(concept_id: str, bundle_dir: str | None = None) -> dict[str, Any] | None:
    """Retrieve full concept markdown and metadata."""
    engine = OKFMemoryEngine(default_root=bundle_dir) if bundle_dir else _DEFAULT_ENGINE
    return engine.show(concept_id=concept_id, bundle_dir=bundle_dir)


def okf_validate_cmd(strict: bool = False, bundle_dir: str | None = None) -> dict[str, Any]:
    """Validate knowledge bundle against OKF v0.2 normative schema."""
    engine = OKFMemoryEngine(default_root=bundle_dir) if bundle_dir else _DEFAULT_ENGINE
    return engine.validate(strict=strict, bundle_dir=bundle_dir)


# -----------------------------------------------------------------------------
# Click CLI Group & Subcommands (Rule 6 — Single-Source Consolidation)
# -----------------------------------------------------------------------------

@click.group("okf")
def okf_group() -> None:
    """Manage, scope, and query Git-native OKF agent memory bundles."""


@okf_group.command("scope")
@click.argument("target_path")
@click.option("--bundle-dir", default=None, help="Root directory of knowledge bundle (default: 'knowledge')")
@click.option("--json", "as_json", is_flag=True, help="Output raw JSON results")
def okf_scope(target_path: str, bundle_dir: str | None, as_json: bool) -> None:
    """Pre-edit governance scoping for a target code path before editing."""
    res = okf_scope_cmd(target_path, bundle_dir=bundle_dir)
    if as_json:
        click.echo(json.dumps(res, indent=2))
        return

    click.echo(f"🛡️  Governance Scope Check for: {target_path}")
    click.echo("━" * 70)
    matched = res.get("results", [])
    if not matched:
        click.echo("✓ No governing concepts or architectural invariants found for this path.")
        return

    click.echo(f"Found {len(matched)} governing concept(s):")
    for item in matched:
        click.echo(f"\n  • [{item['id']}] {item['title']} (Score: {item['score']})")
        gov = item.get("governance", [])
        if gov:
            click.echo("    Governance Rules:")
            for rule in gov:
                click.echo(f"      - {rule}")
        matched_refs = item.get("matched_refs", [])
        if matched_refs:
            click.echo(f"    Matched code_refs: {', '.join(matched_refs)}")
    click.echo("━" * 70)


@okf_group.command("search")
@click.argument("query")
@click.option("--limit", "-l", default=3, help="Maximum matching concepts to return (default: 3)")
@click.option("--bundle-dir", default=None, help="Root directory of knowledge bundle (default: 'knowledge')")
@click.option("--json", "as_json", is_flag=True, help="Output raw JSON results")
def okf_search(query: str, limit: int, bundle_dir: str | None, as_json: bool) -> None:
    """Search knowledge bundle via BM25 lexical ranking."""
    res = okf_search_cmd(query, limit=limit, bundle_dir=bundle_dir)
    if as_json:
        click.echo(json.dumps(res, indent=2))
        return

    click.echo(f"🔍 BM25 Search Results for: {query!r} ({res['results_count']} found)")
    click.echo("━" * 70)
    results = res.get("results", [])
    if not results:
        click.echo("No matching concepts found.")
        return

    for idx, item in enumerate(results, 1):
        click.echo(f"{idx}. [{item['id']}] {item['title']} (Score: {item['score']})")
        click.echo(f"   Type: {item['type']} | File: {item.get('path', '')}")
        if item.get("description"):
            click.echo(f"   Summary: {item['description']}")
        gov = item.get("governance", [])
        if gov:
            click.echo(f"   Governance Invariants ({len(gov)} rules):")
            for rule in gov[:3]:
                click.echo(f"     - {rule}")
    click.echo("━" * 70)


@okf_group.command("show")
@click.argument("concept_id")
@click.option("--bundle-dir", default=None, help="Root directory of knowledge bundle (default: 'knowledge')")
@click.option("--json", "as_json", is_flag=True, help="Output raw JSON record")
def okf_show(concept_id: str, bundle_dir: str | None, as_json: bool) -> None:
    """Inspect full Markdown body and metadata for a specific concept."""
    rec = okf_show_cmd(concept_id, bundle_dir=bundle_dir)
    if rec is None:
        click.echo(f"✗ Concept '{concept_id}' not found.", err=True)
        sys.exit(1)

    if as_json:
        click.echo(json.dumps(rec, indent=2))
        return

    click.echo(f"📄 Concept: {rec['title']} ({rec['id']})")
    click.echo("━" * 70)
    click.echo(f"Type:        {rec['type']}")
    click.echo(f"Description: {rec['description']}")
    if rec.get("code_refs"):
        click.echo(f"Code Refs:   {', '.join(rec['code_refs'])}")
    if rec.get("governance"):
        click.echo("Governance Invariants:")
        for rule in rec["governance"]:
            click.echo(f"  - {rule}")
    click.echo("━" * 70)
    click.echo("Markdown Body:")
    click.echo(rec.get("body", "").strip() or "(No body content)")


@okf_group.command("validate")
@click.option("--strict", is_flag=True, help="Enforce zero warnings (fail if any warnings found)")
@click.option("--bundle-dir", default=None, help="Root directory of knowledge bundle (default: 'knowledge')")
@click.option("--json", "as_json", is_flag=True, help="Output raw JSON report")
def okf_validate(strict: bool, bundle_dir: str | None, as_json: bool) -> None:
    """Validate knowledge bundle against OKF v0.2 specifications."""
    rep = okf_validate_cmd(strict=strict, bundle_dir=bundle_dir)
    if as_json:
        click.echo(json.dumps(rep, indent=2))
        if not rep["valid"]:
            sys.exit(1)
        return

    status_str = "✓ VALID" if rep["valid"] else "✗ INVALID"
    click.echo(f"OKF Knowledge Bundle Validation Report: {status_str}")
    click.echo("━" * 70)
    click.echo(f"Total Concepts Parsed: {rep['concept_count']}")

    if rep["errors"]:
        click.echo("\nCritical Errors:")
        for err in rep["errors"]:
            click.echo(f"  ✗ {err}", err=True)

    if rep["warnings"]:
        click.echo("\nHygiene Warnings:")
        for warn in rep["warnings"]:
            click.echo(f"  ⚠ {warn}")

    if rep["valid"] and not rep["warnings"]:
        click.echo("✓ Bundle is 100% compliant with OKF v0.2 specifications.")

    click.echo("━" * 70)
    if not rep["valid"]:
        sys.exit(1)
