"""Tests for Unified Context Optimization Pipeline (Memory & Epistemics Bridge)."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from plugins.memory_and_epistemics.unified_context_pipeline import (
    UNIFIED_CONTEXT_PIPELINE_SERVICE_KEY,
    PipelineMessage,
    UnifiedContextPipeline,
)


@pytest.mark.unit
class TestUnifiedContextPipeline:
    def test_end_to_end_pipeline_decay_pruning_and_token_savings(self) -> None:
        pipeline = UnifiedContextPipeline()
        session_id = "test_unified_session"

        # Prepare a complex message sequence:
        # - msg_0: System instruction (channel='instruction', should decay very slowly)
        # - msg_1: Expired tool output (will be evicted by Pass 1 pruning)
        # - msg_2: Current tool output with DEFINE:schema_key
        # - msg_3: Duplicate doc passage 1
        # - msg_4: Duplicate doc passage 2 (will be collapsed by Pass 2)
        # - msg_5: User query referencing REF:schema_key
        messages = [
            {
                "id": "msg_0",
                "role": "system",
                "content": "You are a code synthesis assistant.",
                "channel": "instruction",
                "stability": 20.0,
            },
            {
                "id": "msg_1",
                "role": "tool_output",
                "content": "Old search output",
                "channel": "tool_output",
                "tool_call_key": "search",
            },
            {
                "id": "msg_2",
                "role": "tool_output",
                "content": "Updated search output DEFINE:schema_key",
                "channel": "tool_output",
                "tool_call_key": "search",
            },
            {
                "id": "msg_3",
                "role": "retrieved_doc",
                "content": "Database migration guide notes.",
                "channel": "evidence",
            },
            {
                "id": "msg_4",
                "role": "retrieved_doc",
                "content": "database MIGRATION guide notes.",
                "channel": "evidence",
            },
            {
                "id": "msg_5",
                "role": "user",
                "content": "Please verify REF:schema_key against the database.",
                "channel": "memory",
            },
        ]

        result = pipeline.process(
            session_id=session_id,
            messages=messages,
            advance_turn=False,
        )

        assert result.session_id == session_id
        assert result.input_messages_count == 6
        # Duplicate doc msg_4 should be removed, expired msg_1 should be removed
        assert "msg_4" in result.pruner_removed_ids
        assert "msg_1" in result.pruner_removed_ids
        assert result.final_messages_count == 4
        assert result.tokens_optimized < result.tokens_raw
        assert result.token_savings_pct > 0.0
        assert "[SYSTEM] You are a code synthesis assistant." in result.assembled_prompt

    def test_pipeline_with_code_compilation(self) -> None:
        pipeline = UnifiedContextPipeline()
        with tempfile.TemporaryDirectory() as temp_repo:
            root = Path(temp_repo)
            mod_a = root / "module_a.py"
            mod_a.write_text("class Alpha:\n    def run(self):\n        return 42\n")

            messages = [
                PipelineMessage(id="u1", role="user", content="Inspect module_a"),
            ]

            result = pipeline.process(
                session_id="code_sess",
                messages=messages,
                target_repo_path=str(root),
                target_file_path=str(mod_a),
                advance_turn=False,
            )

            assert result.final_messages_count == 1
            assert "class Alpha:" in result.code_context

    def test_service_key_identity(self) -> None:
        assert UNIFIED_CONTEXT_PIPELINE_SERVICE_KEY.name == "domain.unified_context_pipeline"
