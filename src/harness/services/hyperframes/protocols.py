"""Protocol definition for HyperFrames video rendering service."""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from harness.services.hyperframes.models import RenderOutput, RenderRequest, VideoScene


@runtime_checkable
class HyperFramesService(Protocol):
    """Protocol for programmatic multimedia rendering via HyperFrames."""

    def check_runtime(self) -> tuple[bool, str]:
        """Check whether Node.js and the renderer CLI are available."""
        ...

    def render(self, request: RenderRequest) -> RenderOutput:
        """Synchronously render a VideoScene sequence into a video artifact."""
        ...

    async def render_async(self, request: RenderRequest) -> RenderOutput:
        """Asynchronously render a VideoScene sequence into a video artifact."""
        ...

    def generate_scene_preview(self, scene: VideoScene) -> str:
        """Generate a standalone self-contained HTML preview for a single scene."""
        ...
