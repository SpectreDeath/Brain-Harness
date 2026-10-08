"""Single-seam resolver factory for Brain Bridge service (AGENTS.md Rule 58)."""

from __future__ import annotations

from harness.kernel.context import ServiceContext
from .core import DefaultBrainBridgeService
from .protocols import BRAIN_BRIDGE_KEY, BrainBridgeService


def resolve_brain_bridge(ctx: ServiceContext | None = None) -> BrainBridgeService:
    """Resolve BrainBridgeService from IoC context or fall back to DefaultBrainBridgeService."""
    if ctx is not None:
        svc = ctx.optional(BRAIN_BRIDGE_KEY)
        if svc is not None and isinstance(svc, BrainBridgeService):
            return svc
    return DefaultBrainBridgeService()
