"""
Tests for AgentWikis Router and CLI engine.
Verifies discovery, scope triage, offline full-text extraction, and skill matching.
"""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import pytest

CLI_PATH = Path(".agents/skills/agentwikis-router/scripts/agentwikis_cli.py").resolve()
CORPUS_DIR = Path(r"D:\AgentWikis")


def run_cli(*args: str) -> tuple[int, str, str]:
    """Helper to execute agentwikis_cli in subprocess."""
    cmd = [sys.executable, str(CLI_PATH)] + list(args)
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return proc.returncode, proc.stdout, proc.stderr


@pytest.mark.unit
def test_cli_help() -> None:
    code, out, _ = run_cli("--help")
    assert code == 0
    assert "agentwikis_cli" in out
    assert "list-wikis" in out
    assert "scope" in out
    assert "match-skill" in out
    assert "search" in out
    assert "read-doc" in out
    assert "mcp-config" in out


@pytest.mark.unit
def test_list_wikis() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        out_file = Path(tmpdir) / "wikis.json"
        code, out, err = run_cli("list-wikis", "--category", "inference", "--output", str(out_file))
        assert code == 0
        assert out_file.exists()

        data = json.loads(out_file.read_text(encoding="utf-8"))
        assert "total" in data
        assert data["total"] > 0
        slugs = [w["slug"] for w in data["wikis"]]
        assert "vllm" in slugs or "llama-cpp" in slugs or "unsloth" in slugs


@pytest.mark.unit
def test_scope_known_and_unknown() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        out_file = Path(tmpdir) / "scope_hermes.json"
        code, out, err = run_cli("scope", "hermes", "--output", str(out_file))
        assert code == 0
        assert out_file.exists()

        data = json.loads(out_file.read_text(encoding="utf-8"))
        assert data["slug"] == "hermes"
        assert "covers" in data["scope"]
        assert "not_covered" in data["scope"]
        assert "current_as" in data["scope"]

        # Non-existent wiki
        err_out = Path(tmpdir) / "scope_unknown.json"
        code_err, _, err_msg = run_cli("scope", "non_existent_wiki_xyz", "--output", str(err_out))
        assert code_err != 0
        assert "not found in registry" in err_msg


@pytest.mark.unit
def test_match_skill_in_scope() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        out_file = Path(tmpdir) / "match_lora.json"
        code, out, _ = run_cli(
            "match-skill",
            "how to do LoRA fine-tuning with unsloth",
            "--limit",
            "3",
            "--output",
            str(out_file),
        )
        assert code == 0
        assert out_file.exists()

        data = json.loads(out_file.read_text(encoding="utf-8"))
        assert data["in_scope"] is True
        assert data["confidence"] >= 0.5
        top_wikis = [w["slug"] for w in data["recommended_wikis"]]
        assert "unsloth" in top_wikis
        top_skills = [s["name"] for s in data["recommended_agentwikis_skills"]]
        assert any("training" in s or "inference" in s for s in top_skills)


@pytest.mark.unit
def test_match_skill_local_workspace() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        out_file = Path(tmpdir) / "match_pocock.json"
        code, out, _ = run_cli(
            "match-skill",
            "Matt Pocock shoehorn type assertions",
            "--limit",
            "3",
            "--output",
            str(out_file),
        )
        assert code == 0
        assert out_file.exists()

        data = json.loads(out_file.read_text(encoding="utf-8"))
        assert data["in_scope"] is True
        assert "pocock-skills" in data["recommended_local_workspace_skills"]


@pytest.mark.unit
def test_match_skill_out_of_scope() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        out_file = Path(tmpdir) / "match_out.json"
        code, out, _ = run_cli(
            "match-skill",
            "how to bake sourdough bread in high altitude",
            "--limit",
            "3",
            "--output",
            str(out_file),
        )
        assert code == 0
        assert out_file.exists()

        data = json.loads(out_file.read_text(encoding="utf-8"))
        assert data["in_scope"] is False
        assert data["fallback_recommendation"] == "web_search"


@pytest.mark.unit
def test_search_and_confidence() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        out_file = Path(tmpdir) / "search.json"
        code, out, _ = run_cli(
            "search",
            "bot mode",
            "--wiki",
            "hermes",
            "--limit",
            "3",
            "--output",
            str(out_file),
        )
        assert code == 0
        assert out_file.exists()

        data = json.loads(out_file.read_text(encoding="utf-8"))
        assert data["total_matches"] > 0
        assert len(data["results"]) <= 3
        assert data["confident"] is True


@pytest.mark.unit
def test_read_doc_offline() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        out_file = Path(tmpdir) / "doc.md"
        code, out, _ = run_cli(
            "read-doc",
            "hermes/wiki/concepts/bot-mode.md",
            "--output",
            str(out_file),
        )
        assert code == 0
        assert out_file.exists()

        content = out_file.read_text(encoding="utf-8")
        assert len(content) > 100
        assert "Bot Mode" in content


@pytest.mark.unit
def test_mcp_config_generation() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        out_claude = Path(tmpdir) / "mcp_claude.json"
        code, _, _ = run_cli("mcp-config", "--client", "claude", "--output", str(out_claude))
        assert code == 0
        data_claude = json.loads(out_claude.read_text(encoding="utf-8"))
        assert "agentwikis" in data_claude["mcpServers"]
        assert "claude mcp add" in data_claude["cli_command"]

        out_ag = Path(tmpdir) / "mcp_ag.json"
        code, _, _ = run_cli("mcp-config", "--client", "antigravity", "--output", str(out_ag))
        assert code == 0
        data_ag = json.loads(out_ag.read_text(encoding="utf-8"))
        assert "agentwikis" in data_ag["mcpServers"]


@pytest.mark.unit
def test_slotted_frozen_domain_models_immutability() -> None:
    """Verify Rule 12 and Rule 43: Slotted & Frozen Dataclass Immutability."""
    sys.path.insert(0, str(Path(".agents/skills/agentwikis-router/scripts").resolve()))
    from agentwikis_engine import WikiScope, WikiEntity, SkillEntity, DocumentSlice

    scope = WikiScope(covers="LLM serving", not_covered="Pricing", current_as="2026-03")
    assert scope.covers == "LLM serving"

    # Rule 43: Direct attribute assignment assertion
    with pytest.raises((AttributeError, TypeError)):
        scope.covers = "Mutated"  # type: ignore

    entity = WikiEntity(
        slug="vllm",
        title="vLLM",
        description="High-throughput inference",
        category="inference",
        tags=("llm", "serving"),
        scope=scope,
        document_count=45,
        last_updated="2026-03-01",
        raw_base="https://agentwikis.com/raw/vllm",
        html_base="https://agentwikis.com/wiki/vllm",
        xl_document_count=10,
    )
    assert entity.slug == "vllm"
    assert entity.document_count == 45

    with pytest.raises((AttributeError, TypeError)):
        entity.document_count = 99  # type: ignore

    doc_slice = DocumentSlice(
        wiki_slug="vllm",
        relative_path="wiki/index.md",
        title="vLLM Master Index",
        content="# vLLM Documentation",
    )
    with pytest.raises((AttributeError, TypeError)):
        doc_slice.content = "New content"  # type: ignore


@pytest.mark.unit
def test_validate_contract_cli() -> None:
    """Verify Open Data Contract (ODCS) validation via CLI."""
    contract_path = Path(".agents/skills/agentwikis-router/contracts/agentwikis_contract.yaml").resolve()
    assert contract_path.exists(), f"Contract file must exist at {contract_path}"

    with tempfile.TemporaryDirectory() as tmpdir:
        out_file = Path(tmpdir) / "contract_report.json"
        code, out, err = run_cli(
            "validate-contract",
            "--contract",
            str(contract_path),
            "--output",
            str(out_file),
        )
        assert code == 0, f"Contract validation failed: {err}\n{out}"
        assert out_file.exists()

        data = json.loads(out_file.read_text(encoding="utf-8"))
        assert data["is_compliant"] is True
        assert data["total_entities_checked"] >= 62
        assert data["violations_count"] == 0


@pytest.mark.unit
def test_quality_profile_cli() -> None:
    """Verify DAMA-DMBOK 6-dimension data quality profiling via CLI."""
    with tempfile.TemporaryDirectory() as tmpdir:
        out_json = Path(tmpdir) / "quality.json"
        code, out, err = run_cli("quality-profile", "--min-score", "85.0", "--output", str(out_json))
        assert code == 0, f"Quality profile failed: {err}\n{out}"
        assert out_json.exists()

        data = json.loads(out_json.read_text(encoding="utf-8"))
        assert data["passed"] is True
        assert data["overall_score"] >= 85.0
        dims = {d["dimension"]: d["score"] for d in data["dimensions"]}
        assert "Completeness" in dims
        assert "Accuracy" in dims
        assert "Consistency" in dims
        assert "Validity" in dims
        assert "Uniqueness" in dims
        assert "Timeliness" in dims

        # Test Markdown formatting
        out_md = Path(tmpdir) / "quality.md"
        code_md, _, _ = run_cli("quality-profile", "--min-score", "85.0", "--output", str(out_md))
        assert code_md == 0
        md_text = out_md.read_text(encoding="utf-8")
        assert "# AgentWikis 6-Dimension Data Quality Scorecard" in md_text
        assert "Overall Score" in md_text


@pytest.mark.unit
def test_engine_direct_medallion_pipeline() -> None:
    """Verify direct Python API of AgentWikisEngine across Medallion tiers."""
    sys.path.insert(0, str(Path(".agents/skills/agentwikis-router/scripts").resolve()))
    from agentwikis_engine import AgentWikisEngine

    engine = AgentWikisEngine()
    wikis, skills = engine.load_entities()
    assert len(wikis) >= 60
    assert len(skills) >= 20

    # Silver tier check
    hermes = wikis.get("hermes")
    assert hermes is not None
    assert hermes.category == "agents"
    assert "Hermes Agent" in hermes.scope.covers

    # Gold tier slice check
    slice_doc = engine.extract_document("hermes/README.md")
    assert slice_doc.wiki_slug == "hermes"
    assert len(slice_doc.content) > 50
    assert "Hermes" in slice_doc.title


@pytest.mark.unit
def test_context_pack_cli() -> None:
    """Verify context-pack CLI subcommand compiles token-bounded Markdown pack."""
    with tempfile.TemporaryDirectory() as tmpdir:
        out_file = Path(tmpdir) / "pack.md"
        code, out, err = run_cli(
            "context-pack",
            "how to serve models using vllm",
            "--max-tokens",
            "1000",
            "--output",
            str(out_file),
        )
        assert code == 0, f"context-pack CLI failed: {err}\n{out}"
        assert out_file.exists()

        content = out_file.read_text(encoding="utf-8")
        assert "# AgentWikis Context Pack" in content
        assert "vLLM" in content or "vllm" in content
        assert "## Provenance & Isnad Lineage" in content


