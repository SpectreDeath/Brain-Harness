"""Single-seam service resolvers for ContextCompiler per Rule 58."""

from __future__ import annotations

from pathlib import Path

from harness.kernel.context import ServiceContext
from plugins.memory_and_epistemics.context_compiler.compiler_core.compiler import ContextCompiler
from plugins.memory_and_epistemics.context_compiler.compiler_core.protocols import (
    CONTEXT_COMPILER_KEY,
    ContextCompilerProtocol,
)


def resolve_context_compiler(
    context: ServiceContext | None = None,
    repo_root: str | Path = ".",
    max_hops: int = 2,
) -> ContextCompilerProtocol:
    """Resolve ContextCompiler from IoC context or instantiate fallback."""
    if context is not None:
        service = context.optional(CONTEXT_COMPILER_KEY)
        if service is not None:
            return service
    return ContextCompiler(repo_root=repo_root, max_hops=max_hops)
