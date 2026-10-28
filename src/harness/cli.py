"""CLI entry point — canonical commands and declared alias routing for Brain Harness."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure src and workspace root are in sys.path when executed directly
_src_dir = Path(__file__).resolve().parent.parent
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))
if str(_src_dir.parent) not in sys.path:
    sys.path.insert(0, str(_src_dir.parent))

import click
import structlog

from harness.commands._utils import _run_async
from harness.commands.agent import agent_group
from harness.commands.aliases import (
    CLI_ALIASES,
    AliasedGroup,
    generate_cli_docstring,
    get_command_catalog,
)
from harness.commands.antigravity import antigravity_group
from harness.commands.bigquery import bigquery_group
from harness.commands.brain_miner import brain_miner_group
from harness.commands.bridges import bridge_group
from harness.commands.calibrator import calibrator_group
from harness.commands.compass import compass_group
from harness.commands.compute import assess_compute_cli
from harness.commands.context import context_group
from harness.commands.creator import (
    creator_archetypes,
    creator_build,
    creator_group,
    creator_validate,
)
from harness.commands.data import data_group
from harness.commands.datasets import datasets_group
from harness.commands.doc import doc_group
from harness.commands.doc_builder import doc_builder_group
from harness.commands.events import events_cli
from harness.commands.facet import facet_group
from harness.commands.garf import garf_group
from harness.commands.gate import gate_group
from harness.commands.gemini_vercel import gemini_vercel_group
from harness.commands.gis import gis_group
from harness.commands.gradio_app import gradio_group
from harness.commands.harness_architect import architect_group
from harness.commands.icm import icm_group
from harness.commands.mcp import mcp_group
from harness.commands.model_router import model_router_group
from harness.commands.network_forensics import network_forensics_group
from harness.commands.okf import okf_group
from harness.commands.plugins import plugin_group
from harness.commands.pre_commit_security import pre_commit_security_group
from harness.commands.redteam import redteam_group
from harness.commands.reflection import knowledge_group, reflect_cli
from harness.commands.rol import rol_group
from harness.commands.runtime import apply_cli, config_group, run_cli, ui_cli
from harness.commands.self_eval import eval_group
from harness.commands.session import session_group
from harness.commands.skills import skills_group
from harness.commands.system import introspect_cli, services_cli
from harness.commands.tau import tau_group
from harness.commands.temp_miner import temp_miner_group
from harness.commands.tools import tool_group
from harness.commands.trajectory_miner import trajectory_group
from harness.commands.uncertainty import uncertainty_group
from harness.commands.validation_loop import validation_loop_group
from harness.commands.workspace import init_cli, watch_cli

logger = structlog.get_logger()


@click.group(cls=AliasedGroup)
@click.version_option(version="0.1.0", prog_name="harness")
@click.option("--debug", is_flag=True, help="Enable verbose debug logging")
def main(debug: bool) -> None:
    """Harness — Modular agent harness where everything is a plugin."""
    if sys.platform == "win32":
        try:
            if hasattr(sys.stdout, "reconfigure"):
                sys.stdout.reconfigure(encoding="utf-8")
            if hasattr(sys.stderr, "reconfigure"):
                sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass

    import logging

    log_level = logging.DEBUG if debug else logging.WARNING
    structlog.configure(
        processors=[
            structlog.stdlib.add_level_to_event_dict if hasattr(structlog.stdlib, "add_level_to_event_dict") else structlog.stdlib.add_log_level,
            structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
    )


# --- Register Canonical Command Groups (Rule 6: Single-Source Co-located Block) ---
_CANONICAL_GROUPS = [
    ("agent", agent_group),
    ("antigravity", antigravity_group),
    ("architect", architect_group),
    ("bigquery", bigquery_group),
    ("brain-miner", brain_miner_group),
    ("bridge", bridge_group),
    ("calibrate", calibrator_group),
    ("compass", compass_group),
    ("config", config_group),
    ("context", context_group),
    ("creator", creator_group),
    ("data", data_group),
    ("datasets", datasets_group),
    ("doc", doc_group),
    ("doc-builder", doc_builder_group),
    ("eval", eval_group),
    ("facet", facet_group),
    ("garf", garf_group),
    ("gate", gate_group),
    ("gemini-vercel", gemini_vercel_group),
    ("gis", gis_group),
    ("gradio", gradio_group),
    ("icm", icm_group),
    ("knowledge", knowledge_group),
    ("mcp", mcp_group),
    ("network-forensics", network_forensics_group),
    ("okf", okf_group),
    ("plugin", plugin_group),
    ("pre-commit-security", pre_commit_security_group),
    ("redteam", redteam_group),
    ("rol", rol_group),
    ("router", model_router_group),
    ("session", session_group),
    ("skills", skills_group),
    ("tau", tau_group),
    ("temp", temp_miner_group),
    ("tool", tool_group),
    ("trajectory", trajectory_group),
    ("uncertainty", uncertainty_group),
    ("validation-loop", validation_loop_group),
]

for name, grp in _CANONICAL_GROUPS:
    main.add_command(grp, name=name)

# --- Register Standalone Commands ---
_STANDALONE_COMMANDS = [
    ("apply", apply_cli),
    ("assess-compute", assess_compute_cli),
    ("events", events_cli),
    ("init", init_cli),
    ("introspect", introspect_cli),
    ("reflect", reflect_cli),
    ("run", run_cli),
    ("services", services_cli),
    ("ui", ui_cli),
    ("watch", watch_cli),
]

for name, cmd in _STANDALONE_COMMANDS:
    main.add_command(cmd, name=name)

# --- Register Declared Aliases & Top-Level Shortcuts ---
for alias, target in CLI_ALIASES.items():
    main.add_alias(alias, target)

# Top-level direct shortcuts
main.add_alias("create", creator_build)
main.add_alias("scaffold", creator_build)
main.add_alias("validate", creator_validate)
main.add_alias("archetypes", creator_archetypes)

# Update docstring with dynamically formatted command catalog
main.__doc__ = generate_cli_docstring(main)


__all__ = [
    "CLI_ALIASES",
    "AliasedGroup",
    "_run_async",
    "generate_cli_docstring",
    "get_command_catalog",
    "main",
]


if __name__ == "__main__":
    main()
