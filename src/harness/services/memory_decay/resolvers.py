"""Single-seam resolver for MemoryDecayService."""

from __future__ import annotations

from harness.kernel.context import ServiceContext
from harness.services.memory_decay.keys import MEMORY_DECAY_SERVICE_KEY
from harness.services.memory_decay.protocols import MemoryDecayService
from harness.services.memory_decay.service import DefaultMemoryDecayService


def resolve_memory_decay(context: ServiceContext | None = None) -> MemoryDecayService:
    """Resolve MemoryDecayService from context or return DefaultMemoryDecayService."""
    if context is not None and hasattr(context, "has") and context.has(MEMORY_DECAY_SERVICE_KEY):
        return context.require(MEMORY_DECAY_SERVICE_KEY)
    return DefaultMemoryDecayService()
