"""CLI command aliasing, resolution engine, and catalog generation.

Enforces clean canonical group listings in --help while transparently resolving
all declared aliases and legacy shortcut commands.
"""

from __future__ import annotations

from typing import Any

import click


class AliasedGroup(click.Group):
    """Click Group that resolves declared aliases while keeping help output canonical."""

    def __init__(
        self,
        *args: Any,
        aliases: dict[str, str | click.Command] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.aliases: dict[str, str | click.Command] = aliases or {}

    def add_alias(self, alias_name: str, target: str | click.Command) -> None:
        """Register a declared alias mapping to a canonical command or group."""
        self.aliases[alias_name] = target

    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:
        """Resolve a command by canonical name first, falling back to declared aliases."""
        cmd = super().get_command(ctx, cmd_name)
        if cmd is not None:
            return cmd
        if cmd_name in self.aliases:
            target = self.aliases[cmd_name]
            if isinstance(target, click.Command):
                return target
            return super().get_command(ctx, target)
        return None

    def list_commands(self, ctx: click.Context) -> list[str]:
        """Return only canonical registered commands in help output, eliminating sprawl."""
        return sorted(self.commands.keys())


# Canonical Group Alias Mappings (alias_name -> canonical_name)
CLI_ALIASES: dict[str, str] = {
    # Engineering & Architecture
    "hf-doc-builder": "doc-builder",
    "harness-architect": "architect",
    "ai-native-harness": "gate",
    "harness-compass": "compass",
    "gradio-app": "gradio",
    "streaming-chatbot": "gemini-vercel",
    "gemini-chat": "gemini-vercel",
    "coding-harness": "tau",
    "icm-architect": "icm",
    # Data & Analytics
    "bq": "bigquery",
    "open-source-gis": "gis",
    "garf-reporting": "garf",
    # Memory & Mining
    "miner": "brain-miner",
    "artifact-miner": "brain-miner",
    "trajectory-miner": "trajectory",
    "conversation-miner": "trajectory",
    "temp-miner": "temp",
    "ephemeral-miner": "temp",
    # Security, Calibration & Evaluation
    "security-guard": "pre-commit-security",
    "shift-left": "pre-commit-security",
    "net-diag": "network-forensics",
    "network": "network-forensics",
    "calibrator": "calibrate",
    "validate-loop": "validation-loop",
    "model-router": "router",
    "self-eval": "eval",
    "uncertainty-guard": "uncertainty",
    "obligation-ledger": "rol",
    "differential-facet": "facet",
}


def get_command_catalog(group: click.Group) -> list[dict[str, Any]]:
    """Introspect group and generate a structured catalog of all canonical commands."""
    catalog: list[dict[str, Any]] = []
    for name in sorted(group.commands.keys()):
        cmd = group.commands[name]
        is_group = isinstance(cmd, click.Group)
        subcmds = sorted(cmd.commands.keys()) if is_group else []
        desc = (cmd.help or cmd.short_help or "").strip().split("\n")[0]
        catalog.append({
            "name": name,
            "kind": "group" if is_group else "command",
            "subcommands": subcmds,
            "subcommand_count": len(subcmds),
            "description": desc,
        })
    return catalog


def generate_cli_docstring(group: click.Group) -> str:
    """Dynamically format a markdown-compatible command catalog table."""
    catalog = get_command_catalog(group)
    lines = [
        "CLI entry point — authoritative command catalog for Brain Harness.",
        "",
        "Canonical Commands & Groups:",
    ]
    for item in catalog:
        sub_info = f" ({item['subcommand_count']} subcommands)" if item["kind"] == "group" else ""
        lines.append(f"    harness {item['name']:22}{sub_info:20} — {item['description']}")
    return "\n".join(lines)


__all__ = [
    "CLI_ALIASES",
    "AliasedGroup",
    "generate_cli_docstring",
    "get_command_catalog",
]
