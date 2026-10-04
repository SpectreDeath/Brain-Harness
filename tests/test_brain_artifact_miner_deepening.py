"""Comprehensive contract tests for brain_artifact_miner architectural deepening.

Verifies:
1. Micro-kernel IoC service protocol and ServiceKey registration (Rule 1, Rule 2, Rule 49)
2. Domain-partitioned plugin lifecycle in plugins/memory_and_epistemics/ (Rule 45)
3. Dual-transcript O(1) binary seek & automatic truncation dereference (Rule 22, Rule 48)
4. Slotted and frozen immutability assertions (Rule 12, Rule 43)
5. Canonical Knowledge Vault dual-file generation with isnad claims (Rule 40, Rule 41)
6. Headless Click CLI introspection suite (Rule 6, Rule 10)
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest
from click.testing import CliRunner

from harness.kernel.context import ServiceContext
from harness.services.brain_artifact_miner import (
    BRAIN_ARTIFACT_MINER_KEY,
    ArtifactLifecycleEntry,
    BrainArtifactMinerService,
    ByteOffsetEntry,
    DualTranscriptStep,
    ScratchCatalog,
    ScratchCatalogItem,
    StandardBrainArtifactMinerService,
    TaskTriageReport,
)
from plugins.memory_and_epistemics.brain_artifact_miner.main import (
    BrainArtifactMinerPlugin,
    plugin as brain_miner_plugin_singleton,
)
from harness.commands.brain_miner import brain_miner_group
from harness.cli import main as harness_cli_main


@pytest.mark.unit
class TestBrainArtifactMinerDeepening:
    """Contract tests for deepened brain artifact miner architecture."""

    def test_service_protocol_conformance_and_singleton(self) -> None:
        """Verify StandardBrainArtifactMinerService satisfies BrainArtifactMinerService protocol (Rule 49)."""
        service = StandardBrainArtifactMinerService()
        assert isinstance(service, BrainArtifactMinerService)
        assert brain_miner_plugin_singleton is not None
        assert isinstance(brain_miner_plugin_singleton, BrainArtifactMinerPlugin)

    @pytest.mark.asyncio
    async def test_ioc_registration_and_resolution(self) -> None:
        """Verify BrainArtifactMinerPlugin registers BRAIN_ARTIFACT_MINER_KEY into IoC container (Rule 1, 2)."""
        ctx = ServiceContext()
        plugin = BrainArtifactMinerPlugin()
        assert BRAIN_ARTIFACT_MINER_KEY in plugin.provides

        await plugin.on_load(ctx)
        resolved_service = ctx.require(BRAIN_ARTIFACT_MINER_KEY)
        assert resolved_service is not None
        assert isinstance(resolved_service, BrainArtifactMinerService)

    def test_dual_transcript_binary_seek_and_dereference(self, tmp_path: Path) -> None:
        """Verify O(1) binary seek and automatic truncation dereferencing (Rule 22, Rule 48)."""
        # Create synthetic dual-transcript files
        compact_file = tmp_path / "transcript.jsonl"
        full_file = tmp_path / "transcript_full.jsonl"

        step_0 = {
            "step_index": 0,
            "source": "USER",
            "type": "USER_INPUT",
            "status": "DONE",
            "content": "Start task",
            "is_truncated": False,
        }
        step_1_compact = {
            "step_index": 1,
            "source": "MODEL",
            "type": "PLANNER_RESPONSE",
            "status": "DONE",
            "content": "Thought truncated...",
            "is_truncated": True,
            "tool_calls": [],
        }
        step_1_full = {
            "step_index": 1,
            "source": "MODEL",
            "type": "PLANNER_RESPONSE",
            "status": "DONE",
            "content": "Full untruncated deep thought with all details",
            "is_truncated": False,
            "tool_calls": [{"name": "scan_tools", "args": {"brain_dir": "test"}}],
        }

        compact_file.write_text(
            json.dumps(step_0) + "\n" + json.dumps(step_1_compact) + "\n",
            encoding="utf-8",
        )
        full_file.write_text(
            json.dumps(step_0) + "\n" + json.dumps(step_1_full) + "\n",
            encoding="utf-8",
        )

        service = StandardBrainArtifactMinerService()

        # Test index compilation
        index = service.build_offset_index(compact_file)
        assert 0 in index
        assert 1 in index

        # Test step 0 (not truncated)
        s0 = service.get_step(compact_file, 0)
        assert s0 is not None
        assert s0["step_index"] == 0
        assert s0["content"] == "Start task"
        assert s0["is_truncated"] is False
        assert s0["dereferenced"] is False

        # Test step 1 with auto-dereference (Rule 22)
        s1 = service.get_step(compact_file, 1, dereference_truncated=True)
        assert s1 is not None
        assert s1["step_index"] == 1
        assert s1["content"] == "Full untruncated deep thought with all details"
        assert len(s1["tool_calls"]) == 1
        assert s1["tool_calls"][0]["name"] == "scan_tools"
        assert s1["is_truncated"] is False
        assert s1["dereferenced"] is True

        # Test step 1 with no-dereference
        s1_raw = service.get_step(compact_file, 1, dereference_truncated=False)
        assert s1_raw is not None
        assert s1_raw["content"] == "Thought truncated..."
        assert s1_raw["is_truncated"] is True
        assert s1_raw["dereferenced"] is False

        # Test stream_steps
        steps = list(service.stream_steps(compact_file, dereference_truncated=True))
        assert len(steps) == 2
        assert steps[1]["dereferenced"] is True

        # Test non-existent step
        assert service.get_step(compact_file, 99) is None

    def test_slotted_frozen_dataclass_immutability(self) -> None:
        """Verify slotted and frozen immutability across all domain models (Rule 12, Rule 43)."""
        item = ScratchCatalogItem(
            category="ast_and_lint",
            path="script.py",
            functions=["foo"],
            imports=["ast"],
            docstring="doc",
        )
        catalog = ScratchCatalog(
            total_scanned=1,
            classified_count=1,
            items_by_category={"ast_and_lint": [item]},
        )
        report = TaskTriageReport(total_tasks=1, failed_count=0, deadlock_count=0, samples=[])
        offset = ByteOffsetEntry(step_index=0, byte_offset=0, byte_length=100)
        step = DualTranscriptStep(
            step_index=0,
            source="USER",
            step_type="USER_INPUT",
            status="DONE",
            content="test",
            is_truncated=False,
            tool_calls=[],
            dereferenced=False,
        )
        lifecycle = ArtifactLifecycleEntry(
            conversation_id="cid_01",
            artifact_name="plan.md",
            has_plan=True,
            has_walkthrough=False,
            has_task=True,
            mtime=123456.7,
        )

        with pytest.raises((AttributeError, TypeError)):
            item.category = "other"  # type: ignore

        with pytest.raises((AttributeError, TypeError)):
            catalog.total_scanned = 10  # type: ignore

        with pytest.raises((AttributeError, TypeError)):
            report.failed_count = 2  # type: ignore

        with pytest.raises((AttributeError, TypeError)):
            offset.byte_offset = 50  # type: ignore

        with pytest.raises((AttributeError, TypeError)):
            step.dereferenced = True  # type: ignore

        with pytest.raises((AttributeError, TypeError)):
            lifecycle.has_plan = False  # type: ignore

    def test_canonical_knowledge_vault_exporter(self, tmp_path: Path) -> None:
        """Verify Knowledge Vault export produces dual-file format with isnad claims (Rule 40, 41)."""
        service = StandardBrainArtifactMinerService()
        meta_file, summary_file = service.export_knowledge_item(
            output_dir=tmp_path,
            ki_id="ki_test_mining_01",
            title="Test Mining Knowledge Item",
            category="memory_and_epistemics",
            summary="Distilled learning about artifact topology.",
            claims=[
                {
                    "assertion": "Brain artifact stores contain scratch tools.",
                    "lineage": [{"node_type": "empirical_test", "verified": True}],
                }
            ],
        )

        assert meta_file.exists()
        assert summary_file.exists()
        assert meta_file.name == "metadata.json"
        assert summary_file.name == "summary.md"

        data = json.loads(meta_file.read_text(encoding="utf-8"))
        assert data["id"] == "ki_test_mining_01"
        assert data["isnad"]["status"] == "VERIFIED"
        assert len(data["isnad"]["claims"]) == 1

        summary_text = summary_file.read_text(encoding="utf-8")
        assert "# Test Mining Knowledge Item" in summary_text
        assert "Distilled learning about artifact topology." in summary_text

    def test_click_cli_group_and_subcommands(self, tmp_path: Path) -> None:
        """Verify Click CLI commands (scan, triage, step, brief) via CliRunner (Rule 6, Rule 10)."""
        runner = CliRunner()

        # 1. Group help
        res = runner.invoke(brain_miner_group, ["--help"])
        assert res.exit_code == 0
        assert "scan" in res.output
        assert "triage" in res.output
        assert "step" in res.output
        assert "brief" in res.output

        # 2. Top-level harness CLI registration aliases
        res_harness = runner.invoke(harness_cli_main, ["brain-miner", "--help"])
        assert res_harness.exit_code == 0
        res_alias = runner.invoke(harness_cli_main, ["miner", "--help"])
        assert res_alias.exit_code == 0

        # 3. Scan command on empty dir
        res_scan = runner.invoke(brain_miner_group, ["scan", "--brain-dir", str(tmp_path), "--json-output"])
        assert res_scan.exit_code == 0
        scan_data = json.loads(res_scan.output)
        assert scan_data["total_scanned"] == 0

        # 4. Triage command on empty dir
        res_triage = runner.invoke(brain_miner_group, ["triage", "--brain-dir", str(tmp_path), "--json-output"])
        assert res_triage.exit_code == 0
        triage_data = json.loads(res_triage.output)
        assert triage_data["total_tasks"] == 0

        # 5. Step command with test file
        test_file = tmp_path / "transcript.jsonl"
        test_file.write_text(json.dumps({"step_index": 0, "type": "USER_INPUT", "content": "hello"}) + "\n")
        res_step = runner.invoke(brain_miner_group, ["step", str(test_file), "0", "--json-output"])
        assert res_step.exit_code == 0
        step_data = json.loads(res_step.output)
        assert step_data["step_index"] == 0
        assert step_data["content"] == "hello"

        # 6. Brief command
        brief_out = tmp_path / "brief.html"
        res_brief = runner.invoke(brain_miner_group, ["brief", "--brain-dir", str(tmp_path), "--out", str(brief_out)])
        assert res_brief.exit_code == 0
        assert brief_out.exists()
        assert "<!DOCTYPE html>" in brief_out.read_text(encoding="utf-8")
