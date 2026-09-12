"""
Comprehensive Capability & Evaluation Test Suite for agentwikis-router.

Verifies:
1. Stage 1: Scope & Trust Triage (intent mapping, boundary adherence, calibrated abstention ~94%)
2. Stage 2: Contract-First Ingestion & Medallion Pipeline (ODCS schema, slotted/frozen immutability Rule 12/43)
3. Stage 3: Visual Brief & Topology Review (Mermaid DAG, blast radius matrix, HTML generation)
4. Stage 4: 6-Dimension Data Quality Gating (DAMA dimensions, threshold enforcement, scorecard formats)
5. Stage 5: Zero-Latency Slice Retrieval & Skill Dispatch (O(1) seek <50ms, section slicing, context packs, MCP)
6. Google 2x2 Continuous Evaluation Benchmark Suite (DOMINANT_UPLIFT, accuracy >=15%, token savings >=30%)
7. Zero-Fork Configuration & Platform Skill Craft Standards (config.default.yaml, SkillValidator)
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import pytest
import yaml

# Ensure skill scripts directory is on sys.path
SKILL_ROOT = Path(".agents/skills/agentwikis-router").resolve()
SCRIPTS_DIR = SKILL_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from agentwikis_engine import (
    AgentWikisEngine,
    ContractValidationReport,
    DocumentSlice,
    QualityScorecard,
    WikiEntity,
    WikiScope,
)
from run_eval_suite import BenchmarkRunner, EvalQuadrant

CLI_PATH = SCRIPTS_DIR / "agentwikis_cli.py"


def run_cli(*args: str) -> tuple[int, str, str]:
    """Helper to execute agentwikis_cli subprocess with UTF-8 encoding."""
    cmd = [sys.executable, str(CLI_PATH)] + list(args)
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return proc.returncode, proc.stdout, proc.stderr


@pytest.fixture
def engine() -> AgentWikisEngine:
    """Fixture providing initialized AgentWikisEngine."""
    return AgentWikisEngine()


# ---------------------------------------------------------------------------
# Stage 1: Scope & Trust Triage Tests
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestStage1ScopeAndTrustTriage:
    """Verify Stage 1 intent classification, negative boundaries, and calibrated abstention."""

    def test_in_scope_inference_matching(self, engine: AgentWikisEngine) -> None:
        """Inference queries match vllm, unsloth, or llama-cpp with high confidence."""
        match = engine.match_intent(
            "how to configure continuous batching and chunked prefill in vLLM"
        )
        assert match.in_scope is True
        assert match.calibrated_confident is True
        assert len(match.matched_wikis) > 0
        top_slugs = [w.slug for w in match.matched_wikis]
        assert "vllm" in top_slugs

    def test_in_scope_agent_matching(self, engine: AgentWikisEngine) -> None:
        """Agent queries match hermes or openclaw."""
        match = engine.match_intent("Hermes bot mode teammate rooms")
        assert match.in_scope is True
        assert match.calibrated_confident is True
        top_slugs = [w.slug for w in match.matched_wikis]
        assert "hermes" in top_slugs

    def test_out_of_scope_calibrated_abstention(self, engine: AgentWikisEngine) -> None:
        """Unrelated domain queries force immediate abstention and fallback recommendation."""
        match = engine.match_intent(
            "how to bake sourdough bread in high altitude with wild yeast"
        )
        assert match.in_scope is False
        assert match.calibrated_confident is False
        assert match.fallback_recommendation == "web_search"
        assert len(match.matched_wikis) == 0

    def test_negative_boundary_scope_not_covered(
        self, engine: AgentWikisEngine
    ) -> None:
        """Query touching explicit scope.notCovered flags the concept and abstains cleanly."""
        # Uniswap v3 live exchange rates / pricing is not covered
        match = engine.match_intent(
            "What is the live exchange rate for Solana on Uniswap v3 right now?"
        )
        assert match.in_scope is False
        assert match.calibrated_confident is False
        assert match.fallback_recommendation == "web_search"
        assert match.rejection_reason is not None

    def test_local_workspace_skill_recommendation(self) -> None:
        """CLI match-skill routes to local workspace skills when applicable."""
        with tempfile.TemporaryDirectory() as tmpdir:
            out_file = Path(tmpdir) / "match.json"
            code, _, _ = run_cli(
                "match-skill",
                "Matt Pocock shoehorn type assertion migration",
                "--output",
                str(out_file),
            )
            assert code == 0
            assert out_file.exists()
            data = json.loads(out_file.read_text(encoding="utf-8"))
            assert data["in_scope"] is True
            assert "pocock-skills" in data["recommended_local_workspace_skills"]

    def test_scope_cli_valid_and_invalid(self) -> None:
        """CLI scope returns declared boundaries or rejects invalid wiki."""
        with tempfile.TemporaryDirectory() as tmpdir:
            out_valid = Path(tmpdir) / "scope_vllm.json"
            code, _, _ = run_cli("scope", "vllm", "--output", str(out_valid))
            assert code == 0
            data = json.loads(out_valid.read_text(encoding="utf-8"))
            assert data["slug"] == "vllm"
            assert len(data["scope"]["covers"]) > 0

            out_invalid = Path(tmpdir) / "scope_bad.json"
            code_bad, _, err = run_cli(
                "scope", "non_existent_wiki_xyz", "--output", str(out_invalid)
            )
            assert code_bad != 0
            assert "not found in registry" in err


# ---------------------------------------------------------------------------
# Stage 2: Contract-First Ingestion & Medallion Pipeline Tests
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestStage2ContractFirstMedallion:
    """Verify Open Data Contract compliance and Rule 12/43 domain immutability."""

    def test_odcs_contract_validation_success(self, engine: AgentWikisEngine) -> None:
        """Production corpus passes Open Data Contract with zero violations."""
        contract_path = SKILL_ROOT / "contracts" / "agentwikis_contract.yaml"
        assert contract_path.exists()
        report = engine.validate_contract(contract_path)

        assert isinstance(report, ContractValidationReport)
        assert report.is_compliant is True
        assert report.total_entities_checked >= 62
        assert len(report.violations) == 0

    def test_odcs_contract_violation_detection_on_defect(
        self, engine: AgentWikisEngine, tmp_path: Path
    ) -> None:
        """Contract validator catches missing required fields."""
        defective_contract = {
            "info": {"title": "Defective Contract", "version": "1.0.0"},
            "models": {
                "wikis": {
                    "required": ["slug", "title", "non_existent_mandatory_field"]
                },
                "skills": {"required": ["name"]},
            },
        }
        contract_file = tmp_path / "defect_contract.yaml"
        contract_file.write_text(yaml.dump(defective_contract), encoding="utf-8")

        report = engine.validate_contract(contract_file)
        assert report.is_compliant is False
        assert len(report.violations) > 0
        assert any(
            "non_existent_mandatory_field" in v.field_name for v in report.violations
        )

    def test_slotted_frozen_immutability_rule_12_rule_43(self) -> None:
        """Domain entities enforce slots=True and frozen=True immutability via attribute assignment."""
        scope = WikiScope(covers="Serving", not_covered="Pricing", current_as="2026-03")
        with pytest.raises((AttributeError, TypeError)):
            scope.covers = "mutated"  # type: ignore

        entity = WikiEntity(
            slug="test-wiki",
            title="Test Wiki",
            description="Test desc",
            category="test",
            tags=("test",),
            scope=scope,
            document_count=10,
            last_updated="2026-03-01",
            raw_base="https://agentwikis.com/raw/test",
            html_base="https://agentwikis.com/wiki/test",
        )
        with pytest.raises((AttributeError, TypeError)):
            entity.document_count = 20  # type: ignore

        doc_slice = DocumentSlice(
            wiki_slug="test",
            relative_path="README.md",
            title="Title",
            content="Content",
        )
        with pytest.raises((AttributeError, TypeError)):
            doc_slice.content = "New"  # type: ignore

    def test_lakehouse_caching(self, engine: AgentWikisEngine) -> None:
        """Entities are cached in memory after first load to avoid redundant disk I/O."""
        wikis1, skills1 = engine.load_entities()
        wikis2, skills2 = engine.load_entities()
        assert wikis1 is wikis2
        assert skills1 is skills2


# ---------------------------------------------------------------------------
# Stage 3: Visual Brief & Topology Review Tests
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestStage3VisualBriefAndTopology:
    """Verify Stage 3 Visual Brief generation, Mermaid DAG, and blast radius table."""

    def test_generate_visual_brief_creates_valid_html(
        self, engine: AgentWikisEngine, tmp_path: Path
    ) -> None:
        """generate_visual_brief writes self-contained HTML with Mermaid DAG and table."""
        out_html = tmp_path / "test_brief.html"
        brief_path = engine.generate_visual_brief(
            output_path=out_html,
            query="how to serve models with vLLM",
            wiki_slug="vllm",
        )
        assert brief_path.exists()
        content = brief_path.read_text(encoding="utf-8")

        # HTML Structure assertions
        assert "<!DOCTYPE html>" in content
        assert "AgentWikis Hybrid Topology & Routing Brief" in content
        assert "mermaid.min.js" in content
        assert "graph TD" in content
        assert "Interactive Blast Radius Matrix" in content
        assert "vLLM" in content
        assert "vllm" in content
        assert "badge-in-scope" in content

    def test_visual_brief_cli_subcommand(self, tmp_path: Path) -> None:
        """CLI visual-brief generates file and exits 0."""
        out_file = tmp_path / "cli_brief.html"
        code, out, err = run_cli(
            "visual-brief",
            "--output",
            str(out_file),
            "--query",
            "Hermes bot mode",
            "--wiki",
            "hermes",
        )
        assert code == 0, f"CLI visual-brief failed: {err}\n{out}"
        assert out_file.exists()
        assert "Success! Visual Brief generated:" in out


# ---------------------------------------------------------------------------
# Stage 4: 6-Dimension Quality Gating Tests
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestStage4QualityGating:
    """Verify DAMA-DMBOK 6-dimension data quality profiling across the corpus."""

    def test_dama_quality_profile_metrics(self, engine: AgentWikisEngine) -> None:
        """Evaluates Accuracy, Completeness, Consistency, Timeliness, Validity, Uniqueness."""
        scorecard = engine.profile_data_quality(min_passing_score=85.0)

        assert isinstance(scorecard, QualityScorecard)
        assert scorecard.passed is True
        assert scorecard.overall_score >= 85.0

        dim_names = {d.dimension for d in scorecard.dimensions}
        assert dim_names == {
            "Completeness",
            "Accuracy",
            "Consistency",
            "Validity",
            "Uniqueness",
            "Timeliness",
        }
        # Assert each dimension achieves baseline threshold
        for d in scorecard.dimensions:
            assert d.score >= 70.0, (
                f"Dimension {d.dimension} failed threshold: {d.score}"
            )

    def test_dama_quality_markdown_scorecard(self, engine: AgentWikisEngine) -> None:
        """Markdown scorecard formats clean diagnostic table."""
        scorecard = engine.profile_data_quality()
        md = scorecard.generate_markdown()
        assert "# AgentWikis 6-Dimension Data Quality Scorecard" in md
        assert "**Overall Score**:" in md
        assert "| **Completeness** |" in md
        assert "| **Accuracy** |" in md
        assert "✓ PASS" in md

    def test_quality_profile_cli_formats(self, tmp_path: Path) -> None:
        """CLI quality-profile generates valid JSON and Markdown outputs."""
        out_json = tmp_path / "q.json"
        code, _, _ = run_cli(
            "quality-profile", "--min-score", "85.0", "--output", str(out_json)
        )
        assert code == 0
        data = json.loads(out_json.read_text(encoding="utf-8"))
        assert data["passed"] is True
        assert data["overall_score"] >= 85.0

        out_md = tmp_path / "q.md"
        code_md, _, _ = run_cli(
            "quality-profile", "--min-score", "85.0", "--output", str(out_md)
        )
        assert code_md == 0
        assert "# AgentWikis 6-Dimension Data Quality Scorecard" in out_md.read_text(
            encoding="utf-8"
        )


# ---------------------------------------------------------------------------
# Stage 5: Zero-Latency Slice Retrieval & Skill Dispatch Tests
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestStage5SliceRetrievalAndDispatch:
    """Verify O(1) byte-offset seek, section slicing, context packing, and MCP."""

    def test_byte_offset_seeking_sub_50ms(self, engine: AgentWikisEngine) -> None:
        """Extracting document slice from llms-full.txt via byte offset executes in <50ms."""
        offset_table = engine._ensure_offset_table()
        if offset_table:
            assert offset_table.total_blocks > 100

            t0 = time.perf_counter()
            doc = engine.extract_document("hermes/wiki/concepts/bot-mode.md")
            elapsed_ms = (time.perf_counter() - t0) * 1000

            assert doc is not None
            assert doc.wiki_slug == "hermes"
            assert "Bot Mode" in doc.content
            assert doc.source_isnad == "local_llms_full_txt"
            assert elapsed_ms < 50.0

    def test_section_heading_slicing(self, engine: AgentWikisEngine) -> None:
        """Extracting with section_heading slices exact markdown section."""
        doc = engine.extract_document(
            "hermes/wiki/concepts/bot-mode.md",
            section_heading="Bot Mode & Teammate Rooms",
        )
        assert doc is not None
        assert doc.section == "Bot Mode & Teammate Rooms"
        assert "Bot Mode" in doc.content

    def test_batch_extract(self, engine: AgentWikisEngine) -> None:
        """batch_extract retrieves multiple slices accurately."""
        specs = [
            ("hermes/README.md", None),
            ("vllm/README.md", None),
        ]
        slices = engine.batch_extract(specs)
        assert len(slices) == 2
        assert slices[0].wiki_slug == "hermes"
        assert slices[1].wiki_slug == "vllm"

    def test_context_pack_in_scope_budget_bounds(
        self, engine: AgentWikisEngine
    ) -> None:
        """prepare_context_pack bounds token budget and cites isnad provenance."""
        pack = engine.prepare_context_pack(
            "how to serve models with vLLM", max_tokens=1000
        )
        assert "# AgentWikis Context Pack" in pack
        assert "vllm" in pack.lower()
        assert "## Provenance & Isnad Lineage" in pack
        # 1000 tokens ≈ max 4000-5000 chars
        assert len(pack) <= 5500

    def test_context_pack_out_of_scope_graceful_rejection(
        self, engine: AgentWikisEngine
    ) -> None:
        """prepare_context_pack for out-of-scope tasks returns clean rejection message."""
        pack = engine.prepare_context_pack(
            "how to bake sourdough bread in high altitude"
        )
        assert "Out of Scope" in pack
        assert "sourdough bread" in pack

    def test_mcp_config_cli_formats(self, tmp_path: Path) -> None:
        """CLI mcp-config generates valid config files for antigravity and claude."""
        out_ag = tmp_path / "mcp_ag.json"
        code, _, _ = run_cli(
            "mcp-config", "--client", "antigravity", "--output", str(out_ag)
        )
        assert code == 0
        data_ag = json.loads(out_ag.read_text(encoding="utf-8"))
        assert "agentwikis" in data_ag["mcpServers"]

        out_cl = tmp_path / "mcp_cl.json"
        code_cl, _, _ = run_cli(
            "mcp-config", "--client", "claude", "--output", str(out_cl)
        )
        assert code_cl == 0
        data_cl = json.loads(out_cl.read_text(encoding="utf-8"))
        assert "claude mcp add" in data_cl["cli_command"]


# ---------------------------------------------------------------------------
# Google 2x2 Continuous Evaluation Benchmark Suite Tests
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestContinuousEvaluationSuite:
    """Verify Google 2x2 continuous evaluation matrix and uplift calculations."""

    def test_benchmark_runner_all_cases_pass_dominant_uplift(
        self, engine: AgentWikisEngine
    ) -> None:
        """BenchmarkRunner executes all 4 evaluation cases and passes DOMINANT_UPLIFT."""
        runner = BenchmarkRunner(engine=engine)
        report = runner.run_suite()

        assert report.total_cases == 4
        assert report.passed_cases == 4
        assert report.passed_gate is True
        assert report.overall_quadrant == EvalQuadrant.DOMINANT_UPLIFT
        assert report.avg_accuracy_uplift_pct >= 15.0
        assert report.avg_token_efficiency_uplift_pct >= 30.0

        case_map = {c.case_id: c for c in report.case_results}
        assert "eval_001_scope_boundary_abstention" in case_map
        assert "eval_002_offline_slice_extraction" in case_map
        assert "eval_003_open_data_contract_validation" in case_map
        assert "eval_004_dama_quality_profiling" in case_map

        # All 4 cases must be in DOMINANT_UPLIFT
        for cid, case_res in case_map.items():
            assert case_res.quadrant == EvalQuadrant.DOMINANT_UPLIFT, (
                f"Case {cid} failed quadrant: {case_res.quadrant}"
            )
            assert case_res.passed is True

    def test_run_eval_suite_script_cli(self, tmp_path: Path) -> None:
        """run_eval_suite.py CLI runs and generates markdown report with code 0."""
        out_report = tmp_path / "eval_report.md"
        cmd = [
            sys.executable,
            str(SCRIPTS_DIR / "run_eval_suite.py"),
            "--output",
            str(out_report),
        ]
        proc = subprocess.run(
            cmd, capture_output=True, text=True, encoding="utf-8", check=False
        )
        assert proc.returncode == 0, (
            f"run_eval_suite failed: {proc.stderr}\n{proc.stdout}"
        )
        assert out_report.exists()
        text = out_report.read_text(encoding="utf-8")
        assert "DOMINANT_UPLIFT" in text
        assert "eval_001_scope_boundary_abstention" in text


# ---------------------------------------------------------------------------
# Zero-Fork Configuration & Platform Skill Craft Standards
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestZeroForkConfigAndHygiene:
    """Verify config.default.yaml precedence and Harness SkillValidator compliance."""

    def test_zero_fork_config_default_schema(self) -> None:
        """config.default.yaml defines operational budgets and timeouts."""
        cfg_path = SKILL_ROOT / "config.default.yaml"
        assert cfg_path.exists()
        with open(cfg_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)

        assert "corpus_dir" in cfg
        assert "token_budget_limit" in cfg
        assert "min_quality_score" in cfg
        assert "confidence_floor" in cfg
        assert "supported_clients" in cfg
        assert cfg["min_quality_score"] >= 80.0

    def test_platform_skill_validator_compliance(self) -> None:
        """SkillValidator passes 100% on agentwikis-router."""
        sys.path.insert(0, str(Path("src").resolve()))
        from harness.creator.skills import SkillValidator

        report = SkillValidator.validate(SKILL_ROOT)
        assert report.valid is True, (
            f"SkillValidator failed: {[c.message for c in report.checks if not c.passed]}"
        )
        # Ensure all checks passed
        for check in report.checks:
            assert check.passed is True, f"Check failed: {check.name} - {check.message}"
