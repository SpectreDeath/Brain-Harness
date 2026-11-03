"""Test contract: CLI content drift assertions between live Click commands and docs."""

from __future__ import annotations

import re
from pathlib import Path
import click
import pytest

from harness.cli import main
from harness.commands.aliases import CLI_ALIASES


def test_cli_md_documents_all_command_groups_and_subcommands():
    cli_md_path = Path("docs/reference/cli.md")
    assert cli_md_path.exists(), "docs/reference/cli.md not found"
    content = cli_md_path.read_text(encoding="utf-8")

    # Assert all groups are documented
    for name, cmd in main.commands.items():
        if isinstance(cmd, click.Group):
            # Header exists
            assert f"## `harness {name}`" in content, f"Missing group section for 'harness {name}' in cli.md"
            # All subcommands documented
            for sub_name in cmd.commands.keys():
                assert f"harness {name} {sub_name}" in content, (
                    f"Missing subcommand 'harness {name} {sub_name}' in cli.md"
                )
        else:
            assert f"## `harness {name}`" in content, f"Missing standalone command section for 'harness {name}'"


def test_integrated_toolkits_matches_live_subcommands():
    toolkits_md_path = Path("docs/reference/integrated-toolkits.md")
    assert toolkits_md_path.exists(), "docs/reference/integrated-toolkits.md not found"
    content = toolkits_md_path.read_text(encoding="utf-8")

    # Check key toolkits
    expected_matches = {
        "rea": ["callgraph", "decompile", "devices", "diff", "inspect", "learn", "learned", "list", "providers", "signatures"],
        "dock": ["inspect", "link", "list", "run", "tools"],
        "network-forensics": ["brief", "cleartext", "decode-flags", "diagnose-7layer", "scan-ports", "subnet", "traceroute"],
        "okf": ["scope", "search", "show", "validate"],
        "rol": ["export", "ingest", "obligation", "verify"],
        "redteam": ["scan", "status", "techniques"],
    }

    for grp_name, subcmds in expected_matches.items():
        assert grp_name in main.commands, f"Command group '{grp_name}' not on live CLI"
        live_subcmds = sorted(main.commands[grp_name].commands.keys())
        assert live_subcmds == sorted(subcmds), f"Mismatch in live subcommands for '{grp_name}': {live_subcmds} vs {subcmds}"
        # Assert each subcommand is mentioned in the markdown row for that group
        for sub in subcmds:
            assert sub in content, f"Subcommand '{sub}' of '{grp_name}' not in integrated-toolkits.md"

    # Assert canonical service keys
    assert "service.skill_knowledge_graph" in content
    assert "service.network_forensics" in content
    assert "service.rea_toolkit" in content
    assert "service.dock" in content
    assert "service.okf_memory" in content
    assert "service.reconstruction_obligation" in content
