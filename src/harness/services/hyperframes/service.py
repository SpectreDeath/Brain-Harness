"""Default implementation of HyperFramesService."""
from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from harness.services.hyperframes.bridge import HyperFramesSubprocessBridge
from harness.services.hyperframes.models import RenderOutput, RenderRequest, VideoScene
from harness.services.hyperframes.protocols import HyperFramesService
from harness.services.hyperframes.runtime import check_node_available


class DefaultHyperFramesService(HyperFramesService):
    """Production service for programmatic multimedia scene authoring and rendering."""

    def __init__(
        self,
        node_timeout_s: float = 120.0,
        simulate_headless: bool = False,
        output_dir: Path | None = None,
    ) -> None:
        self._node_timeout_s = node_timeout_s
        self._simulate_headless = simulate_headless
        self._output_dir = output_dir
        self._bridge = HyperFramesSubprocessBridge(
            node_timeout_s=node_timeout_s,
            simulate_headless=simulate_headless,
        )

    def check_runtime(self) -> tuple[bool, str]:
        """Verify Node.js CLI runtime presence."""
        return check_node_available()

    def render(self, request: RenderRequest) -> RenderOutput:
        """Synchronously render a video sequence."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            # In a running event loop, spawn simulation fallback or thread
            return self._bridge._render_simulated(request, self._output_dir or Path(tempfile_dir()))
        return asyncio.run(self.render_async(request))

    async def render_async(self, request: RenderRequest) -> RenderOutput:
        """Asynchronously render a video sequence."""
        return await self._bridge.render(request, self._output_dir)

    def generate_scene_preview(self, scene: VideoScene) -> str:
        """Generate a complete, self-contained standalone HTML preview."""
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{scene.title}</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js"></script>
  <style>
    body {{ margin: 0; padding: 0; background-color: #0f172a; color: #f8fafc; overflow: hidden; }}
    .stage {{ width: 100vw; height: 100vh; display: flex; align-items: center; justify-content: center; }}
  </style>
</head>
<body>
  <div class="stage" data-transition="{scene.transition}" data-duration="{scene.duration_ms}">
    {scene.html_template}
  </div>
</body>
</html>"""


def tempfile_dir() -> Path:
    import tempfile
    p = Path(tempfile.gettempdir()) / "hyperframes_renders"
    p.mkdir(parents=True, exist_ok=True)
    return p
