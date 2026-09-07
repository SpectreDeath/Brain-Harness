"""
Test suite for ai-file-analysis-agent skill.
Verifies pre-flight file validation, prompt grounding assembly, role profiles, and CLI operations.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

# Add scripts directory to sys.path for direct module import
SKILL_DIR = Path(__file__).resolve().parent.parent / ".agents" / "skills" / "ai-file-analysis-agent"
SCRIPTS_DIR = SKILL_DIR / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from file_agent_cli import (  # noqa: E402
    DEFAULT_GROUNDING_CONSTRAINTS,
    FileAnalysisEngine,
    FileAnalysisSession,
    FileValidationResult,
    GroundedPrompt,
    GroundingAuditReport,
    GroundingAuditor,
    GroundingCatalog,
    assemble_grounded_instructions,
    build_staged_payload,
    load_config,
    validate_target_file,
)


@pytest.mark.unit
def test_config_loading() -> None:
    """Verifies that default skill configuration loads and contains expected keys."""
    cfg = load_config()
    assert isinstance(cfg, dict)
    assert "allowed_extensions" in cfg
    assert ".pdf" in cfg["allowed_extensions"]
    assert cfg.get("max_direct_file_bytes") == 52428800
    assert cfg.get("default_model") == "gpt-4o"


@pytest.mark.unit
def test_validate_target_file_nonexistent(tmp_path: Path) -> None:
    """Verifies that missing files are rejected gracefully."""
    fake_file = tmp_path / "does_not_exist.txt"
    res = validate_target_file(str(fake_file))
    assert isinstance(res, FileValidationResult)
    assert not res.valid
    assert not res.direct_api_eligible
    assert "File not found" in (res.error or "")


@pytest.mark.unit
def test_validate_target_file_directory(tmp_path: Path) -> None:
    """Verifies that directory paths are rejected."""
    res = validate_target_file(str(tmp_path))
    assert not res.valid
    assert "not a regular file" in (res.error or "")


@pytest.mark.unit
def test_validate_target_file_unsupported_extension(tmp_path: Path) -> None:
    """Verifies that unapproved extensions are filtered out."""
    bad_file = tmp_path / "payload.exe"
    bad_file.write_bytes(b"binary payload")
    res = validate_target_file(str(bad_file))
    assert not res.valid
    assert "Unsupported file extension" in (res.error or "")


@pytest.mark.unit
def test_validate_target_file_supported_extensions(tmp_path: Path) -> None:
    """Verifies that approved extensions pass validation."""
    for ext in [".txt", ".csv", ".pdf", ".docx"]:
        test_file = tmp_path / f"sample{ext}"
        test_file.write_text("sample content", encoding="utf-8")
        res = validate_target_file(str(test_file))
        assert res.valid, f"Failed for extension {ext}"
        assert res.extension == ext
        assert res.direct_api_eligible
        assert res.error is None


@pytest.mark.unit
def test_validate_target_file_oversized(tmp_path: Path) -> None:
    """Verifies that files exceeding direct threshold are flagged for RAG triage."""
    large_file = tmp_path / "large_corpus.txt"
    large_file.write_text("A" * 100, encoding="utf-8")
    # Simulate a 50-byte direct limit
    res = validate_target_file(str(large_file), max_direct_bytes=50)
    assert res.valid
    assert not res.direct_api_eligible
    assert "route to RAG" in (res.error or "")


@pytest.mark.unit
def test_assemble_grounded_instructions_all_rules() -> None:
    """Verifies that all 10 grounding rules are included sequentially in instructions."""
    prompt = assemble_grounded_instructions()
    assert "You are an AI file analysis assistant." in prompt
    for idx, rule in enumerate(DEFAULT_GROUNDING_CONSTRAINTS, start=1):
        assert f"{idx}. {rule}" in prompt


@pytest.mark.unit
@pytest.mark.parametrize("role", ["research", "legal", "resume", "tabular"])
def test_assemble_grounded_instructions_roles(role: str) -> None:
    """Verifies that specialized role addenda are correctly appended."""
    prompt = assemble_grounded_instructions(role=role)
    assert f"Role: {role.capitalize()}" in prompt or role.upper() in prompt.upper()


@pytest.mark.unit
def test_build_staged_payload(tmp_path: Path) -> None:
    """Verifies that staged payload matches OpenAI responses input schema."""
    doc = tmp_path / "contract.docx"
    doc.write_text("Dummy Contract Text", encoding="utf-8")

    payload = build_staged_payload(
        file_path=str(doc),
        question="What is the liability cap?",
        role="legal",
        model="gpt-4o",
    )

    assert payload["model"] == "gpt-4o"
    assert "Role: Legal" in payload["instructions"]
    assert len(payload["input"]) == 1
    content = payload["input"][0]["content"]
    assert content[0]["text"] == "What is the liability cap?"
    assert content[1]["file_path"] == str(doc.resolve())


@pytest.mark.unit
def test_cli_validate_file_json(tmp_path: Path) -> None:
    """Verifies CLI execution of validate-file subcommand with --json flag."""
    sample = tmp_path / "data.csv"
    sample.write_text("id,val\n1,10\n", encoding="utf-8")

    cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "file_agent_cli.py"),
        "validate-file",
        str(sample),
        "--json",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
    out = json.loads(proc.stdout)
    assert out["valid"] is True
    assert out["extension"] == ".csv"
    assert out["direct_api_eligible"] is True


@pytest.mark.unit
def test_cli_assemble_prompt_json() -> None:
    """Verifies CLI execution of assemble-prompt subcommand."""
    cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "file_agent_cli.py"),
        "assemble-prompt",
        "--role",
        "research",
        "--json",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
    out = json.loads(proc.stdout)
    assert out["role"] == "research"
    assert "Research Assistant" in out["instructions"]


@pytest.mark.unit
def test_file_analysis_engine_session_creation(tmp_path: Path) -> None:
    """Verifies that FileAnalysisEngine sets up a valid stateful session."""
    doc = tmp_path / "paper.pdf"
    doc.write_text("Abstract and findings...", encoding="utf-8")

    engine = FileAnalysisEngine.default()
    session = engine.prepare_session(str(doc), role="research")

    assert isinstance(session, FileAnalysisSession)
    assert session.file_result.valid is True
    assert session.strategy == "direct_upload"
    assert session.model == "gpt-4o"
    assert session.turn_count == 0
    assert "Research Assistant" in session.prompt.instructions

    # Test turn payload creation
    payload = engine.create_turn_payload(session, "What was the sample size?")
    assert session.turn_count == 1
    assert payload["turn"] == 1
    assert payload["input"][0]["content"][0]["text"] == "What was the sample size?"


@pytest.mark.unit
def test_grounding_catalog_dynamic_roles() -> None:
    """Verifies that GroundingCatalog dynamically parses custom YAML roles."""
    custom_roles = {
        "bioinformatics": {
            "name": "Bioinformatics Auditor",
            "instructions": "Evaluate FASTA sequences and alignment scores strictly.",
        }
    }
    catalog = GroundingCatalog(roles_config=custom_roles)
    prompt = catalog.compile_prompt(role="bioinformatics")

    assert isinstance(prompt, GroundedPrompt)
    assert prompt.role == "bioinformatics"
    assert prompt.role_name == "Bioinformatics Auditor"
    assert "Bioinformatics Auditor" in prompt.instructions
    assert "Evaluate FASTA sequences" in prompt.instructions


@pytest.mark.unit
def test_grounding_auditor_insufficient_context() -> None:
    """Verifies that GroundingAuditor detects Rule 4 refusal statements."""
    response = "The provided file does not contain enough information to determine the quarterly revenue."
    report = GroundingAuditor.audit(response)

    assert isinstance(report, GroundingAuditReport)
    assert report.has_insufficient_context_refusal is True
    assert report.passed is True
    assert report.score >= 70.0


@pytest.mark.unit
def test_grounding_auditor_inferences_extracted() -> None:
    """Verifies that GroundingAuditor extracts [INFERENCE] tags and verifies formatting."""
    response = """
Here are the key takeaways:
- Finding 1: The study tested 40 participants.
- Finding 2: [INFERENCE] The sample size may be underpowered for subtle effect detection.
"""
    report = GroundingAuditor.audit(response)

    assert report.passed is True
    assert report.has_structural_formatting is True
    assert len(report.inferences_detected) == 1
    assert "underpowered for subtle effect detection" in report.inferences_detected[0]


@pytest.mark.unit
def test_grounding_auditor_empty_response() -> None:
    """Verifies that empty model responses fail audit with zero score."""
    report = GroundingAuditor.audit("   ")
    assert report.passed is False
    assert report.score == 0.0


@pytest.mark.unit
def test_cli_audit_response_json() -> None:
    """Verifies CLI execution of audit-response subcommand with --json flag."""
    cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "file_agent_cli.py"),
        "audit-response",
        "--text",
        "- Metric A was 42. - Metric B was 100.",
        "--json",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
    out = json.loads(proc.stdout)
    assert out["passed"] is True
    assert out["score"] >= 80.0
    assert out["has_structural_formatting"] is True
