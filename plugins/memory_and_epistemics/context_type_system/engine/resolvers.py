"""Single-seam resolver for Context Type System Service per Rule 58."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from harness.kernel.context import ServiceContext
from harness.services.context_type_system import (
    CONTEXT_TYPE_SYSTEM_KEY,
    ContextTypeService,
)

if TYPE_CHECKING:
    from plugins.memory_and_epistemics.context_type_system.main import ContextTypeSystemPlugin


def resolve_context_type_system(
    context: Optional[ServiceContext] = None,
) -> ContextTypeService:
    """Resolve ContextTypeService from ServiceContext or instantiate fallback singleton."""
    if context is not None:
        service = context.optional(CONTEXT_TYPE_SYSTEM_KEY)
        if service is not None:
            return service

    # Fallback to in-process plugin implementation
    from plugins.memory_and_epistemics.context_type_system.main import ContextTypeSystemPlugin
    return ContextTypeSystemPlugin()
