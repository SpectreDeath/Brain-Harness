"""Test suite for Skill-Driven Dynamic Swarm Orchestrator."""

from unittest.mock import MagicMock

import pytest

from harness.agent.swarm import SwarmCoordinator, SwarmDAG, SwarmNode
from harness.kernel.context import ServiceContext
from harness.services.skill_graph import (
    SKILL_REGISTRY_KEY,
    SkillCardDefinition,
    SkillRegistryService,
    SkillStageDefinition,
)


@pytest.fixture
def mock_context():
    ctx = ServiceContext()
    mock_registry = MagicMock(spec=SkillRegistryService)

    # Mock skill definition
    skill_deepen = SkillCardDefinition(
        name="deepen-architecture",
        category="codebase",
        target="Iterative architecture deepening loop",
        stages=[
            SkillStageDefinition(stage_num=1, name="Analyze", completion_gate="Friction sites identified"),
            SkillStageDefinition(stage_num=2, name="Assess", completion_gate="Candidates scored"),
            SkillStageDefinition(stage_num=3, name="Recommend", completion_gate="Visual brief rendered"),
        ],
        tools=["view_file", "grep_search"],
    )

    mock_registry.get_skill.side_effect = lambda name: skill_deepen if name == "deepen-architecture" else None
    mock_registry.route_intent.return_value = {
        "status": "ok",
        "matches": [{"skill_name": "deepen-architecture", "score": 3.5}],
    }

    ctx.provide(SKILL_REGISTRY_KEY, mock_registry)
    return ctx


def test_decompose_with_skills_explicit(mock_context):
    coordinator = SwarmCoordinator(context=mock_context)
    dag = coordinator.decompose_with_skills(
        "Refactor auth seam",
        skill_names=["deepen-architecture"],
        include_verifier=True,
    )

    assert isinstance(dag, SwarmDAG)
    assert len(dag.nodes) == 4  # 3 stages + 1 verifier

    node_ids = list(dag.nodes.keys())
    assert node_ids[0] == "deepen-architecture_stage_1"
    assert node_ids[1] == "deepen-architecture_stage_2"
    assert node_ids[2] == "deepen-architecture_stage_3"
    assert node_ids[3] == "adversarial_verifier"

    # Verify dependency chain
    assert dag.nodes["deepen-architecture_stage_2"].dependencies == ["deepen-architecture_stage_1"]
    assert dag.nodes["deepen-architecture_stage_3"].dependencies == ["deepen-architecture_stage_2"]
    assert dag.nodes["adversarial_verifier"].dependencies == ["deepen-architecture_stage_3"]


def test_decompose_with_skills_intent_routing(mock_context):
    coordinator = SwarmCoordinator(context=mock_context)
    # Without skill_names, should use route_intent
    dag = coordinator.decompose_with_skills(
        "Audit architecture seams and eliminate shallow modules",
        include_verifier=False,
    )

    assert len(dag.nodes) == 3  # 3 stages, no verifier
    assert "deepen-architecture_stage_1" in dag.nodes


@pytest.mark.asyncio
async def test_dispatch_skill_swarm_execution(mock_context):
    coordinator = SwarmCoordinator(context=mock_context)

    executed_nodes = []

    def mock_executor(node: SwarmNode, ctx: dict):
        executed_nodes.append(node.id)
        return {"status": "ok", "vote": "approve"}

    res = await coordinator.dispatch_skill_swarm(
        "Audit architecture",
        skill_names=["deepen-architecture"],
        custom_executor=mock_executor,
        include_verifier=True,
    )

    assert res.status == "completed"
    assert len(executed_nodes) == 4
    assert executed_nodes[-1] == "adversarial_verifier"
