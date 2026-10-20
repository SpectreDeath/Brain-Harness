"""HyperFrames video rendering micro-kernel service."""
from __future__ import annotations

from harness.services.hyperframes.keys import HYPERFRAMES_SERVICE_KEY
from harness.services.hyperframes.models import RenderOutput, RenderRequest, VideoScene
from harness.services.hyperframes.protocols import HyperFramesService
from harness.services.hyperframes.resolvers import resolve_hyperframes
from harness.services.hyperframes.runtime import check_node_available
from harness.services.hyperframes.service import DefaultHyperFramesService

__all__ = [
    "HYPERFRAMES_SERVICE_KEY",
    "DefaultHyperFramesService",
    "HyperFramesService",
    "RenderOutput",
    "RenderRequest",
    "VideoScene",
    "check_node_available",
    "resolve_hyperframes",
]
