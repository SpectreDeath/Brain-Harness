"""Contract tests for HyperFrames multimedia rendering service and plugin."""
from __future__ import annotations

import os
from pathlib import Path
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from harness.kernel.context import ServiceContext
from harness.services.hyperframes import (
    HYPERFRAMES_SERVICE_KEY,
    DefaultHyperFramesService,
    HyperFramesService,
    RenderOutput,
    RenderRequest,
    VideoScene,
    check_node_available,
    resolve_hyperframes,
)
from plugins.developer_tooling.hyperframes_renderer.main import HyperFramesPlugin
from plugins.developer_tooling.hyperframes_renderer.tools import (
    hyperframes_preview_html,
    hyperframes_render_pr_diff_timeline,
    hyperframes_render_trajectory_video,
    hyperframes_runtime_status,
)


def test_video_scene_immutability_and_validation() -> None:
    """VideoScene enforces slotted frozen semantics and field constraints."""
    scene = VideoScene(
        scene_id="intro",
        title="Welcome",
        duration_ms=3000,
        html_template="<div>Hello</div>",
        transition="fade",
    )
    assert scene.scene_id == "intro"
    assert scene.duration_ms == 3000

    # Rule 43: Immutability via direct assignment
    with pytest.raises((AttributeError, TypeError)):
        scene.duration_ms = 4000  # type: ignore

    with pytest.raises(ValueError, match="scene_id must not be empty"):
        VideoScene(scene_id="", title="A", duration_ms=1000, html_template="<div/>")

    with pytest.raises(ValueError, match="duration_ms must be positive"):
        VideoScene(scene_id="s1", title="A", duration_ms=0, html_template="<div/>")

    with pytest.raises(ValueError, match="Invalid transition"):
        VideoScene(scene_id="s1", title="A", duration_ms=1000, html_template="<div/>", transition="warp")


def test_render_request_validation() -> None:
    """RenderRequest enforces non-empty scene lists and bounds."""
    scene = VideoScene(scene_id="s1", title="A", duration_ms=2000, html_template="<div/>")
    req = RenderRequest(scenes=(scene,), fps=30, resolution=(1280, 720))
    assert len(req.scenes) == 1
    assert req.fps == 30

    with pytest.raises(ValueError, match="scenes must contain at least one VideoScene"):
        RenderRequest(scenes=())

    with pytest.raises(ValueError, match="fps must be between 1 and 120"):
        RenderRequest(scenes=(scene,), fps=0)

    with pytest.raises(ValueError, match="resolution must be a tuple of two positive integers"):
        RenderRequest(scenes=(scene,), resolution=(0, 720))

    with pytest.raises(ValueError, match="Unsupported output_format"):
        RenderRequest(scenes=(scene,), output_format="avi")


def test_check_node_available_mocked() -> None:
    """Runtime check returns structured tuple indicating Node.js status."""
    with patch("shutil.which", return_value=None):
        avail, msg = check_node_available()
        assert not avail
        assert "not found" in msg

    with patch("shutil.which", side_effect=lambda cmd: f"/usr/bin/{cmd}"),          patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="v20.10.0\n")
        avail, msg = check_node_available()
        assert avail
        assert "Node.js v20.10.0" in msg


@pytest.mark.asyncio
async def test_hyperframes_service_simulated_render() -> None:
    """DefaultHyperFramesService executes simulated render creating verifiable artifact."""
    with tempfile.TemporaryDirectory() as tmpdir:
        out_dir = Path(tmpdir)
        service = DefaultHyperFramesService(simulate_headless=True, output_dir=out_dir)

        scene = VideoScene(
            scene_id="scene_intro",
            title="Overview",
            duration_ms=2000,
            html_template="<div class=\"title\">Intro</div>",
        )
        req = RenderRequest(scenes=(scene,), fps=30)

        out = await service.render_async(req)
        assert isinstance(out, RenderOutput)
        assert out.duration_ms == 2000
        assert out.frame_count == 60
        assert Path(out.artifact_path).exists()
        assert out.metadata.get("renderer") == "simulated_headless"


def test_hyperframes_preview_generation() -> None:
    """Service generates complete HTML preview containing Tailwind and GSAP."""
    service = DefaultHyperFramesService()
    scene = VideoScene(
        scene_id="preview_1",
        title="Motion Test",
        duration_ms=2500,
        html_template="<h1 class=\"text-2xl\">Test</h1>",
    )
    html = service.generate_scene_preview(scene)
    assert "<title>Motion Test</title>" in html
    assert "cdn.tailwindcss.com" in html
    assert "gsap.min.js" in html


@pytest.mark.asyncio
async def test_hyperframes_plugin_lifecycle_and_ioc() -> None:
    """Plugin loads into ServiceContext and provides typed service key."""
    plugin = HyperFramesPlugin()
    assert HYPERFRAMES_SERVICE_KEY in plugin.provides
    assert plugin.requires == []

    context = ServiceContext()
    await plugin.on_load(context)

    svc = resolve_hyperframes(context)
    assert isinstance(svc, HyperFramesService)
    assert isinstance(svc, DefaultHyperFramesService)


def test_hyperframes_tools_execution() -> None:
    """Plugin tools execute and return valid response dictionaries."""
    status = hyperframes_runtime_status()
    assert "status" in status
    assert "node_available" in status

    preview = hyperframes_preview_html(
        title="Sample",
        html_template="<p>Test Content</p>",
    )
    assert preview["status"] == "success"
    assert "<!DOCTYPE html>" in preview["preview_html"]

    traj = hyperframes_render_trajectory_video(
        session_id="test_sess_01",
        title="Agent Step Walkthrough",
    )
    assert traj["status"] == "success"
    assert "artifact_path" in traj
    assert traj["duration_ms"] > 0

    diff = hyperframes_render_pr_diff_timeline(
        pr_title="PR #104 Refactor",
        diff_text="+ def new_code():\n+     return 42\n- def old_code(): pass",
    )
    assert diff["status"] == "success"
    assert "artifact_path" in diff
