"""Contract verification tests for Context Compiler (compiler_core) decomposition."""

from __future__ import annotations

from pathlib import Path
import pytest

from harness.kernel.context import ServiceContext
from plugins.memory_and_epistemics.context_compiler.compiler_core import (
    CHARS_PER_TOKEN,
    CONTEXT_COMPILER_KEY,
    CodeSkeletonizer,
    CompiledContext,
    ContextCompiler,
    ContextCompilerProtocol,
    FileSymbols,
    KNOWN_EVENT_DECORATORS,
    ModuleIndex,
    ReachabilityResult,
    SkeletonizerRegistry,
    SymbolResolver,
    TierEntry,
    _BUILTIN_NAMES,
    estimate_tokens,
    extract_symbols,
    resolve_context_compiler,
    skeletonize_source,
)


def test_compiler_core_facade_exports():
    """Verify all submodules and symbols are re-exported by compiler_core facade."""
    assert callable(estimate_tokens)
    assert CHARS_PER_TOKEN == 4
    assert isinstance(KNOWN_EVENT_DECORATORS, set)
    assert "receiver" in KNOWN_EVENT_DECORATORS
    assert isinstance(_BUILTIN_NAMES, set)
    assert "len" in _BUILTIN_NAMES

    assert issubclass(ContextCompiler, ContextCompilerProtocol)
    assert CONTEXT_COMPILER_KEY.name == "compiler.context_compiler"


def test_slotted_frozen_dataclass_contracts():
    """Verify slots=True and frozen=True per Rule 12 and Rule 43."""
    entry = TierEntry(
        path=Path("dummy.py"),
        tier=1,
        content="x = 1",
        tokens=2,
        hop_distance=0,
    )
    assert hasattr(entry, "__slots__")
    with pytest.raises((AttributeError, TypeError)):
        entry.tokens = 999  # Frozen immutability guard

    symbols = FileSymbols()
    assert hasattr(symbols, "__slots__")

    reachability = ReachabilityResult()
    assert hasattr(reachability, "__slots__")

    compiled = CompiledContext(target_file=Path("dummy.py"))
    assert hasattr(compiled, "__slots__")


def test_single_seam_resolver():
    """Verify resolve_context_compiler IoC behavior per Rule 58."""
    ctx = ServiceContext()
    # Unregistered fallback
    resolved = resolve_context_compiler(ctx, repo_root=".")
    assert isinstance(resolved, ContextCompiler)

    # Registered provider override
    mock_compiler = ContextCompiler(repo_root=".")
    ctx.provide(CONTEXT_COMPILER_KEY, mock_compiler)
    assert resolve_context_compiler(ctx) is mock_compiler


def test_polyglot_skeletonizer_registry():
    """Verify skeletonization across JSON, Markdown, and text fallbacks."""
    # JSON outline
    json_data = '{"users": [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}], "status": "active"}'
    json_skeleton, stripped_json = SkeletonizerRegistry.skeletonize_json(json_data)
    assert "users" in json_skeleton
    assert stripped_json == 1

    # Markdown outline
    md_data = "# Heading 1\nParagraph text here that will be stripped.\n## Heading 2\n- Item 1\n- Item 2"
    md_skeleton, stripped_md = SkeletonizerRegistry.skeletonize_markdown(md_data)
    assert "# Heading 1" in md_skeleton
    assert "## Heading 2" in md_skeleton
    assert "- Item 1" in md_skeleton
    assert "Paragraph text here" not in md_skeleton
    assert stripped_md > 0

    # General text fallback
    long_text = "\n".join([f"line {i}" for i in range(50)])
    text_skeleton, omitted = SkeletonizerRegistry.skeletonize("sample.txt", long_text)
    assert "lines omitted" in text_skeleton
    assert omitted == 30


def test_context_compiler_e2e(tmp_path: Path):
    """Verify end-to-end multi-tier compilation."""
    # Scaffold mini repository
    mod_a = tmp_path / "module_a.py"
    mod_a.write_text("def helper():\n    '''Help'''\n    return 42\n", encoding="utf-8")

    mod_b = tmp_path / "module_b.py"
    mod_b.write_text("import module_a\n\ndef main():\n    return module_a.helper()\n", encoding="utf-8")

    compiler = ContextCompiler(repo_root=tmp_path, max_hops=1)
    compiled = compiler.compile(mod_b)

    assert compiled.target_file == mod_b.resolve()
    assert len(compiled.entries) >= 1
    assert compiled.entries[0].tier == 1
    assert "import module_a" in compiled.entries[0].content

    # Prompt rendering
    prompt = compiled.to_prompt_string()
    assert "[FULL SOURCE]" in prompt
    assert compiled.summary() is not None
