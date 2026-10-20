"""Subprocess JSON-RPC bridge for HyperFrames with pipe drainage."""
from __future__ import annotations

import asyncio
from collections import deque
import json
import logging
import os
from pathlib import Path
import tempfile
import time
from typing import Any

from harness.services.hyperframes.models import RenderOutput, RenderRequest, VideoScene
from harness.services.hyperframes.runtime import check_node_available

logger = logging.getLogger(__name__)


class HyperFramesBridgeError(RuntimeError):
    """Raised when HyperFrames subprocess execution fails."""


class HyperFramesSubprocessBridge:
    """IPC Bridge to Node.js HyperFrames renderer adhering to Rules 14 and 56."""

    def __init__(self, node_timeout_s: float = 120.0, simulate_headless: bool = False) -> None:
        self._node_timeout_s = node_timeout_s
        self._simulate_headless = simulate_headless

    async def render(self, request: RenderRequest, output_dir: Path | None = None) -> RenderOutput:
        """Execute video render via Node.js CLI or headless simulation."""
        target_dir = output_dir or Path(tempfile.gettempdir()) / "hyperframes_renders"
        target_dir.mkdir(parents=True, exist_ok=True)

        is_avail, desc = check_node_available()
        if not is_avail or self._simulate_headless:
            return self._render_simulated(request, target_dir)

        return await self._render_subprocess(request, target_dir)

    def _render_simulated(self, request: RenderRequest, target_dir: Path) -> RenderOutput:
        """Headless simulation fallback when Node is unavailable or under CI."""
        start_t = time.perf_counter()
        total_duration_ms = sum(s.duration_ms for s in request.scenes)
        frame_count = int((total_duration_ms / 1000.0) * request.fps)

        slug = request.scenes[0].scene_id.lower().replace(" ", "_")
        out_filename = f"{slug}_{int(time.time())}.{request.output_format}"
        out_path = target_dir / out_filename

        # Write simulated video metadata artifact
        html_bundle = "\n<hr/>\n".join(
            f"<!-- Scene: {s.scene_id} ({s.duration_ms}ms) -->\n{s.html_template}"
            for s in request.scenes
        )
        simulated_payload = {
            "title": request.scenes[0].title,
            "scene_count": len(request.scenes),
            "total_duration_ms": total_duration_ms,
            "fps": request.fps,
            "resolution": request.resolution,
            "format": request.output_format,
            "html_bundle": html_bundle,
            "simulated": True,
        }
        out_path.write_text(json.dumps(simulated_payload, indent=2), encoding="utf-8")

        render_ms = (time.perf_counter() - start_t) * 1000.0
        return RenderOutput(
            artifact_path=str(out_path),
            duration_ms=total_duration_ms,
            frame_count=frame_count,
            size_bytes=out_path.stat().st_size,
            render_time_ms=round(render_ms, 2),
            metadata={"renderer": "simulated_headless", "scene_count": len(request.scenes)},
        )

    async def _render_subprocess(self, request: RenderRequest, target_dir: Path) -> RenderOutput:
        """Run JSON-RPC subprocess with Rule 14 pipe drainage and Rule 56 loopback."""
        start_t = time.perf_counter()
        total_duration_ms = sum(s.duration_ms for s in request.scenes)
        frame_count = int((total_duration_ms / 1000.0) * request.fps)

        slug = request.scenes[0].scene_id.lower().replace(" ", "_")
        out_filename = f"{slug}_{int(time.time())}.{request.output_format}"
        out_path = target_dir / out_filename

        env = os.environ.copy()
        # Rule 56: Preserve local loopback connections
        env.setdefault("NO_PROXY", "127.0.0.1,localhost,::1")

        cmd = ["npx", "@heygen/hyperframes", "render", "--headless", "--out", str(out_path)]
        stderr_ring: deque[str] = deque(maxlen=50)
        proc: asyncio.subprocess.Process | None = None

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )

            async def _drain_stderr() -> None:
                if proc and proc.stderr:
                    while True:
                        line = await proc.stderr.readline()
                        if not line:
                            break
                        stderr_ring.append(line.decode("utf-8", errors="replace").strip())

            drain_task = asyncio.create_task(_drain_stderr())

            payload = {
                "jsonrpc": "2.0",
                "method": "renderScenes",
                "params": {
                    "scenes": [
                        {
                            "id": s.scene_id,
                            "title": s.title,
                            "duration": s.duration_ms,
                            "template": s.html_template,
                            "transition": s.transition,
                        }
                        for s in request.scenes
                    ],
                    "fps": request.fps,
                    "resolution": request.resolution,
                    "format": request.output_format,
                },
            }

            if proc.stdin:
                proc.stdin.write(json.dumps(payload).encode("utf-8"))
                await proc.stdin.drain()
                proc.stdin.close()

            await asyncio.wait_for(proc.wait(), timeout=self._node_timeout_s)
            await drain_task

            if proc.returncode != 0:
                err_summary = "\n".join(stderr_ring) or f"Exit code {proc.returncode}"
                raise HyperFramesBridgeError(f"HyperFrames render failed: {err_summary}")

            render_ms = (time.perf_counter() - start_t) * 1000.0
            size_b = out_path.stat().st_size if out_path.exists() else 0
            return RenderOutput(
                artifact_path=str(out_path),
                duration_ms=total_duration_ms,
                frame_count=frame_count,
                size_bytes=size_b,
                render_time_ms=round(render_ms, 2),
                metadata={"renderer": "npx_hyperframes", "scene_count": len(request.scenes)},
            )
        finally:
            # Rule 14: Subprocess Pipe Transport Disposal Invariant
            if proc is not None:
                if proc.stdin and not proc.stdin.is_closing():
                    try:
                        proc.stdin.close()
                    except Exception:
                        pass
                if proc.returncode is None:
                    try:
                        proc.kill()
                    except Exception:
                        pass
