"""ServiceKey definition for HyperFrames video rendering service."""
from __future__ import annotations

from harness.kernel.context import ServiceKey
from harness.services.hyperframes.protocols import HyperFramesService

HYPERFRAMES_SERVICE_KEY = ServiceKey[HyperFramesService]("service.hyperframes")
