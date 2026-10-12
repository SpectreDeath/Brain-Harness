"""Authoritative in-memory domain engine subpackage (decomposed)."""

from __future__ import annotations

from harness.services.doc_builder.engine.autodoc import inspect_autodoc
from harness.services.doc_builder.engine.chunker import chunk_markdown
from harness.services.doc_builder.engine.convert import convert_format
from harness.services.doc_builder.engine.links import verify_links
from harness.services.doc_builder.engine.linter import lint_style
from harness.services.doc_builder.engine.service import DocBuilderDomainEngine

__all__ = [
    "DocBuilderDomainEngine",
    "chunk_markdown",
    "convert_format",
    "inspect_autodoc",
    "lint_style",
    "verify_links",
]
