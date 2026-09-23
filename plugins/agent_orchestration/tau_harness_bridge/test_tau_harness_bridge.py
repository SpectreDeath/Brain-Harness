"""Tests for TauHarnessBridgePlugin and Service."""

from pathlib import Path

import pytest

from harness.kernel.context import ServiceContext
from harness.services.tau_bridge import (
    TAU_HARNESS_BRIDGE_SERVICE_KEY,
    HistoryRepairReport,
    ProjectTrustEvaluation,
    RpcProtocolEnvelope,
    SessionPathResult,
)
from plugins.agent_orchestration.tau_harness_bridge.main import (
    TauHarnessBridgePlugin,
    plugin,
)
from plugins.agent_orchestration.tau_harness_bridge.service import (
    DefaultTauHarnessBridgeService,
)


@pytest.fixture
def service() -> DefaultTauHarnessBridgeService:
    return DefaultTauHarnessBridgeService()


def test_session_tree_resolution(service: DefaultTauHarnessBridgeService) -> None:
    """Test resolving linear ancestry in a branchable session tree DAG."""
    entries = [
        {"id": "entry_1", "parent_id": None, "role": "user", "content": "hello"},
        {"id": "entry_2", "parent_id": "entry_1", "role": "assistant", "content": "hi"},
        {"id": "entry_3a", "parent_id": "entry_2", "role": "user", "content": "branch A"},
        {"id": "entry_3b", "parent_id": "entry_2", "role": "user", "content": "branch B"},
        {"id": "entry_4b", "parent_id": "entry_3b", "role": "assistant", "content": "response B"},
    ]

    # Resolve branch B
    res_b: SessionPathResult = service.resolve_session_path(entries, "entry_4b")
    assert res_b.target_id == "entry_4b"
    assert res_b.depth == 4
    assert [e["id"] for e in res_b.path_entries] == ["entry_1", "entry_2", "entry_3b", "entry_4b"]
    assert res_b.branch_count == 1  # entry_2 has 2 children
    assert res_b.total_tree_entries == 5

    # Resolve branch A
    res_a: SessionPathResult = service.resolve_session_path(entries, "entry_3a")
    assert res_a.target_id == "entry_3a"
    assert res_a.depth == 3
    assert [e["id"] for e in res_a.path_entries] == ["entry_1", "entry_2", "entry_3a"]

    # Target not found
    with pytest.raises(KeyError):
        service.resolve_session_path(entries, "entry_unknown")


def test_tool_history_repair_orphan_dropped(service: DefaultTauHarnessBridgeService) -> None:
    """Test dropping orphan tool messages without preceding tool calls."""
    messages = [
        {"role": "user", "content": "search files"},
        {"role": "tool", "tool_call_id": "orphan_call_999", "content": "results"},
    ]

    report: HistoryRepairReport = service.repair_tool_history(messages)
    assert report.is_modified is True
    assert report.dropped_count == 1
    assert len(report.repaired_messages) == 1
    assert report.repaired_messages[0]["role"] == "user"


def test_tool_history_repair_unresponded_synthesized(service: DefaultTauHarnessBridgeService) -> None:
    """Test synthesizing placeholder results for unresponded assistant tool calls."""
    messages = [
        {"role": "user", "content": "run command"},
        {
            "role": "assistant",
            "content": "running...",
            "tool_calls": [{"id": "call_abc", "type": "function", "function": {"name": "bash"}}],
        },
        # Missing tool response message
        {"role": "user", "content": "what happened?"},
    ]

    report: HistoryRepairReport = service.repair_tool_history(messages)
    assert report.is_modified is True
    assert report.synthesized_count == 1
    # Check that placeholder tool response was inserted
    tool_msgs = [m for m in report.repaired_messages if m.get("role") == "tool"]
    assert len(tool_msgs) == 1
    assert tool_msgs[0]["tool_call_id"] == "call_abc"
    assert "Notice: Tool execution was interrupted" in tool_msgs[0]["content"]


def test_tool_history_clean_passthrough(service: DefaultTauHarnessBridgeService) -> None:
    """Test that clean, paired tool histories pass through unchanged."""
    messages = [
        {"role": "user", "content": "read file"},
        {
            "role": "assistant",
            "tool_calls": [{"id": "call_1", "type": "function"}],
        },
        {"role": "tool", "tool_call_id": "call_1", "content": "file contents"},
        {"role": "assistant", "content": "done"},
    ]

    report: HistoryRepairReport = service.repair_tool_history(messages)
    assert report.is_modified is False
    assert report.dropped_count == 0
    assert report.synthesized_count == 0
    assert len(report.repaired_messages) == 4


def test_project_trust_evaluation(service: DefaultTauHarnessBridgeService, tmp_path: Path) -> None:
    """Test project trust evaluation and sensitive file detection."""
    proj = tmp_path / "sample_project"
    proj.mkdir()
    # Add a sensitive file
    (proj / ".env").write_text("SECRET_KEY=12345", encoding="utf-8")

    eval_result: ProjectTrustEvaluation = service.evaluate_project_trust(str(proj))
    assert eval_result.project_path == str(proj.resolve())
    assert ".env" in eval_result.protected_assets
    assert len(eval_result.warnings) > 0


def test_rpc_protocol_formatting(service: DefaultTauHarnessBridgeService) -> None:
    """Test formatting Pi-compatible JSONL RPC response envelopes."""
    success_env: RpcProtocolEnvelope = service.format_rpc_envelope(
        request_id="req-123", result={"status": "ok"}
    )
    assert success_env.id == "req-123"
    assert success_env.result == {"status": "ok"}
    assert success_env.error is None
    assert success_env.jsonrpc == "2.0"

    err_env: RpcProtocolEnvelope = service.format_rpc_envelope(
        request_id=456, error={"code": -32600, "message": "Invalid Request"}
    )
    assert err_env.id == 456
    assert err_env.error["code"] == -32600
    assert err_env.result is None


def test_journal_and_tree_services(service: DefaultTauHarnessBridgeService, tmp_path: Path) -> None:
    """Test append_journal_entry, load_journal_entries, and render_session_tree."""
    journal = tmp_path / "test_journal.jsonl"
    e1 = service.append_journal_entry(
        journal, {"id": "msg_1", "parent_id": None, "role": "user", "content": "hello"}
    )
    e2 = service.append_journal_entry(
        journal, {"id": "msg_2", "parent_id": "msg_1", "role": "assistant", "content": "world"}
    )
    assert e1["id"] == "msg_1"
    assert e2["id"] == "msg_2"

    loaded = service.load_journal_entries(journal)
    assert len(loaded) == 2
    assert loaded[0]["id"] == "msg_1"
    assert loaded[1]["id"] == "msg_2"

    tree = service.render_session_tree(loaded)
    assert "[msg_1]" in tree
    assert "[msg_2]" in tree

    leaves = service.find_branch_leaves(loaded)
    assert len(leaves) == 1
    assert leaves[0]["id"] == "msg_2"

    assert service.is_path_confined(journal, tmp_path) is True


@pytest.mark.asyncio
async def test_tau_harness_bridge_plugin_ioc_lifecycle() -> None:
    """Test plugin registration and resolution in ServiceContext (Rule 45)."""
    context = ServiceContext()
    p = TauHarnessBridgePlugin()
    await p.on_load(context)

    # Resolve via ServiceKey
    resolved = context.require(TAU_HARNESS_BRIDGE_SERVICE_KEY)
    assert resolved is p
    assert p.name == "plugin.tau_harness_bridge"

    # Verify singleton
    assert plugin is not None
    assert plugin.name == "plugin.tau_harness_bridge"
