"""Tests for Swarm Live DAG Web Canvas endpoints (/api/swarm/dispatch-skill, /api/swarm/runs/{id}/mermaid)."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from harness.agent.swarm import (
    SWARM_COORDINATOR_KEY,
    SwarmCoordinator,
    SwarmExecutionTree,
    SwarmNodeExecution,
    SwarmTaskResult,
    SwarmWaveMetrics,
)
from harness.events.bus import EventBus
from harness.kernel.context import ServiceContext
from harness.kernel.lifecycle import PluginLifecycle
from harness.services.agent_graph import (
    AGENT_GRAPH_STORE_KEY,
    ExecutionGraphExport,
    ExecutionGraphNode,
)
from harness.ui.server import create_app


class MockAgentGraphService:
    def __init__(self) -> None:
        self.threads: dict[str, ExecutionGraphNode] = {}

    def export_graph(self, root_node_id: str | None = None) -> ExecutionGraphExport:
        matching = {
            k: v
            for k, v in self.threads.items()
            if root_node_id is None or k.startswith(root_node_id) or v.parent_id == root_node_id
        }
        return ExecutionGraphExport(
            status="ok",
            root_node_id=root_node_id,
            total_nodes=len(matching),
            total_edges=0,
            total_tokens_rollup=1200,
            nodes=matching,
            edges=[],
        )


@pytest.mark.unit
@pytest.mark.asyncio
class TestUISwarmCanvas:
    async def test_swarm_dispatch_skill_endpoint(self) -> None:
        ctx = ServiceContext()
        lifecycle = PluginLifecycle(ctx)
        bus = EventBus()

        coord = SwarmCoordinator(ctx, event_bus=bus)
        ctx.provide(SWARM_COORDINATOR_KEY, coord)

        app = create_app(ctx, lifecycle, bus)
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            res = await client.post(
                "/api/swarm/dispatch-skill",
                json={
                    "objective": "Audit and modernize legacy seams",
                    "skills": ["tdd", "codebase-design"],
                    "max_tokens": 80000,
                    "include_verifier": True,
                },
            )
            assert res.status_code == 200
            data = res.json()
            assert data["status"] == "ok"
            assert "result" in data
            result = data["result"]
            assert result["status"] == "completed"
            assert "run_id" in result
            assert "execution_tree" in result

    async def test_swarm_mermaid_and_tree_endpoints(self) -> None:
        ctx = ServiceContext()
        lifecycle = PluginLifecycle(ctx)
        bus = EventBus()

        coord = SwarmCoordinator(ctx, event_bus=bus)
        ctx.provide(SWARM_COORDINATOR_KEY, coord)

        # Pre-seed a known run with execution tree
        run_id = "test_run_mermaid_42"
        nodes = {
            "node_step1": SwarmNodeExecution(
                id="node_step1",
                role="planner",
                task="Plan architecture",
                status="completed",
                duration=1.5,
                tokens_used=400,
                dependencies=[],
            ),
            "node_step2": SwarmNodeExecution(
                id="node_step2",
                role="executor",
                task="Refactor seams",
                status="completed",
                duration=3.2,
                tokens_used=1200,
                dependencies=["node_step1"],
            ),
            "node_verifier": SwarmNodeExecution(
                id="node_verifier",
                role="verifier",
                task="Adversarial verification",
                status="completed",
                duration=0.8,
                tokens_used=300,
                dependencies=["node_step2"],
            ),
        }
        waves = [
            SwarmWaveMetrics(wave_index=0, node_ids=["node_step1"], duration=1.5, total_tokens=400),
            SwarmWaveMetrics(
                wave_index=1,
                node_ids=["node_step2"],
                duration=3.2,
                total_tokens=1200,
                bottleneck_node_id="node_step2",
            ),
            SwarmWaveMetrics(wave_index=2, node_ids=["node_verifier"], duration=0.8, total_tokens=300),
        ]
        exec_tree = SwarmExecutionTree(
            run_id=run_id,
            objective="Seam refactoring mission",
            status="completed",
            duration=5.5,
            total_tokens=1900,
            nodes=nodes,
            waves=waves,
            critical_path=["node_step1", "node_step2", "node_verifier"],
            critical_path_duration=5.5,
            bottlenecks=[{"node_id": "node_step2", "reasons": ["high_tokens (1200)"]}],
        )
        task_res = SwarmTaskResult(
            run_id=run_id,
            objective="Seam refactoring mission",
            status="completed",
            total_tokens=1900,
            execution_tree=exec_tree,
        )
        coord._run_history[run_id] = task_res

        app = create_app(ctx, lifecycle, bus)
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 1. Test GET /api/swarm/runs/{run_id}/mermaid
            m_res = await client.get(f"/api/swarm/runs/{run_id}/mermaid")
            assert m_res.status_code == 200
            m_data = m_res.json()
            assert m_data["status"] == "ok"
            assert m_data["run_id"] == run_id
            mermaid_code = m_data["mermaid"]
            assert "graph TD" in mermaid_code
            assert "node_step1" in mermaid_code
            assert "node_step2" in mermaid_code
            assert "node_verifier" in mermaid_code
            assert "node_step1 --> node_step2" in mermaid_code
            assert "node_step2 --> node_verifier" in mermaid_code
            # Verify critical path classes are present
            assert "class node_step1 completedCritical" in mermaid_code
            assert "class node_step2 completedCritical" in mermaid_code
            assert "class node_verifier completedCritical" in mermaid_code

            # 2. Test GET /api/swarm/runs/{run_id}/tree
            t_res = await client.get(f"/api/swarm/runs/{run_id}/tree")
            assert t_res.status_code == 200
            t_data = t_res.json()
            assert t_data["status"] == "ok"
            tree = t_data["tree"]
            assert tree["run_id"] == run_id
            assert len(tree["nodes"]) == 3
            assert tree["critical_path"] == ["node_step1", "node_step2", "node_verifier"]
            assert len(tree["waves"]) == 3
            assert len(tree["bottlenecks"]) == 1
            assert tree["bottlenecks"][0]["node_id"] == "node_step2"

    async def test_swarm_mermaid_fallback_agent_graph(self) -> None:
        ctx = ServiceContext()
        lifecycle = PluginLifecycle(ctx)
        bus = EventBus()

        mock_graph = MockAgentGraphService()
        run_id = "agent_graph_run_99"
        mock_graph.threads = {
            f"{run_id}_worker1": ExecutionGraphNode(
                node_id=f"{run_id}_worker1",
                role="researcher",
                status="completed",
                tokens_used=500,
                parent_id=run_id,
            ),
            f"{run_id}_worker2": ExecutionGraphNode(
                node_id=f"{run_id}_worker2",
                role="synthesizer",
                status="completed",
                tokens_used=700,
                parent_id=f"{run_id}_worker1",
            ),
        }
        ctx.provide(AGENT_GRAPH_STORE_KEY, mock_graph)

        app = create_app(ctx, lifecycle, bus)
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            res = await client.get(f"/api/swarm/runs/{run_id}/mermaid")
            assert res.status_code == 200
            data = res.json()
            assert data["status"] == "ok"
            assert data["run_id"] == run_id
            assert "graph TD" in data["mermaid"]
            assert f"{run_id}_worker1" in data["mermaid"]
            assert f"{run_id}_worker2" in data["mermaid"]
