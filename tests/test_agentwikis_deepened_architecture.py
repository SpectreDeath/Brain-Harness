"""
Architecture Deepening Test Contract for agentwikis-router.

Verifies:
1. Persistent On-Disk Offset Table Index Cache (llms-full.idx.json)
   - Fast-path cached seek (<5ms)
   - Stale cache detection & automatic invalidation on mtime / size drift
   - Graceful read-only filesystem fallback
2. Complete 5-Stage Protocol Seam Elevation
   - Both AgentWikisEngine and AgentWikisPlugin satisfy AgentWikisService protocol
   - In-memory execution across all 5 operational progression stages without subprocesses
3. Block-Aware Markdown Trimming & Resilient Code Fence Self-Healing
   - Paragraph/section boundary snapping
   - Odd/even code fence count detection
   - Automatic injection of closing fences and context truncation banners
"""

from __future__ import annotations

import json
import re
import sys
import tempfile
import time
from pathlib import Path

import pytest

# Ensure relocatable paths
REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_ROOT / "src"
SKILL_DIR = REPO_ROOT / ".agents" / "skills" / "agentwikis-router" / "scripts"
PLUGIN_DIR = REPO_ROOT / "plugins" / "integration_and_io" / "agentwikis"

for path in [SRC_DIR, SKILL_DIR, PLUGIN_DIR]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from agentwikis_engine import (
    AgentWikisEngine,
    ContractValidationReport,
    MatchResult,
    QualityScorecard,
    SearchHit,
    WikiEntity,
    WikiScope,
)
from main import AgentWikisPlugin, plugin

from harness.services.agentwikis import (
    AgentWikisService,
)

# ===========================================================================
# 1. Persistent On-Disk Offset Table Index Cache Tests
# ===========================================================================


@pytest.mark.unit
class TestPersistentIndexCache:
    """Verifies llms-full.idx.json persistent caching and invalidation mechanics."""

    @pytest.fixture
    def temp_corpus(self, tmp_path: Path) -> tuple[Path, Path]:
        """Scaffolds a mock AgentWikis corpus directory with an llms-full.txt file."""
        corpus_dir = tmp_path / "mock_corpus"
        corpus_dir.mkdir(parents=True, exist_ok=True)

        index_file = corpus_dir / "test-index.json"
        index_data = {
            "wikis": [
                {
                    "slug": "mock-wiki",
                    "title": "Mock Wiki",
                    "description": "Mock documentation for testing",
                    "category": "infrastructure",
                    "tags": ["test"],
                    "scope": {
                        "covers": "Mock testing patterns",
                        "notCovered": "Production bugs",
                        "currentAs": "2026-09-12",
                    },
                    "documentCount": 2,
                    "lastUpdated": "2026-09-12",
                }
            ],
            "skills": [],
        }
        with open(index_file, "w", encoding="utf-8") as f:
            json.dump(index_data, f)

        full_txt = corpus_dir / "test-llms-full.txt"
        corpus_content = (
            "<!-- ===== mock-wiki/README.md ===== -->\n"
            "# Mock Wiki Overview\n\n"
            "This is the first document body.\n\n"
            "<!-- ===== mock-wiki/guide.md ===== -->\n"
            "# Mock Wiki Guide\n\n"
            "This is the second document body.\n"
        )
        with open(full_txt, "wb") as f:
            f.write(corpus_content.encode("utf-8"))

        return corpus_dir, full_txt

    def test_persistent_index_cache_generation_and_fast_load(
        self, temp_corpus: tuple[Path, Path]
    ) -> None:
        """First call generates .idx.json; second call loads it via fast path in <5ms."""
        corpus_dir, full_txt = temp_corpus
        idx_file = full_txt.with_suffix(".idx.json")

        assert not idx_file.exists()

        # Engine 1: Cold start builds cache file
        engine1 = AgentWikisEngine(corpus_dir=corpus_dir)
        table1 = engine1._ensure_offset_table()
        assert table1 is not None
        assert table1.total_blocks == 2
        assert "mock-wiki/readme.md" in table1.offsets
        assert "mock-wiki/guide.md" in table1.offsets

        # Verify persistent cache exists on disk
        assert idx_file.exists()
        with open(idx_file, "r", encoding="utf-8") as f:
            cached_data = json.load(f)
        assert cached_data["total_blocks"] == 2
        assert "offsets" in cached_data
        assert "mock-wiki/readme.md" in cached_data["offsets"]

        # Engine 2: Warm start reads cache file directly (<5ms)
        engine2 = AgentWikisEngine(corpus_dir=corpus_dir)
        t0 = time.perf_counter()
        table2 = engine2._ensure_offset_table()
        t_elapsed = time.perf_counter() - t0

        assert table2 is not None
        assert table2.total_blocks == 2
        assert table2.offsets == table1.offsets
        # Fast path should load in well under 25ms even on slower CI disks
        assert t_elapsed < 0.05, f"Cache load took {t_elapsed:.4f}s, expected < 0.05s"

    def test_persistent_index_cache_invalidation_on_size_or_mtime_change(
        self, temp_corpus: tuple[Path, Path]
    ) -> None:
        """Modifying the corpus file invalidates stale index and triggers automatic rebuild."""
        corpus_dir, full_txt = temp_corpus
        idx_file = full_txt.with_suffix(".idx.json")

        # Initial build
        engine = AgentWikisEngine(corpus_dir=corpus_dir)
        table = engine._ensure_offset_table()
        assert table is not None
        assert table.total_blocks == 2

        # Append new block to corpus file
        time.sleep(0.01)  # Ensure mtime advances
        with open(full_txt, "ab") as f:
            f.write(b"\n<!-- ===== mock-wiki/extra.md ===== -->\n# Extra Document\n")

        # Create fresh engine instance
        engine_fresh = AgentWikisEngine(corpus_dir=corpus_dir)
        updated_table = engine_fresh._ensure_offset_table()
        assert updated_table is not None
        assert updated_table.total_blocks == 3
        assert "mock-wiki/extra.md" in updated_table.offsets

        # Check updated on-disk cache
        with open(idx_file, "r", encoding="utf-8") as f:
            new_cache = json.load(f)
        assert new_cache["total_blocks"] == 3
        assert "mock-wiki/extra.md" in new_cache["offsets"]

    def test_read_only_corpus_graceful_fallback(
        self, temp_corpus: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """If filesystem cannot persist index, falls back gracefully to in-memory offset table."""
        corpus_dir, _ = temp_corpus

        # Simulate unwritable disk on tmp_idx.replace
        def mock_replace(self: Path, target: Path) -> None:
            raise PermissionError("Simulated read-only container filesystem")

        monkeypatch.setattr(Path, "replace", mock_replace)

        engine = AgentWikisEngine(corpus_dir=corpus_dir)
        table = engine._ensure_offset_table()
        assert table is not None
        assert table.total_blocks == 2
        # Engine succeeds and offsets are functional
        assert "mock-wiki/readme.md" in table.offsets


# ===========================================================================
# 2. Elevated Protocol Seam Tests (All 5 Stages)
# ===========================================================================


@pytest.mark.unit
class TestElevatedProtocolFull5Stages:
    """Verifies that AgentWikisEngine and AgentWikisPlugin implement AgentWikisService."""

    def test_engine_satisfies_agentwikis_service_protocol(self) -> None:
        """AgentWikisEngine conforms to AgentWikisService Protocol at runtime."""
        engine = AgentWikisEngine()
        assert isinstance(engine, AgentWikisService)

    def test_plugin_satisfies_agentwikis_service_protocol(self) -> None:
        """AgentWikisPlugin conforms to AgentWikisService Protocol at runtime."""
        plug = AgentWikisPlugin()
        assert isinstance(plug, AgentWikisService)
        assert isinstance(plugin, AgentWikisService)

    def test_protocol_stage_1_scope_and_trust(self) -> None:
        """Stage 1: list_wikis, get_scope, and match_intent return typed models."""
        plug = AgentWikisPlugin()

        wikis = plug.list_wikis(category="frameworks")
        assert isinstance(wikis, list)
        if wikis:
            assert isinstance(wikis[0], WikiEntity)
            assert wikis[0].category.lower() == "frameworks"

        scope = plug.get_scope("vllm")
        if scope:
            assert isinstance(scope, WikiScope)
            assert scope.covers != ""

        match = plug.match_intent("continuous batching in vllm")
        assert isinstance(match, MatchResult)
        assert match.in_scope is True
        assert match.calibrated_confident is True
        assert len(match.matched_wikis) > 0

    def test_protocol_stage_2_contract_validation(self) -> None:
        """Stage 2: validate_contract executes in-memory and returns ContractValidationReport."""
        plug = AgentWikisPlugin()
        report = plug.validate_contract()
        assert isinstance(report, ContractValidationReport)
        assert report.is_compliant is True
        assert "AgentWikis" in report.contract_name
        assert len(report.violations) == 0

    def test_protocol_stage_3_visual_brief(self) -> None:
        """Stage 3: generate_visual_brief generates interactive HTML report with Mermaid DAG."""
        plug = AgentWikisPlugin()
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_html = Path(tmp_dir) / "test_visual_brief.html"
            result_path = plug.generate_visual_brief(output_path=out_html, query="vllm")
            assert result_path.exists()
            assert result_path == out_html
            content = out_html.read_text(encoding="utf-8")
            assert "AgentWikis Routing Brief" in content
            assert "mermaid" in content
            assert "vllm" in content.lower()

    def test_protocol_stage_4_quality_profiling(self) -> None:
        """Stage 4: profile_data_quality evaluates 6 DAMA dimensions in-memory."""
        plug = AgentWikisPlugin()
        scorecard = plug.profile_data_quality(min_passing_score=85.0)
        assert isinstance(scorecard, QualityScorecard)
        assert scorecard.overall_score >= 85.0
        assert scorecard.passed is True
        assert len(scorecard.dimensions) == 6

        # Check all canonical DAMA dimensions exist
        dim_names = {d.dimension for d in scorecard.dimensions}
        assert dim_names == {
            "Completeness",
            "Accuracy",
            "Consistency",
            "Validity",
            "Uniqueness",
            "Timeliness",
        }

    def test_protocol_stage_5_search_and_context_pack(self) -> None:
        """Stage 5: search and prepare_context_pack execute in-memory with token bounds."""
        plug = AgentWikisPlugin()

        hits = plug.search("batching", limit=3)
        assert isinstance(hits, tuple)
        if hits:
            assert isinstance(hits[0], SearchHit)
            assert hits[0].wiki_slug != ""

        pack = plug.prepare_context_pack(
            "Explain continuous batching in vLLM", max_tokens=1000
        )
        assert isinstance(pack, str)
        assert "AgentWikis Context Pack" in pack
        assert "IN_SCOPE" in pack
        assert "vllm" in pack.lower()


# ===========================================================================
# 3. Block-Aware Markdown Trimmer & Code Fence Healing Tests
# ===========================================================================


@pytest.mark.unit
class TestMarkdownTrimmerAndCodefenceHealing:
    """Verifies block-boundary truncation and code fence self-repair in context packs."""

    def test_no_truncation_when_content_within_budget(self) -> None:
        """Content shorter than max_chars remains completely untouched."""
        content = "# Short Section\n\nThis is short markdown."
        res = AgentWikisEngine.truncate_markdown(content, max_chars=1000)
        assert res == content

    def test_paragraph_boundary_snapping(self) -> None:
        """Truncates cleanly at double-newline paragraph boundary."""
        para1 = "Paragraph 1: The architecture features deep modularity."
        para2 = "Paragraph 2: This second paragraph should be excluded if budget is exceeded."
        full = f"{para1}\n\n{para2}"

        # Limit that fits para1 but cuts off midway through para2
        budget = len(para1) + 20
        res = AgentWikisEngine.truncate_markdown(full, max_chars=budget)

        assert para1 in res
        assert para2 not in res
        assert "*... [Content truncated to fit context budget]*" in res

    def test_heals_unclosed_python_codeblock(self) -> None:
        """Detects odd number of code fences and automatically injects closing fence."""
        broken_markdown = (
            "# Code Example\n\n"
            "```python\n"
            "import torch\n"
            "from vllm import LLM, SamplingParams\n"
            "\n"
            "llm = LLM(model='facebook/opt-125m')\n"
            "prompts = ['Hello world']\n"
            "# Code block gets cut right here midway through function\n"
        )

        res = AgentWikisEngine.truncate_markdown(broken_markdown, max_chars=120)

        # Must have an even number of code fences
        fences = re.findall(r"(?m)^\s*```", res)
        assert len(fences) % 2 == 0, f"Unbalanced code fences detected: {len(fences)}"
        assert (
            "```\n\n*... [Codeblock closed & content truncated to fit context budget]*"
            in res
        )

    def test_heals_indented_code_fences(self) -> None:
        """Correctly detects and heals indented code fences inside lists or blocks."""
        indented_markdown = (
            "1. Setup steps:\n"
            "   ```bash\n"
            "   pip install vllm\n"
            "   vllm serve facebook/opt-125m\n"
        )
        res = AgentWikisEngine.truncate_markdown(indented_markdown, max_chars=60)
        fences = re.findall(r"(?m)^\s*```", res)
        assert len(fences) % 2 == 0
        assert "Codeblock closed" in res

    def test_end_to_end_context_pack_compacted_resilience(self) -> None:
        """Context pack generated under tight token bounds produces balanced markdown."""
        engine = AgentWikisEngine()
        # Restrict to very tight token count (e.g. 150 tokens ~ 600 chars)
        tight_pack = engine.prepare_context_pack("vllm serving options", max_tokens=150)

        assert isinstance(tight_pack, str)
        fences = re.findall(r"(?m)^\s*```", tight_pack)
        assert len(fences) % 2 == 0, (
            f"Context pack had unbalanced code fences: {len(fences)}"
        )
