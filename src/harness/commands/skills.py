"""Skill commands — pure async and sync programmatic entry points for skill knowledge and authoring.

Provides an authoritative seam for indexing, routing, chain discovery, topology inspection,
scaffolding, and validation across agent skills. Delegates to BuiltinSkillRegistryService.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import structlog

from harness.creator.skills import (
    SkillOptions,
    SkillResult,
    SkillScaffoldEngine,
    SkillValidator,
)
from harness.creator.validator import ValidationReport
from harness.services.skill_graph import (
    BuiltinSkillGraphService,
    BuiltinSkillRegistryService,
    SkillCardDefinition,
)

logger = structlog.get_logger()

# Global default registry instance
_DEFAULT_REGISTRY = BuiltinSkillRegistryService()
_DEFAULT_GRAPH = BuiltinSkillGraphService(registry=_DEFAULT_REGISTRY)


def index_skills_cmd(root_path: str | Path = ".") -> dict[str, Any]:
    """Scan workspace (.agents/skills, plugins) and construct the skill knowledge graph."""
    registry = BuiltinSkillRegistryService(default_root=str(root_path))
    skills = registry.discover_all(str(root_path))
    categories = sorted({s.category for s in skills})

    total_edges = sum(len(s.dependencies) for s in skills)

    return {
        "status": "ok",
        "indexed_skills": len(skills),
        "categories": categories,
        "total_nodes": len(skills),
        "total_edges": total_edges,
    }


def export_skill_graph_visual_cmd(output_path: str | Path | None = None) -> dict[str, Any]:
    """Generate an interactive HTML visual brief of the skill graph."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            html_path = pool.submit(asyncio.run, _DEFAULT_GRAPH.export_html_brief(str(output_path) if output_path else None)).result()
    else:
        html_path = asyncio.run(_DEFAULT_GRAPH.export_html_brief(str(output_path) if output_path else None))

    skills = _DEFAULT_REGISTRY.discover_all()
    return {
        "status": "ok",
        "html_path": html_path,
        "total_skills": len(skills),
        "node_count": len(skills),
    }


def route_skills_cmd(intent: str, top_k: int = 3, root_path: str | Path = ".") -> dict[str, Any]:
    """Route natural language task intent to matching skills and recommended chains."""
    registry = BuiltinSkillRegistryService(default_root=str(root_path))
    return registry.route_intent(intent, top_k=top_k)


def find_skill_chain_cmd(start_skill: str, target_skill: str) -> dict[str, Any]:
    """Find directed execution path between two skills."""
    res = _DEFAULT_REGISTRY.get_chain(start_skill, target_skill)
    return {
        "status": res.status,
        "start": res.start_skill,
        "target": res.target_skill,
        "start_skill": res.start_skill,
        "target_skill": res.target_skill,
        "chain": res.chain,
        "length": res.length,
    }


def get_skill_topology_cmd(skill_name: str) -> dict[str, Any]:
    """Inspect topological dependencies, prerequisites, and anti-patterns for a skill."""
    skill = _DEFAULT_REGISTRY.get_skill(skill_name)
    if not skill:
        return {"status": "error", "reason": f"Skill '{skill_name}' not found"}

    return {
        "status": "ok",
        "topology": {
            "skill": {
                "name": skill.name,
                "version": skill.version,
                "category": skill.category,
                "invocation": skill.invocation,
                "target": skill.target,
                "description": skill.target,
                "stages": [s.model_dump() for s in skill.stages],
                "anti_patterns": [ap.model_dump() for ap in skill.anti_patterns],
                "invariants": [inv.model_dump() for inv in skill.invariants],
            },
            "prerequisites": skill.dependencies,
            "downstream_handoffs": [],
            "mitigated_anti_patterns": [ap.name for ap in skill.anti_patterns],
        },
    }


def list_skills_cmd(root_path: str | Path = ".") -> list[SkillCardDefinition]:
    """List all discovered skill cards."""
    registry = BuiltinSkillRegistryService(default_root=str(root_path))
    return registry.discover_all(str(root_path))


def scaffold_skill_cmd(
    name: str,
    *,
    description: str = "",
    category: str = "engineering / meta-skills",
    target_dir: str | Path | None = None,
    triggers: list[str] | tuple[str, ...] | None = None,
    auto_validate: bool = False,
) -> SkillResult:
    """Scaffold a high-precision agent skill with SKILL.md and CARD.md specifications."""
    clean_name = name.strip().lower().replace("_", "-")
    out_dir = Path(target_dir) if target_dir else Path(".agents") / "skills" / clean_name

    opts = SkillOptions(
        name=clean_name,
        description=description,
        category=category,
        triggers=list(triggers) if triggers else [],
        auto_validate=auto_validate,
    )
    return SkillScaffoldEngine.scaffold(out_dir, options=opts)


def validate_skill_cmd(skill_dir: str | Path = ".") -> ValidationReport:
    """Validate an agent skill package against deep-module craft standards."""
    target = Path(skill_dir).resolve()
    return SkillValidator.validate(target)


# --- Click CLI adapters ---
import sys
import click


@click.group("skills")
def skills_group() -> None:
    """Manage and query the agent skill knowledge graph."""


@skills_group.command("graph")
@click.option("--visual", is_flag=True, help="Generate interactive HTML visual brief in %TEMP%")
@click.option("--path", default=".", help="Root directory to scan for skills")
def skills_graph(visual: bool, path: str) -> None:
    """Index and display the workspace skill knowledge graph."""
    res = index_skills_cmd(path)
    click.echo(f"📊 Indexed {res['indexed_skills']} skills across {len(res['categories'])} categories.")
    click.echo(f"   Nodes: {res['total_nodes']} | Relation Edges: {res['total_edges']}")
    click.echo(f"   Categories: {', '.join(res['categories'])}")

    if visual:
        vis_res = export_skill_graph_visual_cmd()
        click.echo(f"\n🌐 Visual Brief generated: {vis_res['html_path']}")


@skills_group.command("route")
@click.argument("intent")
@click.option("--top-k", default=3, help="Max matches to return")
def skills_route(intent: str, top_k: int) -> None:
    """Route natural language task intent to matching skills."""
    res = route_skills_cmd(intent, top_k=top_k)
    click.echo(f"🎯 Route matches for: {intent!r}")
    for idx, match in enumerate(res["matches"], 1):
        click.echo(f"  {idx}. {match['skill_name']} [{match['category']}] - Confidence: {match['confidence']*100:.1f}%")
        if match["matched_triggers"]:
            click.echo(f"     Triggers: {', '.join(match['matched_triggers'])}")
    if res["recommended_chain"]:
        click.echo(f"\n🔗 Recommended Execution Chain: {' → '.join(res['recommended_chain'])}")


@skills_group.command("chain")
@click.argument("start_skill")
@click.argument("target_skill")
def skills_chain(start_skill: str, target_skill: str) -> None:
    """Find directed execution path between two skills."""
    res = find_skill_chain_cmd(start_skill, target_skill)
    if res["status"] == "ok":
        click.echo(f"🔗 Execution Path ({res['length']} steps):")
        click.echo(f"   {' → '.join(res['chain'])}")
    else:
        click.echo(f"✗ No path found between '{start_skill}' and '{target_skill}'.")


@skills_group.command("info")
@click.argument("skill_name")
def skills_info(skill_name: str) -> None:
    """Inspect topological dependencies and anti-patterns for a skill."""
    res = get_skill_topology_cmd(skill_name)
    if res["status"] == "ok":
        topo = res["topology"]
        skill = topo["skill"]
        click.echo(f"🏷️  Skill: {skill['name']} (v{skill['version']})")
        click.echo(f"   Category: {skill['category']} | Invocation: {skill['invocation']}")
        click.echo(f"   Target: {skill['target'] or skill['description']}")
        if topo["prerequisites"]:
            click.echo(f"   Prerequisites: {', '.join(topo['prerequisites'])}")
        if topo["downstream_handoffs"]:
            click.echo(f"   Downstream Handoffs: {', '.join(topo['downstream_handoffs'])}")
        if topo["mitigated_anti_patterns"]:
            click.echo(f"   Mitigated Anti-Patterns: {', '.join(topo['mitigated_anti_patterns'])}")
    else:
        click.echo(f"✗ {res.get('reason', 'Skill not found')}", err=True)


@skills_group.command("create")
@click.argument("name")
@click.option("--description", "-d", default="", help="Skill description and trigger bounds")
@click.option("--category", "-c", default="engineering / meta-skills", help="Skill domain category")
@click.option("--target-dir", "-t", default=None, help="Destination directory (defaults to .agents/skills/<name>)")
@click.option("--trigger", "-g", "triggers", multiple=True, help="Trigger phrases for skill routing")
@click.option("--validate", "auto_validate", is_flag=True, help="Validate skill specifications on creation")
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


@skills_group.command("validate")
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


__all__ = [
    "export_skill_graph_visual_cmd",
    "find_skill_chain_cmd",
    "get_skill_topology_cmd",
    "index_skills_cmd",
    "list_skills_cmd",
    "route_skills_cmd",
    "scaffold_skill_cmd",
    "skills_group",
    "validate_skill_cmd",
]
