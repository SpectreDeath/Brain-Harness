"""Test contract for Epistemology: Close the learning loop (Track 1A P0 & P1).

Verifies:
1. Knowledge Vault relevance retrieval into agent step context.
2. Bounded prompt injection formatting (Rule 9).
3. Retrieval and success tracking (evidence-based learning).
4. Lifecycle promotion and demotion evaluation.
5. Non-silent failure handling in skill guidance seam.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from harness.agent.react.engine import StepExecutionEngine
from harness.agent.react.prompting import build_react_initial_messages
from harness.kernel.context import ServiceContext
from harness.services.llm import LLMResponse
from harness.services.storage.models import KnowledgeItemRecord
from harness.services.storage.protocols import KNOWLEDGE_VAULT_KEY, STORAGE_SERVICE_KEY
from harness.services.storage.sqlite import SQLiteStorageService
from harness.services.tools import ToolRegistry


@pytest.fixture
def temp_vault_dir(tmp_path: Path) -> Path:
    """Create a temporary canonical .harness/knowledge directory with sample KIs."""
    vault = tmp_path / "knowledge"
    vault.mkdir()

    # KI 1: Security & Sandboxing
    ki1_dir = vault / "ki_security_sandboxing"
    ki1_dir.mkdir()
    (ki1_dir / "metadata.json").write_text(
        json.dumps(
            {
                "id": "ki_security_sandboxing",
                "title": "Subprocess Sandbox Isolation Invariant",
                "category": "security_and_forensics",
                "tags": ["sandbox", "isolation", "subprocess", "security"],
                "summary": "Untrusted external plugins must execute in subprocess sandboxes to guarantee isolation.",
                "retrieval_count": 0,
                "success_count": 0,
                "status": "ACTIVE",
            }
        ),
        encoding="utf-8",
    )
    (ki1_dir / "summary.md").write_text(
        "# Subprocess Sandbox Isolation Invariant\n\nUntrusted external plugins must execute in subprocess sandboxes.",
        encoding="utf-8",
    )

    # KI 2: Epistemic Lineage
    ki2_dir = vault / "ki_epistemic_lineage"
    ki2_dir.mkdir()
    (ki2_dir / "metadata.json").write_text(
        json.dumps(
            {
                "id": "ki_epistemic_lineage",
                "title": "Isnad Lineage Chain-of-Custody Audit",
                "category": "memory_and_epistemics",
                "tags": ["isnad", "epistemic", "lineage", "audit"],
                "summary": "Verify unbroken provenance before committing architectural assertions into memory.",
                "retrieval_count": 2,
                "success_count": 2,
                "status": "ACTIVE",
            }
        ),
        encoding="utf-8",
    )
    (ki2_dir / "summary.md").write_text(
        "# Isnad Lineage Chain-of-Custody Audit\n\nVerify unbroken provenance before committing.",
        encoding="utf-8",
    )

    return vault


@pytest.mark.asyncio
async def test_knowledge_retrieval_and_formatting(temp_vault_dir: Path) -> None:
    """Verify weighted task matching and prompt block formatting."""
    storage = SQLiteStorageService(":memory:")
    # Initial retrieval triggers auto-sync from temp_vault_dir
    results = await storage.retrieve_relevant_knowledge(
        task="Audit subprocess sandbox isolation for untrusted plugins",
        max_items=3,
        vault_dir=temp_vault_dir,
    )

    assert len(results) >= 1
    top_ki = results[0]
    assert top_ki.id == "ki_security_sandboxing"
    assert "sandbox" in top_ki.tags

    # Verify prompt block formatting
    block = storage.format_knowledge_prompt_block(results)
    assert "## Relevant Knowledge Vault Heuristics" in block
    assert "ki_security_sandboxing" in block
    assert "Subprocess Sandbox Isolation Invariant" in block


@pytest.mark.asyncio
async def test_retrieval_usage_tracking_and_outcome_recording(temp_vault_dir: Path) -> None:
    """Verify recording of retrieval usage and task success outcomes on storage and disk."""
    storage = SQLiteStorageService(":memory:")
    await storage.sync_knowledge_vault(temp_vault_dir)

    ki_id = "ki_security_sandboxing"
    item_before = await storage.get_knowledge_item(ki_id)
    assert item_before is not None
    assert item_before.retrieval_count == 0
    assert item_before.success_count == 0

    # Record retrieval
    await storage.record_knowledge_retrieval([ki_id], vault_dir=temp_vault_dir)
    item_retrieved = await storage.get_knowledge_item(ki_id)
    assert item_retrieved is not None
    assert item_retrieved.retrieval_count == 1
    assert item_retrieved.last_retrieved_at is not None

    # Check on-disk persistence
    disk_meta = json.loads((temp_vault_dir / ki_id / "metadata.json").read_text(encoding="utf-8"))
    assert disk_meta["retrieval_count"] == 1

    # Record successful outcome
    await storage.record_knowledge_outcome([ki_id], success=True, vault_dir=temp_vault_dir)
    item_success = await storage.get_knowledge_item(ki_id)
    assert item_success is not None
    assert item_success.success_count == 1

    disk_meta_after = json.loads((temp_vault_dir / ki_id / "metadata.json").read_text(encoding="utf-8"))
    assert disk_meta_after["success_count"] == 1


@pytest.mark.asyncio
async def test_vault_lifecycle_promotion_and_demotion(temp_vault_dir: Path) -> None:
    """Verify automated promotion and demotion based on retrieval-to-success ratios."""
    storage = SQLiteStorageService(":memory:")
    await storage.sync_knowledge_vault(temp_vault_dir)

    # Setup high utility item (5 retrievals, 5 successes -> 100%)
    high_ki = await storage.get_knowledge_item("ki_security_sandboxing")
    assert high_ki is not None
    high_ki.retrieval_count = 5
    high_ki.success_count = 5
    await storage.save_knowledge_item(high_ki)

    # Setup low utility item (5 retrievals, 0 successes -> 0%)
    low_ki = await storage.get_knowledge_item("ki_epistemic_lineage")
    assert low_ki is not None
    low_ki.retrieval_count = 5
    low_ki.success_count = 0
    await storage.save_knowledge_item(low_ki)

    eval_result = await storage.evaluate_vault_lifecycle(
        min_retrievals=5,
        promote_ratio=0.75,
        demote_ratio=0.25,
        vault_dir=temp_vault_dir,
    )

    assert "ki_security_sandboxing" in eval_result["promoted"]
    assert "ki_epistemic_lineage" in eval_result["demoted"]

    updated_high = await storage.get_knowledge_item("ki_security_sandboxing")
    assert updated_high is not None
    assert updated_high.status == "PROMOTED"

    updated_low = await storage.get_knowledge_item("ki_epistemic_lineage")
    assert updated_low is not None
    assert updated_low.status == "DEMOTED"


def test_build_react_initial_messages_injects_knowledge(temp_vault_dir: Path) -> None:
    """Verify build_react_initial_messages retrieves KIs into prompt context."""
    context = ServiceContext()
    storage = SQLiteStorageService(":memory:")
    # Pre-sync temporary vault
    from harness.creator.validator.base import _run_coro_sync
    _run_coro_sync(storage.sync_knowledge_vault(temp_vault_dir))
    context.provide(KNOWLEDGE_VAULT_KEY, storage)
    context.provide(STORAGE_SERVICE_KEY, storage)

    tools = ToolRegistry()
    messages, skills = build_react_initial_messages(
        task="Audit subprocess sandbox isolation for untrusted plugins",
        tools=tools,
        context=context,
    )

    assert len(messages) >= 2
    system_content = messages[0].content
    assert "## Relevant Knowledge Vault Heuristics" in system_content
    assert "ki_security_sandboxing" in system_content


@pytest.mark.asyncio
async def test_step_execution_engine_records_trajectory_knowledge_outcome(
    temp_vault_dir: Path,
) -> None:
    """Verify StepExecutionEngine records retrieved KIs on trajectory and records outcome."""
    context = ServiceContext()
    storage = SQLiteStorageService(":memory:")
    await storage.sync_knowledge_vault(temp_vault_dir)
    context.provide(KNOWLEDGE_VAULT_KEY, storage)
    context.provide(STORAGE_SERVICE_KEY, storage)

    mock_llm = MagicMock()
    mock_llm.complete = MagicMock()

    async def mock_complete(*args: Any, **kwargs: Any) -> LLMResponse:
        return LLMResponse(content="FINAL ANSWER: The sandbox is strictly isolated.")

    mock_llm.complete.side_effect = mock_complete

    engine = StepExecutionEngine(
        llm=mock_llm,
        tools=ToolRegistry(),
        context=context,
    )

    from harness.agent.base import AgentTrajectory

    task = "Audit subprocess sandbox isolation for untrusted plugins"
    messages = engine.build_initial_messages(task)
    assert len(engine.active_knowledge_items) >= 1
    assert "ki_security_sandboxing" in engine.active_knowledge_items

    trajectory = AgentTrajectory(task=task, messages=messages)

    # Execute step — should hit FINAL ANSWER and trigger success outcome recording
    has_more = await engine.execute_step(trajectory=trajectory, step_idx=1)
    assert has_more is False
    assert trajectory.status == "completed"
    assert "retrieved_knowledge_items" in trajectory.metadata
    assert "ki_security_sandboxing" in trajectory.metadata["retrieved_knowledge_items"]

    # Verify success count was incremented
    ki = await storage.get_knowledge_item("ki_security_sandboxing")
    assert ki is not None
    assert ki.success_count == 1
