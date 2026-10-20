"""Resolver helper for HyperFramesService."""
from __future__ import annotations

from harness.kernel.context import ServiceContext
from harness.services.hyperframes.keys import HYPERFRAMES_SERVICE_KEY
from harness.services.hyperframes.protocols import HyperFramesService


def resolve_hyperframes(context: ServiceContext) -> HyperFramesService:
    """Resolve the HyperFrames video rendering service from the IoC container."""
    return context.require(HYPERFRAMES_SERVICE_KEY)
