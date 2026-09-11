"""Tests for Omarchy Command Router Plugin."""

from pathlib import Path
import pytest
import sys

# Ensure Harness core is on path
_HARNESS_SRC = Path(__file__).resolve().parents[3] / "src"
if _HARNESS_SRC.exists() and str(_HARNESS_SRC) not in sys.path:
    sys.path.insert(0, str(_HARNESS_SRC))

from harness.kernel.context import ServiceContext
from plugins.developer_tooling.omarchy_command_router.main import (
    OmarchyCommandRouterServiceImpl,
    OmarchyCommandRouterPlugin,
    OMARCHY_COMMAND_ROUTER_SERVICE_KEY,
    omarchy_list_commands,
    omarchy_get_command,
    omarchy_search_commands,
    omarchy_list_groups,
    plugin,
)


@pytest.fixture
def mock_omarchy_dir(tmp_path: Path) -> Path:
    """Create a temporary directory structure mimicking Omarchy's bin layout."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(parents=True)

    # Command 1: visible theme command
    cmd1 = bin_dir / "omarchy-theme-set"
    cmd1.write_text(
        "#!/usr/bin/env bash\n"
        "# omarchy:group=theme\n"
        "# omarchy:summary=Switch desktop theme\n"
        "# omarchy:usage=omarchy-theme-set <name>\n"
        "# omarchy:examples=omarchy-theme-set tokyo-night\n"
        "# omarchy:aliases=theme-set,set-theme\n"
        "echo 'setting theme'\n",
        encoding="utf-8",
    )

    # Command 2: hidden theme command requiring sudo
    cmd2 = bin_dir / "omarchy-theme-install-internal"
    cmd2.write_text(
        "#!/usr/bin/env bash\n"
        "# omarchy:group=theme\n"
        "# omarchy:summary=Internal theme installer\n"
        "# omarchy:hidden=true\n"
        "# omarchy:requires_sudo=true\n"
        "echo 'internal'\n",
        encoding="utf-8",
    )

    # Command 3: agent command
    cmd3 = bin_dir / "omarchy-agent-status"
    cmd3.write_text(
        "#!/usr/bin/env bash\n"
        "# omarchy:group=agent\n"
        "# omarchy:summary=Check AI agent daemon status\n"
        "# omarchy:usage=omarchy-agent-status\n"
        "echo 'agent running'\n",
        encoding="utf-8",
    )

    return tmp_path


def test_command_router_metadata_parsing(mock_omarchy_dir: Path) -> None:
    service = OmarchyCommandRouterServiceImpl(source_dir=mock_omarchy_dir)
    cmds = service.list_commands(include_hidden=True)
    assert len(cmds) == 3

    theme_set = service.get_command("omarchy-theme-set")
    assert theme_set["group"] == "theme"
    assert theme_set["summary"] == "Switch desktop theme"
    assert "theme-set" in theme_set["aliases"]
    assert theme_set["hidden"] is False
    assert theme_set["requires_sudo"] is False


def test_command_router_alias_and_prefix_resolution(mock_omarchy_dir: Path) -> None:
    service = OmarchyCommandRouterServiceImpl(source_dir=mock_omarchy_dir)

    # Lookup without prefix
    cmd1 = service.get_command("theme-set")
    assert cmd1["name"] == "omarchy-theme-set"

    # Lookup via explicit alias
    cmd2 = service.get_command("set-theme")
    assert cmd2["name"] == "omarchy-theme-set"


def test_command_router_group_filtering(mock_omarchy_dir: Path) -> None:
    service = OmarchyCommandRouterServiceImpl(source_dir=mock_omarchy_dir)

    # Only visible commands
    theme_cmds = service.list_commands(group="theme", include_hidden=False)
    assert len(theme_cmds) == 1
    assert theme_cmds[0]["name"] == "omarchy-theme-set"

    # Include hidden commands
    all_theme_cmds = service.list_commands(group="theme", include_hidden=True)
    assert len(all_theme_cmds) == 2

    # Agent group
    agent_cmds = service.list_commands(group="agent")
    assert len(agent_cmds) == 1
    assert agent_cmds[0]["name"] == "omarchy-agent-status"


def test_command_router_search(mock_omarchy_dir: Path) -> None:
    service = OmarchyCommandRouterServiceImpl(source_dir=mock_omarchy_dir)

    results = service.search_commands("tokyo-night")
    assert len(results) == 1
    assert results[0]["name"] == "omarchy-theme-set"

    results_agent = service.search_commands("daemon")
    assert len(results_agent) == 1
    assert results_agent[0]["name"] == "omarchy-agent-status"


def test_command_router_list_groups(mock_omarchy_dir: Path) -> None:
    service = OmarchyCommandRouterServiceImpl(source_dir=mock_omarchy_dir)
    groups = service.list_groups()
    group_dict = {g["group"]: g for g in groups}

    assert "theme" in group_dict
    assert group_dict["theme"]["total_commands"] == 2
    assert group_dict["theme"]["visible_commands"] == 1
    assert group_dict["theme"]["hidden_commands"] == 1

    assert "agent" in group_dict
    assert group_dict["agent"]["total_commands"] == 1


def test_command_router_nonexistent_command(mock_omarchy_dir: Path) -> None:
    service = OmarchyCommandRouterServiceImpl(source_dir=mock_omarchy_dir)
    result = service.get_command("nonexistent-command-xyz")
    assert result.get("available") is False
    assert "error" in result


@pytest.mark.asyncio
async def test_command_router_plugin_lifecycle() -> None:
    context = ServiceContext()
    p = OmarchyCommandRouterPlugin()

    await p.enable(context)
    resolved = context.require(OMARCHY_COMMAND_ROUTER_SERVICE_KEY)
    assert resolved is not None
    assert hasattr(resolved, "list_commands")
    assert hasattr(resolved, "get_command")
    assert hasattr(resolved, "search_commands")
    assert hasattr(resolved, "list_groups")

    await p.disable(context)


def test_real_omarchy_source_if_available() -> None:
    """Smoke test against real Omarchy checkout if available."""
    real_path = Path(r"D:\GitHub\cloned\omarchy-quattro\omarchy-quattro")
    if not real_path.exists():
        pytest.skip("Real Omarchy checkout not found at D:\\GitHub\\cloned\\omarchy-quattro\\omarchy-quattro")

    service = OmarchyCommandRouterServiceImpl(source_dir=real_path)
    cmds = service.list_commands(include_hidden=False)
    assert len(cmds) > 100
    groups = service.list_groups()
    assert len(groups) > 10
