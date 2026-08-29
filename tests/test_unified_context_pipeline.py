"""Unit tests for the deepened UnifiedContextPipelineService."""

from __future__ import annotations

import tempfile
from pathlib import Path
import pytest

from harness.services.unified_context import (
    UNIFIED_CONTEXT_PIPELINE_KEY,
    DefaultUnifiedContextPipeline,
    UnifiedContextPipelineService,
    UnifiedContextRequest,
)


@pytest.mark.unit
def test_unified_context_pipeline_service_key() -> None:
    """Verify ServiceKey name for unified context pipeline."""
    assert UNIFIED_CONTEXT_PIPELINE_KEY.name == "service.unified_context_pipeline"


@pytest.mark.unit
def test_pipeline_observation_truncation_and_compaction() -> None:
    """Test full multi-pass pipeline processing."""
    pipeline = DefaultUnifiedContextPipeline()

    huge_observation = "A" * 8000
    messages = [
        {"role": "system", "content": "You are Harness agent."},
        {"role": "user", "content": "Analyze system."},
        {"role": "assistant", "content": "Listing dir."},
        {"role": "observation", "content": f"Observation: {huge_observation}"},
        {"role": "assistant", "content": "Reading file."},
        {"role": "observation", "content": "Observation: file content"},
        {"role": "assistant", "content": "Final step."},
    ]

    req = UnifiedContextRequest(
        messages=messages,
        max_observation_chars=1000,
        recent_messages_preserve=2,
    )

    res = pipeline.process_context(req)
    assert res.status == "ok"
    assert res.original_message_count == len(messages)
    assert res.optimized_message_count <= len(messages)
    # Check that the huge observation was truncated
    obs_msg = [m for m in res.assembled_messages if "Observation:" in str(m.get("content", ""))]
    if obs_msg:
        assert len(str(obs_msg[0].get("content", ""))) < 8000


@pytest.mark.unit
def test_pipeline_repomap_integration() -> None:
    """Test AST RepoMap injection inside the unified pipeline."""
    pipeline = DefaultUnifiedContextPipeline()

    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "calculator.py").write_text("class Calculator:\n    def add(a, b): pass\n", encoding="utf-8")

        messages = [
            {"role": "system", "content": "You are a coding agent."},
            {"role": "user", "content": "Fix Calculator.add logic."},
        ]

        req = UnifiedContextRequest(
            messages=messages,
            repo_map_root=str(root),
            repo_map_budget_tokens=500,
            query_context="Fix Calculator add",
        )

        res = pipeline.process_context(req)
        assert res.status == "ok"
        assert res.repo_map_injected is True
        assert "Repository Map:" in res.assembled_messages[0]["content"]
        assert "calculator.py:" in res.assembled_messages[0]["content"]
