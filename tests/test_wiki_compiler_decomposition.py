"""Contract verification tests for Wiki Compiler (compiler_core) decomposition."""

from __future__ import annotations

from pathlib import Path
import pytest

from harness.kernel.context import ServiceContext
from plugins.data_engineering.wiki_compiler.compiler_core import (
    DefaultWikiCompiler,
    Entity,
    LintReport,
    WIKI_COMPILER_KEY,
    WikiCompilerProtocol,
    WikiGraphQuery,
    _derive_name_from_filename,
    _parse_existing_sections,
    _slugify,
    build_graph,
    compile_pages,
    compile_pages_incremental,
    compile_virtual_wiki,
    compile_wiki,
    extract_all,
    extract_entity,
    extract_entity_from_text,
    generate_corpus,
    lint,
    orphan_ids,
    render_page,
    resolve_wiki_compiler,
)


def test_wiki_compiler_facade_exports():
    """Verify all submodules and symbols are re-exported by compiler_core facade."""
    assert callable(extract_entity_from_text)
    assert callable(extract_entity)
    assert callable(extract_all)
    assert callable(build_graph)
    assert callable(orphan_ids)
    assert callable(render_page)
    assert callable(compile_virtual_wiki)
    assert callable(compile_pages)
    assert callable(compile_pages_incremental)
    assert callable(lint)
    assert callable(generate_corpus)
    assert callable(compile_wiki)

    assert issubclass(DefaultWikiCompiler, WikiCompilerProtocol)
    assert WIKI_COMPILER_KEY.name == "domain.wiki_compiler"


def test_slotted_dataclass_contracts():
    """Verify slots=True per Rule 12 for Entity and LintReport."""
    ent = Entity(
        entity_id="test_id",
        name="Test Name",
        aliases=["t1"],
        created="2026-10-12",
        body="Body content",
        source_path="test.md",
    )
    assert hasattr(ent, "__slots__")
    ent_dict = ent.to_dict()
    assert ent_dict["entity_id"] == "test_id"
    assert ent_dict["name"] == "Test Name"

    report = LintReport(total_pages=5, broken_links=[("a.md", "b")], orphan_pages=["c.md"])
    assert hasattr(report, "__slots__")
    assert not report.is_clean()
    assert report.to_dict()["total_pages"] == 5


def test_single_seam_resolver():
    """Verify resolve_wiki_compiler IoC behavior per Rule 58."""
    ctx = ServiceContext()
    # Unregistered fallback
    resolved = resolve_wiki_compiler(ctx)
    assert isinstance(resolved, DefaultWikiCompiler)

    # Registered provider override
    mock_compiler = DefaultWikiCompiler()
    ctx.provide(WIKI_COMPILER_KEY, mock_compiler)
    assert resolve_wiki_compiler(ctx) is mock_compiler


def test_incremental_dirty_tracking_compiler(tmp_path: Path):
    """Verify dirty-tracking diff compilation skips unchanged files."""
    notes_dir = tmp_path / "raw"
    notes_dir.mkdir()
    out_dir = tmp_path / "wiki"
    out_dir.mkdir()

    note1 = notes_dir / "note1.txt"
    note1.write_text("# Note One\nMentions Note Two here.", encoding="utf-8")
    note2 = notes_dir / "note2.txt"
    note2.write_text("# Note Two\nMentions Note One here.", encoding="utf-8")

    entities = extract_all(str(notes_dir))
    graph = build_graph(entities)

    # First compile writes 2 pages
    res1 = compile_pages_incremental(entities, graph, str(out_dir))
    assert res1["written_count"] == 2
    assert res1["skipped_count"] == 0

    # Second compile with no changes skips both pages
    res2 = compile_pages_incremental(entities, graph, str(out_dir))
    assert res2["written_count"] == 0
    assert res2["skipped_count"] == 2


def test_wiki_lint_and_corpus_generation(tmp_path: Path):
    """Verify synthetic corpus generation and wiki linting."""
    corpus_dir = tmp_path / "corpus"
    paths = generate_corpus(str(corpus_dir), num_files=5, seed=123)
    assert len(paths) == 5

    wiki_dir = tmp_path / "compiled_wiki"
    res = compile_wiki(str(corpus_dir), str(wiki_dir), run_lint=True)
    assert res["entities_count"] == 5
    assert len(res["written_paths"]) == 5
    assert res["lint_report"] is not None
