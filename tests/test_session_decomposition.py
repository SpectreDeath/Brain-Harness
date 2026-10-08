"""Characterization and contract test suite for Session package decomposition (Phase 1).

Validates:
1. Isolated submodule importability across session models, store, exporter, scope, manager, and plugin.
2. Slotted & frozen dataclass contracts (Rule 12 & Rule 43) for session tree structures.
3. Standalone store lifecycle operations (save, get, list, delete) without manager coupling.
4. Dedicated SessionTreeExporter formatting (ASCII tree, Markdown, JSON).
5. 100% backward compatibility of all exports from `harness.agent.session`.
"""

from __future__ import annotations

import time
import pytest

from harness.agent.base import AgentStep


def test_session_submodule_isolated_imports() -> None:
    """Verify all session submodules can be imported independently."""
    from harness.agent.session import exporter, manager, models, plugin, scope, store

    assert hasattr(models, "AgentSession")
    assert hasattr(models, "SessionTreeNode")
    assert hasattr(models, "SessionTreeSnapshot")
    assert hasattr(store, "AgentSessionStore")
    assert hasattr(store, "InMemoryAgentSessionStore")
    assert hasattr(store, "StorageBackedSessionStore")
    assert hasattr(exporter, "SessionTreeExporter")
    assert hasattr(scope, "AgentSessionScope")
    assert hasattr(manager, "AgentSessionManager")
    assert hasattr(plugin, "AgentSessionPlugin")
    assert hasattr(manager, "AGENT_SESSION_MANAGER_KEY")


def test_session_package_backward_compatible_re_exports() -> None:
    """Verify harness.agent.session maintains 100% backward compatibility."""
    import harness.agent.session as session_mod

    expected_symbols = [
        "AgentSession",
        "SessionTreeNode",
        "SessionTreeSnapshot",
        "AgentSessionStore",
        "InMemoryAgentSessionStore",
        "StorageBackedSessionStore",
        "AgentSessionScope",
        "AgentSessionManager",
        "AgentSessionPlugin",
        "AGENT_SESSION_MANAGER_KEY",
        "SessionTreeExporter",
    ]
    for sym in expected_symbols:
        assert hasattr(session_mod, sym), f"Missing symbol '{sym}' in session package facade"


def test_slotted_frozen_session_tree_dataclasses() -> None:
    """Verify SessionTreeNode and SessionTreeSnapshot enforce Rule 12 and Rule 43 immutability."""
    from harness.agent.session.models import SessionTreeNode, SessionTreeSnapshot

    now = time.time()
    node = SessionTreeNode(
        session_id="sess_123",
        task="Test task",
        status="completed",
        created_at=now,
        updated_at=now,
        completed_at=now,
        final_answer="Done",
        total_tokens=150,
        steps_count=2,
    )

    # Rule 43: Frozen Dataclass Mutation Assertion Invariant
    with pytest.raises((AttributeError, TypeError)):
        node.final_answer = "Mutated"

    with pytest.raises((AttributeError, TypeError)):
        node.total_tokens = 999

    snapshot = SessionTreeSnapshot(
        root=node,
        total_sessions=1,
        total_tokens=150,
        total_steps=2,
        total_duration=1.5,
        max_depth=0,
        completed_count=1,
        failed_count=0,
    )

    with pytest.raises((AttributeError, TypeError)):
        snapshot.total_sessions = 5


@pytest.mark.asyncio
async def test_standalone_session_store_lifecycle() -> None:
    """Verify InMemoryAgentSessionStore functions independently of manager or event bus."""
    from harness.agent.session.models import AgentSession
    from harness.agent.session.store import InMemoryAgentSessionStore

    store = InMemoryAgentSessionStore()
    sess = AgentSession(
        session_id="s1",
        task="Calculate pi",
        status="running",
    )
    await store.save(sess)

    fetched = await store.get("s1")
    assert fetched is not None
    assert fetched.task == "Calculate pi"

    items = await store.list()
    assert len(items) == 1
    assert items[0].session_id == "s1"

    deleted = await store.delete("s1")
    assert deleted is True
    assert await store.get("s1") is None


def test_session_tree_exporter_formats() -> None:
    """Verify SessionTreeExporter renders ASCII trees, Markdown transcripts, and JSON schemas."""
    from harness.agent.session.exporter import SessionTreeExporter
    from harness.agent.session.models import AgentSession, SessionTreeNode, SessionTreeSnapshot

    now = time.time()
    root_node = SessionTreeNode(
        session_id="root_sess",
        task="Root task",
        status="completed",
        created_at=now,
        updated_at=now,
        completed_at=now,
        final_answer="Root complete",
        total_tokens=100,
        steps_count=1,
        children=(
            SessionTreeNode(
                session_id="child_sess",
                task="Child sub-task",
                status="completed",
                created_at=now,
                updated_at=now,
                completed_at=now,
                final_answer="Child complete",
                total_tokens=50,
                steps_count=1,
                parent_session_id="root_sess",
                depth=1,
            ),
        ),
    )

    snapshot = SessionTreeSnapshot(
        root=root_node,
        total_sessions=2,
        total_tokens=150,
        total_steps=2,
        total_duration=2.0,
        max_depth=1,
        completed_count=2,
        failed_count=0,
    )

    # 1. ASCII Tree Render
    ascii_tree = SessionTreeExporter.render_ascii_tree(snapshot)
    assert "root_sess" in ascii_tree
    assert "child_sess" in ascii_tree
    assert "Root task" in ascii_tree

    # 2. JSON Export
    json_out = SessionTreeExporter.to_json(snapshot)
    assert '"root_sess"' in json_out
    assert '"child_sess"' in json_out

    # 3. Markdown Transcript
    sess = AgentSession(
        session_id="s_md",
        task="Markdown test",
        steps=[
            AgentStep(step_number=1, thought="Thinking...", action="test_tool", action_input={"k": "v"}, observation="Tool output")
        ],
        final_answer="All good",
    )
    md_out = SessionTreeExporter.to_markdown(sess)
    assert "# Agent Execution Session: `s_md`" in md_out
    assert "Markdown test" in md_out
    assert "Thinking..." in md_out
    assert "test_tool" in md_out
