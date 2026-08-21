"""Tests for brain_bridge plugin."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from plugins.memory_and_epistemics.brain_bridge.main import (
    _detect_brain_format,
    brain_attach,
    brain_detach,
    brain_list_attached,
    brain_query,
)


@pytest.mark.unit
class TestBrainBridgePlugin:
    def test_format_detection(self, tmp_path: Path) -> None:
        # 1. Antigravity Brain
        ag_dir = tmp_path / "ag_brain"
        (ag_dir / ".system_generated" / "logs").mkdir(parents=True)
        (ag_dir / ".system_generated" / "logs" / "transcript.jsonl").write_text("{}\n")
        assert _detect_brain_format(ag_dir) == "antigravity_brain"

        # 2. Harness Instance
        harness_dir = tmp_path / "harness_repo"
        (harness_dir / ".harness").mkdir(parents=True)
        assert _detect_brain_format(harness_dir) == "harness_instance"

        # 3. IDE Memo (Claude / Cursor)
        ide_dir = tmp_path / "ide_repo"
        ide_dir.mkdir()
        (ide_dir / ".cursorrules").write_text("rule content")
        assert _detect_brain_format(ide_dir) == "ide_memo"

        # 4. Obsidian Vault
        vault_dir = tmp_path / "obsidian_vault"
        vault_dir.mkdir()
        (vault_dir / "note.md").write_text("# Knowledge\nSee [[Architecture]] for details.")
        assert _detect_brain_format(vault_dir) == "obsidian_vault"

        # 5. Raw Docs
        raw_dir = tmp_path / "raw_docs"
        raw_dir.mkdir()
        (raw_dir / "guide.txt").write_text("Plain text documentation.")
        assert _detect_brain_format(raw_dir) == "raw_docs"

    def test_brain_attach_and_query(self, tmp_path: Path) -> None:
        target = tmp_path / "external_brain"
        target.mkdir()

        # Write doc file
        (target / "architecture.md").write_text(
            "# Kernel Design\n"
            "The micro-kernel uses typed ServiceKey[T] and an immutable event bus.\n"
        )

        # Write transcript file
        transcript_line = {
            "step_index": 1,
            "type": "PLANNER_RESPONSE",
            "content": "Refactored topological sorting in plugin dependency manager.",
            "tool_calls": [{"name": "replace_file_content", "args": {}}],
            "status": "DONE",
        }
        (target / "transcript.jsonl").write_text(json.dumps(transcript_line) + "\n")

        # Attach
        attach_res = brain_attach(str(target), alias="test_brain")
        assert attach_res["status"] == "ok"
        assert attach_res["alias"] == "test_brain"
        assert attach_res["summary"]["total_chunks"] >= 2
        assert attach_res["summary"]["trajectories_recorded"] == 1

        # List
        list_res = brain_list_attached()
        assert list_res["status"] == "ok"
        assert list_res["attached_count"] >= 1
        aliases = [b["alias"] for b in list_res["brains"]]
        assert "test_brain" in aliases

        # Query doc
        query_doc = brain_query("ServiceKey micro-kernel architecture", brain_alias="test_brain")
        assert query_doc["status"] == "ok"
        assert query_doc["results_count"] >= 1
        assert "architecture.md" in query_doc["results"][0]["file"]

        # Query transcript trajectory
        query_traj = brain_query("topological sorting dependency manager", brain_alias="test_brain")
        assert query_traj["status"] == "ok"
        assert query_traj["results_count"] >= 1
        assert query_traj["results"][0]["type"] == "transcript_step"

        # Detach
        detach_res = brain_detach("test_brain")
        assert detach_res["status"] == "ok"
        assert detach_res["detached_alias"] == "test_brain"

        # Query after detach
        list_after = brain_list_attached()
        assert "test_brain" not in [b["alias"] for b in list_after["brains"]]

    def test_invalid_path_attach(self) -> None:
        res = brain_attach("/non/existent/path/for/sure")
        assert res["status"] == "error"
        assert "not found" in res["error"].lower()
