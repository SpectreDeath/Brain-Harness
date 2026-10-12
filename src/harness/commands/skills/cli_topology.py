"""Click CLI subcommands for skill topology, chains, clusters, and capabilities."""

from __future__ import annotations

import json

import click

from harness.commands.skills.topology import (
    check_chain_feasibility_cmd,
    cluster_skills_cmd,
    discover_capabilities_cmd,
    find_skill_chain_cmd,
    get_prerequisite_closure_cmd,
    get_skill_topology_cmd,
)


@click.command("clusters")
@click.option("--min-size", default=2, help="Minimum cluster size")
@click.option("--path", default=".", help="Root directory to scan")
def skills_clusters(min_size: int, path: str) -> None:
    """Cluster workspace skills into functional domains and display emergent capabilities."""
    res = cluster_skills_cmd(min_cluster_size=min_size, root_path=path)
    clusters = res["clusters"]

    click.echo(f"\n🌐 Discovered Skill Clusters ({len(clusters)} total)")
    click.echo("━" * 80)
    for c in clusters:
        emergent_badge = (
            f" [✨ {len(c['emergent_capabilities'])} emergent capabilities]"
            if c["emergent_capabilities"]
            else ""
        )
        click.echo(
            f"🏷️  {c['name']} (Size: {len(c['skills'])}, Cohesion: {c['cohesion_score'] * 100:.0f}%){emergent_badge}"
        )
        click.echo(f"   Central Hub: {c['central_hub_skill']} | Domain: {c['domain']}")
        click.echo(
            f"   Skills: {', '.join(c['skills'][:6])}{' ...' if len(c['skills']) > 6 else ''}"
        )
        for cap in c["emergent_capabilities"][:2]:
            click.echo(f"   ✨ {cap['title']}")
        click.echo("─" * 80)


@click.command("capabilities")
@click.option("--query", default=None, help="Filter capabilities by keyword or domain")
@click.option("--path", default=".", help="Root directory to scan")
def skills_capabilities(query: str | None, path: str) -> None:
    """Display novel emergent macro-capabilities discovered from the skill graph."""
    res = discover_capabilities_cmd(query=query, root_path=path)
    caps = res["capabilities"]

    click.echo(f"\n✨ Emergent Macro-Capabilities ({len(caps)} total)")
    click.echo("━" * 80)
    for idx, cap in enumerate(caps, 1):
        click.echo(f"{idx}. {cap['title']}")
        click.echo(f"   ID: {cap['id']}")
        click.echo(f"   Constituent Skills: {', '.join(cap['primary_skills'])}")
        click.echo(f"   Pipeline: {' → '.join(cap['recommended_pipeline'])}")
        click.echo(f"   Novelty Rationale: {cap['novelty_rationale']}")
        if cap["target_outcomes"]:
            click.echo(f"   Outcomes: {', '.join(cap['target_outcomes'])}")
        click.echo("─" * 80)


@click.command("chain")
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


@click.command("info")
@click.argument("skill_name")
def skills_info(skill_name: str) -> None:
    """Inspect topological dependencies and anti-patterns for a skill."""
    res = get_skill_topology_cmd(skill_name)
    if res["status"] == "ok":
        topo = res["topology"]
        skill = topo["skill"]
        click.echo(f"🏷️  Skill: {skill['name']} (v{skill['version']})")
        click.echo(
            f"   Category: {skill['category']} | Invocation: {skill['invocation']}"
        )
        click.echo(f"   Target: {skill['target'] or skill['description']}")
        if topo["prerequisites"]:
            click.echo(f"   Prerequisites: {', '.join(topo['prerequisites'])}")
        if topo["downstream_handoffs"]:
            click.echo(
                f"   Downstream Handoffs: {', '.join(topo['downstream_handoffs'])}"
            )
        if topo["mitigated_anti_patterns"]:
            click.echo(
                f"   Mitigated Anti-Patterns: {', '.join(topo['mitigated_anti_patterns'])}"
            )
    else:
        click.echo(f"✗ {res.get('reason', 'Skill not found')}", err=True)


@click.command("prereqs")
@click.argument("skill_name")
@click.option("--json", "as_json", is_flag=True, help="Output raw JSON format")
@click.option("--path", default=".", help="Root directory to scan for skills")
def skills_prereqs(skill_name: str, as_json: bool, path: str) -> None:
    """Inspect full transitive prerequisite closure for a skill in topological order."""
    res = get_prerequisite_closure_cmd(skill_name, root_path=path)
    if as_json:
        click.echo(json.dumps(res, indent=2))
        return

    click.echo(f"\n🔗 Transitive Prerequisite Closure: {skill_name}")
    click.echo("━" * 80)
    if res["prerequisites"]:
        click.echo(f"Required execution sequence ({res['count']} skills):")
        for idx, p in enumerate(res["prerequisites"], start=1):
            click.echo(f"  {idx}. {p}")
    else:
        click.echo(f"  Skill '{skill_name}' has no upstream prerequisite dependencies (root skill).")
    click.echo("━" * 80)


@click.command("check-chain")
@click.argument("skills", nargs=-1, required=True)
@click.option("--verify-prereqs/--no-verify-prereqs", default=True, help="Verify topological prerequisite closure")
@click.option("--json", "as_json", is_flag=True, help="Output raw JSON format")
@click.option("--path", default=".", help="Root directory to scan for skills")
def skills_check_chain(
    skills: tuple[str, ...],
    verify_prereqs: bool,
    as_json: bool,
    path: str,
) -> None:
    """Evaluate whether an execution sequence of skills is feasible with all preconditions met (Rule 10)."""
    chain = list(skills)
    res = check_chain_feasibility_cmd(
        chain=chain,
        root_path=path,
        verify_prerequisites=verify_prereqs,
    )
    if as_json:
        click.echo(json.dumps(res, indent=2))
        return

    click.echo(f"\n🔗 Chain Feasibility Assessment ({len(chain)} steps)")
    click.echo("━" * 80)
    click.echo(f"Chain: {' -> '.join(chain)}")
    status_badge = "✓ FEASIBLE (All preconditions met)" if res["feasible"] else "✗ BLOCKED (Missing dependencies/prerequisites)"
    click.echo(f"Status: {status_badge}")
    if res["missing_items"]:
        click.echo(f"\nMissing Items ({res['missing_count']} total):")
        for item in res["missing_items"]:
            click.echo(f"   ❌ {item}")
    else:
        click.echo("   Zero missing prerequisites or unsatisfied service preconditions.")
    click.echo("━" * 80)
