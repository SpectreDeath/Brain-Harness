"""Single-seam resolver for MemGraphRAG engine per Rule 58."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from harness.kernel.context import ServiceContext
    from .core import MemGraphRAGEngine


def resolve_memgraphrag_engine(ctx: ServiceContext | None = None) -> MemGraphRAGEngine:
    """Resolve MemGraphRAGEngine from IoC context or instantiate default instance."""
    from .core import MemGraphRAGEngine

    if ctx is not None:
        from harness.services.memgraphrag import MEMGRAPHRAG_MEMORY_KEY

        service = ctx.optional(MEMGRAPHRAG_MEMORY_KEY)
        if service is not None and hasattr(service, "_engine"):
            return service._engine  # type: ignore[no-any-return]

    return MemGraphRAGEngine()
