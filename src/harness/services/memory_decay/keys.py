"""Typed service keys for Ebbinghaus Memory Decay Engine (Rule 2)."""

from __future__ import annotations

from typing import TYPE_CHECKING
from harness.kernel.context import ServiceKey

if TYPE_CHECKING:
    from harness.services.memory_decay.protocols import MemoryDecayService

MEMORY_DECAY_SERVICE_KEY = ServiceKey["MemoryDecayService"]("service.memory_decay")
