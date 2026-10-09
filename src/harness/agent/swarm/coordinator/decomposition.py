"""Objective decomposition into Swarm DAGs via default archetypes or skill graph intelligence."""

from __future__ import annotations

from typing import Any

from harness.agent.swarm.models import SwarmDAG, SwarmNode
from harness.kernel.context import ServiceContext


def decompose_objective(
    objective: str,
    agents: list[dict[str, Any]] | None = None,
) -> SwarmDAG:
    """Decompose a high-level objective into a structured SwarmDAG."""
    dag = SwarmDAG()

    if not agents:
        agents = [
            {
                "id": "researcher",
                "role": "researcher",
                "task": f"Research and gather facts for: {objective}",
            },
            {
                "id": "developer",
                "role": "developer",
                "task": f"Implement solution based on research for: {objective}",
                "dependencies": ["researcher"],
            },
            {
                "id": "critic",
                "role": "critic",
                "task": f"Review and validate developer output for: {objective}",
                "dependencies": ["developer"],
            },
            {
                "id": "synthesizer",
                "role": "synthesizer",
                "task": f"Synthesize final deliverable for: {objective}",
                "dependencies": ["critic"],
            },
        ]

    for a in agents:
        node = SwarmNode(
            id=a["id"],
            role=a.get("role", "worker"),
            task=a.get("task", objective),
            dependencies=list(a.get("dependencies", [])),
            tools=list(a.get("tools", [])),
            allocated_tokens=int(a.get("allocated_tokens", 10_000)),
        )
        dag.add_node(node)

    return dag


def decompose_objective_with_skills(
    context: ServiceContext,
    objective: str,
    skill_names: list[str] | None = None,
    top_k: int = 3,
    include_verifier: bool = True,
) -> SwarmDAG:
    """Decompose a high-level objective into a structured SwarmDAG derived from agent skills."""
    try:
        from harness.services.skill_graph import resolve_skill_intelligence

        intelligence = resolve_skill_intelligence(context)
    except Exception:
        intelligence = None

    if intelligence is None:
        return decompose_objective(objective)

    target_skills: list[str] = []
    if skill_names:
        target_skills = list(skill_names)
    else:
        try:
            guidance = intelligence.compile_execution_guidance(
                objective, max_skills=top_k, include_verifier=include_verifier
            )
            if guidance and guidance.execution_pipeline:
                target_skills = list(guidance.execution_pipeline)
        except Exception:
            pass

        if not target_skills:
            try:
                plan = intelligence.select_skills_for_task(
                    objective, max_skills=top_k, include_verifier=include_verifier
                )
                if plan and getattr(plan, "execution_pipeline", None):
                    target_skills = list(plan.execution_pipeline)
            except Exception:
                pass

        if not target_skills:
            routing = intelligence.route_intent(objective, top_k=top_k)
            target_skills = [
                m.get("skill_name") or m.get("name")
                for m in (routing.get("matches") or [])
                if (m.get("skill_name") or m.get("name"))
            ]
        if not target_skills:
            return decompose_objective(objective)

    dag = SwarmDAG()
    prev_node_id: str | None = None

    for skill_name in target_skills:
        skill = intelligence.get_skill(skill_name)
        if not skill:
            continue

        if skill.stages:
            for stage in skill.stages:
                node_id = f"{skill.name}_stage_{stage.stage_num}"
                deps = [prev_node_id] if prev_node_id else []
                task_desc = (
                    f"Execute [{skill.name}] Stage {stage.stage_num} ({stage.name}) "
                    f"for objective: {objective}. Gate: {stage.completion_gate}"
                )
                node = SwarmNode(
                    id=node_id,
                    role=f"{skill.name}:{stage.name}",
                    task=task_desc,
                    dependencies=deps,
                    tools=list(skill.tools) if skill.tools else [],
                    allocated_tokens=15_000,
                )
                dag.add_node(node)
                prev_node_id = node_id
        else:
            node_id = f"skill_{skill.name}"
            deps = [prev_node_id] if prev_node_id else []
            node = SwarmNode(
                id=node_id,
                role=f"specialist:{skill.name}",
                task=f"Apply skill [{skill.name}] target: {skill.target} on objective: {objective}",
                dependencies=deps,
                tools=list(skill.tools) if skill.tools else [],
                allocated_tokens=20_000,
            )
            dag.add_node(node)
            prev_node_id = node_id

    if include_verifier and prev_node_id and not any("verifier" in n for n in dag.nodes):
        verifier_id = "adversarial_verifier"
        dag.add_node(
            SwarmNode(
                id=verifier_id,
                role="adversarial_verifier",
                task=f"Rigorously verify outputs and assert invariants for objective: {objective}",
                dependencies=[prev_node_id],
                tools=["verify_contract", "arch_lint"],
                allocated_tokens=10_000,
            )
        )

    if not dag.nodes:
        return decompose_objective(objective)

    return dag
