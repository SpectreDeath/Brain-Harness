"""Tests for Webwright Harness Plugin and Kernel Service Integration."""

import json
import tempfile
from pathlib import Path
import pytest

from harness.kernel.context import ServiceContext
from harness.services.webwright_harness import (
    WEBWRIGHT_HARNESS_KEY,
    WebwrightBrowserStatus,
    WebwrightHarnessService,
    WebwrightImageQAResult,
    WebwrightLearnResult,
    WebwrightRetrieveResult,
    WebwrightRouteResult,
    WebwrightSelfReflectionResult,
)
from plugins.integration_and_io.webwright_harness import (
    WebwrightHarnessEngine,
    WebwrightHarnessPlugin,
)
from plugins.integration_and_io.webwright_harness.main import (
    webwright_browser_session_manage,
    webwright_image_qa,
    webwright_self_reflection,
    webwright_skill_learn,
    webwright_skill_retrieve,
    webwright_skill_route_and_execute,
)


@pytest.fixture
def temp_workspace(tmp_path: Path) -> Path:
    """Create a temporary workspace with mock trajectory runs."""
    traj_dir = tmp_path / "trajectories" / "traj_1"
    traj_dir.mkdir(parents=True, exist_ok=True)

    task_json = {"task": "Find flight from SFO to BOS", "task_id": "sfo_bos"}
    agent_resp = {"retrieved_data": [{"flight": "UA101", "price": "$350"}]}
    script_content = (
        "def solve(params):\n"
        "    return {'flight': 'UA101', 'origin': params.get('origin', 'SFO'), 'destination': params.get('destination', 'BOS')}\n"
    )

    (traj_dir / "task.json").write_text(json.dumps(task_json), encoding="utf-8")
    (traj_dir / "agent_response.json").write_text(json.dumps(agent_resp), encoding="utf-8")
    (traj_dir / "final_script.py").write_text(script_content, encoding="utf-8")

    return tmp_path


@pytest.mark.unit
def test_webwright_skill_learning_and_retrieval(temp_workspace: Path):
    """Test trajectory learning and semantic retrieval."""
    engine = WebwrightHarnessEngine(base_dir=temp_workspace)
    traj_path = str(temp_workspace / "trajectories" / "traj_1")

    # 1. Learn skill
    learn_res = engine.learn_skill(
        trajectory_dirs=[traj_path],
        template="Find flight from {origin} to {destination}",
        library_dir="skills",
    )
    assert learn_res["status"] == "ok"
    assert learn_res["skill_id"] is not None
    assert "origin" in learn_res["signature"]["params"]
    assert "destination" in learn_res["signature"]["params"]
    assert Path(learn_res["file_path"]).exists()

    # 2. Retrieve skill
    ret_res = engine.retrieve_skills(
        task="Find flight from Seattle to New York",
        k=3,
        library_dir="skills",
    )
    assert ret_res["status"] == "ok"
    assert len(ret_res["candidates"]) >= 1
    assert ret_res["candidates"][0]["skill_id"] == learn_res["skill_id"]


@pytest.mark.unit
def test_webwright_routing_and_execution(temp_workspace: Path):
    """Test routing decision and direct skill execution."""
    engine = WebwrightHarnessEngine(base_dir=temp_workspace)
    traj_path = str(temp_workspace / "trajectories" / "traj_1")

    # Learn skill first
    engine.learn_skill(
        trajectory_dirs=[traj_path],
        template="Find flight from {origin} to {destination}",
        library_dir="skills",
    )

    # Route matching task
    route_res = engine.route_and_execute(
        task="Find flight from SFO to BOS",
        start_url="https://flights.example.com",
        library_dir="skills",
    )
    assert route_res["status"] == "ok"
    assert route_res["decision"] == "run"
    assert route_res["result"] is not None
    assert route_res["result"].get("flight") == "UA101"

    # Route unmatched task (fallback to skip)
    unmatched = engine.route_and_execute(
        task="Summarize this PDF document completely",
        start_url="https://pdf.example.com",
        library_dir="skills",
    )
    assert unmatched["decision"] == "skip"


@pytest.mark.unit
def test_webwright_browser_session_lifecycle(temp_workspace: Path):
    """Test Chromium browser daemon create, info, release."""
    engine = WebwrightHarnessEngine(base_dir=temp_workspace)

    # 1. Info before create
    info_before = engine.manage_browser_session(action="info", port=9250)
    assert info_before["status"] == "not_running"

    # 2. Create daemon
    create_res = engine.manage_browser_session(action="create", port=9250)
    assert create_res["status"] == "ok"
    assert create_res["pid"] is not None
    assert create_res["cdp_url"] == "http://127.0.0.1:9250"

    # 3. Info after create
    info_after = engine.manage_browser_session(action="info", port=9250)
    assert info_after["status"] == "ok"
    assert info_after["pid"] == create_res["pid"]

    # 4. Release daemon
    rel_res = engine.manage_browser_session(action="release", port=9250)
    assert rel_res["status"] == "ok"


@pytest.mark.unit
def test_webwright_image_qa_and_self_reflection(temp_workspace: Path):
    """Test multimodal image QA and trajectory self reflection."""
    engine = WebwrightHarnessEngine(base_dir=temp_workspace)

    # Create dummy screenshot
    shot_dir = temp_workspace / "screenshots"
    shot_dir.mkdir(parents=True, exist_ok=True)
    shot_file = shot_dir / "step_1.png"
    shot_file.write_bytes(b"mock_png_bytes_data")

    # Image QA
    qa_res = engine.image_qa(
        image_path=str(shot_file),
        question="Is the search results table visible?",
    )
    assert qa_res["status"] == "ok"
    assert qa_res["confidence"] > 0.8

    # Self Reflection
    refl_res = engine.self_reflect(
        task="Find flight from SFO to BOS",
        screenshots_dir=str(shot_dir),
        action_history=["navigated to flights", "typed SFO", "typed BOS", "selected flight UA101"],
    )
    assert refl_res["status"] == "ok"
    assert refl_res["verdict"] == "success"
    assert refl_res["confidence"] >= 0.9


@pytest.mark.asyncio
async def test_webwright_plugin_service_integration():
    """Test WebwrightHarnessPlugin service registration and IoC context resolution."""
    plugin = WebwrightHarnessPlugin()
    ctx = ServiceContext()

    assert WEBWRIGHT_HARNESS_KEY in plugin.provides

    await plugin.on_load(ctx)
    await plugin.on_enable()

    service = ctx.require(WEBWRIGHT_HARNESS_KEY)
    assert service is not None

    status = await service.manage_browser_session(action="create", port=9288)
    assert isinstance(status, WebwrightBrowserStatus)
    assert status.status == "ok"

    await plugin.on_disable()
    await plugin.on_unload()
