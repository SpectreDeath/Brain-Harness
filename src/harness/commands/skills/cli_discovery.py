"""Click CLI subcommands for skill discovery, execution, creation, and validation."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from harness.commands.skills.discovery import (
    export_skill_graph_visual_cmd,
    index_skills_cmd,
    list_skills_cmd,
    run_skill_cmd,
    scaffold_skill_cmd,
    validate_skill_cmd,
)


@click.command("list")
@click.option("--path", default=".", help="Root directory to scan for skills")
@click.option("--category", default=None, help="Filter by domain category")
def skills_list(path: str, category: str | None) -> None:
    """List all registered agent skills with category, stages, and invariants."""
    skills = list_skills_cmd(path)
    if category:
        skills = [s for s in skills if s.category.lower() == category.lower()]

    click.echo(f"\n📚 Registered Agent Skills ({len(skills)} total)")
    click.echo("━" * 80)
    click.echo(f"{'Skill Name':<34} {'Category':<24} {'Stages':<8} {'Invariants':<10}")
    click.echo("─" * 80)
    for s in sorted(skills, key=lambda x: x.name):
        invariants_str = f"{len(s.invariants)} rules" if s.invariants else "None"
        click.echo(
            f"{s.name:<34} {s.category:<24} {len(s.stages):<8} {invariants_str:<10}"
        )
    click.echo("━" * 80)


@click.command("run")
@click.argument("skill_name")
@click.option("--path", default=".", help="Workspace root")
@click.option(
    "--source",
    default=None,
    help="Source document or target argument for skill execution",
)
def skills_run(skill_name: str, path: str, source: str | None) -> None:
    """Headlessly execute an automated skill pipeline driver (Rule 10)."""
    clean_name = skill_name.strip().lower().replace("_", "-")
    click.echo(f"🚀 Executing skill pipeline: {clean_name}")
    res = run_skill_cmd(skill_name, root_path=path, source=source)
    if res["status"] != "ok":
        click.echo(f"✗ {res.get('reason', 'Skill execution failed')}", err=True)
        sys.exit(1)

    click.echo(f"   Driver: {res['driver']}")
    click.echo("━" * 60)
    if res.get("stdout"):
        click.echo(res["stdout"])
    if res.get("stderr"):
        click.echo(res["stderr"], err=True)
    click.echo("━" * 60)
    click.echo(f"Pipeline Result: ✓ COMPLETED (exit code {res['returncode']})")


@click.command("graph")
@click.option(
    "--visual", is_flag=True, help="Generate interactive HTML visual brief in %TEMP%"
)
@click.option("--path", default=".", help="Root directory to scan for skills")
def skills_graph(visual: bool, path: str) -> None:
    """Index and display the workspace skill knowledge graph."""
    res = index_skills_cmd(path)
    click.echo(
        f"📊 Indexed {res['indexed_skills']} skills across {len(res['categories'])} categories."
    )
    click.echo(f"   Nodes: {res['total_nodes']} | Relation Edges: {res['total_edges']}")
    click.echo(f"   Categories: {', '.join(res['categories'])}")

    if visual:
        vis_res = export_skill_graph_visual_cmd()
        click.echo(f"\n🌐 Visual Brief generated: {vis_res['html_path']}")


@click.command("create")
@click.argument("name")
@click.option(
    "--description", "-d", default="", help="Skill description and trigger bounds"
)
@click.option(
    "--category",
    "-c",
    default="engineering / meta-skills",
    help="Skill domain category",
)
@click.option(
    "--target-dir",
    "-t",
    default=None,
    help="Destination directory (defaults to .agents/skills/<name>)",
)
@click.option(
    "--trigger",
    "-g",
    "triggers",
    multiple=True,
    help="Trigger phrases for skill routing",
)
@click.option(
    "--validate",
    "auto_validate",
    is_flag=True,
    help="Validate skill specifications on creation",
)
def skills_create(
    name: str,
    description: str,
    category: str,
    target_dir: str | None,
    triggers: tuple[str, ...],
    auto_validate: bool,
) -> None:
    """Scaffold a high-precision agent skill with SKILL.md and CARD.md specifications."""
    clean_name = name.strip().lower().replace("_", "-")
    result = scaffold_skill_cmd(
        name=clean_name,
        description=description,
        category=category,
        target_dir=target_dir,
        triggers=triggers,
        auto_validate=auto_validate,
    )
    click.echo(f"✨ Scaffolded agent skill '{clean_name}' at: {result.path}")
    for gen in result.generated_files:
        click.echo(f"   📄 {gen.name}")

    if result.validation_report:
        rep = result.validation_report
        status = "✓ VALID" if rep.valid else "✗ INVALID"
        click.echo(f"\n🔍 Pre-Flight Validation: {status}")
        if rep.warnings:
            for w in rep.warnings:
                click.echo(f"   ⚠️  {w}")
        if rep.errors:
            for e in rep.errors:
                click.echo(f"   ❌ {e}")


@click.command("validate")
@click.argument("skill_dir", default=".")
def skills_validate(skill_dir: str) -> None:
    """Validate an agent skill package against deep-module craft standards."""
    report = validate_skill_cmd(skill_dir)
    target = Path(skill_dir).resolve()
    status = "✓ PASS" if report.valid else "✗ FAIL"
    click.echo(f"Skill Diagnostic Report: {target}")
    click.echo("━" * 58)
    click.echo(f"Overall Status: {status}\n")
    for c in report.checks:
        mark = "  ✓" if c.passed else "  ✗"
        sev = f"[{c.severity.value.upper()}]" if not c.passed else ""
        click.echo(f"{mark} {c.name:<25} {sev} {c.message}")
    if report.warnings:
        click.echo("\nWarnings:")
        for w in report.warnings:
            click.echo(f"  • {w}")
    if report.errors:
        for err in report.errors:
            click.echo(f"  • {err}")
    if not report.valid:
        sys.exit(1)
