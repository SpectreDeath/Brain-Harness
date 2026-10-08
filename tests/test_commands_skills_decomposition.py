"""Characterization test contract for Skills Commands decomposed package architecture.

Verifies:
1. Submodule independence and public facade parity.
2. Click CLI Group single-source consolidation (Rule 6).
3. All 15 Click subcommands registered on skills_group without shadowing.
4. Programmatic command execution parity across discovery, routing, and topology.
5. IoC registry and graph resolution factory seams (Rule 58).
"""

from __future__ import annotations

from pathlib import Path
import pytest
from click.testing import CliRunner

from harness.cli import main


@pytest.mark.unit
class TestCommandsSkillsDecompositionParity:
    """Verifies submodule isolation, public export parity, and Click group consolidation."""

    def test_submodule_import_isolation(self) -> None:
        """Verify each submodule can be imported independently without circular dependencies."""
        from harness.commands.skills import cli, discovery, routing, seams, topology

        assert hasattr(seams, "get_skill_registry")
        assert hasattr(seams, "get_skill_graph")
        assert hasattr(seams, "get_skill_intelligence")

        assert hasattr(discovery, "index_skills_cmd")
        assert hasattr(discovery, "export_skill_graph_visual_cmd")
        assert hasattr(discovery, "list_skills_cmd")
        assert hasattr(discovery, "scaffold_skill_cmd")
        assert hasattr(discovery, "validate_skill_cmd")
        assert hasattr(discovery, "run_skill_cmd")

        assert hasattr(routing, "route_skills_cmd")
        assert hasattr(routing, "select_skills_cmd")
        assert hasattr(routing, "compile_guidance_cmd")
        assert hasattr(routing, "intercept_action_cmd")

        assert hasattr(topology, "find_skill_chain_cmd")
        assert hasattr(topology, "get_prerequisite_closure_cmd")
        assert hasattr(topology, "check_chain_feasibility_cmd")
        assert hasattr(topology, "get_skill_topology_cmd")
        assert hasattr(topology, "cluster_skills_cmd")
        assert hasattr(topology, "discover_capabilities_cmd")

        assert hasattr(cli, "skills_group")

    def test_facade_all_symbol_export_parity(self) -> None:
        """Verify the facade in __init__.py exports all 20 public symbols."""
        import harness.commands.skills as skills_mod

        expected_symbols = [
            "check_chain_feasibility_cmd",
            "cluster_skills_cmd",
            "compile_guidance_cmd",
            "discover_capabilities_cmd",
            "export_skill_graph_visual_cmd",
            "find_skill_chain_cmd",
            "get_prerequisite_closure_cmd",
            "get_skill_graph",
            "get_skill_intelligence",
            "get_skill_registry",
            "get_skill_topology_cmd",
            "index_skills_cmd",
            "intercept_action_cmd",
            "list_skills_cmd",
            "route_skills_cmd",
            "run_skill_cmd",
            "scaffold_skill_cmd",
            "select_skills_cmd",
            "skills_group",
            "validate_skill_cmd",
        ]
        for sym in expected_symbols:
            assert hasattr(skills_mod, sym), f"Facade missing original symbol: {sym}"
            assert sym in skills_mod.__all__, f"__all__ missing symbol: {sym}"

    def test_click_group_single_source_consolidation_rule_6(self) -> None:
        """Verify Rule 6: skills_group has all 15 subcommands registered in a single consolidated group."""
        from harness.commands.skills.cli import skills_group

        expected_subcommands = {
            "list",
            "run",
            "graph",
            "route",
            "select",
            "clusters",
            "capabilities",
            "chain",
            "info",
            "create",
            "validate",
            "guidance",
            "intercept",
            "prereqs",
            "check-chain",
        }
        registered_subcommands = set(skills_group.commands.keys())
        missing = expected_subcommands - registered_subcommands
        assert not missing, f"skills_group missing subcommands: {missing}"
        assert expected_subcommands.issubset(registered_subcommands)


@pytest.mark.unit
class TestCommandsSkillsExecution:
    """Verifies programmatic command execution and Click CLI invocation."""

    def test_programmatic_discovery_and_routing_commands(self) -> None:
        """Verify index, route, and list commands execute properly."""
        from harness.commands.skills.discovery import index_skills_cmd, list_skills_cmd
        from harness.commands.skills.routing import route_skills_cmd

        index_res = index_skills_cmd()
        assert index_res["status"] == "ok"
        assert "indexed_skills" in index_res

        skills = list_skills_cmd()
        assert isinstance(skills, list)

        route_res = route_skills_cmd("review pull request diff", top_k=2)
        assert "matches" in route_res
        assert isinstance(route_res["matches"], list)

    def test_programmatic_topology_and_chain_commands(self) -> None:
        """Verify topology and chain resolution commands."""
        from harness.commands.skills.topology import find_skill_chain_cmd

        res = find_skill_chain_cmd("codebase-design", "deepen-architecture")
        assert res["status"] in ("ok", "no_path")
        if res["status"] == "ok":
            assert len(res["chain"]) >= 2

    def test_click_cli_command_runner_execution(self) -> None:
        """Verify CLI runner invokes skills subcommands cleanly."""
        runner = CliRunner()
        result = runner.invoke(main, ["skills", "list"])
        assert result.exit_code == 0
        assert "Registered Agent Skills" in result.output

        route_res = runner.invoke(main, ["skills", "route", "test code changes"])
        assert route_res.exit_code == 0
        assert "Route matches" in route_res.output

    def test_scaffold_and_validate_programmatic_commands(self, tmp_path: Path) -> None:
        """Verify scaffold_skill_cmd and validate_skill_cmd work through decomposed package."""
        from harness.commands.skills.discovery import scaffold_skill_cmd, validate_skill_cmd

        target = tmp_path / "custom_skill"
        res = scaffold_skill_cmd(
            name="custom-skill",
            description="Custom skill description.",
            target_dir=target,
            auto_validate=True,
        )
        assert res.skill_file.exists()
        assert res.card_file is not None and res.card_file.exists()

        report = validate_skill_cmd(target)
        assert report.valid is True
