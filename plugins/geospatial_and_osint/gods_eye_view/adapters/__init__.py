"""MCP Bridge Tier 2 adapter mixins."""

from __future__ import annotations

from .tier2_sensing import Tier2SensingMixin
from .tier2_tracking import Tier2TrackingMixin


class Tier2AdapterMixin(Tier2SensingMixin, Tier2TrackingMixin):
    """Unified Tier 2 mixin combining sensing and tracking adapters."""
    pass


__all__ = ["Tier2AdapterMixin", "Tier2SensingMixin", "Tier2TrackingMixin"]
