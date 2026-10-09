"""Contract test suite for ConversationTrajectoryMiner architecture deepening and decomposition."""

from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from harness.kernel.context import ServiceContext
from harness.services.conversation_trajectory_miner import (
    CONVERSATION_TRAJECTORY_MINER_KEY,
    ByteOffsetSeekTable,
    CognitiveBifurcationReport,
    ConversationManifest,
    ConversationTrajectoryMinerService,
    FailureCluster,
    FrictionScorecard,
    IsnadClaimRecord,
    STATUS_MAP,
    STEP_TYPE_MAP,
    StandardConversationTrajectoryMinerService,
    TrajectoryStepRecord,
    resolve_conversation_trajectory_miner,
)


@pytest.fixture
def mock_conversation_db(tmp_path: Path) -> Path:
    """Create a temporary SQLite database mimicking Antigravity IDE conversation store."""
    db_file = tmp_path / "mock_session.db"
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE steps (
            idx INTEGER PRIMARY KEY,
            step_type INTEGER,
            status INTEGER,
            task_details TEXT,
            error_details TEXT,
            step_payload BLOB
        )
        """
    )
    # Insert steps: prompt, normal tool, failing tool, recovery tool
    cur.execute(
        "INSERT INTO steps VALUES (?, ?, ?, ?, ?, ?)",
        (0, 5, 3, "User request: fix bug in module", "", b"Please fix the bug in module A"),
    )
    cur.execute(
        "INSERT INTO steps VALUES (?, ?, ?, ?, ?, ?)",
        (1, 8, 3, "view_file path/to/file.py", "", b"viewing file"),
    )
    cur.execute(
        "INSERT INTO steps VALUES (?, ?, ?, ?, ?, ?)",
        (2, 8, 7, "replace_file_content target=foo", "FileNotFoundError: No such file or directory", b""),
    )
    cur.execute(
        "INSERT INTO steps VALUES (?, ?, ?, ?, ?, ?)",
        (3, 8, 3, "write_to_file path=foo.py", "", b"created file"),
    )
    conn.commit()
    conn.close()
    return db_file


@pytest.mark.unit
def test_facade_reexports_and_backward_compatibility() -> None:
    """Verify all public symbols are accessible from package root facade."""
    assert issubclass(StandardConversationTrajectoryMinerService, ConversationTrajectoryMinerService)
    assert callable(resolve_conversation_trajectory_miner)
    assert callable(ByteOffsetSeekTable)
    assert len(STATUS_MAP) >= 8
    assert len(STEP_TYPE_MAP) >= 12
    assert CONVERSATION_TRAJECTORY_MINER_KEY.name == "conversation_trajectory_miner_service"


@pytest.mark.unit
def test_submodule_line_counts_strictly_bounded() -> None:
    """Verify all submodules in conversation_trajectory_miner remain strictly under 200 lines per Rule 11."""
    pkg_dir = Path("src/harness/services/conversation_trajectory_miner")
    py_files = list(pkg_dir.glob("*.py"))
    assert len(py_files) >= 8, f"Expected at least 8 submodules, found {len(py_files)}"

    for py_file in py_files:
        lines = len(py_file.read_text(encoding="utf-8").splitlines())
        assert lines < 200, f"Module {py_file.name} has {lines} lines, exceeding 200 limit"


@pytest.mark.unit
def test_slotted_frozen_dataclass_invariants() -> None:
    """Verify Rule 12 & Rule 43: immutability and post_init bounds."""
    step = TrajectoryStepRecord(idx=0, step_type="USER_INPUT", status="DONE")
    assert step.idx == 0

    with pytest.raises((AttributeError, TypeError)):
        step.idx = 1  # type: ignore[misc]

    with pytest.raises(ValueError):
        TrajectoryStepRecord(idx=-1, step_type="USER_INPUT", status="DONE")

    cluster = FailureCluster(
        error_type="SyntaxError",
        count=3,
        sample_cids=("cid1",),
        tool_names=("write_file",),
        sample_messages=("parse error",),
    )
    assert cluster.count == 3
    with pytest.raises(ValueError):
        FailureCluster(
            error_type="SyntaxError",
            count=-1,
            sample_cids=(),
            tool_names=(),
            sample_messages=(),
        )


@pytest.mark.unit
def test_binary_seek_table_operations(tmp_path: Path) -> None:
    """Verify Rule 48: O(1) binary byte-offset seek table."""
    log_file = tmp_path / "test.jsonl"
    lines = [f'{{"step": {i}, "msg": "line {i}"}}\n' for i in range(10)]
    log_file.write_bytes("".join(lines).encode("utf-8"))

    seek_table = ByteOffsetSeekTable(log_file)
    assert seek_table.total_lines() == 10
    assert seek_table.get_line(0).strip() == lines[0].strip()
    assert seek_table.get_line(5).strip() == lines[5].strip()
    assert seek_table.get_line(9).strip() == lines[9].strip()
    assert seek_table.get_line(99) is None


@pytest.mark.unit
def test_proactor_safe_read_only_connection(mock_conversation_db: Path) -> None:
    """Verify Rule 22: read-only SQLite URI mode connection."""
    svc = StandardConversationTrajectoryMinerService()
    conn = svc.connect_ro(mock_conversation_db)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM steps")
    count = cur.fetchone()[0]
    assert count == 4
    conn.close()


@pytest.mark.unit
def test_inspect_conversation_and_scan_corpus(mock_conversation_db: Path) -> None:
    """Verify database inspection extracts manifest, error count, and snippets."""
    svc = StandardConversationTrajectoryMinerService()
    manifest = svc.inspect_conversation(mock_conversation_db)
    assert manifest is not None
    assert manifest.cid == mock_conversation_db.stem
    assert manifest.step_count == 4
    assert manifest.errors_detected == 1
    assert "bug in module" in manifest.first_prompt_snippet

    manifests = svc.scan_corpus(mock_conversation_db.parent)
    assert len(manifests) >= 1
    assert any(m.cid == mock_conversation_db.stem for m in manifests)


@pytest.mark.unit
def test_friction_scorecard_and_failure_clusters(mock_conversation_db: Path) -> None:
    """Verify friction scorecard calculation and failure clustering."""
    svc = StandardConversationTrajectoryMinerService()
    manifests = svc.scan_corpus(mock_conversation_db.parent)
    scorecard = svc.compile_friction_scorecard(manifests)

    assert scorecard.total_conversations >= 1
    assert scorecard.total_steps >= 4
    assert scorecard.total_errors >= 1
    assert scorecard.error_rate > 0.0
    assert len(scorecard.failure_clusters) >= 1

    clusters = svc.mine_failure_clusters(mock_conversation_db.parent)
    assert len(clusters) >= 1
    assert any("FileNotFoundError" in c.error_type for c in clusters)


@pytest.mark.unit
def test_bifurcate_distillation_and_knowledge_export(
    mock_conversation_db: Path, tmp_path: Path
) -> None:
    """Verify Rule 40 & Rule 41: dual-lens distillation into Knowledge Vault and skill rules."""
    svc = StandardConversationTrajectoryMinerService()
    vault_dir = tmp_path / "vault"
    skills_dir = tmp_path / "skills"

    report = svc.bifurcate_distillation(
        cid=mock_conversation_db.stem,
        db_path=mock_conversation_db,
        output_vault_dir=vault_dir,
        output_skills_dir=skills_dir,
    )

    assert report.cid == mock_conversation_db.stem
    assert Path(report.knowledge_vault_path).exists()
    assert (Path(report.knowledge_vault_path) / "metadata.json").exists()
    assert (Path(report.knowledge_vault_path) / "summary.md").exists()
    assert Path(report.skill_scaffold_path).exists()
    assert (Path(report.skill_scaffold_path) / "CARD.md").exists()
    assert (Path(report.skill_scaffold_path) / "SKILL.md").exists()
    assert len(report.extracted_invariants) >= 1
    assert len(report.procedural_rules) >= 1


@pytest.mark.unit
def test_single_seam_resolver() -> None:
    """Verify Rule 58: resolve_conversation_trajectory_miner resolver seam."""
    fallback_svc = resolve_conversation_trajectory_miner(None)
    assert isinstance(fallback_svc, StandardConversationTrajectoryMinerService)

    ctx = MagicMock(spec=ServiceContext)
    custom_svc = StandardConversationTrajectoryMinerService()
    ctx.optional.return_value = custom_svc

    resolved = resolve_conversation_trajectory_miner(ctx)
    assert resolved is custom_svc
    ctx.optional.assert_called_once_with(CONVERSATION_TRAJECTORY_MINER_KEY)
