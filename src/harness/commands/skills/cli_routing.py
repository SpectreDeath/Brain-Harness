"""Click CLI subcommands for skill routing, selection, guidance, and action interception."""

from __future__ import annotations

import json
from typing import Any

import click

from harness.commands.skills.routing import (
    compile_guidance_cmd,
    intercept_action_cmd,
    route_skills_cmd,
    select_skills_cmd,
)


@click.command("route")
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


@click.command("select")
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


@click.command("guidance")
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


@click.command("intercept")
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
