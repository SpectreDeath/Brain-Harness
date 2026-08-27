"""Tests for Domain: Wiki Compiler plugin (Personal Knowledge Base Markdown Compiler)."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from harness.creator.validator import PluginValidator
from plugins.data_engineering.wiki_compiler.compiler_core import (
    extract_entity_from_text,
    render_page,
)
from plugins.data_engineering.wiki_compiler.main import (
    WIKI_COMPILER_SERVICE_KEY,
    WikiCompilerService,
    compile_virtual_wiki,
    compile_wiki_directory,
    compile_wiki_incremental,
    generate_synthetic_notes,
    lint_wiki,
    query_wiki_graph,
)


@pytest.mark.unit
class TestWikiCompilerPlugin:
    def test_extract_entity(self) -> None:
        raw_text = """# Neural Synthesis Engine
created: 2026-08-20
aliases: neural-engine, nse

The Neural Synthesis Engine coordinates deep models.
"""
        ent = extract_entity_from_text(raw_text, "test_note")
        assert ent.name == "Neural Synthesis Engine"
        assert ent.entity_id == "neural_synthesis_engine"
        assert "neural-engine" in ent.aliases
        assert "nse" in ent.aliases
        assert "coordinates deep models" in ent.body

    def test_virtual_wiki_compilation_and_graph_queries(self) -> None:
        notes = {
            "alpha": "# Alpha Engine\nThis relates to Beta Core in all deployments.",
            "beta": "# Beta Core\nCoordinates with Gamma Subsystem heavily.",
            "gamma": "# Gamma Subsystem\nIndependent leaf node.",
        }

        # 1. Virtual compile (in-memory)
        res = compile_virtual_wiki(notes)
        assert res["status"] == "ok"
        assert res["entities_count"] == 3
        assert "alpha_engine.md" in res["pages"]
        assert "[[Beta Core]]" in res["pages"]["alpha_engine.md"]

        # 2. Graph query - neighborhood
        q_nbr = query_wiki_graph(notes=notes, query_type="neighborhood", root_entity="alpha_engine", max_hops=2)
        assert q_nbr["status"] == "ok"
        assert q_nbr["neighborhood"]["node_count"] >= 2

        # 3. Graph query - path
        q_path = query_wiki_graph(notes=notes, query_type="path", root_entity="alpha_engine", target_entity="gamma_subsystem")
        assert q_path["status"] == "ok"
        assert q_path["path"] == ["alpha_engine", "beta_core", "gamma_subsystem"]

        # 4. Graph query - backlinks
        q_back = query_wiki_graph(notes=notes, query_type="backlinks", root_entity="beta_core")
        assert q_back["status"] == "ok"
        assert any(b["entity_id"] == "alpha_engine" for b in q_back["backlinks"])

    def test_notes_section_preservation_across_recompiles(self) -> None:
        ent = extract_entity_from_text("# Kernel Arch\nCore kernel mechanics.", "kernel_arch")
        graph_edges = {"outgoing": set(), "incoming": set()}
        entities = {ent.entity_id: ent}

        existing_page = """# Kernel Arch
## Metadata
- created: 2026-08-01

## Related
- (none)

## Body
Old body.

## Notes
My vital human insights here!
"""
        rendered = render_page(ent, graph_edges, entities, existing_content=existing_page)
        assert "My vital human insights here!" in rendered
        assert "## Notes" in rendered

    def test_full_pipeline_and_incremental_compiler(self) -> None:
        with tempfile.TemporaryDirectory() as raw_dir, tempfile.TemporaryDirectory() as out_dir:
            # Generate corpus
            gen_res = generate_synthetic_notes(raw_dir, num_files=10, seed=42)
            assert gen_res["status"] == "ok"
            assert gen_res["generated_count"] == 10

            # Compile directory
            comp_res = compile_wiki_directory(raw_dir, out_dir, run_linter=True)
            assert comp_res["status"] == "ok"
            assert comp_res["entities_compiled"] == 10
            assert comp_res["written_pages_count"] == 10

            # Incremental compile (should write 0 files because nothing changed)
            inc_res = compile_wiki_incremental(raw_dir, out_dir)
            assert inc_res["status"] == "ok"
            assert inc_res["written_count"] == 0
            assert inc_res["skipped_count"] == 10

            # Lint
            lint_res = lint_wiki(out_dir)
            assert lint_res["status"] == "ok"
            assert lint_res["lint_report"]["total_pages"] == 10

    def test_service_facade_and_service_key(self) -> None:
        svc = WikiCompilerService()
        notes = {"doc1": "# Doc One\nBody text."}
        res = svc.compile_virtual(notes)
        assert res["status"] == "ok"
        assert WIKI_COMPILER_SERVICE_KEY.name == "domain.wiki_compiler"

    @pytest.mark.asyncio
    async def test_plugin_validator_compliance(self) -> None:
        plugin_dir = Path("plugins/data_engineering/wiki_compiler")
        report = await PluginValidator.validate(plugin_dir)
        assert report.valid, f"Validation errors: {report.errors}"
        assert len(report.errors) == 0
