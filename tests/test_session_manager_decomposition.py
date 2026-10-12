"""Contract verification tests for AgentSessionManager decomposition."""

from __future__ import annotations

import pytest

from harness.agent.session import (
    AGENT_SESSION_MANAGER_KEY,
    AgentSessionManager,
    SessionCreationMixin,
    SessionExportMixin,
    SessionHierarchyMixin,
    SessionLifecycleMixin,
    SessionQueryMixin,
    resolve_session_manager,
)
from harness.agent.base import AgentStep
from harness.kernel.context import ServiceContext


@pytest.mark.asyncio
async def test_session_manager_imports_and_mixins():
    """Verify subpackage exports and class inheritance hierarchy."""
    manager = AgentSessionManager()
    assert isinstance(manager, SessionCreationMixin)
    assert isinstance(manager, SessionLifecycleMixin)
    assert isinstance(manager, SessionHierarchyMixin)
    assert isinstance(manager, SessionQueryMixin)
    assert isinstance(manager, SessionExportMixin)


@pytest.mark.asyncio
async def test_session_manager_resolver():
    """Verify single-seam resolver per Rule 58."""
    ctx = ServiceContext()
    # When not registered, resolver instantiates a default AgentSessionManager
    resolved = resolve_session_manager(ctx)
    assert isinstance(resolved, AgentSessionManager)

    # When registered, resolver returns the provided instance
    custom_mgr = AgentSessionManager()
    ctx.provide(AGENT_SESSION_MANAGER_KEY, custom_mgr)
    assert resolve_session_manager(ctx) is custom_mgr


@pytest.mark.asyncio
async def test_session_creation_lifecycle_and_step_recording():
    """Verify session creation, step recording, and completion."""
    manager = AgentSessionManager()

    session = await manager.create_session("Root exploration task", metadata={"priority": "high"})
    assert session.session_id.startswith("sess_")
    assert session.task == "Root exploration task"
    assert session.status == "running"

    step = AgentStep(
        step_number=1,
        action="inspect_repository",
        observation="Found 4 hotspots",
    )
    updated = await manager.record_step(session.session_id, step)
    assert len(updated.steps) == 1
    assert updated.steps[0].action == "inspect_repository"

    completed = await manager.complete_session(session.session_id, "Completed exploration", total_tokens=150)
    assert completed.status == "completed"
    assert completed.final_answer == "Completed exploration"
    assert completed.total_tokens == 150


@pytest.mark.asyncio
async def test_session_hierarchy_and_metrics():
    """Verify parent-child session creation and subtree metric aggregation."""
    manager = AgentSessionManager()

    parent = await manager.create_session("Parent swarm task")
    child_1 = await manager.create_child_session(parent.session_id, "Worker 1 task")
    child_2 = await manager.create_child_session(parent.session_id, "Worker 2 task")

    await manager.complete_session(child_1.session_id, "Worker 1 done", total_tokens=80)
    await manager.fail_session(child_2.session_id, "Worker 2 error")
    await manager.complete_session(parent.session_id, "Parent finished", total_tokens=120)

    metrics = await manager.get_subtree_metrics(parent.session_id)
    assert metrics["total_sessions"] == 3
    assert metrics["completed_count"] == 2
    assert metrics["failed_count"] == 1
    assert metrics["total_tokens"] == 200

    snapshot = await manager.get_tree_snapshot(parent.session_id)
    assert snapshot.root.session_id == parent.session_id
    assert snapshot.total_sessions == 3
    assert len(snapshot.root.children) == 2


@pytest.mark.asyncio
async def test_session_export_and_query():
    """Verify session querying and tree export."""
    manager = AgentSessionManager()

    parent = await manager.create_session("Export test session")
    child = await manager.create_child_session(parent.session_id, "Child export test")

    queried = await manager.get_session(parent.session_id)
    assert queried is not None
    assert queried.session_id == parent.session_id

    roots = await manager.list_root_sessions()
    root_ids = [r.session_id for r in roots]
    assert parent.session_id in root_ids
    assert child.session_id not in root_ids

    ascii_tree = await manager.export_session(parent.session_id, format="ascii")
    assert parent.session_id in ascii_tree

    json_export = await manager.export_session(parent.session_id, format="json")
    assert parent.session_id in json_export
