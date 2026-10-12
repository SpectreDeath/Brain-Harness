"""Composite domain engine for documentation compilation and verification."""

from __future__ import annotations

import sys

from harness.services.doc_builder.engine.autodoc import inspect_autodoc
from harness.services.doc_builder.engine.chunker import chunk_markdown
from harness.services.doc_builder.engine.convert import convert_format
from harness.services.doc_builder.engine.links import verify_links
from harness.services.doc_builder.engine.linter import lint_style

# Rule 23: Windows UTF-8 Stream Codec Entrypoint Invariant
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


class DocBuilderDomainEngine:
    """Authoritative in-memory domain engine for documentation compilation and verification."""

    inspect_autodoc = staticmethod(inspect_autodoc)
    verify_links = staticmethod(verify_links)
    convert_format = staticmethod(convert_format)
    lint_style = staticmethod(lint_style)
    chunk_markdown = staticmethod(chunk_markdown)
