"""Single-seam resolver factory for OpenCode Bridge service (AGENTS.md Rule 58)."""

from __future__ import annotations

from harness.kernel.context import ServiceContext
from .engine import DefaultOpenCodeBridgeService
from .protocols import OPENCODE_BRIDGE_KEY, OpenCodeBridgeService


def resolve_opencode_bridge(ctx: ServiceContext | None = None) -> OpenCodeBridgeService:
    """Resolve OpenCodeBridgeService from IoC context or fall back to DefaultOpenCodeBridgeService."""
    if ctx is not None:
        svc = ctx.optional(OPENCODE_BRIDGE_KEY)
        if svc is not None and isinstance(svc, OpenCodeBridgeService):
            return svc
    return DefaultOpenCodeBridgeService()
