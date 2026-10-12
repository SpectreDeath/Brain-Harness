"""Single-seam service resolvers for WikiCompiler per Rule 58."""

from __future__ import annotations

from typing import Any

from harness.kernel.context import ServiceContext
from plugins.data_engineering.wiki_compiler.compiler_core.compiler import (
    compile_virtual_wiki,
    compile_wiki,
)
from plugins.data_engineering.wiki_compiler.compiler_core.protocols import (
    WIKI_COMPILER_KEY,
    WikiCompilerProtocol,
)


class DefaultWikiCompiler:
    """Default implementation of WikiCompilerProtocol delegating to pure functional compiler."""

    def compile(self, raw_dir: str, output_dir: str, run_lint: bool = True) -> dict[str, Any]:
        return compile_wiki(raw_dir=raw_dir, output_dir=output_dir, run_lint=run_lint)

    def compile_virtual(
        self,
        notes: dict[str, str],
        preserve_sections: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        return compile_virtual_wiki(notes=notes, preserve_sections=preserve_sections)


def resolve_wiki_compiler(context: ServiceContext | None = None) -> WikiCompilerProtocol:
    """Resolve WikiCompilerProtocol from IoC container or instantiate default fallback."""
    if context is not None:
        service = context.optional(WIKI_COMPILER_KEY)
        if service is not None:
            return service
    return DefaultWikiCompiler()
