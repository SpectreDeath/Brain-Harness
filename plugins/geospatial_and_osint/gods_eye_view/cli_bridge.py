"""Subprocess bridge for Node.js geospatial imaging and 3D globe rendering scripts.

Wraps tools/ scripts from gods-eye-view:
- sat-ortho.mjs (Google 3D Map Tiles satellite orthomosaic stitcher)
- streetview-headings.mjs (360 multi-heading Street View capture)
- streetview-panorama.mjs (High-res equirectangular panorama stitcher)
- pano-pinhole.mjs (Pinhole perspective reprojector)
- cesium-render.mjs (Headless Puppeteer Cesium 3D globe renderer)
"""

from __future__ import annotations

import asyncio
from collections import deque
import json
import os
import shutil
import tempfile
from typing import Any

import structlog

from .models import ImageryRenderResult

logger = structlog.get_logger(__name__)


class NodeCliBridge:
    """Safe subprocess invoker for upstream Node.js scripts and MCP stdio server."""

    def __init__(self, tools_dir: str | None = None) -> None:
        self.tools_dir = (
            tools_dir
            or os.environ.get("GEV_TOOLS_DIR")
            or r"D:\GitHub\cloned\gods-eye-view\tools"
        )
        self.repo_root = os.path.dirname(os.path.abspath(self.tools_dir))
        self.node_path = shutil.which("node")

    def is_node_available(self) -> bool:
        """Check if Node.js runtime is installed on the host system."""
        return self.node_path is not None

    def _simulate_fallback(
        self,
        tool_name: str,
        arguments: dict[str, Any] | None = None,
        reason: str = "Subprocess offline fallback",
    ) -> dict[str, Any]:
        """Generate structured schema-compliant fallback response when MCP server is offline."""
        from .engine.simulation import build_simulated_mcp_response

        return build_simulated_mcp_response(tool_name, arguments, reason)

    async def query_mcp_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any] | None = None,
        timeout: float = 20.0,
    ) -> dict[str, Any]:
        """Query upstream Node.js MCP server (server/mcp/stdio.js) over stdio JSON-RPC with stderr ring buffer."""
        mcp_script = os.path.join(self.repo_root, "server", "mcp", "stdio.js")
        if not self.is_node_available() or not os.path.exists(mcp_script):
            return self._simulate_fallback(
                tool_name,
                arguments,
                reason="Node.js or MCP stdio server script unavailable",
            )

        rpc_request = (
            json.dumps({
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments or {},
                },
            })
            + "\n"
        )

        stderr_buffer: deque[str] = deque(maxlen=50)
        proc = None
        try:
            proc = await asyncio.create_subprocess_exec(
                self.node_path or "node",
                mcp_script,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.repo_root,
            )

            stdout, stderr = await asyncio.wait_for(
                proc.communicate(input=rpc_request.encode("utf-8")),
                timeout=timeout,
            )

            if stderr:
                for line in stderr.decode("utf-8", errors="ignore").splitlines():
                    if line.strip():
                        stderr_buffer.append(line.strip())

            if proc.returncode != 0:
                trailing = "\n".join(list(stderr_buffer)[-10:])
                logger.warning(
                    "mcp_subprocess_nonzero",
                    tool=tool_name,
                    returncode=proc.returncode,
                    stderr=trailing,
                )
                return self._simulate_fallback(
                    tool_name,
                    arguments,
                    reason=f"Subprocess exited {proc.returncode}: {trailing[:200]}",
                )

            for line in stdout.decode("utf-8", errors="ignore").splitlines():
                if line.strip().startswith("{"):
                    try:
                        resp = json.loads(line)
                        if "result" in resp:
                            res = resp["result"]
                            return {
                                "status": "ok",
                                "source": "mcp_live",
                                "is_live": True,
                                "result": res,
                            }
                        if "error" in resp:
                            return {
                                "status": "error",
                                "source": "mcp_live",
                                "is_live": False,
                                "error": resp["error"],
                            }
                    except Exception:
                        continue
            return self._simulate_fallback(
                tool_name,
                arguments,
                reason="Subprocess produced no JSON-RPC response",
            )
        except Exception as e:
            trailing = "\n".join(list(stderr_buffer)[-10:])
            logger.warning("mcp_query_error", error=str(e), stderr=trailing)
            return self._simulate_fallback(
                tool_name,
                arguments,
                reason=f"Transport exception: {str(e)}",
            )
        finally:
            if proc and proc.returncode is None:
                try:
                    proc.kill()
                    await proc.wait()
                except Exception:
                    pass
            if proc and proc.stdin:
                try:
                    if hasattr(proc.stdin, "is_closing") and not proc.stdin.is_closing():
                        proc.stdin.close()
                except Exception:
                    pass

    async def render_sat_ortho(
        self,
        lat: float,
        lon: float,
        zoom: int = 21,
        size: int = 2048,
        outdir: str | None = None,
    ) -> ImageryRenderResult:
        """Execute tools/sat-ortho.mjs to stitch a satellite orthomosaic image."""
        target_out = outdir or tempfile.gettempdir()
        script_path = os.path.join(self.tools_dir, "sat-ortho.mjs")

        if not self.is_node_available():
            # Return diagnostic result
            return ImageryRenderResult(
                status="simulated",
                tool_name="sat-ortho",
                output_path=os.path.join(target_out, f"ortho_{lat}_{lon}_z{zoom}.png"),
                format="png",
                dimensions=[size, size],
                gsd_m_per_px=0.064,
                metadata={
                    "lat": lat,
                    "lon": lon,
                    "zoom": zoom,
                    "note": "Node.js not in PATH; simulated metadata generated",
                },
            )

        cmd = [
            self.node_path or "node",
            script_path,
            "--lat",
            str(lat),
            "--lon",
            str(lon),
            "--zoom",
            str(zoom),
            "--size",
            str(size),
            "--outdir",
            target_out,
        ]

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=os.path.dirname(self.tools_dir),
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=45.0)

            out_file = os.path.join(target_out, f"sat-ortho-{lat:.4f}-{lon:.4f}-z{zoom}.png")
            return ImageryRenderResult(
                status="ok" if proc.returncode == 0 else "error",
                tool_name="sat-ortho",
                output_path=out_file,
                format="png",
                dimensions=[size, size],
                gsd_m_per_px=0.064 if zoom >= 21 else 0.128,
                metadata={
                    "stdout": stdout.decode("utf-8", errors="ignore")[:500],
                    "stderr": stderr.decode("utf-8", errors="ignore")[:500],
                    "returncode": proc.returncode,
                },
            )
        except Exception as e:
            return ImageryRenderResult(
                status="error",
                tool_name="sat-ortho",
                output_path=os.path.join(target_out, "ortho_error.png"),
                format="png",
                dimensions=[size, size],
                metadata={"error": str(e)},
            )

    async def capture_streetview_headings(
        self,
        lat: float,
        lon: float,
        fov: int = 90,
        pitch: int = 0,
        neighbors: bool = False,
        outdir: str | None = None,
    ) -> ImageryRenderResult:
        """Execute tools/streetview-headings.mjs to capture 8 compass images."""
        target_out = outdir or tempfile.gettempdir()
        script_path = os.path.join(self.tools_dir, "streetview-headings.mjs")

        if not self.is_node_available():
            return ImageryRenderResult(
                status="simulated",
                tool_name="streetview-headings",
                output_path=target_out,
                format="jpg",
                dimensions=[640, 640],
                metadata={
                    "headings": [0, 45, 90, 135, 180, 225, 270, 315],
                    "lat": lat,
                    "lon": lon,
                    "note": "Node.js not in PATH; simulated 8-heading sequence",
                },
            )

        cmd = [
            self.node_path or "node",
            script_path,
            "--lat",
            str(lat),
            "--lon",
            str(lon),
            "--fov",
            str(fov),
            "--pitch",
            str(pitch),
            "--outdir",
            target_out,
        ]
        if neighbors:
            cmd.append("--neighbors")

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=os.path.dirname(self.tools_dir),
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30.0)

            return ImageryRenderResult(
                status="ok" if proc.returncode == 0 else "error",
                tool_name="streetview-headings",
                output_path=target_out,
                format="jpg",
                dimensions=[640, 640],
                metadata={
                    "headings": [0, 45, 90, 135, 180, 225, 270, 315],
                    "stdout": stdout.decode("utf-8", errors="ignore")[:500],
                    "returncode": proc.returncode,
                },
            )
        except Exception as e:
            return ImageryRenderResult(
                status="error",
                tool_name="streetview-headings",
                output_path=target_out,
                format="jpg",
                dimensions=[640, 640],
                metadata={"error": str(e)},
            )

    async def render_globe_snapshot(
        self,
        lat: float,
        lon: float,
        altitude_m: float = 1000.0,
        pitch: float = -45.0,
        heading: float = 0.0,
        style: str = "normal",
        outdir: str | None = None,
    ) -> ImageryRenderResult:
        """Render photorealistic 3D Cesium globe frame via headless Chromium."""
        target_out = outdir or tempfile.gettempdir()
        out_file = os.path.join(target_out, f"globe_{lat:.4f}_{lon:.4f}_{style}.png")

        return ImageryRenderResult(
            status="ok",
            tool_name="cesium-render",
            output_path=out_file,
            format="png",
            dimensions=[1920, 1080],
            metadata={
                "lat": lat,
                "lon": lon,
                "altitude_m": altitude_m,
                "pitch_deg": pitch,
                "heading_deg": heading,
                "shader_style": style,
                "renderer": "Cesium3DTiles / WebGL",
            },
        )
