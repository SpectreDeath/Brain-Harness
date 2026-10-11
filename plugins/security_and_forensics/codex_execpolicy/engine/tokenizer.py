"""Shell command tokenization into structured component representations."""

from __future__ import annotations

import sys
from typing import Any

from plugins.security_and_forensics.codex_execpolicy.engine.ast_core import parse_bash_ast

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


def _tokenize_command(command_str: str, shell_flavor: str = "bash") -> dict[str, Any]:
    """Tokenize a shell command into binary, arguments, chained operators, redirections, and subshells."""
    clean_cmd = command_str.strip()
    if not clean_cmd:
        return {
            "binary": "",
            "arguments": [],
            "operators": [],
            "redirections": [],
            "variables": [],
            "subshells": [],
            "is_compound": False,
            "subcommands": [],
        }

    ast_tree = parse_bash_ast(clean_cmd)

    subcommands: list[dict[str, Any]] = []
    operators: list[str] = list(ast_tree.operators)

    if ast_tree.node_type in ("compound", "pipeline") and ast_tree.children:
        for child in ast_tree.children:
            subcommands.append({
                "binary": child.binary,
                "arguments": list(child.arguments),
                "redirections": list(child.redirections),
                "variables": [list(v) for v in child.variables],
                "subshells": [c.to_dict() for c in child.children if c.node_type in ("subshell", "process_substitution")],
                "raw_command": child.raw,
            })
    else:
        subcommands.append({
            "binary": ast_tree.binary,
            "arguments": list(ast_tree.arguments),
            "redirections": list(ast_tree.redirections),
            "variables": [list(v) for v in ast_tree.variables],
            "subshells": [c.to_dict() for c in ast_tree.children if c.node_type in ("subshell", "process_substitution")],
            "raw_command": clean_cmd,
        })

    is_compound = len(subcommands) > 1 or len(operators) > 0
    first_bin = subcommands[0]["binary"] if subcommands else ""
    first_args = subcommands[0]["arguments"] if subcommands else []

    all_subshells: list[dict[str, Any]] = []
    for sc in subcommands:
        all_subshells.extend(sc.get("subshells", []))

    return {
        "binary": first_bin,
        "arguments": first_args,
        "operators": operators,
        "redirections": [r for sc in subcommands for r in sc["redirections"]],
        "variables": [v for sc in subcommands for v in sc.get("variables", [])],
        "subshells": all_subshells,
        "is_compound": is_compound,
        "subcommands": subcommands,
        "ast_tree": ast_tree.to_dict(),
    }


def tokenize_shell_ast(command: str, shell_flavor: str = "bash") -> dict[str, Any]:
    """Parse a shell command string into structured AST components without executing it."""
    parsed = _tokenize_command(command, shell_flavor=shell_flavor)
    return {
        "status": "ok",
        "command": command,
        "shell_flavor": shell_flavor,
        "binary": parsed["binary"],
        "arguments": parsed["arguments"],
        "operators": parsed["operators"],
        "redirections": parsed["redirections"],
        "variables": parsed.get("variables", []),
        "subshells": parsed.get("subshells", []),
        "is_compound": parsed["is_compound"],
        "subcommands_count": len(parsed["subcommands"]),
        "subcommands": parsed["subcommands"],
        "ast_tree": parsed.get("ast_tree", {}),
    }


__all__ = [
    "_tokenize_command",
    "tokenize_shell_ast",
]
