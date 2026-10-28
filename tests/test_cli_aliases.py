"""Unit tests for CLI AliasedGroup, alias routing, and command catalog."""

from __future__ import annotations

import click
import pytest
from click.testing import CliRunner

from harness.cli import main
from harness.commands.aliases import CLI_ALIASES, get_command_catalog


@pytest.mark.unit
class TestCliAliases:
    def test_cli_help_lists_canonical_only(self) -> None:
        runner = CliRunner()
        res = runner.invoke(main, ["--help"])
        assert res.exit_code == 0

        # Canonical commands must appear
        assert "brain-miner" in res.output
        assert "bigquery" in res.output
        assert "doc-builder" in res.output
        assert "creator" in res.output

        # Direct listing should only return canonical registered commands
        listed = main.list_commands(None)  # type: ignore[arg-type]
        assert "brain-miner" in listed
        assert "bigquery" in listed
        assert "doc-builder" in listed

        # Alias names must NOT be in the canonical commands listing
        for alias in CLI_ALIASES:
            assert alias not in listed, f"Alias {alias} unexpectedly found in canonical command list"

    def test_group_alias_resolution(self) -> None:
        runner = CliRunner()
        test_cases = [
            ("miner", "Brain workspace archaeology"),
            ("artifact-miner", "Brain workspace archaeology"),
            ("bq", "BigQuery in-database augmented analytics"),
            ("hf-doc-builder", "HF Doc Builder"),
            ("harness-architect", "Agent harness architecture audit"),
            ("garf-reporting", "Google Garf Declarative SQL"),
            ("self-eval", "Self-Evaluating AI Pipeline"),
            ("icm-architect", "Interpretable Context Methodology"),
        ]

        for alias, expected_snippet in test_cases:
            res = runner.invoke(main, [alias, "--help"])
            assert res.exit_code == 0, f"Failed invoking alias '{alias}': {res.output}"
            assert expected_snippet in res.output, f"Snippet not found in '{alias}' output: {res.output}"

    def test_shortcut_alias_resolution(self) -> None:
        runner = CliRunner()
        # Direct shortcuts for creator commands
        res_create = runner.invoke(main, ["create", "--help"])
        assert res_create.exit_code == 0
        assert "Scaffold a new plugin project" in res_create.output

        res_validate = runner.invoke(main, ["validate", "--help"])
        assert res_validate.exit_code == 0
        assert "Validate a plugin" in res_validate.output

        res_arch = runner.invoke(main, ["archetypes", "--help"])
        assert res_arch.exit_code == 0
        assert "List all available plugin archetypes" in res_arch.output

    def test_command_catalog_generation(self) -> None:
        catalog = get_command_catalog(main)
        assert len(catalog) >= 50

        names = {item["name"] for item in catalog}
        assert "brain-miner" in names
        assert "agent" in names
        assert "skills" in names
        assert "creator" in names

        # Every item should have structured metadata
        for item in catalog:
            assert "name" in item
            assert item["kind"] in ("group", "command")
            assert isinstance(item["subcommands"], list)
            assert isinstance(item["subcommand_count"], int)
            assert isinstance(item["description"], str)
