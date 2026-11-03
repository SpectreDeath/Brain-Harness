"""Contract verification tests for Track 10b: Dock leftovers and security guarantees."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
from click.testing import CliRunner
import pytest
import yaml

from harness.cli import main
from harness.kernel.context import ServiceContext
from harness.kernel.runtime.factory import create_runtime
from harness.kernel.runtime.lifecycle_runner import start_runtime
from harness.services.dock import (
    DOCK_SERVICE_KEY,
    DefaultDockService,
    DockBoundaries,
    DockBoundaryViolationError,
    DockManifest,
    DockPermissions,
    DockProcedure,
    DockStep,
    resolve_dock_service,
)


@pytest.fixture
def isolated_dock_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    state_file = tmp_path / "test_docks_state.json"
    monkeypatch.setenv("HARNESS_DOCKS_STATE_FILE", str(state_file))
    return tmp_path, state_file


def test_dock_env_scrubbing(isolated_dock_env: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch) -> None:
    """Test Hole 1: Subprocess execution scrubs TOKEN, SECRET, PASSWORD, and KEY from environment."""
    tmp_path, state_file = isolated_dock_env
    repo_dir = tmp_path / "test_repo"
    repo_dir.mkdir()

    # Set secret environment variables
    monkeypatch.setenv("HARNESS_TEST_TOKEN", "super-secret-token")
    monkeypatch.setenv("AGENT_SECRET_KEY", "sensitive-secret-val")
    monkeypatch.setenv("USER_PASSWORD_HASH", "do-not-leak")
    monkeypatch.setenv("SAFE_PATH_VAR", "allowlisted-value")

    probe_script = repo_dir / "probe_env.py"
    probe_script.write_text(
        "import os\n"
        "leaked = [k for k in os.environ if any(x in k.upper() for x in ['TOKEN', 'SECRET', 'PASSWORD'])]\n"
        "print('LEAKED_COUNT=' + str(len(leaked)))\n",
        encoding="utf-8",
    )

    manifest_data = {
        "name": "env-scrub-dock",
        "description": "Dock verifying environment scrubbing",
        "permissions": {"read": True, "run": True, "write": False, "push": False},
        "boundaries": {"paths": [], "operations": []},
        "entrypoints": {
            "probe": {
                "description": "Probe environment variables",
                "steps": [
                    {
                        "command": f'"{sys.executable}" probe_env.py',
                        "workdir": ".",
                        "expected_output": "LEAKED_COUNT=0",
                    }
                ],
            }
        },
    }
    (repo_dir / "dock.yaml").write_text(yaml.dump(manifest_data), encoding="utf-8")

    service = DefaultDockService(workspace_root=tmp_path, state_file=state_file)
    service.link(str(repo_dir), approve=True)

    result = service.run("env-scrub-dock", "probe")
    assert result.success is True, f"Procedure failed: {result.error}"
    assert "LEAKED_COUNT=0" in result.steps[0].stdout


def test_dock_step_failure_stops(isolated_dock_env: tuple[Path, Path]) -> None:
    """Test Hole 2: Execution stops immediately upon step failure; subsequent steps are skipped."""
    tmp_path, state_file = isolated_dock_env
    repo_dir = tmp_path / "test_repo"
    repo_dir.mkdir()

    canary_file = repo_dir / "canary.txt"
    manifest_data = {
        "name": "step-stop-dock",
        "description": "Dock verifying step failure stops sequence",
        "permissions": {"read": True, "run": True, "write": True, "push": False},
        "boundaries": {"paths": [], "operations": []},
        "entrypoints": {
            "failing-seq": {
                "description": "Sequence that fails on step 1",
                "steps": [
                    {
                        "command": f'"{sys.executable}" -c "import sys; sys.exit(42)"',
                        "workdir": ".",
                    },
                    {
                        "command": f'"{sys.executable}" -c "from pathlib import Path; Path(\'{canary_file.name}\').write_text(\'touched\')"',
                        "workdir": ".",
                    },
                ],
            }
        },
    }
    (repo_dir / "dock.yaml").write_text(yaml.dump(manifest_data), encoding="utf-8")

    service = DefaultDockService(workspace_root=tmp_path, state_file=state_file)
    service.link(str(repo_dir), approve=True)

    result = service.run("step-stop-dock", "failing-seq")
    assert result.success is False
    assert result.failed_step_index == 1
    assert len(result.steps) == 1
    assert result.steps[0].returncode == 42
    assert not canary_file.exists(), "Step 2 must NOT run when step 1 fails"


def test_dock_expected_output_mismatch(isolated_dock_env: tuple[Path, Path]) -> None:
    """Test Hole 3: expected_output mismatch converts exit 0 to failure with code 1 and diagnostic."""
    tmp_path, state_file = isolated_dock_env
    repo_dir = tmp_path / "test_repo"
    repo_dir.mkdir()

    manifest_data = {
        "name": "expected-out-dock",
        "description": "Dock verifying expected_output enforcement",
        "permissions": {"read": True, "run": True, "write": False, "push": False},
        "boundaries": {"paths": [], "operations": []},
        "entrypoints": {
            "mismatch-proc": {
                "description": "Procedure with expected_output mismatch",
                "steps": [
                    {
                        "command": f'"{sys.executable}" -c "print(\'actual output\')"',
                        "workdir": ".",
                        "expected_output": "required secret token",
                    }
                ],
            }
        },
    }
    (repo_dir / "dock.yaml").write_text(yaml.dump(manifest_data), encoding="utf-8")

    service = DefaultDockService(workspace_root=tmp_path, state_file=state_file)
    service.link(str(repo_dir), approve=True)

    result = service.run("expected-out-dock", "mismatch-proc")
    assert result.success is False
    assert result.steps[0].returncode == 1
    assert "Expected output 'required secret token' not found" in result.steps[0].stderr


def test_dock_boundary_refusal_through_run(isolated_dock_env: tuple[Path, Path]) -> None:
    """Test Hole 4: service.run() refuses boundary-violating steps before executing any subprocess."""
    tmp_path, state_file = isolated_dock_env
    repo_dir = tmp_path / "test_repo"
    repo_dir.mkdir()

    manifest_data = {
        "name": "boundary-dock",
        "description": "Dock testing boundary refusal",
        "permissions": {"read": True, "run": True, "write": False, "push": False},
        "boundaries": {
            "paths": [".git/", ".env"],
            "operations": ["git push --force"],
        },
        "entrypoints": {
            "read-env": {
                "description": "Attempt to access boundary path .env",
                "steps": [
                    {
                        "command": "cat .env",
                        "workdir": ".",
                    }
                ],
            }
        },
    }
    (repo_dir / "dock.yaml").write_text(yaml.dump(manifest_data), encoding="utf-8")

    service = DefaultDockService(workspace_root=tmp_path, state_file=state_file)
    service.link(str(repo_dir), approve=True)

    with pytest.raises(DockBoundaryViolationError) as exc_info:
        service.run("boundary-dock", "read-env")
    assert "boundary violation" in str(exc_info.value).lower()


def test_dock_cli_inspect_generic_fallback(tmp_path: Path) -> None:
    """Test Hole 5: CLI inspect falls back to synthesized generic dock when dock.yaml is absent."""
    empty_repo = tmp_path / "unadorned_repo"
    empty_repo.mkdir()

    runner = CliRunner()
    result = runner.invoke(main, ["dock", "inspect", str(empty_repo), "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)

    assert data["name"] == "unadorned_repo"
    assert data["declared"] is False
    assert "permissions" in data
    assert "boundaries" in data
    assert len(data["tools"]) > 0


@pytest.mark.asyncio
async def test_dock_service_ioc_registration(tmp_path: Path) -> None:
    """Test Hole 6: DOCK_SERVICE_KEY is provided in ServiceContext upon runtime startup."""
    from harness.kernel.runtime import HarnessRuntime

    runtime = create_runtime(
        HarnessRuntime,
        plugin_dirs=[tmp_path / "plugins"],
        auto_load_user_plugins=False,
    )
    await start_runtime(runtime)
    assert runtime.context.has(DOCK_SERVICE_KEY)
    resolved = runtime.context.require(DOCK_SERVICE_KEY)
    assert isinstance(resolved, DefaultDockService)
