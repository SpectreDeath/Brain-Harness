"""Comprehensive contract tests for conversation_trajectory_miner architectural deepening.

Verifies:
1. Micro-kernel IoC service protocol and ServiceKey registration (Rule 1, Rule 2, Rule 49)
2. Domain-partitioned plugin lifecycle in plugins/memory_and_epistemics/ (Rule 45)
3. Slotted and frozen immutability assertions (Rule 12, Rule 43)
4. Proactor-safe read-only SQLite connections with WAL support (Rule 22)
5. Failure cluster archaeology and retry cascade detection
6. Canonical Knowledge Vault dual-file generation with isnad claims (Rule 40, Rule 41)
7. Headless Click CLI introspection suite (Rule 6, Rule 10)
8. Backward-compatible script adapter execution
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
import pytest
from click.testing import CliRunner

from harness.kernel.context import ServiceContext
from harness.creator.skills import SkillValidator
from harness.services.conversation_trajectory_miner import (
    CONVERSATION_TRAJECTORY_MINER_KEY,
    ByteOffsetSeekTable,
    CognitiveBifurcationReport,
    ConversationManifest,
    ConversationTrajectoryMinerService,
    FailureCluster,
    FrictionScorecard,
    IsnadClaimRecord,
    StandardConversationTrajectoryMinerService,
    TrajectoryStepRecord,
)
from plugins.memory_and_epistemics.conversation_trajectory_miner.main import (
    ConversationTrajectoryMinerPlugin,
    plugin as trajectory_miner_plugin_singleton,
)
from harness.commands.trajectory_miner import trajectory_group
from harness.cli import main as harness_cli_main


@pytest.mark.unit
class TestConversationTrajectoryMinerDeepening:
    """Contract tests for deepened conversation trajectory miner architecture."""

    def test_service_protocol_conformance_and_singleton(self) -> None:
        """Verify StandardConversationTrajectoryMinerService satisfies protocol and singleton exists (Rule 49)."""
        service = StandardConversationTrajectoryMinerService()
        assert isinstance(service, ConversationTrajectoryMinerService)
        assert trajectory_miner_plugin_singleton is not None
        assert isinstance(trajectory_miner_plugin_singleton, ConversationTrajectoryMinerPlugin)

    @pytest.mark.asyncio
    async def test_ioc_registration_and_resolution(self) -> None:
        """Verify ConversationTrajectoryMinerPlugin registers CONVERSATION_TRAJECTORY_MINER_KEY into IoC (Rule 1, 2)."""
        ctx = ServiceContext()
        plugin = ConversationTrajectoryMinerPlugin()
        assert CONVERSATION_TRAJECTORY_MINER_KEY in plugin.provides

        await plugin.on_load(ctx)
        resolved_service = ctx.require(CONVERSATION_TRAJECTORY_MINER_KEY)
        assert resolved_service is not None
        assert isinstance(resolved_service, ConversationTrajectoryMinerService)

    def test_slotted_frozen_dataclass_immutability(self) -> None:
        """Verify slotted and frozen immutability across all domain models (Rule 12, Rule 43)."""
        step = TrajectoryStepRecord(
            idx=0,
            step_type="USER_INPUT",
            status="DONE",
            has_subtrajectory=False,
            task_details="task",
            error_details="",
            byte_offset=0,
            byte_length=100,
        )
        cluster = FailureCluster(
            error_type="SyntaxError / Script Parse",
            count=3,
            sample_cids=("cid_01",),
            tool_names=("write_file",),
            sample_messages=("invalid syntax",),
        )
        manifest = ConversationManifest(
            cid="cid_test",
            db_path="/tmp/test.db",
            file_size_bytes=1024,
            step_count=5,
            has_wal=True,
            step_types={"USER_INPUT": 1, "TOOL_EXECUTION": 4},
            errors_detected=1,
            first_prompt_snippet="hello",
            retry_count=1,
        )
        card = FrictionScorecard(
            total_conversations=1,
            total_steps=5,
            total_bytes_mb=0.01,
            total_errors=1,
            error_rate=0.2,
            step_type_distribution={"USER_INPUT": 1},
            high_friction_sessions=(),
            failure_clusters=(cluster,),
        )
        claim = IsnadClaimRecord(
            claim_id="claim-1",
            assertion="Invariant asserted",
            isnad_source="conversations/cid_test.db",
            test_anchor="test_regression_1",
            confidence=0.95,
        )
        report = CognitiveBifurcationReport(
            cid="cid_test",
            knowledge_vault_path="/vault/ki_01",
            skill_scaffold_path="/skills/learned_01",
            extracted_invariants=("Invariant 1",),
            procedural_rules=("Rule 1",),
        )

        with pytest.raises((AttributeError, TypeError)):
            step.idx = 1  # type: ignore

        with pytest.raises((AttributeError, TypeError)):
            cluster.count = 5  # type: ignore

        with pytest.raises((AttributeError, TypeError)):
            manifest.step_count = 10  # type: ignore

        with pytest.raises((AttributeError, TypeError)):
            card.total_errors = 3  # type: ignore

        with pytest.raises((AttributeError, TypeError)):
            claim.confidence = 0.5  # type: ignore

        with pytest.raises((AttributeError, TypeError)):
            report.cid = "cid_mutated"  # type: ignore

    def test_proactor_safe_ro_connection(self, tmp_path: Path) -> None:
        """Verify proactor-safe read-only connection on SQLite database with WAL (Rule 22)."""
        db_path = tmp_path / "test_session.db"
        with sqlite3.connect(db_path) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute(
                "CREATE TABLE steps (idx INTEGER PRIMARY KEY, step_type INTEGER, status INTEGER, task_details TEXT, error_details TEXT, step_payload BLOB)"
            )
            conn.execute(
                "INSERT INTO steps VALUES (0, 5, 3, 'initial user prompt', '', ?)",
                (b"Hello from test user inquiry about code architecture!",),
            )
            conn.commit()

        service = StandardConversationTrajectoryMinerService()
        manifest = service.inspect_conversation(db_path)
        assert manifest is not None
        assert manifest.cid == "test_session"
        assert manifest.step_count == 1
        assert manifest.errors_detected == 0
        assert "USER_INPUT" in manifest.step_types
        assert "Hello from test user inquiry" in manifest.first_prompt_snippet

    def test_failure_cluster_and_retry_detection(self, tmp_path: Path) -> None:
        """Verify detection of consecutive retry cascades and error clustering (Rule 22)."""
        db_path = tmp_path / "error_session.db"
        with sqlite3.connect(db_path) as conn:
            conn.execute(
                "CREATE TABLE steps (idx INTEGER PRIMARY KEY, step_type INTEGER, status INTEGER, task_details TEXT, error_details TEXT, step_payload BLOB)"
            )
            # Step 0: User prompt
            conn.execute("INSERT INTO steps VALUES (0, 5, 3, 'prompt', '', ?)", (b"start",))
            # Step 1: Tool execution fails with FileNotFoundError
            conn.execute(
                "INSERT INTO steps VALUES (1, 8, 7, 'run_command', 'FileNotFoundError: [Errno 2] No such file or directory: missing.py', ?)",
                (b"",),
            )
            # Step 2: Immediate retry tool execution fails again (retry cascade)
            conn.execute(
                "INSERT INTO steps VALUES (2, 8, 7, 'run_command', 'FileNotFoundError: still missing', ?)",
                (b"",),
            )
            # Step 3: Tool execution succeeds
            conn.execute("INSERT INTO steps VALUES (3, 8, 3, 'run_command', '', ?)", (b"ok",))
            conn.commit()

        service = StandardConversationTrajectoryMinerService()
        manifest = service.inspect_conversation(db_path)
        assert manifest is not None
        assert manifest.step_count == 4
        assert manifest.errors_detected == 2
        assert manifest.retry_count == 1  # 1 consecutive failure after previous failure

        # Compile friction scorecard across corpus
        manifests = service.scan_corpus(tmp_path)
        scorecard = service.compile_friction_scorecard(manifests)
        assert scorecard.total_errors == 2
        assert len(scorecard.failure_clusters) >= 1

        top_cluster = scorecard.failure_clusters[0]
        assert "FileNotFoundError" in top_cluster.error_type
        assert top_cluster.count == 2
        assert "error_session" in top_cluster.sample_cids

    def test_canonical_knowledge_vault_export(self, tmp_path: Path) -> None:
        """Verify Knowledge Vault export produces dual-file format with isnad claims (Rule 40, 41)."""
        db_path = tmp_path / "bifurcate_session.db"
        vault_dir = tmp_path / "knowledge_vault"
        skills_dir = tmp_path / "skills"

        with sqlite3.connect(db_path) as conn:
            conn.execute(
                "CREATE TABLE steps (idx INTEGER PRIMARY KEY, step_type INTEGER, status INTEGER, task_details TEXT, error_details TEXT, step_payload BLOB)"
            )
            conn.execute("INSERT INTO steps VALUES (0, 5, 3, 'prompt', '', ?)", (b"start",))
            conn.execute(
                "INSERT INTO steps VALUES (1, 8, 7, 'write_to_file', 'SyntaxError: invalid syntax', ?)",
                (b"",),
            )
            conn.execute("INSERT INTO steps VALUES (2, 8, 3, 'write_to_file', '', ?)", (b"fixed",))
            conn.commit()

        service = StandardConversationTrajectoryMinerService()
        report = service.bifurcate_distillation(
            cid="bifurcate_session",
            db_path=db_path,
            output_vault_dir=vault_dir,
            output_skills_dir=skills_dir,
        )

        assert report.cid == "bifurcate_session"
        assert Path(report.knowledge_vault_path).exists()
        meta_file = Path(report.knowledge_vault_path) / "metadata.json"
        summary_file = Path(report.knowledge_vault_path) / "summary.md"
        assert meta_file.exists()
        assert summary_file.exists()

        # Verify metadata.json adheres to schema
        meta_json = json.loads(meta_file.read_text(encoding="utf-8"))
        assert "claims" in meta_json
        assert len(meta_json["claims"]) >= 1
        assert meta_json["provenance"]["isnad_verified"] is True

        # Verify summary.md includes isnad citations
        summary_text = summary_file.read_text(encoding="utf-8")
        assert "Verified Isnad Claims" in summary_text

        # Verify skill CARD.md generated
        assert report.skill_scaffold_path != ""
        card_file = Path(report.skill_scaffold_path) / "CARD.md"
        assert card_file.exists()
        assert "SKILL: trajectory-learned-" in card_file.read_text(encoding="utf-8")

    def test_headless_click_cli_commands(self, tmp_path: Path) -> None:
        """Verify Click CLI commands (scan, friction, inspect, bifurcate) execute cleanly (Rule 6, 10)."""
        db_path = tmp_path / "cli_test_session.db"
        with sqlite3.connect(db_path) as conn:
            conn.execute(
                "CREATE TABLE steps (idx INTEGER PRIMARY KEY, step_type INTEGER, status INTEGER, task_details TEXT, error_details TEXT, step_payload BLOB)"
            )
            conn.execute("INSERT INTO steps VALUES (0, 5, 3, 'prompt', '', ?)", (b"cli test prompt",))
            conn.commit()

        runner = CliRunner()

        # Test scan command
        res_scan = runner.invoke(
            trajectory_group,
            ["scan", "--corpus-dir", str(tmp_path), "--json-output"],
        )
        assert res_scan.exit_code == 0
        scan_data = json.loads(res_scan.output)
        assert len(scan_data) == 1
        assert scan_data[0]["cid"] == "cli_test_session"

        # Test friction command
        res_fric = runner.invoke(
            trajectory_group,
            ["friction", "--corpus-dir", str(tmp_path), "--json-output"],
        )
        assert res_fric.exit_code == 0
        fric_data = json.loads(res_fric.output)
        assert fric_data["total_conversations"] == 1
        assert fric_data["total_errors"] == 0

        # Test inspect command
        res_insp = runner.invoke(
            trajectory_group,
            ["inspect", "cli_test_session", "--corpus-dir", str(tmp_path), "--json-output"],
        )
        assert res_insp.exit_code == 0
        insp_data = json.loads(res_insp.output)
        assert insp_data["cid"] == "cli_test_session"
        assert insp_data["step_count"] == 1

        # Test main CLI alias routing
        res_alias = runner.invoke(harness_cli_main, ["trajectory", "--help"])
        assert res_alias.exit_code == 0
        assert "scan" in res_alias.output
        assert "friction" in res_alias.output

    def test_byte_offset_seek_table(self, tmp_path: Path) -> None:
        """Verify ByteOffsetSeekTable builds offset index and seeks lines in O(1) time (Rule 48)."""
        transcript_file = tmp_path / "test_transcript.jsonl"
        lines = [
            json.dumps({"step": 0, "msg": "first line"}) + "\n",
            json.dumps({"step": 1, "msg": "second line with extra details"}) + "\n",
            json.dumps({"step": 2, "msg": "third line"}) + "\n",
        ]
        # Write bytes directly to avoid Windows CRLF translation in text mode
        transcript_file.write_bytes("".join(lines).encode("utf-8"))

        table = ByteOffsetSeekTable(transcript_file)
        assert table.total_lines() == 3
        assert table.get_line(0) == lines[0]
        assert table.get_line(1) == lines[1]
        assert table.get_line(2) == lines[2]
        assert table.get_line(3) is None

        # Verify non-existent file handling
        missing_table = ByteOffsetSeekTable(tmp_path / "non_existent.jsonl")
        assert missing_table.total_lines() == 0
        assert missing_table.get_line(0) is None

    def test_corrupt_database_defensive_handling(self, tmp_path: Path) -> None:
        """Verify corrupt or non-database files are handled defensively without leaking locks (Rule 32)."""
        corrupt_db = tmp_path / "corrupt.db"
        corrupt_db.write_text("NOT A SQLITE FILE AT ALL", encoding="utf-8")

        service = StandardConversationTrajectoryMinerService()
        manifest = service.inspect_conversation(corrupt_db)
        assert manifest is None

        # Zero-byte empty file handling: SQLite opens, finds no steps table, returns step_count 0
        empty_db = tmp_path / "empty.db"
        empty_db.write_bytes(b"")
        manifest_empty = service.inspect_conversation(empty_db)
        assert manifest_empty is not None
        assert manifest_empty.step_count == 0

    def test_cli_cid_resolution_with_db_extension_and_path(self, tmp_path: Path) -> None:
        """Verify inspect and bifurcate CLI commands handle .db suffix and absolute file paths."""
        db_path = tmp_path / "flexible_session.db"
        with sqlite3.connect(db_path) as conn:
            conn.execute(
                "CREATE TABLE steps (idx INTEGER PRIMARY KEY, step_type INTEGER, status INTEGER, task_details TEXT, error_details TEXT, step_payload BLOB)"
            )
            conn.execute("INSERT INTO steps VALUES (0, 5, 3, 'prompt', '', ?)", (b"flexible prompt",))
            conn.commit()

        runner = CliRunner()

        # Invocation with .db suffix in argument
        res_suffix = runner.invoke(
            trajectory_group,
            ["inspect", "flexible_session.db", "--corpus-dir", str(tmp_path), "--json-output"],
        )
        assert res_suffix.exit_code == 0
        data_suffix = json.loads(res_suffix.output)
        assert data_suffix["cid"] == "flexible_session"

        # Invocation with full absolute file path
        res_path = runner.invoke(
            trajectory_group,
            ["inspect", str(db_path), "--corpus-dir", str(tmp_path), "--json-output"],
        )
        assert res_path.exit_code == 0
        data_path = json.loads(res_path.output)
        assert data_path["cid"] == "flexible_session"

    def test_bifurcated_skill_passes_skill_validator(self, tmp_path: Path) -> None:
        """Verify skill scaffold synthesized by bifurcate_distillation passes SkillValidator (Rule 34, 37)."""
        db_path = tmp_path / "valid_bifurcate.db"
        vault_dir = tmp_path / "vault"
        skills_dir = tmp_path / "skills"

        with sqlite3.connect(db_path) as conn:
            conn.execute(
                "CREATE TABLE steps (idx INTEGER PRIMARY KEY, step_type INTEGER, status INTEGER, task_details TEXT, error_details TEXT, step_payload BLOB)"
            )
            conn.execute("INSERT INTO steps VALUES (0, 5, 3, 'prompt', '', ?)", (b"test prompt",))
            conn.execute(
                "INSERT INTO steps VALUES (1, 8, 7, 'tool_call', 'PermissionDenied: access is denied', ?)",
                (b"",),
            )
            conn.execute("INSERT INTO steps VALUES (2, 8, 3, 'tool_call', '', ?)", (b"success",))
            conn.commit()

        service = StandardConversationTrajectoryMinerService()
        report = service.bifurcate_distillation(
            cid="valid_bifurcate_session",
            db_path=db_path,
            output_vault_dir=vault_dir,
            output_skills_dir=skills_dir,
        )

        scaffold_path = Path(report.skill_scaffold_path)
        assert scaffold_path.exists()
        assert (scaffold_path / "CARD.md").exists()
        assert (scaffold_path / "SKILL.md").exists()

        # Run SkillValidator on generated skill
        validator_report = SkillValidator.validate_sync(scaffold_path)
        assert validator_report.valid is True
        assert len(validator_report.errors) == 0

    def test_backward_compatible_script_wrapper(self, tmp_path: Path) -> None:
        """Verify script adapter in .agents/skills/ exports compatible types and runs CLI."""
        import importlib.util
        import sys

        script_path = (
            Path(".agents/skills/conversation-trajectory-miner/scripts/trajectory_miner.py")
        )
        spec = importlib.util.spec_from_file_location(
            "trajectory_miner_script", str(script_path)
        )
        assert spec is not None and spec.loader is not None
        miner_module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = miner_module
        spec.loader.exec_module(miner_module)

        assert miner_module.STATUS_MAP[3] == "DONE"
        assert miner_module.STEP_TYPE_MAP[5] == "USER_INPUT"
        step = miner_module.StepRecord(idx=0, step_type="USER_INPUT", status="DONE")
        assert step.idx == 0

        # Create dummy database
        db_path = tmp_path / "adapter_test.db"
        with sqlite3.connect(db_path) as conn:
            conn.execute(
                "CREATE TABLE steps (idx INTEGER PRIMARY KEY, step_type INTEGER, status INTEGER, task_details TEXT, error_details TEXT, step_payload BLOB)"
            )
            conn.execute("INSERT INTO steps VALUES (0, 5, 3, 'prompt', '', ?)", (b"adapter",))
            conn.commit()

        adapter = miner_module.ConversationTrajectoryMiner(corpus_dir=tmp_path)
        manifests = adapter.scan_corpus()
        assert len(manifests) == 1
        scorecard = adapter.compile_friction_scorecard(manifests)
        assert scorecard["total_conversations"] == 1
        assert scorecard["total_steps"] == 1


