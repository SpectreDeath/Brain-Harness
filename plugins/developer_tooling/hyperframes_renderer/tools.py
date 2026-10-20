"""Tool definitions for HyperFrames video rendering plugin."""
from __future__ import annotations

import logging
from typing import Any

from harness.services.hyperframes.models import RenderRequest, VideoScene
from harness.services.hyperframes.runtime import check_node_available
from harness.services.hyperframes.service import DefaultHyperFramesService

logger = logging.getLogger(__name__)


def hyperframes_runtime_status() -> dict[str, Any]:
    """Check Node.js and HyperFrames renderer runtime status."""
    available, desc = check_node_available()
    return {
        "status": "ok" if available else "degraded",
        "node_available": available,
        "runtime_info": desc,
    }


def hyperframes_preview_html(
    title: str,
    html_template: str,
    duration_ms: int = 3000,
    transition: str = "fade",
) -> dict[str, Any]:
    """Generate a self-contained HTML/CSS/GSAP preview for a single video scene."""
    try:
        scene = VideoScene(
            scene_id="preview_scene",
            title=title,
            duration_ms=duration_ms,
            html_template=html_template,
            transition=transition,
        )
        svc = DefaultHyperFramesService(simulate_headless=True)
        preview_html = svc.generate_scene_preview(scene)
        return {
            "status": "success",
            "preview_html": preview_html,
            "scene_id": scene.scene_id,
            "duration_ms": duration_ms,
        }
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


def hyperframes_render_trajectory_video(
    session_id: str,
    title: str = "Trajectory Playback",
    steps: list[dict[str, str]] | None = None,
    fps: int = 30,
) -> dict[str, Any]:
    """Render an agent execution trajectory into an animated video."""
    try:
        step_items = steps or [
            {"step": "Plan", "detail": f"Initial plan for session {session_id}"},
            {"step": "Action", "detail": "Executing tool invocations"},
            {"step": "Settlement", "detail": "Completed session successfully"},
        ]

        scenes: list[VideoScene] = []
        for idx, item in enumerate(step_items, start=1):
            tmpl = f"""
            <div class="flex flex-col items-center justify-center p-8 bg-slate-900 border border-slate-700 rounded-xl text-center shadow-2xl">
              <span class="text-xs font-semibold tracking-widest text-emerald-400 uppercase">Step {idx}</span>
              <h2 class="text-3xl font-bold mt-2 text-white">{item.get('step', 'Step')}</h2>
              <p class="mt-4 text-slate-300 max-w-lg">{item.get('detail', '')}</p>
            </div>
            """
            scenes.append(
                VideoScene(
                    scene_id=f"step_{idx}",
                    title=f"Step {idx}: {item.get('step')}",
                    duration_ms=2500,
                    html_template=tmpl,
                    transition="fade",
                )
            )

        req = RenderRequest(scenes=tuple(scenes), fps=fps)
        svc = DefaultHyperFramesService(simulate_headless=True)
        out = svc.render(req)

        return {
            "status": "success",
            "artifact_path": out.artifact_path,
            "duration_ms": out.duration_ms,
            "frame_count": out.frame_count,
            "size_bytes": out.size_bytes,
            "render_time_ms": out.render_time_ms,
        }
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


def hyperframes_render_pr_diff_timeline(
    pr_title: str,
    diff_text: str,
    fps: int = 30,
) -> dict[str, Any]:
    """Render a GitHub PR diff visual timeline animation."""
    try:
        lines = [line for line in diff_text.strip().splitlines() if line]
        chunks = [lines[i : i + 8] for i in range(0, min(len(lines), 32), 8)] or [["No diff content"]]

        scenes: list[VideoScene] = []
        for idx, chunk in enumerate(chunks, start=1):
            code_html = "<br/>".join(
                f'<span class="{"text-emerald-400" if c.startswith("+") else "text-rose-400" if c.startswith("-") else "text-slate-400"}">{c}</span>'
                for c in chunk
            )
            tmpl = f"""
            <div class="p-6 bg-slate-950 border border-slate-800 rounded-lg font-mono text-sm shadow-xl">
              <div class="text-indigo-400 font-bold mb-2">{pr_title} (Part {idx})</div>
              <div class="bg-black/60 p-4 rounded">{code_html}</div>
            </div>
            """
            scenes.append(
                VideoScene(
                    scene_id=f"diff_part_{idx}",
                    title=f"{pr_title} Part {idx}",
                    duration_ms=3000,
                    html_template=tmpl,
                    transition="slide",
                )
            )

        req = RenderRequest(scenes=tuple(scenes), fps=fps)
        svc = DefaultHyperFramesService(simulate_headless=True)
        out = svc.render(req)

        return {
            "status": "success",
            "artifact_path": out.artifact_path,
            "duration_ms": out.duration_ms,
            "frame_count": out.frame_count,
            "size_bytes": out.size_bytes,
        }
    except Exception as exc:
        return {"status": "error", "error": str(exc)}
