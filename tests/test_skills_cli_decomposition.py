"""Contract verification tests for Cycle 54: Skills CLI Command Decomposition.

Verifies:
- Direct imports from decomposed CLI submodules (cli_discovery, cli_routing, cli_topology)
- Group consolidation: skills_group has exactly 15 registered subcommands (Rule 6)
- Headless execution of discovery, routing, and topology commands via CliRunner (Rule 10)
"""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from harness.commands.skills.cli import skills_group
from harness.commands.skills.cli_discovery import (
    skills_create,
    skills_graph,
    skills_list,
    skills_run,
    skills_validate,
)
from harness.commands.skills.cli_routing import (
    skills_guidance,
    skills_intercept,
    skills_route,
    skills_select,
)
from harness.commands.skills.cli_topology import (
    skills_capabilities,
    skills_chain,
    skills_check_chain,
    skills_clusters,
    skills_info,
    skills_prereqs,
)


@pytest.mark.unit
def test_skills_cli_submodule_exports() -> None:
    """Verify all 15 Click commands are properly exported from decomposed modules."""
    discovery_cmds = [skills_list, skills_run, skills_graph, skills_create, skills_validate]
    routing_cmds = [skills_route, skills_select, skills_guidance, skills_intercept]
    topology_cmds = [skills_clusters, skills_capabilities, skills_chain, skills_info, skills_prereqs, skills_check_chain]

    assert len(discovery_cmds) == 5
    assert len(routing_cmds) == 4
    assert len(topology_cmds) == 6


@pytest.mark.unit
def test_skills_cli_group_consolidation_rule_6() -> None:
    """Verify Rule 6: skills_group has all 15 subcommands registered in a single consolidated group."""
    expected = {
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
    registered = set(skills_group.commands.keys())
    assert expected == registered, f"Mismatch in registered commands: {expected.symmetric_difference(registered)}"


@pytest.mark.unit
def test_skills_cli_headless_execution() -> None:
    """Verify headless execution of skills subcommands via CliRunner."""
    runner = CliRunner()

    # 1. list
    r1 = runner.invoke(skills_group, ["list"])
    assert r1.exit_code == 0
    assert "Registered Agent Skills" in r1.output

    # 2. route
    r2 = runner.invoke(skills_group, ["route", "audit legacy codebase", "--top-k", "2"])
    assert r2.exit_code == 0
    assert "Route matches for:" in r2.output

    # 3. check-chain with root skill
    r3 = runner.invoke(skills_group, ["check-chain", "agent-instruction-architect"])
    assert r3.exit_code == 0
    assert "Chain Feasibility Assessment" in r3.output
