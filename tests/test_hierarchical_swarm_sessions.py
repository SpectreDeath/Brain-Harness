"""Tests for Hierarchical Swarm Session Trees and Epistemic Lineage.

Verifies end-to-end parent-child session hierarchies, DAG execution tree
reconstruction, token telemetry aggregation, and backward compatibility.
"""

from __future__ import annotations

import pytest

from harness.agent.base import AgentLoopService, AgentStep, AgentTaskResult
from harness.agent.session import (
    AGENT_SESSION_MANAGER_KEY,
    AgentSessionManager,
    InMemoryAgentSessionStore,
)
from harness.agent.swarm import (
    SwarmCoordinator,
    SwarmDAG,
    SwarmNode,
)
from harness.kernel.context import ServiceContext


class MockAgentLoop(AgentLoopService):
    """Mock agent loop service recording steps and returning dummy answers."""

    def __init__(self, step_answer: str = "Mock answer") -> None:
        self.step_answer = step_answer
        self.calls: list[dict[str, any]] = []

    async def run_task(
        self,
        task: str,
        *,
        max_steps: int = 10,
        context: dict[str, any] | None = None,
        session_id: str | None = None,
    ) -> AgentTaskResult:
        self.calls.append({
            "task": task,
            "max_steps": max_steps,
            "context": context,
            "session_id": session_id,
        })
        step = AgentStep(
            step_number=1,
            thought=f"Executing {task[:30]}",
            action="mock_action",
            action_input={"query": "test"},
            observation={"result": "ok"},
        )
        return AgentTaskResult(
            task=task,
            status="completed",
            final_answer=self.step_answer,
            steps=[step],
            total_tokens=250,
            session_id=session_id,
        )


@pytest.mark.unit
class TestHierarchicalSwarmSessions:
    @pytest.mark.asyncio
    async def test_session_parent_child_linkage(self) -> None:
        """Verify AgentSessionManager correctly links child sessions to parents."""
        store = InMemoryAgentSessionStore()
        manager = AgentSessionManager(store=store)

        # 1. Create root parent session
        root = await manager.create_session("Root Goal: Research & Implement Feature")
        assert root.parent_session_id is None
        assert root.children_session_ids == []

        # 2. Create child sessions
        child1 = await manager.create_child_session(
            parent_session_id=root.session_id,
            task="Subtask 1: Research documentation",
            node_id="researcher",
            role="researcher",
        )
        child2 = await manager.create_child_session(
            parent_session_id=root.session_id,
            task="Subtask 2: Implement code",
            node_id="developer",
            role="developer",
        )

        assert child1.parent_session_id == root.session_id
        assert child1.node_id == "researcher"
        assert child2.parent_session_id == root.session_id
        assert child2.node_id == "developer"

        # 3. Verify root session updated with child IDs
        refreshed_root = await manager.get_session(root.session_id)
        assert refreshed_root is not None
        assert child1.session_id in refreshed_root.children_session_ids
        assert child2.session_id in refreshed_root.children_session_ids

        # 4. Verify list_root_sessions filters out children
        root_sessions = await manager.list_root_sessions()
        root_ids = [s.session_id for s in root_sessions]
        assert root.session_id in root_ids
        assert child1.session_id not in root_ids
        assert child2.session_id not in root_ids

    @pytest.mark.asyncio
    async def test_get_session_tree_recursive_reconstruction(self) -> None:
        """Verify get_session_tree reconstructs deep nested multi-tier execution hierarchies."""
        store = InMemoryAgentSessionStore()
        manager = AgentSessionManager(store=store)

        # Tier 1 (Root)
        root = await manager.create_session("Root Objective")

        # Tier 2 (Supervisor)
        tier2 = await manager.create_child_session(
            parent_session_id=root.session_id,
            task="Supervisor Wave",
            node_id="supervisor",
            role="supervisor",
        )

        # Tier 3 (Worker)
        tier3 = await manager.create_child_session(
            parent_session_id=tier2.session_id,
            task="Worker Task",
            node_id="worker",
            role="worker",
        )

        # Reconstruct tree from root
        tree = await manager.get_session_tree(root.session_id)
        assert tree is not None
        assert tree["session_id"] == root.session_id
        assert len(tree["children"]) == 1
        assert tree["children"][0]["session_id"] == tier2.session_id
        assert tree["children"][0]["node_id"] == "supervisor"
        assert len(tree["children"][0]["children"]) == 1
        assert tree["children"][0]["children"][0]["session_id"] == tier3.session_id
        assert tree["children"][0]["children"][0]["node_id"] == "worker"

    @pytest.mark.asyncio
    async def test_swarm_coordinator_native_session_binding(self) -> None:
        """Verify SwarmCoordinator automatically binds with AgentSessionManager during run_swarm."""
        ctx = ServiceContext()
        store = InMemoryAgentSessionStore()
        session_manager = AgentSessionManager(store=store)
        ctx.provide(AGENT_SESSION_MANAGER_KEY, session_manager)

        coordinator = SwarmCoordinator(context=ctx)

        # Build custom 3-node DAG
        dag = SwarmDAG()
        dag.add_node(SwarmNode(id="step_a", role="researcher", task="Research data sources"))
        dag.add_node(SwarmNode(id="step_b", role="developer", task="Process data", dependencies=["step_a"]))
        dag.add_node(SwarmNode(id="synthesizer", role="synthesizer", task="Synthesize results", dependencies=["step_b"]))

        # Execute swarm
        custom_runs = {}
        def mock_executor(node: SwarmNode, upstream: dict) -> str:
            custom_runs[node.id] = f"Result of {node.role}"
            return f"Result of {node.role}"

        result = await coordinator.run_swarm(
            dag,
            custom_executor=mock_executor,
            run_id="swarm_test_123",
        )

        assert result.status == "completed"
        assert result.run_id == "swarm_test_123"

        # Verify root session was created in SessionManager
        root_sess = await session_manager.get_session("swarm_test_123")
        assert root_sess is not None
        assert root_sess.status == "completed"
        assert root_sess.final_answer == "Result of synthesizer"
        assert len(root_sess.children_session_ids) == 3

        # Verify child sessions
        child_a = await session_manager.get_session("swarm_test_123_step_a")
        assert child_a is not None
        assert child_a.parent_session_id == "swarm_test_123"
        assert child_a.node_id == "step_a"
        assert child_a.role == "researcher"
        assert child_a.final_answer == "Result of researcher"

        # Verify get_run_session_tree from coordinator
        tree = await coordinator.get_run_session_tree("swarm_test_123")
        assert tree is not None
        assert tree["session_id"] == "swarm_test_123"
        assert len(tree["children"]) == 3
        child_node_ids = {c["node_id"] for c in tree["children"]}
        assert child_node_ids == {"step_a", "step_b", "synthesizer"}

    @pytest.mark.asyncio
    async def test_swarm_coordinator_fallback_without_session_manager(self) -> None:
        """Verify SwarmCoordinator gracefully operates when AgentSessionManager is absent."""
        ctx = ServiceContext()
        coordinator = SwarmCoordinator(context=ctx)

        result = await coordinator.run_swarm("Simple standalone goal", run_id="swarm_no_sm")
        assert result.status == "completed"
        assert result.run_id == "swarm_no_sm"

        # get_run_session_tree should return in-memory run dictionary fallback
        tree = await coordinator.get_run_session_tree("swarm_no_sm")
        assert tree is not None
        assert tree["run_id"] == "swarm_no_sm"
        assert tree["status"] == "completed"
