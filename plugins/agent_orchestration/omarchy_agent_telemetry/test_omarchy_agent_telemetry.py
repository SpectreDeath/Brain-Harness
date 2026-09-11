"""Tests for Omarchy Agent Telemetry Plugin."""

from pathlib import Path
import pytest
import sys

# Ensure Harness core is on path
_HARNESS_SRC = Path(__file__).resolve().parents[3] / "src"
if _HARNESS_SRC.exists() and str(_HARNESS_SRC) not in sys.path:
    sys.path.insert(0, str(_HARNESS_SRC))

from harness.kernel.context import ServiceContext
from plugins.agent_orchestration.omarchy_agent_telemetry.main import (
    OmarchyAgentTelemetryServiceImpl,
    OmarchyAgentTelemetryPlugin,
    OMARCHY_AGENT_TELEMETRY_SERVICE_KEY,
    omarchy_list_agent_skills,
    omarchy_get_agent_skill,
    omarchy_inspect_agent_usage_scripts,
    plugin,
)


@pytest.fixture
def mock_agent_dir(tmp_path: Path) -> Path:
    """Create mock structure for Omarchy agent skills and usage scripts."""
    # 1. Developer guides
    dev_skills = tmp_path / "agents" / "skills"
    dev_skills.mkdir(parents=True)
    (dev_skills / "acceptance-tests.md").write_text(
        "# Acceptance Tests\n\nRun automated shell tests using bats and tmux.\n",
        encoding="utf-8",
    )
    (dev_skills / "shell-dev.md").write_text(
        "# Shell Development\n\nBest practices for writing modular bash scripts.\n",
        encoding="utf-8",
    )

    # 2. Runtime skills
    rt_skills = tmp_path / "default" / "agents" / "skills"
    omarchy_skill_dir = rt_skills / "omarchy"
    omarchy_skill_dir.mkdir(parents=True)
    (omarchy_skill_dir / "SKILL.md").write_text(
        "# Omarchy Desktop Customization\n\nConfigure wallpapers, waybar, and themes.\n\n"
        "## Usage\n\nRun omarchy menu.\n\n### Hyprland Bindings\n\nSuper+Return\n",
        encoding="utf-8",
    )
    (omarchy_skill_dir / "theming.md").write_text(
        "# Theming Companion\n\nDetails on theme generation.\n",
        encoding="utf-8",
    )

    # 3. Telemetry usage scripts
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    (bin_dir / "omarchy-agent-usage-claude").write_text(
        "#!/usr/bin/python3\n"
        "# omarchy:summary=Print Claude Code usage record\n"
        "# omarchy:args=[--force]\n"
        '"""Extract Claude usage records from local project sqlite and oauth."""\n'
        "import os\n"
        "key = os.environ.get('ANTHROPIC_API_KEY')\n",
        encoding="utf-8",
    )

    return tmp_path


def test_list_agent_skills(mock_agent_dir: Path) -> None:
    service = OmarchyAgentTelemetryServiceImpl(source_dir=mock_agent_dir)
    skills = service.list_agent_skills()

    assert len(skills) == 3
    skill_names = {s["name"] for s in skills}
    assert "acceptance-tests" in skill_names
    assert "shell-dev" in skill_names
    assert "omarchy" in skill_names

    omarchy_skill = next(s for s in skills if s["name"] == "omarchy")
    assert omarchy_skill["category"] == "runtime_skill"
    assert "theming.md" in omarchy_skill["companion_docs"]


def test_get_agent_skill(mock_agent_dir: Path) -> None:
    service = OmarchyAgentTelemetryServiceImpl(source_dir=mock_agent_dir)

    # Fetch runtime skill
    omarchy_skill = service.get_agent_skill("omarchy")
    assert omarchy_skill["name"] == "omarchy"
    assert "theming.md" in omarchy_skill["companion_docs"]
    assert len(omarchy_skill["outline"]) == 3
    assert omarchy_skill["outline"][0]["title"] == "Omarchy Desktop Customization"
    assert omarchy_skill["outline"][1]["title"] == "Usage"
    assert omarchy_skill["outline"][2]["title"] == "Hyprland Bindings"

    # Fetch developer guide
    guide = service.get_agent_skill("acceptance-tests")
    assert guide["name"] == "acceptance-tests"
    assert "Acceptance Tests" in guide["content"]

    # Fetch nonexistent skill
    nonexistent = service.get_agent_skill("unknown-skill")
    assert "error" in nonexistent


def test_inspect_agent_usage_scripts(mock_agent_dir: Path) -> None:
    service = OmarchyAgentTelemetryServiceImpl(source_dir=mock_agent_dir)
    scripts = service.inspect_agent_usage_scripts()

    assert len(scripts) == 1
    claude_script = scripts[0]
    assert claude_script["script_name"] == "omarchy-agent-usage-claude"
    assert claude_script["target_provider"] == "anthropic_claude"
    assert claude_script["summary"] == "Print Claude Code usage record"
    assert "ANTHROPIC_API_KEY" in claude_script["env_vars_detected"]
    assert "Extract Claude usage records" in claude_script["docstring"]


@pytest.mark.asyncio
async def test_agent_telemetry_plugin_lifecycle() -> None:
    context = ServiceContext()
    p = OmarchyAgentTelemetryPlugin()

    await p.enable(context)
    resolved = context.require(OMARCHY_AGENT_TELEMETRY_SERVICE_KEY)
    assert resolved is not None
    assert hasattr(resolved, "list_agent_skills")
    assert hasattr(resolved, "get_agent_skill")
    assert hasattr(resolved, "inspect_agent_usage_scripts")

    await p.disable(context)


def test_real_omarchy_agent_skills_if_available() -> None:
    real_path = Path(r"D:\GitHub\cloned\omarchy-quattro\omarchy-quattro")
    if not real_path.exists():
        pytest.skip("Real Omarchy checkout not found")

    service = OmarchyAgentTelemetryServiceImpl(source_dir=real_path)
    skills = service.list_agent_skills()
    assert len(skills) >= 9

    # Test real usage scripts
    scripts = service.inspect_agent_usage_scripts()
    assert len(scripts) >= 3
    names = {s["script_name"] for s in scripts}
    assert "omarchy-agent-usage-claude" in names
    assert "omarchy-agent-usage-codex" in names
    assert "omarchy-agent-usage-fireworks" in names
