"""Contract verification tests for DocBuilderDomainEngine decomposition."""

from __future__ import annotations

from pathlib import Path
import pytest

from harness.services.doc_builder.engine import (
    DocBuilderDomainEngine,
    chunk_markdown,
    convert_format,
    inspect_autodoc,
    lint_style,
    verify_links,
)
from harness.services.doc_builder.engine.autodoc import inspect_autodoc as direct_autodoc
from harness.services.doc_builder.engine.chunker import chunk_markdown as direct_chunk
from harness.services.doc_builder.engine.convert import convert_format as direct_convert
from harness.services.doc_builder.engine.links import verify_links as direct_links
from harness.services.doc_builder.engine.linter import lint_style as direct_lint


def test_engine_subpackage_facade_parity():
    """Verify facade re-exports match underlying direct functions."""
    assert inspect_autodoc is direct_autodoc
    assert verify_links is direct_links
    assert convert_format is direct_convert
    assert lint_style is direct_lint
    assert chunk_markdown is direct_chunk

    assert hasattr(DocBuilderDomainEngine, "inspect_autodoc")
    assert hasattr(DocBuilderDomainEngine, "verify_links")
    assert hasattr(DocBuilderDomainEngine, "convert_format")
    assert hasattr(DocBuilderDomainEngine, "lint_style")
    assert hasattr(DocBuilderDomainEngine, "chunk_markdown")


def test_inspect_autodoc():
    """Verify inspect_autodoc signature extraction."""
    sig = DocBuilderDomainEngine.inspect_autodoc("json", "dumps")
    assert "dumps" in sig.object_path
    assert sig.docstring != ""
    assert sig.docstring_format == "markdown"


def test_convert_format_svelte_injection():
    """Verify sphinx directive and markdown blockquote transpilation."""
    raw = """
.. note::
    Important note text.

> [!WARNING]
Beware of edge cases.
"""
    res = DocBuilderDomainEngine.convert_format(raw, target_format="mdx")
    assert "<Tip>" in res.converted_content
    assert "<Warning>" in res.converted_content
    assert "<Tip>" in res.svelte_components_injected
    assert "<Warning>" in res.svelte_components_injected


def test_lint_style():
    """Verify code example trailing whitespace detection and fix."""
    dirty = "```python\ndef foo():   \n    return 1   \n```"
    lint_res = DocBuilderDomainEngine.lint_style(dirty, fix=False)
    assert lint_res.issues_count > 0

    fixed_res = DocBuilderDomainEngine.lint_style(dirty, fix=True)
    assert fixed_res.formatted_content is not None
    assert "   \n" not in fixed_res.formatted_content


def test_chunk_markdown():
    """Verify heading-based hierarchical chunking."""
    doc = """# Introduction
Intro body.

## Architecture
Architecture body.

### Seams
Seams body.
"""
    chunks = DocBuilderDomainEngine.chunk_markdown(doc, page_title="Guide")
    assert len(chunks) == 3
    assert chunks[0].title == "Introduction"
    assert chunks[1].title == "Architecture"
    assert chunks[2].title == "Seams"
