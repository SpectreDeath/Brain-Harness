"""Contract test verifying AGENTS.md Rule 6 (Click CLI Group Single-Source Consolidation)."""

from __future__ import annotations

import ast
from collections import defaultdict
from pathlib import Path

import click
import pytest

from harness import cli


@pytest.mark.unit
class TestCliRule6SingleSource:
    """Enforces AGENTS.md Rule 6:

    CLI command groups (e.g. @main.group("bridge")) must be declared exactly once
    in a single co-located block to prevent later definitions from shadowing subcommands.
    """

    def test_no_duplicate_cli_group_definitions_in_ast(self) -> None:
        """Scan AST of all command modules ensuring no group is defined more than once."""
        repo_root = Path(__file__).resolve().parents[1]
        commands_dir = repo_root / "src" / "harness" / "commands"

        group_definitions: dict[str, list[tuple[str, int]]] = defaultdict(list)

        for py_file in commands_dir.rglob("*.py"):
            if py_file.name.startswith("__"):
                continue
            content = py_file.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(content, filename=str(py_file))
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    for dec in node.decorator_list:
                        call_node = dec if isinstance(dec, ast.Call) else None
                        if call_node and isinstance(call_node.func, ast.Attribute) and call_node.func.attr == "group":
                            name = None
                            if call_node.args and isinstance(call_node.args[0], ast.Constant):
                                name = str(call_node.args[0].value)
                            for kw in call_node.keywords:
                                if kw.arg == "name" and isinstance(kw.value, ast.Constant):
                                    name = str(kw.value.value)
                            if not name:
                                name = node.name.replace("_group", "").replace("_cli", "")
                            rel_path = str(py_file.relative_to(repo_root)).replace("\\", "/")
                            group_definitions[name].append((rel_path, node.lineno))

        duplicates = {k: v for k, v in group_definitions.items() if len(v) > 1}
        assert not duplicates, f"Rule 6 violation: CLI group declared in multiple files: {duplicates}"

    def test_cli_main_single_source_co_located_registration(self) -> None:
        """Assert cli.main registers each canonical group exactly once in a single block."""
        repo_root = Path(__file__).resolve().parents[1]
        cli_file = repo_root / "src" / "harness" / "cli.py"
        content = cli_file.read_text(encoding="utf-8")

        tree = ast.parse(content, filename=str(cli_file))

        # Check _CANONICAL_GROUPS list definition
        canonical_names: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "_CANONICAL_GROUPS":
                        assert isinstance(node.value, ast.List), "_CANONICAL_GROUPS must be a list"
                        for elt in node.value.elts:
                            if isinstance(elt, ast.Tuple) and isinstance(elt.elts[0], ast.Constant):
                                canonical_names.append(str(elt.elts[0].value))

        assert canonical_names, "Could not find _CANONICAL_GROUPS in cli.py"
        assert len(canonical_names) == len(set(canonical_names)), (
            f"Duplicate canonical group registrations in cli.py: "
            f"{[name for name in canonical_names if canonical_names.count(name) > 1]}"
        )

    def test_canonical_and_alias_disjointness(self) -> None:
        """Assert that declared aliases never overwrite canonical group names."""
        canonical_names = set(cli.main.commands.keys())
        alias_names = set(cli.main.aliases.keys())

        overlap = canonical_names.intersection(alias_names)
        assert not overlap, f"Alias names collision with canonical commands: {overlap}"
