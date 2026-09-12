"""
Executable Test Cases for Real-World AgentWikis Router Examples.

Directly validates the 5 canonical usage scenarios:
1. Example A: Configuring High-Throughput Inference in vLLM (Offline O(1) Slice Retrieval)
2. Example B: Compiling a Token-Bounded Context Pack (Unsloth LoRA Fine-Tuning)
3. Example C: Detecting Scope Boundaries & Abstaining on Live Data (Uniswap v3 Solana Pricing)
4. Example D: Dispatching to Local Workspace Skills (Matt Pocock Shoehorn Migration)
5. Example E: In-Memory IoC Micro-Kernel Resolution in Harness Kernel Loop
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import pytest

# Ensure scripts directory is on sys.path
SKILL_ROOT = Path(".agents/skills/agentwikis-router").resolve()
SCRIPTS_DIR = SKILL_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from agentwikis_engine import AgentWikisEngine

from harness.kernel.context import ServiceContext
from harness.services.agentwikis import AGENTWIKIS_SERVICE_KEY, AgentWikisService
from plugins.integration_and_io.agentwikis.main import AgentWikisPlugin

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


@pytest.mark.unit
class TestAgentWikisRealWorldExamples:
    """Tests the 5 canonical usage scenarios as concrete, automated test cases."""

    def test_example_a_vllm_offline_read_doc(self, engine: AgentWikisEngine) -> None:
        """Example A: Instant offline extraction of vLLM continuous batching docs in <50ms."""
        # 1. Engine Direct API Verification (ensure table is indexed, then measure pure seek)
        engine._ensure_offset_table()
        t0 = time.perf_counter()
        doc = engine.extract_document("vllm/README.md")
        elapsed_ms = (time.perf_counter() - t0) * 1000

        assert doc is not None
        assert doc.wiki_slug == "vllm"
        assert len(doc.content) > 100
        assert doc.source_isnad == "local_llms_full_txt"
        assert elapsed_ms < 50.0, f"Seek took too long: {elapsed_ms:.1f}ms"

        # 2. CLI Seam Verification
        with tempfile.TemporaryDirectory() as tmpdir:
            out_file = Path(tmpdir) / "vllm_guide.md"
            code, out, err = run_cli(
                "read-doc", "vllm/README.md", "--output", str(out_file)
            )
            assert code == 0, f"CLI read-doc failed: {err}\n{out}"
            assert out_file.exists()
            content = out_file.read_text(encoding="utf-8")
            assert len(content) > 100
            assert (
                "vllm" in content.lower()
                or "throughput" in content.lower()
                or "llm" in content.lower()
            )

    def test_example_b_unsloth_context_pack_budget(
        self, engine: AgentWikisEngine
    ) -> None:
        """Example B: Compiling a token-bounded context pack for Unsloth LoRA fine-tuning."""
        prompt = "how to do LoRA fine-tuning with unsloth"

        # 1. Engine Direct API Verification
        pack = engine.prepare_context_pack(prompt, max_tokens=1500)
        assert "# AgentWikis Context Pack" in pack
        assert "unsloth" in pack.lower()
        assert "## Provenance & Isnad Lineage" in pack
        # 1500 tokens ≈ max 6000 chars
        assert len(pack) <= 6500

        # 2. CLI Seam Verification
        with tempfile.TemporaryDirectory() as tmpdir:
            out_file = Path(tmpdir) / "context_pack.md"
            code, out, err = run_cli(
                "context-pack",
                prompt,
                "--max-tokens",
                "1500",
                "--output",
                str(out_file),
            )
            assert code == 0, f"CLI context-pack failed: {err}\n{out}"
            assert out_file.exists()
            cli_pack = out_file.read_text(encoding="utf-8")
            assert "unsloth" in cli_pack.lower()
            assert len(cli_pack) <= 6500

    def test_example_c_solana_uniswap_live_data_abstention(
        self, engine: AgentWikisEngine
    ) -> None:
        """Example C: Detecting scope boundaries and cleanly abstaining on live market data."""
        prompt = "What is the live exchange rate for Solana on Uniswap v3 right now?"

        # 1. Engine Direct API Verification
        match = engine.match_intent(prompt)
        assert match.in_scope is False
        assert match.calibrated_confident is False
        assert match.fallback_recommendation == "web_search"
        assert match.rejection_reason is not None

        # 2. CLI Seam Verification
        with tempfile.TemporaryDirectory() as tmpdir:
            out_file = Path(tmpdir) / "match.json"
            code, out, err = run_cli("match-skill", prompt, "--output", str(out_file))
            assert code == 0, f"CLI match-skill failed: {err}\n{out}"
            assert out_file.exists()
            data = json.loads(out_file.read_text(encoding="utf-8"))
            assert data["in_scope"] is False
            assert data["calibrated_confident"] is False
            assert data["fallback_recommendation"] == "web_search"

    def test_example_d_pocock_shoehorn_workspace_dispatch(self) -> None:
        """Example D: Identifying tasks that dispatch to local workspace skills (pocock-skills)."""
        prompt = "Matt Pocock shoehorn type assertions"

        with tempfile.TemporaryDirectory() as tmpdir:
            out_file = Path(tmpdir) / "match.json"
            code, out, err = run_cli("match-skill", prompt, "--output", str(out_file))
            assert code == 0, f"CLI match-skill failed: {err}\n{out}"
            assert out_file.exists()
            data = json.loads(out_file.read_text(encoding="utf-8"))
            assert data["in_scope"] is True
            assert "pocock-skills" in data["recommended_local_workspace_skills"]

    @pytest.mark.asyncio
    async def test_example_e_ioc_microkernel_in_memory_service(self) -> None:
        """Example E: Direct in-memory IoC micro-kernel resolution via ServiceContext."""
        # 1. Initialize IoC container
        context = ServiceContext()
        plugin = AgentWikisPlugin()

        # 2. Lifecycle on_load registers AGENTWIKIS_SERVICE_KEY
        await plugin.on_load(context)

        # 3. Require service from IoC container
        service = context.require(AGENTWIKIS_SERVICE_KEY)
        assert service is not None
        assert isinstance(service, AgentWikisService)

        # 4. In-memory document slice retrieval (ensure seek table indexed)
        from plugins.integration_and_io.agentwikis.main import get_engine

        get_engine()._ensure_offset_table()
        t0 = time.perf_counter()
        doc = service.extract_document(
            "hermes/wiki/concepts/bot-mode.md",
            section_heading="Bot Mode & Teammate Rooms",
        )
        elapsed_ms = (time.perf_counter() - t0) * 1000

        assert doc is not None
        assert doc.wiki_slug == "hermes"
        assert doc.section == "Bot Mode & Teammate Rooms"
        assert "Bot Mode" in doc.content
        assert elapsed_ms < 50.0, f"In-memory seek took {elapsed_ms:.1f}ms"
