"""Consolidated Click CLI command group for the skills subsystem.

Enforces Rule 6: Click CLI Group Single-Source Consolidation. All commands for the
'skills' group are declared here in a single co-located block.
"""

from __future__ import annotations

import click

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


@click.group("skills")
def skills_group() -> None:
    """Manage and query the agent skill knowledge graph."""


# Consolidate command registrations in a single place per Rule 6
skills_group.add_command(skills_list, name="list")
skills_group.add_command(skills_run, name="run")
skills_group.add_command(skills_graph, name="graph")
skills_group.add_command(skills_route, name="route")
skills_group.add_command(skills_select, name="select")
skills_group.add_command(skills_clusters, name="clusters")
skills_group.add_command(skills_capabilities, name="capabilities")
skills_group.add_command(skills_chain, name="chain")
skills_group.add_command(skills_info, name="info")
skills_group.add_command(skills_create, name="create")
skills_group.add_command(skills_validate, name="validate")
skills_group.add_command(skills_guidance, name="guidance")
skills_group.add_command(skills_intercept, name="intercept")
skills_group.add_command(skills_prereqs, name="prereqs")
skills_group.add_command(skills_check_chain, name="check-chain")
