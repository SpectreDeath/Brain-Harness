"""OpenCode Bridge Service package (AGENTS.md Rule 1, 2, 12, 49, 58)."""

from __future__ import annotations

from .engine import DefaultOpenCodeBridgeService, BUILTIN_OPENCODE_TOOLS
from .models import (
    OpenCodeCatalogResult,
    OpenCodeRunResult,
    OpenCodeSessionResult,
    OpenCodeStatusResult,
)
from .protocols import OPENCODE_BRIDGE_KEY, OpenCodeBridgeService
from .resolvers import resolve_opencode_bridge

__all__ = [
    "BUILTIN_OPENCODE_TOOLS",
    "DefaultOpenCodeBridgeService",
    "OPENCODE_BRIDGE_KEY",
    "OpenCodeBridgeService",
    "OpenCodeCatalogResult",
    "OpenCodeRunResult",
    "OpenCodeSessionResult",
    "OpenCodeStatusResult",
    "resolve_opencode_bridge",
]
