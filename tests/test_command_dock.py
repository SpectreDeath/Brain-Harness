"""CLI command tests for harness dock commands."""

from __future__ import annotations

import json
from pathlib import Path
from click.testing import CliRunner
import pytest

from harness.cli import main


@pytest.fixture
def cli_runner() -> CliRunner:
    return CliRunner()


@pytest.fixture(autouse=True)
def isolate_dock_state(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Guarantee test suite hermeticity: test runs never write to active repo docks.json."""
    test_state_file = tmp_path / "test_docks.json"
    monkeypatch.setenv("HARNESS_DOCKS_STATE_FILE", str(test_state_file))


def test_dock_help(cli_runner: CliRunner) -> None:
    result = cli_runner.invoke(main, ["dock", "--help"])
    assert result.exit_code == 0
    assert "Agent Dock" in result.output
    assert "inspect" in result.output
    assert "link" in result.output
    assert "list" in result.output
    assert "run" in result.output
    assert "tools" in result.output


def test_dock_inspect_real_repo(cli_runner: CliRunner) -> None:
    result = cli_runner.invoke(main, ["dock", "inspect", "."])
    assert result.exit_code == 0
    assert "Agent Dock: brain-harness" in result.output
    assert "vault-stats" in result.output
    assert "verify-core" in result.output


def test_dock_inspect_json(cli_runner: CliRunner) -> None:
    result = cli_runner.invoke(main, ["dock", "inspect", ".", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["name"] == "brain-harness"
    assert data["declared"] is True
    assert "vault-stats" in data["entrypoints"]


def test_dock_link_and_list_lifecycle(cli_runner: CliRunner, tmp_path: Path) -> None:
    toy_repo = tmp_path / "toy_repo"
    toy_repo.mkdir()
    (toy_repo / "dock.yaml").write_text(
        """name: cli-toy
description: CLI toy repo
entrypoints:
  hi:
    steps:
      - command: echo "hello from dock"
""",
        encoding="utf-8",
    )

    # Link with --approve
    link_res = cli_runner.invoke(main, ["dock", "link", str(toy_repo), "--name", "my-toy", "--approve"])
    assert link_res.exit_code == 0
    assert "Linked dock 'my-toy' [APPROVED]" in link_res.output

    # List docks
    list_res = cli_runner.invoke(main, ["dock", "list"])
    assert list_res.exit_code == 0
    assert "my-toy" in list_res.output
    assert "approved" in list_res.output

    # List tools
    tools_res = cli_runner.invoke(main, ["dock", "tools", "my-toy"])
    assert tools_res.exit_code == 0

    # Run dry-run
    run_dry = cli_runner.invoke(main, ["dock", "run", "my-toy", "hi", "--dry-run"])
    assert run_dry.exit_code == 0
    assert "[DRY-RUN]" in run_dry.output
    assert "echo \"hello from dock\"" in run_dry.output

    # Run real
    run_real = cli_runner.invoke(main, ["dock", "run", "my-toy", "hi"])
    assert run_real.exit_code == 0
    assert "hello from dock" in run_real.output
    assert "completed successfully" in run_real.output


def test_dock_run_unapproved_fails(cli_runner: CliRunner, tmp_path: Path) -> None:
    toy_repo = tmp_path / "unapproved_repo"
    toy_repo.mkdir()
    (toy_repo / "dock.yaml").write_text(
        "name: unapproved\ndescription: desc\nentrypoints:\n  hi:\n    steps:\n      - command: echo hi\n",
        encoding="utf-8",
    )

    # Link non-interactively without --approve
    link_res = cli_runner.invoke(main, ["dock", "link", str(toy_repo), "--name", "unapp"])
    assert link_res.exit_code == 0
    assert "[UNAPPROVED]" in link_res.output

    # Run fails due to approval drift
    run_res = cli_runner.invoke(main, ["dock", "run", "unapp", "hi"])
    assert run_res.exit_code != 0
    assert "Approval drift error" in run_res.output

