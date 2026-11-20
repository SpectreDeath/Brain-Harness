"""CLI diff-review flow: present diff + digest, approve, then spawn with write_permitted (plan Track 2)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from harness.cli import main
from harness.services.harness_spawner import compute_tree_sha256


def _review_json(runner: CliRunner, *extra: str) -> dict:
    res = runner.invoke(
        main,
        ["spawn", "review", "--name", "rev-worker", "--domain", "audit", "--task", "check ledger", "--json", *extra],
    )
    assert res.exit_code == 0, res.output
    return json.loads(res.output)


def _spawn_args(save_dir: Path, *extra: str) -> list[str]:
    return [
        "spawn",
        "run",
        "--name",
        "rev-worker",
        "--domain",
        "audit",
        "--task",
        "check ledger",
        "--save-dir",
        str(save_dir),
        "--write-permitted",
        *extra,
    ]


@pytest.mark.unit
class TestSpawnReviewCli:
    def test_review_prints_human_diff_and_canonical_digest(self) -> None:
        runner = CliRunner()
        res = runner.invoke(
            main, ["spawn", "review", "--name", "rev-worker", "--domain", "audit", "--task", "check ledger"]
        )
        assert res.exit_code == 0, res.output
        digest = compute_tree_sha256(
            {"AGENTS.md": "# Spawned Harness: rev-worker\n\nDomain: audit\nTask: check ledger\n"}
        )
        assert "+++ b/AGENTS.md" in res.output
        assert "Added:    AGENTS.md" in res.output
        assert digest in res.output
        assert _review_json(runner)["tree_sha256"] == digest

    def test_review_diffs_against_base_dir_and_flags_digest_mismatch(self, tmp_path: Path) -> None:
        base = tmp_path / "base"
        base.mkdir()
        (base / "AGENTS.md").write_text("# Old\n", encoding="utf-8")
        runner = CliRunner()
        review = _review_json(runner, "--base-dir", str(base))
        assert review["modified"] == ["AGENTS.md"]
        assert "-# Old" in review["unified_diff"]

        bad = runner.invoke(
            main,
            ["spawn", "review", "--name", "rev-worker", "--domain", "audit", "--approve-digest", "0" * 64],
        )
        assert bad.exit_code == 1
        assert "Supplied digest matches: False" in bad.output

    def test_full_approve_flow_through_cli(self, tmp_path: Path) -> None:
        runner = CliRunner()
        digest = _review_json(runner)["tree_sha256"]

        res = runner.invoke(main, _spawn_args(tmp_path / "spawns", "--approve-digest", digest))
        assert res.exit_code == 0, res.output
        assert json.loads(res.output)["state"] == "RUNNING"

    def test_write_permitted_without_digest_lands_failed(self, tmp_path: Path) -> None:
        res = CliRunner().invoke(main, _spawn_args(tmp_path / "spawns"))
        assert res.exit_code == 1
        payload = json.loads(res.output)
        assert payload["state"] == "FAILED"
        assert "approved_tree_digest" in res.output

    def test_write_permitted_with_drifted_digest_lands_failed(self, tmp_path: Path) -> None:
        runner = CliRunner()
        digest = _review_json(runner)["tree_sha256"]
        drifted = ("0" if digest[0] != "0" else "1") + digest[1:]
        res = runner.invoke(main, _spawn_args(tmp_path / "spawns", "--approve-digest", drifted))
        assert res.exit_code == 1
        assert json.loads(res.output)["state"] == "FAILED"
        assert "drift" in res.output
