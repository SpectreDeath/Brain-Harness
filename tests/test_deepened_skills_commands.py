"""Tests for deepened skill command layer and declarative plugin persistence."""

from __future__ import annotations

import json
from pathlib import Path
import pytest
from click.testing import CliRunner

from harness.cli import main
from harness.commands.plugins import (
    disable_all_plugins,
    enable_all_plugins,
    enable_plugin_by_name,
)
from harness.commands.skills import (
    export_skill_graph_visual_cmd,
    find_skill_chain_cmd,
    get_skill_topology_cmd,
    index_skills_cmd,
    route_skills_cmd,
    scaffold_skill_cmd,
    validate_skill_cmd,
)


@pytest.mark.unit
def test_index_skills_cmd() -> None:
    """Assert indexing returns valid status, skill count, and categories."""
    res = index_skills_cmd()
    assert res["status"] == "ok"
    assert "indexed_skills" in res
    assert isinstance(res["categories"], list)
    assert res["total_nodes"] >= 0


@pytest.mark.unit
def test_export_skill_graph_visual_cmd(tmp_path: Path) -> None:
    """Assert HTML visual brief is successfully generated."""
    out_file = tmp_path / "skill_graph.html"
    res = export_skill_graph_visual_cmd(output_path=out_file)
    assert res["status"] == "ok"
    assert Path(res["html_path"]).exists()
    assert "<html" in out_file.read_text(encoding="utf-8").lower()


@pytest.mark.unit
def test_route_skills_cmd() -> None:
    """Assert natural language intent routing returns matches and confidence scores."""
    res = route_skills_cmd("review pull request code changes", top_k=2)
    assert "matches" in res
    assert isinstance(res["matches"], list)
    assert "recommended_chain" in res


@pytest.mark.unit
def test_find_skill_chain_cmd() -> None:
    """Assert skill chain pathfinding returns valid chain."""
    res = find_skill_chain_cmd("codebase-design", "deepen-architecture")
    assert res["status"] in ("ok", "no_path")
    if res["status"] == "ok":
        assert isinstance(res["chain"], list)
        assert len(res["chain"]) >= 2



@pytest.mark.unit
def test_get_skill_topology_cmd() -> None:
    """Assert topology lookup for a known skill."""
    res = get_skill_topology_cmd("deepen-architecture")
    assert res["status"] in ("ok", "error")
    if res["status"] == "ok":
        assert "topology" in res
        assert "skill" in res["topology"]


@pytest.mark.unit
def test_scaffold_and_validate_skill_cmd(tmp_path: Path) -> None:
    """Assert scaffold and validation pipeline executes cleanly."""
    target_dir = tmp_path / "custom-auditor"
    scaffold_res = scaffold_skill_cmd(
        name="custom-auditor",
        description="Audits architectural invariants and seams",
        category="engineering / quality",
        target_dir=target_dir,
        triggers=["audit invariants", "check seams"],
        auto_validate=True,
    )
    assert scaffold_res.path.exists()
    assert (target_dir / "SKILL.md").exists()
    assert (target_dir / "CARD.md").exists()
    assert scaffold_res.validation_report is not None
    assert scaffold_res.validation_report.valid is True

    val_rep = validate_skill_cmd(target_dir)
    assert val_rep.valid is True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_plugin_declarative_persistence(tmp_path: Path) -> None:
    """Assert standalone enable/disable commands mutate and persist config.json."""
    config_dir = tmp_path / ".harness"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file = config_dir / "config.json"
    config_file.write_text(json.dumps({"enabled_plugins": [], "disabled_plugins": []}), encoding="utf-8")

    # Test enable by name
    await enable_plugin_by_name("non_existent_demo", config_dir=config_dir)
    data = json.loads(config_file.read_text(encoding="utf-8"))
    assert "enabled_plugins" in data

    # Test enable all / disable all persistence
    await enable_all_plugins(config_dir=config_dir)
    data = json.loads(config_file.read_text(encoding="utf-8"))
    assert isinstance(data["enabled_plugins"], list)

    await disable_all_plugins(config_dir=config_dir)
    data = json.loads(config_file.read_text(encoding="utf-8"))
    assert isinstance(data["disabled_plugins"], list)


@pytest.mark.unit
def test_cli_skills_group(tmp_path: Path) -> None:
    """Assert CLI skill commands delegate cleanly through Click."""
    runner = CliRunner()

    # Test skills graph
    result = runner.invoke(main, ["skills", "graph"])
    assert result.exit_code == 0
    assert "Indexed" in result.output

    # Test skills route
    result = runner.invoke(main, ["skills", "route", "code review"])
    assert result.exit_code == 0
    assert "Route matches" in result.output

    # Test skills create & validate
    skill_dir = tmp_path / "cli-test-skill"
    result = runner.invoke(
        main,
        [
            "skills",
            "create",
            "cli-test-skill",
            "--description",
            "CLI test skill description",
            "--target-dir",
            str(skill_dir),
            "--validate",
        ],
    )
    assert result.exit_code == 0
    assert "Scaffolded agent skill" in result.output

    result = runner.invoke(main, ["skills", "validate", str(skill_dir)])
    assert result.exit_code == 0
    assert "Overall Status: ✓ PASS" in result.output
