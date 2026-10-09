"""Single-seam resolver factory for ServiceContext per AGENTS.md Rule 58."""

from __future__ import annotations

from typing import Any

from .core import ServiceContext


def resolve_service_context(context: Any = None) -> ServiceContext:
    """Resolve or construct an authoritative ServiceContext instance (Rule 58).

    If an existing ServiceContext instance is provided, returns it directly.
    Otherwise, instantiates and returns a new root ServiceContext.
    """
    if isinstance(context, ServiceContext):
        return context
    return ServiceContext()
