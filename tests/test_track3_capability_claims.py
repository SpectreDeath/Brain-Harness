"""Tests for Track 3: Capability claims verification, honest reporting, and path verification."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch
import pytest

from harness.plugins.manifest import PluginManifest
from plugins.integration_and_io.agent_reach_bridge.agent_reach_service import AgentReachBridgeService
from plugins.developer_tooling.r_editor_bridge.r_editor_service import REditorBridgeService


def test_agent_reach_envelope_only_behavior():
    service = AgentReachBridgeService()
    envelope = service.read("https://user:pass@github.com/my-repo")
    # Verify credential scrubbing is retained
    assert "user:pass" not in envelope.meta.get("target_url", "")
    assert envelope.ok is True
    # Verify status indicates envelope formatting rather than simulated fake scraping
    assert len(envelope.items) > 0
    assert envelope.items[0].get("status") == "envelope_prepared"


@pytest.mark.asyncio
async def test_agent_reach_cli_path_verification():
    service = AgentReachBridgeService()
    # When binary is missing from PATH, execute_sandboxed_cli must fail loudly with FileNotFoundError
    with patch("shutil.which", return_value=None):
        with pytest.raises(FileNotFoundError, match="agent-reach"):
            await service.execute_sandboxed_cli(["read", "https://example.com"])


def test_triad_pipeline_honest_verification_reporting(tmp_path: Path):
    sys.path.insert(0, str(Path(".agents/skills/repo-triad-forge/scripts").resolve()))
    from triad_pipeline import RepoTriadPipelineEngine, TriadExecutionResult

    # 1. Real test command execution
    cmd = [sys.executable, "-c", "import sys; sys.exit(0)"]
    result = RepoTriadPipelineEngine.run_bounded_verification([cmd])
    assert result.success is True
    assert "PASSED" in result.artifacts[0]

    # 2. Failing test command execution properly halts and reports
    fail_cmd = [sys.executable, "-c", "import sys; sys.exit(1)"]
    fail_result = RepoTriadPipelineEngine.run_bounded_verification([fail_cmd], max_attempts=1)
    assert fail_result.success is False
    assert "failed after 1 attempts" in fail_result.message


def test_r_editor_service_nested_doc():
    service = REditorBridgeService()
    assert "Nested Execution" in service.execute_sandboxed_r_command.__doc__
