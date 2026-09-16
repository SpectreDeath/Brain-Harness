"""Tests for Paperless Document Pipeline Agent Skill."""

from __future__ import annotations

import importlib.util
import sys
import tempfile
from pathlib import Path
import pytest
import yaml

# Dynamic import from .agents/skills/paperless-document-pipeline/scripts/
_SKILL_ROOT = (
    Path(__file__).resolve().parent.parent
    / ".agents"
    / "skills"
    / "paperless-document-pipeline"
)

# 1. domain_models.py
_dm_path = _SKILL_ROOT / "scripts" / "domain_models.py"
_dm_spec = importlib.util.spec_from_file_location("paperless_domain_models", _dm_path)
assert _dm_spec and _dm_spec.loader, f"Failed to load {_dm_path}"
_dm_mod = importlib.util.module_from_spec(_dm_spec)
sys.modules["paperless_domain_models"] = _dm_mod
_dm_spec.loader.exec_module(_dm_mod)

ConsumeTaskStatus = _dm_mod.ConsumeTaskStatus
PaperlessDocument = _dm_mod.PaperlessDocument
RAGQueryResponse = _dm_mod.RAGQueryResponse

# 2. paperless_client.py
_client_path = _SKILL_ROOT / "scripts" / "paperless_client.py"
_client_spec = importlib.util.spec_from_file_location("paperless_client", _client_path)
assert _client_spec and _client_spec.loader, f"Failed to load {_client_path}"
_client_mod = importlib.util.module_from_spec(_client_spec)
sys.modules["paperless_client"] = _client_mod
_client_spec.loader.exec_module(_client_mod)

salvage_json = _client_mod.salvage_json

# 3. validate_pipeline.py
_val_path = _SKILL_ROOT / "scripts" / "validate_pipeline.py"
_val_spec = importlib.util.spec_from_file_location("validate_pipeline", _val_path)
assert _val_spec and _val_spec.loader, f"Failed to load {_val_path}"
_val_mod = importlib.util.module_from_spec(_val_spec)
sys.modules["validate_pipeline"] = _val_mod
_val_spec.loader.exec_module(_val_mod)

validate_file_readiness = _val_mod.validate_file_readiness


@pytest.mark.unit
def test_paperless_document_slotted_immutability() -> None:
    """Verify slots=True and frozen=True immutability per Rule 12 and Rule 43."""
    doc = PaperlessDocument(
        id=42,
        title="Annual Report",
        content="Fiscal year report content...",
        correspondent="Acme Corp",
        document_type="Report",
        tags=("finance", "annual"),
        archive_serial_number=10042,
    )

    assert doc.id == 42
    assert doc.title == "Annual Report"
    assert doc.tags == ("finance", "annual")
    assert doc.archive_serial_number == 10042

    # Direct attribute assignment must raise AttributeError or TypeError (Rule 43)
    with pytest.raises((AttributeError, TypeError)):
        doc.title = "Mutated Title"  # type: ignore[misc]

    with pytest.raises((AttributeError, TypeError)):
        doc.id = 99  # type: ignore[misc]


@pytest.mark.unit
def test_paperless_document_validation_invariants() -> None:
    """Verify __post_init__ assertions for invalid inputs."""
    with pytest.raises(ValueError, match="id must be positive"):
        PaperlessDocument(id=0, title="Zero ID", content="test")

    with pytest.raises(ValueError, match="title must not be empty"):
        PaperlessDocument(id=1, title="   ", content="test")

    with pytest.raises(ValueError, match="archive_serial_number must be non-negative"):
        PaperlessDocument(id=1, title="Test", content="test", archive_serial_number=-5)


@pytest.mark.unit
def test_consume_task_status_invariants() -> None:
    """Verify ConsumeTaskStatus slotted invariants."""
    task = ConsumeTaskStatus(task_id="uuid-1234", status="SUCCESS", progress=100, document_id=10)
    assert task.task_id == "uuid-1234"
    assert task.progress == 100

    # Immutability
    with pytest.raises((AttributeError, TypeError)):
        task.status = "FAILURE"  # type: ignore[misc]

    # Post init checks
    with pytest.raises(ValueError, match="progress must be in range"):
        ConsumeTaskStatus(task_id="t1", status="STARTED", progress=150)


@pytest.mark.unit
def test_rag_query_response_invariants() -> None:
    """Verify RAGQueryResponse slotted invariants."""
    rag = RAGQueryResponse(answer="Ground truth fact", citations=(1, 2), confidence=0.95)
    assert rag.answer == "Ground truth fact"
    assert rag.citations == (1, 2)
    assert rag.confidence == 0.95

    with pytest.raises(ValueError, match="answer must not be empty"):
        RAGQueryResponse(answer="")

    with pytest.raises(ValueError, match="confidence must be in range"):
        RAGQueryResponse(answer="Valid", confidence=1.5)


@pytest.mark.unit
def test_local_string_salvage_resilience() -> None:
    """Verify Rule 42 local string salvage on malformed LLM outputs."""
    # 1. Code fence stripping
    raw_fence = "```json\n{\"id\": 1, \"title\": \"Parsed Doc\"}\n```"
    salvaged = salvage_json(raw_fence)
    assert salvaged.get("id") == 1
    assert salvaged.get("title") == "Parsed Doc"

    # 2. Outer text stripping and trailing comma removal
    raw_trailing = "Here is the result: {\"name\": \"Test\", \"items\": [1, 2, ], } hope that helps!"
    salvaged2 = salvage_json(raw_trailing)
    assert salvaged2.get("name") == "Test"
    assert salvaged2.get("items") == [1, 2]


@pytest.mark.unit
def test_validate_file_readiness() -> None:
    """Verify validate_pipeline file readiness checks."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(b"%PDF-1.4 test content")
        tmp_path = f.name

    try:
        report = validate_file_readiness(tmp_path)
        assert report["valid"] is True
        assert report["extension"] == ".pdf"
        assert report["size_bytes"] > 0
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    # Missing file
    report_missing = validate_file_readiness("non_existent_file.pdf")
    assert report_missing["valid"] is False
    assert "does not exist" in str(report_missing["error"])


@pytest.mark.unit
def test_skill_configuration_default() -> None:
    """Verify config.default.yaml presence and zero-fork schema."""
    config_path = Path(".agents/skills/paperless-document-pipeline/config.default.yaml")
    assert config_path.exists()
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    assert "paperless_base_url" in cfg
    assert "supported_extensions" in cfg
    assert ".pdf" in cfg["supported_extensions"]
