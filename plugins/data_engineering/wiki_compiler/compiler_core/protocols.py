"""Protocols and typed service keys for Wiki Compiler."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from harness.kernel.context import ServiceKey


@runtime_checkable
class WikiCompilerProtocol(Protocol):
    """Protocol for wiki compilation engines."""

    def compile(self, raw_dir: str, output_dir: str, run_lint: bool = True) -> dict[str, Any]: ...

    def compile_virtual(
        self,
        notes: dict[str, str],
        preserve_sections: dict[str, str] | None = None,
    ) -> dict[str, Any]: ...


WIKI_COMPILER_KEY = ServiceKey[WikiCompilerProtocol]("domain.wiki_compiler")
