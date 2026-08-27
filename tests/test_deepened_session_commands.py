"""Tests for session commands, tree hierarchy queries, and CommandRegistry dispatch."""

import pytest
from pathlib import Path

from harness.commands import CommandRegistry
from harness.commands.session import (
    delete_session_cmd,
    export_session_cmd,
    get_session_cmd,
    get_session_tree_cmd,
    list_sessions_cmd,
)
from harness.agent.session import (
    AGENT_SESSION_MANAGER_KEY,
    AgentSessionManager,
    AgentStep,
    InMemoryAgentSessionStore,
)
from harness.kernel.context import ServiceContext


@pytest.mark.asyncio
async def test_session_commands_crud_and_tree(tmp_path: Path):
    ctx = ServiceContext()
    store = InMemoryAgentSessionStore()
    manager = AgentSessionManager(store=store)
    ctx.provide(AGENT_SESSION_MANAGER_KEY, manager)

    # 1. Create root session and child sessions
    root = await manager.create_session("Root Orchestration Task", session_id="sess_root_01")
    child1 = await manager.create_child_session(
        "sess_root_01", "Subtask 1: Fetch Data", session_id="sess_child_01", role="worker"
    )
    child2 = await manager.create_child_session(
        "sess_root_01", "Subtask 2: Process Data", session_id="sess_child_02", role="critic"
    )

    await manager.record_step("sess_root_01", AgentStep(1, "Starting task", "plan", {"target": "all"}))
    await manager.record_step("sess_child_01", AgentStep(1, "Fetching", "web_fetch", {"url": "http://example.com"}))
    await manager.complete_session("sess_child_01", "Fetched 10 records", total_tokens=150)
    await manager.complete_session("sess_child_02", "Processed successfully", total_tokens=220)
    await manager.complete_session("sess_root_01", "Pipeline complete", total_tokens=500)

    # 2. Test list_sessions_cmd
    list_res = await list_sessions_cmd(context=ctx)
    assert list_res.total_count == 3

    root_list = await list_sessions_cmd(root_only=True, context=ctx)
    assert root_list.total_count == 1
    assert root_list.sessions[0]["session_id"] == "sess_root_01"

    # 3. Test get_session_cmd
    detail = await get_session_cmd("sess_root_01", context=ctx)
    assert detail.found is True
    assert detail.session is not None
    assert detail.session["status"] == "completed"

    missing = await get_session_cmd("non_existent", context=ctx)
    assert missing.found is False

    # 4. Test get_session_tree_cmd
    tree_res = await get_session_tree_cmd("sess_root_01", context=ctx)
    assert tree_res.found is True
    assert tree_res.tree is not None
    assert len(tree_res.tree["children"]) == 2
    assert tree_res.metrics["total_sessions"] == 3
    assert tree_res.metrics["completed_count"] == 3
    assert tree_res.metrics["total_tokens"] == 870  # 500 + 150 + 220

    # 5. Test export_session_cmd (Markdown and JSON)
    export_md = await export_session_cmd("sess_root_01", format="markdown", context=ctx)
    assert "# Agent Execution Session: `sess_root_01`" in export_md.content
    assert "Pipeline complete" in export_md.content

    out_file = tmp_path / "session_export.json"
    export_json = await export_session_cmd("sess_root_01", format="json", output_file=out_file, context=ctx)
    assert export_json.written_file is not None
    assert out_file.exists()

    # 6. Test delete_session_cmd
    del_res = await delete_session_cmd("sess_child_02", context=ctx)
    assert del_res.deleted is True
    check_del = await get_session_cmd("sess_child_02", context=ctx)
    assert check_del.found is False


@pytest.mark.asyncio
async def test_session_command_registry_dispatch():
    # Verify dispatch via CommandRegistry
    desc_list = CommandRegistry.get("session.list")
    assert desc_list is not None
    assert desc_list.category == "session"

    desc_tree = CommandRegistry.get("session.tree")
    assert desc_tree is not None

    desc_export = CommandRegistry.get("session.export")
    assert desc_export is not None

    # Execute via CommandRegistry.dispatch
    res = await CommandRegistry.dispatch("session.list")
    assert res.total_count >= 0
