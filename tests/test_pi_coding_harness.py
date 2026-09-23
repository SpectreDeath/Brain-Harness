"""Contract and validation tests for pi-coding-harness skill and engine."""

import sys
from pathlib import Path

import pytest

# Add skill script directory to sys.path
_REPO_ROOT = Path(__file__).resolve().parent.parent
_SKILL_SCRIPTS = _REPO_ROOT / ".agents" / "skills" / "pi-coding-harness" / "scripts"
_SRC_DIR = _REPO_ROOT / "src"

for _p in [_SKILL_SCRIPTS, _SRC_DIR]:
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from pi_harness_engine import (
    BranchPath,
    JournalEntryRecord,
    ProjectTrustEvaluator,
    SessionJournalManager,
    SessionNode,
    SessionTreeResolver,
    ToolCallRecord,
    ToolHistoryRepairEngine,
    TrustScope,
)


def test_slotted_frozen_dataclass_immutability() -> None:
    """Verify Rule 12 & Rule 43: slotted and frozen dataclasses reject mutation via direct assignment."""
    node = SessionNode(id="node_1", role="user", content="hello")
    # Rule 43: Must use direct attribute assignment inside pytest.raises
    with pytest.raises((AttributeError, TypeError)):
        node.content = "modified"  # type: ignore

    with pytest.raises((AttributeError, TypeError)):
        node.id = "new_id"  # type: ignore

    path = BranchPath(
        target_id="node_1",
        path_entries=(node,),
        depth=1,
        total_entries=1,
        branch_count=0,
    )
    with pytest.raises((AttributeError, TypeError)):
        path.depth = 99  # type: ignore

    record = ToolCallRecord(call_id="call_1", tool_name="bash")
    with pytest.raises((AttributeError, TypeError)):
        record.tool_name = "edit"  # type: ignore

    scope = TrustScope(
        project_path="/test",
        is_trusted=True,
        git_root="/test",
        protected_assets=(),
        warnings=(),
        permission_level="TRUSTED",
    )
    with pytest.raises((AttributeError, TypeError)):
        scope.permission_level = "BLOCKED"  # type: ignore

    journal_rec = JournalEntryRecord(
        journal_path="/tmp/session.jsonl",
        entry_id="entry_1",
        byte_offset=0,
        timestamp="2026-09-22T00:00:00Z",
    )
    with pytest.raises((AttributeError, TypeError)):
        journal_rec.byte_offset = 100  # type: ignore


def test_session_node_construction_invariants() -> None:
    """Verify SessionNode __post_init__ assertions."""
    # Empty ID rejected
    with pytest.raises(ValueError, match="id cannot be empty"):
        SessionNode(id="")

    # Self-referencing cycle rejected
    with pytest.raises(ValueError, match="cannot reference itself"):
        SessionNode(id="node_x", parent_id="node_x")


def test_session_tree_ancestry_resolution() -> None:
    """Verify SessionTreeResolver DAG resolution and branch counting."""
    entries = [
        {"id": "root", "parent_id": None, "role": "user", "content": "initial"},
        {"id": "step_1", "parent_id": "root", "role": "assistant", "content": "ack"},
        {"id": "fork_a", "parent_id": "step_1", "role": "user", "content": "path a"},
        {"id": "fork_b", "parent_id": "step_1", "role": "user", "content": "path b"},
        {"id": "step_2b", "parent_id": "fork_b", "role": "assistant", "content": "result b"},
    ]

    branch = SessionTreeResolver.resolve_path(entries, "step_2b")
    assert branch.target_id == "step_2b"
    assert branch.depth == 4
    assert [n.id for n in branch.path_entries] == ["root", "step_1", "fork_b", "step_2b"]
    assert branch.branch_count == 1
    assert branch.total_entries == 5


def test_session_tree_cycle_detection() -> None:
    """Verify cycle detection in session tree traversal."""
    entries = [
        {"id": "a", "parent_id": "b"},
        {"id": "b", "parent_id": "a"},
    ]
    with pytest.raises(ValueError, match="Cycle detected"):
        SessionTreeResolver.resolve_path(entries, "a")


def test_session_tree_leaves_and_fork_points() -> None:
    """Verify discovery of branch leaves and multi-child fork points."""
    entries = [
        {"id": "root", "parent_id": None, "role": "user", "content": "root"},
        {"id": "b1", "parent_id": "root", "role": "assistant", "content": "branch 1"},
        {"id": "b2", "parent_id": "root", "role": "assistant", "content": "branch 2"},
        {"id": "b1_child", "parent_id": "b1", "role": "user", "content": "leaf 1"},
    ]

    leaves = SessionTreeResolver.find_leaves(entries)
    leaf_ids = {node.id for node in leaves}
    assert leaf_ids == {"b2", "b1_child"}

    forks = SessionTreeResolver.find_fork_points(entries)
    assert "root" in forks
    assert set(forks["root"]) == {"b1", "b2"}


def test_session_tree_ascii_rendering() -> None:
    """Verify deterministic ASCII DAG tree generation."""
    entries = [
        {"id": "root", "parent_id": None, "role": "user", "content": "Hello world"},
        {"id": "a1", "parent_id": "root", "role": "assistant", "content": "Hi there"},
        {"id": "u2", "parent_id": "a1", "role": "user", "content": "Write code"},
    ]

    tree_str = SessionTreeResolver.render_ascii_tree(entries)
    assert "[root] user: Hello world" in tree_str
    assert "[a1] assistant: Hi there" in tree_str
    assert "[u2] user: Write code" in tree_str
    assert "└── " in tree_str


def test_session_journal_manager_append_and_load(tmp_path: Path) -> None:
    """Verify append-only journal persistence with advisory file locking."""
    journal_file = tmp_path / "test_session.jsonl"

    node1 = SessionNode(id="n1", parent_id=None, role="user", content="msg 1")
    node2 = SessionNode(id="n2", parent_id="n1", role="assistant", content="msg 2")

    SessionJournalManager.append_entry(journal_file, node1)
    SessionJournalManager.append_entry(journal_file, node2)

    loaded = SessionJournalManager.load_entries(journal_file)
    assert len(loaded) == 2
    assert loaded[0].id == "n1"
    assert loaded[1].id == "n2"
    assert loaded[1].parent_id == "n1"
    assert loaded[0].timestamp != ""


def test_tool_history_repair_pipeline() -> None:
    """Verify in-flight repair of mixed orphan and unresponded tool calls."""
    messages = [
        {"role": "system", "content": "You are a coding assistant."},
        {"role": "user", "content": "run task"},
        {
            "role": "assistant",
            "content": "calling tools",
            "tool_calls": [
                {"id": "call_1", "type": "function"},
                {"id": "call_2", "type": "function"},
            ],
        },
        # call_1 answered
        {"role": "tool", "tool_call_id": "call_1", "content": "result 1"},
        # call_2 was never answered
        # orphan tool result from unknown call
        {"role": "tool", "tool_call_id": "orphan_99", "content": "surprise"},
        {"role": "user", "content": "next prompt"},
    ]

    res = ToolHistoryRepairEngine.repair(messages)
    assert res.is_modified is True
    assert res.dropped_count == 1  # orphan_99 dropped
    assert res.synthesized_count == 1  # call_2 synthesized

    tool_msgs = [m for m in res.repaired_messages if m.get("role") == "tool"]
    assert len(tool_msgs) == 2
    assert tool_msgs[0]["tool_call_id"] == "call_1"
    assert tool_msgs[1]["tool_call_id"] == "call_2"
    assert "interrupted or missing" in tool_msgs[1]["content"]


def test_tool_history_argument_repair_rule21() -> None:
    """Verify Rule 21 auto-repair of tool call arguments (markdown fences & trailing commas)."""
    messages = [
        {
            "role": "assistant",
            "tool_calls": [
                {
                    "id": "call_json_fenced",
                    "type": "function",
                    "function": {
                        "name": "exec",
                        "arguments": '```json\n{"command": "pytest", "timeout": 30,}\n```',
                    },
                }
            ],
        },
        {"role": "tool", "tool_call_id": "call_json_fenced", "content": "ok"},
    ]

    res = ToolHistoryRepairEngine.repair(messages)
    assert res.is_modified is True
    assert any("Repaired tool arguments JSON" in r for r in res.repairs_applied)
    clean_args = res.repaired_messages[0]["tool_calls"][0]["function"]["arguments"]
    assert clean_args == '{"command": "pytest", "timeout": 30}'


def test_project_trust_security_evaluation(tmp_path: Path) -> None:
    """Verify project trust perimeter evaluation, private key blocking, and sensitive dirs."""
    safe_dir = tmp_path / "safe_project"
    safe_dir.mkdir()
    (safe_dir / "src").mkdir()

    res_safe = ProjectTrustEvaluator.evaluate(str(safe_dir))
    assert res_safe.permission_level == "RESTRICTED"  # No .git root

    # Add sensitive SSH key
    (safe_dir / "id_rsa").write_text("DUMMY_PRIVATE_KEY", encoding="utf-8")
    res_blocked = ProjectTrustEvaluator.evaluate(str(safe_dir))
    assert res_blocked.permission_level == "BLOCKED"
    assert res_blocked.is_trusted is False
    assert "id_rsa" in res_blocked.protected_assets

    # Add sensitive .secrets directory
    secrets_dir = safe_dir / ".secrets"
    secrets_dir.mkdir()
    res_secrets = ProjectTrustEvaluator.evaluate(str(safe_dir))
    assert ".secrets/" in res_secrets.protected_assets


def test_project_trust_path_confinement(tmp_path: Path) -> None:
    """Verify path confinement checks prevent directory traversal escape."""
    root = tmp_path / "workspace"
    root.mkdir()
    child = root / "subdir" / "file.txt"
    escaped = tmp_path / "outside.txt"

    assert ProjectTrustEvaluator.is_path_confined(child, root) is True
    assert ProjectTrustEvaluator.is_path_confined(root, root) is True
    assert ProjectTrustEvaluator.is_path_confined(escaped, root) is False


def test_skill_validator_hygiene() -> None:
    """Validate pi-coding-harness skill directory against SkillValidator."""
    from harness.creator.skills import SkillValidator

    skill_dir = _REPO_ROOT / ".agents" / "skills" / "pi-coding-harness"
    report = SkillValidator.validate(skill_dir)
    assert report.valid is True
    assert len(report.errors) == 0
