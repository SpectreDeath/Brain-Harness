"""Tests for headless Click CLI command group 'harness tau' (Rule 6 & Rule 10)."""

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from harness.cli import main
from harness.commands.tau import (
    tau_group,
)


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def test_tau_cli_help(runner: CliRunner) -> None:
    """Verify tau command group help is registered in main CLI."""
    result = runner.invoke(main, ["tau", "--help"])
    assert result.exit_code == 0
    assert "Pi-style coding agent harness commands" in result.output
    assert "tree" in result.output
    assert "resolve-path" in result.output
    assert "repair-history" in result.output
    assert "trust-check" in result.output
    assert "append-journal" in result.output


def test_tau_cli_append_and_tree(runner: CliRunner, tmp_path: Path) -> None:
    """Verify append-journal and tree subcommands."""
    journal_file = tmp_path / "session.jsonl"

    res_append1 = runner.invoke(
        tau_group,
        [
            "append-journal",
            "--file",
            str(journal_file),
            "--id",
            "root",
            "--role",
            "user",
            "--content",
            "Initial prompt",
        ],
    )
    assert res_append1.exit_code == 0
    assert "Appended entry [root]" in res_append1.output

    res_append2 = runner.invoke(
        tau_group,
        [
            "append-journal",
            "--file",
            str(journal_file),
            "--id",
            "step_1",
            "--parent",
            "root",
            "--role",
            "assistant",
            "--content",
            "Working on it",
        ],
    )
    assert res_append2.exit_code == 0

    res_tree = runner.invoke(tau_group, ["tree", "--file", str(journal_file)])
    assert res_tree.exit_code == 0
    assert "[root] user: Initial prompt" in res_tree.output
    assert "[step_1] assistant: Working on it" in res_tree.output


def test_tau_cli_resolve_path(runner: CliRunner, tmp_path: Path) -> None:
    """Verify resolve-path subcommand."""
    journal_file = tmp_path / "session.jsonl"
    entries = [
        {"id": "r", "parent_id": None, "role": "user", "content": "hello"},
        {"id": "s1", "parent_id": "r", "role": "assistant", "content": "hi"},
    ]
    with open(journal_file, "w", encoding="utf-8") as f:
        f.writelines(json.dumps(e) + "\n" for e in entries)

    res = runner.invoke(tau_group, ["resolve-path", "--file", str(journal_file), "--target", "s1"])
    assert res.exit_code == 0
    assert "Depth: 2 entries" in res.output
    assert "[r] user: hello" in res.output
    assert "[s1] assistant: hi" in res.output


def test_tau_cli_repair_history(runner: CliRunner, tmp_path: Path) -> None:
    """Verify repair-history subcommand."""
    messages = [
        {"role": "user", "content": "hi"},
        {"role": "tool", "tool_call_id": "orphan_123", "content": "stray"},
    ]
    in_file = tmp_path / "messages.json"
    out_file = tmp_path / "repaired.json"
    in_file.write_text(json.dumps(messages), encoding="utf-8")

    res = runner.invoke(
        tau_group,
        ["repair-history", "--file", str(in_file), "--output", str(out_file)],
    )
    assert res.exit_code == 0
    assert "Tool History Normalization Complete:" in res.output
    assert "Orphans Dropped:    1" in res.output

    repaired_data = json.loads(out_file.read_text(encoding="utf-8"))
    assert len(repaired_data) == 1
    assert repaired_data[0]["role"] == "user"


def test_tau_cli_trust_check(runner: CliRunner, tmp_path: Path) -> None:
    """Verify trust-check subcommand."""
    proj = tmp_path / "my_project"
    proj.mkdir()
    (proj / "id_rsa").write_text("DUMMY_KEY", encoding="utf-8")

    res = runner.invoke(tau_group, ["trust-check", str(proj)])
    assert res.exit_code == 0
    assert "Workspace Trust Audit" in res.output
    assert "BLOCKED" in res.output
    assert "id_rsa" in res.output
