"""Tests for Track 4 & Track 5: Vault data integrity, storage authority, and error visibility."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
import pytest

from harness.services.storage.models import KnowledgeItemRecord, IsnadClaim
from harness.services.storage.vault_export import export_single_item_to_disk
from harness.services.storage.vault_operations import KnowledgeVaultMixin
from harness.services.storage.vault_retrieval import KnowledgeRetrievalMixin


def test_triad_forge_items_directly_constructible():
    root = Path(".harness/knowledge")
    triad_ids = [
        "ki_agent_reach_layered_backend_fallback",
        "ki_agent_reach_session_isolation_and_credential_scrubbing",
        "ki_agent_reach_stealth_browser_cdp_loopback",
        "ki_agent_reach_unified_envelope_taxonomy",
        "ki_r_c_graphics_device_serialization",
        "ki_r_decoupled_syntax_grammar",
        "ki_r_lsp_textsync_and_diagnostics",
        "ki_r_session_watcher_reflection",
        "ki_token_economizer_dynamic_tool_pruning",
        "ki_token_economizer_microskills_lifecycle",
        "ki_token_economizer_multi_agent_trace_federation",
        "ki_token_economizer_turn_guard_loop_intervention",
    ]
    for ki_id in triad_ids:
        meta_file = root / ki_id / "metadata.json"
        assert meta_file.exists(), f"Missing {ki_id}"
        data = json.loads(meta_file.read_text(encoding="utf-8"))
        assert "category" in data
        assert "created_at" in data
        assert "retrieval_count" in data
        assert "edges" in data
        # Ensure direct Pydantic model validation succeeds without sync healing
        record = KnowledgeItemRecord.model_validate(data)
        assert record.id == ki_id


def test_no_stored_edges_contain_absolute_machine_paths():
    root = Path(".harness/knowledge")
    bad_edges = []
    for ki_dir in root.iterdir():
        if not ki_dir.is_dir():
            continue
        meta_file = ki_dir / "metadata.json"
        if not meta_file.exists():
            continue
        data = json.loads(meta_file.read_text(encoding="utf-8"))
        for edge in data.get("edges", []):
            target = edge.get("target_id") or edge.get("target", "")
            if "D:/GitHub" in target or "d:/GitHub" in target or "D:\\GitHub" in target:
                bad_edges.append((ki_dir.name, target))
    assert bad_edges == [], f"Found absolute path edges: {bad_edges}"


@pytest.mark.asyncio
async def test_export_strips_internal_underscore_keys(tmp_path: Path):
    ki = KnowledgeItemRecord(
        id="test_export_ki",
        title="Test Export KI",
        source_target="test_source",
        summary="A test summary",
        category="engineering",
        **{"_date_source": "synthetic_date", "valid_extra": "should_persist"},
    )
    await export_single_item_to_disk(ki, vault_dir=tmp_path)
    meta_file = tmp_path / "test_export_ki" / "metadata.json"
    assert meta_file.exists()
    saved_meta = json.loads(meta_file.read_text(encoding="utf-8"))
    assert "_date_source" not in saved_meta
    assert saved_meta.get("valid_extra") == "should_persist"


def test_isnad_claim_rejects_invalid_claims():
    ki = KnowledgeItemRecord(
        id="test_isnad_ki",
        title="Test Isnad KI",
        source_target="test_source",
        summary="Summary",
        category="engineering",
        isnad={
            "decision_id": "dec_1",
            "claims": [
                {"assertion": "Valid assertion", "confidence": 0.9},
                {"missing_assertion": True},  # Invalid claim missing required assertion
                "invalid_non_dict_claim",
            ],
        },
    )
    claims = ki.get_claims()
    assert len(claims) == 1
    assert claims[0].assertion == "Valid assertion"


class DummyRetrieval(KnowledgeRetrievalMixin):
    async def get_knowledge_item(self, ki_id: str):
        return None

    async def list_knowledge_items(self, tag=None):
        return []

    async def save_knowledge_item(self, item):
        pass


@pytest.mark.asyncio
async def test_retrieval_corrupt_metadata_does_not_crash(tmp_path: Path):
    ki_dir = tmp_path / "corrupt_ki"
    ki_dir.mkdir(parents=True)
    (ki_dir / "metadata.json").write_text("{corrupt json", encoding="utf-8")

    retrieval = DummyRetrieval()
    # Must not raise an unhandled JSONDecodeError
    await retrieval.record_knowledge_retrieval(["corrupt_ki"], vault_dir=tmp_path)
    await retrieval.record_knowledge_outcome(["corrupt_ki"], success=True, vault_dir=tmp_path)
