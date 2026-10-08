"""Contract verification tests for tau_bridge package decomposition.

Conforms to:
- Rule 12: Slotted & frozen dataclasses with __post_init__ validation.
- Rule 21: In-flight tool-call stream normalization & promotion.
- Rule 43: Immutability verification using direct attribute assignment inside pytest.raises.
- Rule 49: Authoritative in-memory domain engine for micro-kernel IoC elevation.
- Rule 58: Single-seam resolver fallback invariant.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from harness.kernel.context import ServiceContext


@pytest.mark.unit
def test_submodule_direct_imports() -> None:
    """Verify that all decomposed submodules can be imported independently."""
    from harness.services.tau_bridge.engine import PiHarnessEngine
    from harness.services.tau_bridge.journal import SessionJournalManager
    from harness.services.tau_bridge.models import (
        BranchPath,
        HistoryRepairReport,
        HistoryRepairResult,
        JournalEntryRecord,
        ProjectTrustEvaluation,
        RpcProtocolEnvelope,
        SessionNode,
        SessionPathResult,
        ToolCallRecord,
        TrustScope,
    )
    from harness.services.tau_bridge.repair import ToolHistoryRepairEngine
    from harness.services.tau_bridge.service import (
        TAU_HARNESS_BRIDGE_SERVICE_KEY,
        DefaultTauHarnessBridgeService,
        TauBridgeService,
        resolve_tau_bridge,
    )
    from harness.services.tau_bridge.tree import SessionTreeResolver
    from harness.services.tau_bridge.trust import ProjectTrustEvaluator

    # Assert symbols exist
    assert SessionNode is not None
    assert BranchPath is not None
    assert ToolCallRecord is not None
    assert HistoryRepairResult is not None
    assert TrustScope is not None
    assert JournalEntryRecord is not None
    assert SessionPathResult is not None
    assert HistoryRepairReport is not None
    assert ProjectTrustEvaluation is not None
    assert RpcProtocolEnvelope is not None

    assert SessionJournalManager is not None
    assert SessionTreeResolver is not None
    assert ToolHistoryRepairEngine is not None
    assert ProjectTrustEvaluator is not None
    assert PiHarnessEngine is not None

    assert TauBridgeService is not None
    assert DefaultTauHarnessBridgeService is not None
    assert TAU_HARNESS_BRIDGE_SERVICE_KEY is not None
    assert resolve_tau_bridge is not None


@pytest.mark.unit
def test_facade_re_exports_and_backward_compatibility() -> None:
    """Verify that the package __init__.py re-exports all expected symbols."""
    import harness.services.tau_bridge as tb

    expected_symbols = [
        "BranchPath",
        "DefaultTauHarnessBridgeService",
        "HistoryRepairReport",
        "HistoryRepairResult",
        "JournalEntryRecord",
        "PiHarnessEngine",
        "ProjectTrustEvaluation",
        "ProjectTrustEvaluator",
        "RpcProtocolEnvelope",
        "SessionJournalManager",
        "SessionNode",
        "SessionPathResult",
        "SessionTreeResolver",
        "TAU_HARNESS_BRIDGE_SERVICE_KEY",
        "TauBridgeService",
        "ToolCallRecord",
        "ToolHistoryRepairEngine",
        "TrustScope",
        "resolve_tau_bridge",
    ]

    for sym in expected_symbols:
        assert hasattr(tb, sym), f"Missing expected symbol in tau_bridge facade: {sym}"


@pytest.mark.unit
def test_slotted_frozen_dataclasses_immutability_and_validation() -> None:
    """Rule 12 & Rule 43: Test slotted and frozen immutability across domain models."""
    from harness.services.tau_bridge.models import (
        BranchPath,
        HistoryRepairResult,
        JournalEntryRecord,
        SessionNode,
        ToolCallRecord,
        TrustScope,
    )

    # 1. SessionNode
    node = SessionNode(id="node_1", role="user", content="hello world")
    assert node.id == "node_1"
    with pytest.raises((AttributeError, TypeError)):
        node.content = "mutated"  # type: ignore

    # Validation: empty id or self-cycle must raise ValueError
    with pytest.raises(ValueError):
        SessionNode(id="")
    with pytest.raises(ValueError):
        SessionNode(id="node_1", parent_id="node_1")

    # 2. BranchPath
    path = BranchPath(
        target_id="node_1",
        path_entries=(node,),
        depth=1,
        total_entries=1,
        branch_count=0,
    )
    with pytest.raises((AttributeError, TypeError)):
        path.depth = 2  # type: ignore
    with pytest.raises(ValueError):
        BranchPath(
            target_id="node_1",
            path_entries=(node,),
            depth=-1,
            total_entries=1,
            branch_count=0,
        )

    # 3. ToolCallRecord
    tcr = ToolCallRecord(call_id="call_123", tool_name="bash", arguments='{"cmd":"ls"}')
    with pytest.raises((AttributeError, TypeError)):
        tcr.tool_name = "python"  # type: ignore
    with pytest.raises(ValueError):
        ToolCallRecord(call_id="", tool_name="bash")

    # 4. HistoryRepairResult
    hrr = HistoryRepairResult(
        repaired_messages=(),
        dropped_count=0,
        synthesized_count=0,
        repairs_applied=(),
        is_modified=False,
    )
    with pytest.raises((AttributeError, TypeError)):
        hrr.dropped_count = 1  # type: ignore
    with pytest.raises(ValueError):
        HistoryRepairResult(
            repaired_messages=(),
            dropped_count=-1,
            synthesized_count=0,
            repairs_applied=(),
            is_modified=False,
        )

    # 5. TrustScope
    ts = TrustScope(
        project_path="/app",
        is_trusted=True,
        git_root="/app",
        protected_assets=(),
        warnings=(),
        permission_level="TRUSTED",
    )
    with pytest.raises((AttributeError, TypeError)):
        ts.is_trusted = False  # type: ignore
    with pytest.raises(ValueError):
        TrustScope(
            project_path="/app",
            is_trusted=True,
            git_root="/app",
            protected_assets=(),
            warnings=(),
            permission_level="INVALID_LEVEL",
        )

    # 6. JournalEntryRecord
    jer = JournalEntryRecord(
        journal_path="/session.jsonl",
        entry_id="node_1",
        byte_offset=0,
        timestamp="2026-10-06T00:00:00Z",
    )
    with pytest.raises((AttributeError, TypeError)):
        jer.byte_offset = 100  # type: ignore
    with pytest.raises(ValueError):
        JournalEntryRecord(
            journal_path="/session.jsonl",
            entry_id="node_1",
            byte_offset=-1,
            timestamp="2026-10-06T00:00:00Z",
        )


@pytest.mark.unit
def test_session_journal_manager() -> None:
    """Verify locked JSONL append and load operations."""
    from harness.services.tau_bridge.journal import SessionJournalManager
    from harness.services.tau_bridge.models import SessionNode

    with tempfile.TemporaryDirectory() as tmpdir:
        journal_file = Path(tmpdir) / "test_session.jsonl"
        n1 = SessionNode(id="n1", role="user", content="msg 1")
        n2 = SessionNode(id="n2", parent_id="n1", role="assistant", content="msg 2")

        appended1 = SessionJournalManager.append_entry(journal_file, n1)
        assert appended1.id == "n1"
        assert appended1.timestamp != ""

        appended2 = SessionJournalManager.append_entry(journal_file, n2)
        assert appended2.id == "n2"

        loaded = SessionJournalManager.load_entries(journal_file)
        assert len(loaded) == 2
        assert loaded[0].id == "n1"
        assert loaded[1].id == "n2"
        assert loaded[1].parent_id == "n1"


@pytest.mark.unit
def test_session_tree_resolver() -> None:
    """Verify tree DAG ancestry path, leaf detection, and ASCII rendering."""
    from harness.services.tau_bridge.models import SessionNode
    from harness.services.tau_bridge.tree import SessionTreeResolver

    n1 = SessionNode(id="n1", role="user", content="Root message")
    n2a = SessionNode(id="n2a", parent_id="n1", role="assistant", content="Branch A")
    n2b = SessionNode(id="n2b", parent_id="n1", role="assistant", content="Branch B")
    n3a = SessionNode(id="n3a", parent_id="n2a", role="user", content="Leaf A")

    entries = [n1, n2a, n2b, n3a]

    # Resolve linear path to n3a
    path = SessionTreeResolver.resolve_path(entries, "n3a")
    assert path.target_id == "n3a"
    assert path.depth == 3
    assert [n.id for n in path.path_entries] == ["n1", "n2a", "n3a"]
    assert path.branch_count == 1  # n1 has 2 children: n2a, n2b

    # Discover leaves
    leaves = SessionTreeResolver.find_leaves(entries)
    leaf_ids = {n.id for n in leaves}
    assert leaf_ids == {"n2b", "n3a"}

    # Discover fork points
    forks = SessionTreeResolver.find_fork_points(entries)
    assert "n1" in forks
    assert set(forks["n1"]) == {"n2a", "n2b"}

    # ASCII Tree rendering
    ascii_tree = SessionTreeResolver.render_ascii_tree(entries, root_id="n1")
    assert "[n1] user: Root message" in ascii_tree
    assert "[n2a] assistant: Branch A" in ascii_tree
    assert "[n2b] assistant: Branch B" in ascii_tree


@pytest.mark.unit
def test_tool_history_repair_engine() -> None:
    """Rule 21: Verify in-flight argument JSON repair and orphan tool response dropping."""
    from harness.services.tau_bridge.repair import ToolHistoryRepairEngine

    # 1. Sanitize JSON with markdown fences and trailing commas
    dirty_json = "```json\n{\"cmd\": \"ls -la\", \"timeout\": 30,}\n```"
    cleaned = ToolHistoryRepairEngine.sanitize_arguments_json(dirty_json)
    assert '\"cmd\": \"ls -la\"' in cleaned
    assert '\"timeout\": 30' in cleaned
    assert not cleaned.endswith(",}")

    # 2. Repair message history (drop orphan, synthesize placeholder)
    messages = [
        {"role": "user", "content": "run task"},
        {"role": "tool", "tool_call_id": "orphan_call_999", "content": "stray result"},
        {
            "role": "assistant",
            "content": "calling tool",
            "tool_calls": [
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {"name": "run", "arguments": '{"arg": 1,}'},
                },
                {
                    "id": "call_2",
                    "type": "function",
                    "function": {"name": "status", "arguments": "{}"},
                },
            ],
        },
        {"role": "tool", "tool_call_id": "call_1", "content": "success"},
        # call_2 has no response -> should synthesize placeholder
    ]

    repair_result = ToolHistoryRepairEngine.repair(messages)
    assert repair_result.is_modified is True
    assert repair_result.dropped_count == 1  # orphan_call_999 dropped
    assert repair_result.synthesized_count == 1  # call_2 synthesized

    repaired_roles = [m["role"] for m in repair_result.repaired_messages]
    assert repaired_roles == ["user", "assistant", "tool", "tool"]
    # Check synthesized message for call_2
    assert repair_result.repaired_messages[3]["tool_call_id"] == "call_2"
    assert "interrupted or missing" in repair_result.repaired_messages[3]["content"]


@pytest.mark.unit
def test_project_trust_evaluator() -> None:
    """Verify workspace trust evaluation and path confinement."""
    from harness.services.tau_bridge.trust import ProjectTrustEvaluator

    with tempfile.TemporaryDirectory() as tmpdir:
        root_path = Path(tmpdir)
        sub_path = root_path / "subdir"
        sub_path.mkdir()

        # Path confinement
        assert ProjectTrustEvaluator.is_path_confined(sub_path, root_path) is True
        assert ProjectTrustEvaluator.is_path_confined(root_path.parent, root_path) is False

        # Trust evaluation with simulated .git
        (root_path / ".git").mkdir()
        (root_path / ".env").write_text("SECRET=123", encoding="utf-8")

        trust = ProjectTrustEvaluator.evaluate(str(root_path))
        assert trust.git_root == str(root_path)
        assert ".env" in trust.protected_assets
        assert trust.permission_level == "TRUSTED"


@pytest.mark.unit
def test_resolve_tau_bridge_single_seam() -> None:
    """Rule 58: Verify resolve_tau_bridge provides working fallback and IoC resolution."""
    from harness.services.tau_bridge.service import (
        TAU_HARNESS_BRIDGE_SERVICE_KEY,
        DefaultTauHarnessBridgeService,
        TauBridgeService,
        resolve_tau_bridge,
    )

    # 1. Standalone fallback when ctx is None
    svc_none = resolve_tau_bridge(None)
    assert isinstance(svc_none, TauBridgeService)
    assert isinstance(svc_none, DefaultTauHarnessBridgeService)

    # 2. Standalone fallback when ctx is empty
    empty_ctx = ServiceContext()
    svc_empty = resolve_tau_bridge(empty_ctx)
    assert isinstance(svc_empty, TauBridgeService)
    assert isinstance(svc_empty, DefaultTauHarnessBridgeService)

    # 3. Resolves custom service registered in context
    custom_ctx = ServiceContext()

    class CustomTauService(DefaultTauHarnessBridgeService):
        pass

    custom_instance = CustomTauService()
    custom_ctx.provide(TAU_HARNESS_BRIDGE_SERVICE_KEY, custom_instance)

    svc_custom = resolve_tau_bridge(custom_ctx)
    assert svc_custom is custom_instance
