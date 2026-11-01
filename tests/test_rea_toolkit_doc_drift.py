"""Tests asserting REA toolkit documentation, CLI commands, aliases, and links do not drift."""

from __future__ import annotations

import json
from pathlib import Path
import re
import pytest

from harness.commands.rea import rea_group
from harness.services.rea_toolkit import REA_TOOL_ALIASES, ARTIFACT_ROUTING_TABLE

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent


def test_cli_subcommands_documented() -> None:
    """Every subcommand registered on rea_group must be documented in How-To and cli.md."""
    registered_commands = set(rea_group.commands.keys())
    assert len(registered_commands) == 10, f"Expected 10 subcommands, got {len(registered_commands)}: {registered_commands}"

    how_to_path = WORKSPACE_ROOT / "docs" / "how-to" / "use-rea-toolkit.md"
    assert how_to_path.exists(), f"Missing {how_to_path}"
    how_to_text = how_to_path.read_text(encoding="utf-8")

    cli_md_path = WORKSPACE_ROOT / "docs" / "reference" / "cli.md"
    assert cli_md_path.exists(), f"Missing {cli_md_path}"
    cli_md_text = cli_md_path.read_text(encoding="utf-8")

    for cmd_name in registered_commands:
        expected_cli_str = f"harness rea {cmd_name}"
        assert expected_cli_str in how_to_text, f"Subcommand '{cmd_name}' not found in {how_to_path}"
        assert expected_cli_str in cli_md_text, f"Subcommand '{cmd_name}' not found in {cli_md_path}"


def test_all_28_aliases_mapped_to_valid_manifest_entrypoints() -> None:
    """All 28 REA_TOOL_ALIASES must point to real entrypoints declared in plugin.json manifests."""
    assert len(REA_TOOL_ALIASES) == 28, f"Expected 28 tool aliases, got {len(REA_TOOL_ALIASES)}"

    # Collect all declared entrypoints from REA manifests
    manifest_paths = [
        WORKSPACE_ROOT / "plugins" / "data_engineering" / "rea_javascript" / "plugin.json",
        WORKSPACE_ROOT / "plugins" / "security_and_forensics" / "rea_managed_runtime" / "plugin.json",
        WORKSPACE_ROOT / "plugins" / "security_and_forensics" / "rea_mobile_firmware" / "plugin.json",
        WORKSPACE_ROOT / "plugins" / "security_and_forensics" / "rea_native" / "plugin.json",
    ]

    all_declared_tools: set[str] = set()
    for mpath in manifest_paths:
        assert mpath.exists(), f"Manifest not found: {mpath}"
        data = json.loads(mpath.read_text(encoding="utf-8"))
        pname = data["name"]
        for ep in data.get("entrypoints", []):
            all_declared_tools.add(f"{pname}.{ep['name']}")

    for alias, canonical_name in REA_TOOL_ALIASES.items():
        assert alias.startswith("rea."), f"Alias '{alias}' should start with 'rea.'"
        assert canonical_name in all_declared_tools, (
            f"Alias '{alias}' maps to '{canonical_name}', which is not declared in any REA plugin manifest!"
        )


def test_routing_table_matches_supported_categories() -> None:
    """Routing table must cover all 13 categories and valid plugin IDs."""
    assert len(ARTIFACT_ROUTING_TABLE) == 14  # 13 categories + dos_mz
    valid_plugins = {
        "plugin.rea_native",
        "plugin.rea_managed_runtime",
        "plugin.rea_mobile_firmware",
        "plugin.rea_javascript",
    }
    for cat, info in ARTIFACT_ROUTING_TABLE.items():
        assert info["primary_plugin"] in valid_plugins
        for sec in info.get("secondary_plugins", []):
            assert sec in valid_plugins


def test_relative_links_in_rea_docs_resolve() -> None:
    """Assert all markdown relative links in use-rea-toolkit.md resolve to real disk targets (Rule 47)."""
    how_to_path = WORKSPACE_ROOT / "docs" / "how-to" / "use-rea-toolkit.md"
    content = how_to_path.read_text(encoding="utf-8")

    # Match [text](target) excluding web urls or anchors
    link_pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
    for match in link_pattern.finditer(content):
        target = match.group(2)
        if target.startswith("http://") or target.startswith("https://") or target.startswith("#"):
            continue
        # Strip internal anchor if present
        clean_target = target.split("#")[0]
        if not clean_target:
            continue
        resolved_path = (how_to_path.parent / clean_target).resolve()
        assert resolved_path.exists(), f"Broken relative link in {how_to_path}: '{target}' -> '{resolved_path}'"

