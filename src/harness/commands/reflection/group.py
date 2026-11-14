"""Shared Click group and logger for reflection and knowledge commands."""

from __future__ import annotations

import click
import structlog

logger = structlog.get_logger("harness.commands.reflection")


@click.group("knowledge")
def knowledge_group() -> None:
    """Manage and query the distilled Knowledge Vault and Isnad lineage."""
    pass


__all__ = ["knowledge_group", "logger"]
