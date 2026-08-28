"""Tests for Deepened Swarm Coordinator and Context Optimizer Seam (Cycle 12)."""

from __future__ import annotations

import asyncio
from typing import Any
import pytest

from harness.agent.context_optimizer import (
    AGENT_CONTEXT_OPTIMIZER_KEY,
    ContextOptimizationConfig,
    DefaultContextOptimizer,
)
from harness.agent.swarm import (
    SWARM_COORDINATOR_KEY,
    SwarmCoordinator,
    SwarmCoordinatorPlugin,
    SwarmDAG,
    SwarmNode,
    SwarmTaskResult,
)
from harness.kernel.context import ServiceContext


@pytest.mark.asyncio
@pytest.mark.unit
async def test_swarm_coordinator_with_context_optimizer() -> None:
    """Test that SwarmCoordinator applies AgentContextOptimizer compaction to upstream node results."""
    ctx = ServiceContext()

    # Configure aggressive compaction (max 100 chars per observation)
    config = ContextOptimizationConfig(max_observation_chars=100, compact_json=True)
    optimizer = DefaultContextOptimizer(config=config, context=ctx)
    ctx.provide(AGENT_CONTEXT_OPTIMIZER_KEY, optimizer)

    coordinator = SwarmCoordinator(context=ctx)

    dag = SwarmDAG()
    dag.add_node(
        SwarmNode(
            id="node_a",
            role="researcher",
            task="Produce voluminous dataset",
        )
    )
    dag.add_node(
        SwarmNode(
            id="node_b",
            role="synthesizer",
            task="Synthesize insights from node_a",
            dependencies=["node_a"],
        )
    )

    prompts_received: list[str] = []

    def mock_executor(node: SwarmNode, upstream_ctx: dict[str, Any]) -> Any:
        if node.id == "node_a":
            # Generate large dictionary with 50 keys
            return {f"metric_{i}": "x" * 50 for i in range(50)}
        else:
            # Node B receives the compacted upstream context in its prompt/context
            prompts_received.append(str(upstream_ctx.get("node_a")))
            return "Final output from node_b"

    result: SwarmTaskResult = await coordinator.run_swarm(
        dag=dag,
        custom_executor=mock_executor,
    )

    assert result.status == "completed"
    assert "node_a" in result.node_results
    assert "node_b" in result.node_results

    # Verify that Node B received compacted upstream context (< 150 chars, not full massive dict)
    assert len(prompts_received) == 1
    compacted_val = prompts_received[0]
    assert len(compacted_val) <= 150
    assert "..." in compacted_val or "metric_" in compacted_val


@pytest.mark.asyncio
@pytest.mark.unit
async def test_swarm_coordinator_fallback_without_optimizer() -> None:
    """Test that SwarmCoordinator operates cleanly when AgentContextOptimizer is absent."""
    ctx = ServiceContext()
    coordinator = SwarmCoordinator(context=ctx)

    dag = SwarmDAG()
    dag.add_node(SwarmNode(id="n1", role="worker1", task="Task 1"))
    dag.add_node(SwarmNode(id="n2", role="worker2", task="Task 2", dependencies=["n1"]))

    def mock_executor(node: SwarmNode, upstream_ctx: dict[str, Any]) -> Any:
        if node.id == "n1":
            return {"raw_data": 12345}
        return f"Got raw: {upstream_ctx.get('n1')}"

    result = await coordinator.run_swarm(dag=dag, custom_executor=mock_executor)
    assert result.status == "completed"
    assert result.node_results["n2"] == "Got raw: {'raw_data': 12345}"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_swarm_coordinator_plugin_ioc_registration() -> None:
    """Test that SwarmCoordinatorPlugin properly registers SWARM_COORDINATOR_KEY."""
    plugin = SwarmCoordinatorPlugin()
    assert SWARM_COORDINATOR_KEY in plugin.provides

    ctx = ServiceContext()
    await plugin.on_load(ctx)

    coord = ctx.require(SWARM_COORDINATOR_KEY)
    assert coord is not None
    assert hasattr(coord, "run_swarm")
    assert hasattr(coord, "decompose")
