"""Consolidated Click CLI command group for the skills subsystem.

Enforces Rule 6: Click CLI Group Single-Source Consolidation. All commands for the
'skills' group are declared here in a single co-located block.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import click

from harness.commands.skills.discovery import (
    export_skill_graph_visual_cmd,
    index_skills_cmd,
    list_skills_cmd,
    run_skill_cmd,
    scaffold_skill_cmd,
    validate_skill_cmd,
)
from harness.commands.skills.routing import (
    compile_guidance_cmd,
    intercept_action_cmd,
    route_skills_cmd,
    select_skills_cmd,
)
from harness.commands.skills.topology import (
    check_chain_feasibility_cmd,
    cluster_skills_cmd,
    discover_capabilities_cmd,
    find_skill_chain_cmd,
    get_prerequisite_closure_cmd,
    get_skill_topology_cmd,
)


@click.group("skills")
def skills_group() -> None:
    """Manage and query the agent skill knowledge graph."""


@skills_group.command("list")
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


@skills_group.command("run")
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


@skills_group.command("graph")
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


@skills_group.command("route")
@click.argument("intent")
@click.option("--top-k", default=3, help="Max matches to return")
def skills_route(intent: str, top_k: int) -> None:
    """Route natural language task intent to matching skills."""
    res = route_skills_cmd(intent, top_k=top_k)
    click.echo(f"🎯 Route matches for: {intent!r}")
    for idx, match in enumerate(res["matches"], 1):
        click.echo(
            f"  {idx}. {match['skill_name']} [{match['category']}] - Confidence: {match['confidence'] * 100:.1f}%"
        )
        if match["matched_triggers"]:
            click.echo(f"     Triggers: {', '.join(match['matched_triggers'])}")
    if res["recommended_chain"]:
        click.echo(
            f"\n🔗 Recommended Execution Chain: {' → '.join(res['recommended_chain'])}"
        )


@skills_group.command("select")
@click.argument("task")
@click.option("--max-skills", default=5, help="Maximum skills to include")
@click.option(
    "--no-verifier", is_flag=True, help="Disable automatic tail verifier injection"
)
@click.option("--path", default=".", help="Root directory to scan")
def skills_select(task: str, max_skills: int, no_verifier: bool, path: str) -> None:
    """Intelligently select skills and compile an execution plan for a given task."""
    res = select_skills_cmd(
        task, max_skills=max_skills, include_verifier=not no_verifier, root_path=path
    )
    plan = res["plan"]

    click.echo("\n🧠 Intelligent Skill Selection Plan")
    click.echo("━" * 80)
    click.echo(f"Task: {task}")
    click.echo(f"Match Confidence: {plan['confidence'] * 100:.1f}%")

    if plan["emergent_capability"]:
        cap = plan["emergent_capability"]
        click.echo(f"\n✨ Unlocked Emergent Capability: {cap['title']}")
        click.echo(f"   Rationale: {cap['novelty_rationale']}")
        if cap["target_outcomes"]:
            click.echo(f"   Target Outcomes: {', '.join(cap['target_outcomes'])}")

    if plan["prerequisites"]:
        click.echo(f"\n⚡ Pre-Flight Prerequisites: {', '.join(plan['prerequisites'])}")

    click.echo("\n🔗 Topological Execution Pipeline:")
    click.echo(f"   {' → '.join(plan['execution_pipeline'])}")

    if plan["stages"]:
        click.echo(f"\n📋 Execution Stages ({len(plan['stages'])} total):")
        for st in plan["stages"][:8]:
            gate = (
                f" [Gate: {st['completion_gate'][:50]}...]"
                if st["completion_gate"]
                else ""
            )
            click.echo(
                f"   • [{st['skill']}] Stage {st['stage_num']}: {st['name']}{gate}"
            )
        if len(plan["stages"]) > 8:
            click.echo(f"   • ... and {len(plan['stages']) - 8} more stages")

    if plan["active_anti_patterns"]:
        click.echo("\n🛡️ Active Anti-Pattern Guards:")
        for ap in plan["active_anti_patterns"][:4]:
            click.echo(f"   • {ap['anti_pattern']} ({ap['skill']})")

    if plan["recommended_verifier"]:
        click.echo(f"\n🔍 Contract Verifier: {plan['recommended_verifier']}")

    click.echo("━" * 80)


@skills_group.command("clusters")
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


@skills_group.command("capabilities")
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


@skills_group.command("create")
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


@skills_group.command("guidance")
@click.argument("task")
@click.option("--max-skills", default=4, help="Maximum skills to include in pipeline")
@click.option("--json", "as_json", is_flag=True, help="Output raw JSON payload")
@click.option("--path", default=".", help="Root directory to scan for skills")
def skills_guidance(task: str, max_skills: int, as_json: bool, path: str) -> None:
    """Compile and display an end-to-end execution guidance plan for an agent task (Rule 10)."""
    res = compile_guidance_cmd(task, max_skills=max_skills, root_path=path)
    if as_json:
        click.echo(json.dumps(res, indent=2))
        return

    click.echo("\n🧭 Active Skill Knowledge Guidance Plan")
    click.echo("━" * 80)
    click.echo(f"Task: {res['task']}")
    click.echo(f"Match Confidence: {res['confidence'] * 100:.1f}%")
    click.echo(f"Selected Skills: {', '.join(res['selected_skills'])}")
    click.echo(f"Execution Pipeline: {' -> '.join(res['execution_pipeline'])}")

    if res["stages"]:
        click.echo(f"\n📋 Key Stage Gates ({len(res['stages'])} total):")
        for st in res["stages"][:6]:
            gate = f" [Gate: {st['completion_gate'][:50]}...]" if st.get("completion_gate") else ""
            click.echo(f"   • [{st.get('skill', '')}] {st.get('name', '')}{gate}")

    if res["active_anti_patterns"]:
        click.echo("\n🛡️ Guarded Anti-Patterns:")
        for ap in res["active_anti_patterns"][:4]:
            click.echo(f"   • {ap.get('anti_pattern', '')} ({ap.get('skill', '')})")

    click.echo("\n📝 Formatted System Prompt Block:")
    click.echo("─" * 80)
    click.echo(res["prompt_block"].strip())
    click.echo("━" * 80)


@skills_group.command("intercept")
@click.argument("action_name")
@click.option("-p", "--param", "params", multiple=True, help="Action parameters in key=value format")
@click.option("--code", default=None, help="Code block to inspect via AST scanner")
@click.option("-s", "--skill", "skills", multiple=True, help="Active skill names guarding this action")
@click.option("--json", "as_json", is_flag=True, help="Output raw JSON observation")
@click.option("--path", default=".", help="Root directory to scan for skills")
def skills_intercept(
    action_name: str,
    params: tuple[str, ...],
    code: str | None,
    skills: tuple[str, ...],
    as_json: bool,
    path: str,
) -> None:
    """Evaluate a proposed agent action against anti-patterns and AST security gates (Rule 10)."""
    action_input: dict[str, Any] = {}
    for p in params:
        if "=" in p:
            k, v = p.split("=", 1)
            action_input[k.strip()] = v.strip()
    if code:
        action_input["code"] = code

    res = intercept_action_cmd(
        action_name=action_name,
        action_input=action_input,
        active_skills=list(skills) if skills else None,
        root_path=path,
    )

    if as_json:
        click.echo(json.dumps(res, indent=2))
        return

    click.echo("\n🛡️ Action Interception Security Report")
    click.echo("━" * 80)
    click.echo(f"Action: {action_name}")
    status_badge = "✓ PASSED (Clean)" if res["status"] == "ok" else "✗ INTERCEPTED (Violation Detected)"
    click.echo(f"Status: {status_badge}")

    if res["violations"]:
        click.echo(f"\nViolations Found ({len(res['violations'])} total):")
        for v in res["violations"]:
            click.echo(f"   ❌ [{v['skill_name']}] {v['anti_pattern']}")
            if v.get("symptom"):
                click.echo(f"      Symptom: {v['symptom']}")
            if v.get("remedy"):
                click.echo(f"      Remedy:  {v['remedy']}")
        click.echo("\nIn-Flight Self-Repair Observation:")
        click.echo("─" * 80)
        click.echo(json.dumps(res["observation"], indent=2))
    else:
        click.echo("   Zero security or anti-pattern violations detected in action parameters.")
    click.echo("━" * 80)


@skills_group.command("prereqs")
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


@skills_group.command("check-chain")
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
