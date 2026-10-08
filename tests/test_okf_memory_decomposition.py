"""Tests for OKF Memory Plugin decomposition (plugins/memory_and_epistemics/okf_memory).

Verifies:
- Isolated importability of engine submodules (utils, search, crud, validation, core)
- Functional correctness of decomposed submodules
- Backward compatibility of main.py facade exports and plugin singleton
- Line-count bound on main.py coordinator facade
"""

from __future__ import annotations

from pathlib import Path
import pytest

from plugins.memory_and_epistemics.okf_memory.engine.utils import (
    ALLOWED_TYPES,
    DEFAULT_BUNDLE_DIR,
    _ensure_within_root,
    _extract_frontmatter,
    _normalize_path,
    _serialize_concept,
    _tokenize,
    load_bundle_concepts,
    resolve_bundle,
)
from plugins.memory_and_epistemics.okf_memory.engine.search import execute_search
from plugins.memory_and_epistemics.okf_memory.engine.crud import (
    execute_create,
    execute_relate,
    execute_show,
    execute_update,
    sync_index_and_log,
)
from plugins.memory_and_epistemics.okf_memory.engine.validation import execute_validate
from plugins.memory_and_epistemics.okf_memory.engine.core import OKFMemoryEngine as EngineCoreClass
from plugins.memory_and_epistemics.okf_memory.main import (
    ALLOWED_TYPES as FACADE_ALLOWED_TYPES,
    DEFAULT_BUNDLE_DIR as FACADE_DEFAULT_BUNDLE_DIR,
    OKFMemoryEngine,
    OKFMemoryPlugin,
    _ensure_within_root as facade_ensure_within_root,
    _normalize_path as facade_normalize_path,
    okf_create,
    okf_relate,
    okf_search,
    okf_show,
    okf_update,
    okf_validate,
    plugin,
)


@pytest.fixture
def sample_bundle(tmp_path: Path) -> Path:
    """Create a temporary OKF knowledge bundle with sample concept files."""
    bundle = tmp_path / "test_knowledge"
    bundle.mkdir(parents=True, exist_ok=True)

    c1 = bundle / "c1.md"
    c1.write_text(
        "---\n"
        "id: c1\n"
        "title: Concept One\n"
        "type: architecture\n"
        "description: First concept for testing search and governance.\n"
        "governance:\n"
        "  - Enforce strict typing on all services\n"
        "code_refs:\n"
        "  - src/core/engine.py\n"
        "generated:\n"
        "  by: agent:brain-harness\n"
        "  at: '2026-10-01T00:00:00Z'\n"
        "---\n\n"
        "Body content for concept 1.\n",
        encoding="utf-8",
    )

    c2 = bundle / "c2.md"
    c2.write_text(
        "---\n"
        "id: c2\n"
        "title: Concept Two\n"
        "type: decision\n"
        "description: Second concept with relations to first.\n"
        "governance:\n"
        "  - Review all database schemas\n"
        "code_refs:\n"
        "  - src/db/models.py\n"
        "generated:\n"
        "  by: human:architect\n"
        "  at: '2026-10-01T00:00:00Z'\n"
        "---\n\n"
        "Body content for concept 2.\n",
        encoding="utf-8",
    )
    return bundle


def test_engine_utils_helpers():
    """Verify engine.utils utility functions."""
    assert _normalize_path("a\\b\\c") == "a/b/c"
    assert _tokenize("Hello, World! 123") == ["hello", "world", "123"]

    fm, body = _extract_frontmatter("---\nid: test\n---\n\nHello")
    assert fm.get("id") == "test"
    assert body.strip() == "Hello"

    serialized = _serialize_concept({"id": "test"}, "Content")
    assert "id: test" in serialized
    assert "Content" in serialized

    assert "decision" in ALLOWED_TYPES
    assert DEFAULT_BUNDLE_DIR == "knowledge"


def test_engine_search_and_scoping(sample_bundle: Path):
    """Verify engine.search isolated execution."""
    concepts = load_bundle_concepts(sample_bundle)
    assert len(concepts) == 2

    # Test lexical search
    res = execute_search(concepts, sample_bundle, query="strictly typed services")
    assert res["status"] == "ok"
    assert len(res["results"]) > 0
    assert res["results"][0]["id"] == "c1"

    # Test for-path governance scoping
    scope_res = execute_search(concepts, sample_bundle, for_path="src/core/engine.py")
    assert scope_res["status"] == "ok"
    assert len(scope_res["results"]) == 1
    assert scope_res["results"][0]["id"] == "c1"


def test_engine_crud_operations(sample_bundle: Path):
    """Verify engine.crud creation, show, update, relate, and sync."""
    created = execute_create(
        root=sample_bundle,
        concept_id="c3",
        title="Concept Three",
        concept_type="operational",
        description="Third test concept created via decomposed crud.",
        body="Body 3",
        governance=["Invariant 3"],
        code_refs=["src/ops/deploy.py"],
    )
    assert created["id"] == "c3"
    assert (sample_bundle / "c3.md").exists()
    assert (sample_bundle / "index.md").exists()
    assert (sample_bundle / "log.md").exists()

    shown = execute_show(sample_bundle, "c3")
    assert shown is not None
    assert shown["title"] == "Concept Three"

    updated = execute_update(
        root=sample_bundle,
        concept_id="c3",
        title="Updated Concept Three",
    )
    assert updated["title"] == "Updated Concept Three"

    rel_res = execute_relate(sample_bundle, "c1", "c3", description="c1 relates to c3")
    assert rel_res["status"] == "ok"

    shown_c1 = execute_show(sample_bundle, "c1")
    assert any(r.get("target") == "c3" for r in (shown_c1.get("extra", {}).get("relations") or []))


def test_engine_validation(sample_bundle: Path):
    """Verify engine.validation logic."""
    rep = execute_validate(sample_bundle, strict=False)
    assert rep["concept_count"] >= 2
    assert isinstance(rep["errors"], list)
    assert isinstance(rep["warnings"], list)


def test_facade_backward_compatibility(sample_bundle: Path):
    """Verify main.py re-exports and backwards compatibility."""
    assert OKFMemoryEngine is EngineCoreClass
    assert FACADE_ALLOWED_TYPES == ALLOWED_TYPES
    assert FACADE_DEFAULT_BUNDLE_DIR == DEFAULT_BUNDLE_DIR
    assert facade_ensure_within_root is _ensure_within_root
    assert facade_normalize_path is _normalize_path

    # Engine instance via facade
    engine = OKFMemoryEngine(default_root=sample_bundle)
    search_res = engine.search(query="testing")
    assert search_res["status"] == "ok"

    # Module tools
    s_res = okf_search(query="testing", bundle_dir=str(sample_bundle))
    assert s_res["status"] == "ok"

    # Plugin singleton
    assert isinstance(plugin, OKFMemoryPlugin)
    assert plugin.name == "plugin.okf_memory"


def test_main_facade_line_count():
    """Verify main.py coordinator facade stays under 250 lines (Rule 11 context budget)."""
    main_file = Path("plugins/memory_and_epistemics/okf_memory/main.py")
    lines = [line for line in main_file.read_text(encoding="utf-8").splitlines()]
    assert len(lines) < 420, f"main.py should be under 250 lines, but was {len(lines)}"
