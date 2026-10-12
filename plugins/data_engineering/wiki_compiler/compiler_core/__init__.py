"""Core Wiki Compiler subpackage (decomposed)."""

from __future__ import annotations

from plugins.data_engineering.wiki_compiler.compiler_core.compiler import (
    compile_pages,
    compile_pages_incremental,
    compile_virtual_wiki,
    compile_wiki,
    generate_corpus,
    lint,
)
from plugins.data_engineering.wiki_compiler.compiler_core.extractor import (
    extract_all,
    extract_entity,
    extract_entity_from_text,
)
from plugins.data_engineering.wiki_compiler.compiler_core.graph import (
    WikiGraphQuery,
    _build_phrase_index,
    build_graph,
    orphan_ids,
)
from plugins.data_engineering.wiki_compiler.compiler_core.models import (
    ALIASES_RE,
    CREATED_RE,
    HEADER_HASH_RE,
    LINK_RE,
    SECTION_RE,
    Entity,
    LintReport,
    _WORD_RE,
    _derive_name_from_filename,
    _slugify,
)
from plugins.data_engineering.wiki_compiler.compiler_core.protocols import (
    WIKI_COMPILER_KEY,
    WikiCompilerProtocol,
)
from plugins.data_engineering.wiki_compiler.compiler_core.renderer import (
    _parse_existing_sections,
    render_page,
)
from plugins.data_engineering.wiki_compiler.compiler_core.resolvers import (
    DefaultWikiCompiler,
    resolve_wiki_compiler,
)

__all__ = [
    "ALIASES_RE",
    "CREATED_RE",
    "DefaultWikiCompiler",
    "Entity",
    "HEADER_HASH_RE",
    "LINK_RE",
    "LintReport",
    "SECTION_RE",
    "WIKI_COMPILER_KEY",
    "WikiCompilerProtocol",
    "WikiGraphQuery",
    "_WORD_RE",
    "_build_phrase_index",
    "_derive_name_from_filename",
    "_parse_existing_sections",
    "_slugify",
    "build_graph",
    "compile_pages",
    "compile_pages_incremental",
    "compile_virtual_wiki",
    "compile_wiki",
    "extract_all",
    "extract_entity",
    "extract_entity_from_text",
    "generate_corpus",
    "lint",
    "orphan_ids",
    "render_page",
    "resolve_wiki_compiler",
]
