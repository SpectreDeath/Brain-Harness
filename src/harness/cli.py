"""CLI entry point — simple commands for managing the harness.

Commands:
    harness init                      Initialize a workspace
    harness plugin add <url>          Fetch, inspect, and register a GitHub repo
    harness plugin list               List all installed plugins
    harness plugin enable <name>      Enable a plugin
    harness plugin disable <name>     Disable a plugin
    harness plugin remove <name>      Remove a cached plugin
    harness events [--type TYPE]      Show the event log
    harness services                  List registered services
    harness run                       Start the harness (interactive)
    harness agent run "<task>"        Execute an autonomous agent task
    harness introspect                Show live system diagnostics & graph
    harness bridge status             Check ecosystem bridges
    harness creator build <name>      Scaffold a new plugin project
"""

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
from harness.commands.antigravity import antigravity_group
from harness.commands.bigquery import bigquery_group
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
from harness.commands.doc import doc_group
from harness.commands.events import events_cli
from harness.commands.gate import gate_group
from harness.commands.gemini_vercel import gemini_vercel_group
from harness.commands.gradio_app import gradio_group
from harness.commands.harness_architect import architect_group
from harness.commands.mcp import mcp_group
from harness.commands.model_router import model_router_group
from harness.commands.okf import okf_group
from harness.commands.plugins import plugin_group
from harness.commands.pre_commit_security import pre_commit_security_group
from harness.commands.reflection import knowledge_group, reflect_cli
from harness.commands.self_eval import eval_group
from harness.commands.uncertainty import uncertainty_group
from harness.commands.runtime import (
    apply_cli,
    config_group,
    run_cli,
    ui_cli,
)
from harness.commands.session import session_group
from harness.commands.skills import skills_group
from harness.commands.system import introspect_cli, services_cli
from harness.commands.tools import tool_group
from harness.commands.validation_loop import validation_loop_group
from harness.commands.workspace import init_cli, watch_cli

logger = structlog.get_logger()


@click.group()
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
            structlog.stdlib.add_log_level,
            structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
    )


# --- Register Command Groups ---
main.add_command(plugin_group, name="plugin")
main.add_command(tool_group, name="tool")
main.add_command(bridge_group, name="bridge")
main.add_command(agent_group, name="agent")
main.add_command(creator_group, name="creator")
main.add_command(mcp_group, name="mcp")
main.add_command(config_group, name="config")
main.add_command(skills_group, name="skills")
main.add_command(okf_group, name="okf")
main.add_command(knowledge_group, name="knowledge")
main.add_command(session_group, name="session")
main.add_command(context_group, name="context")
main.add_command(antigravity_group, name="antigravity")
main.add_command(data_group, name="data")
main.add_command(doc_group, name="doc")
main.add_command(architect_group, name="architect")
main.add_command(architect_group, name="harness-architect")
main.add_command(gate_group, name="gate")
main.add_command(gate_group, name="ai-native-harness")
main.add_command(bigquery_group, name="bigquery")
main.add_command(bigquery_group, name="bq")
main.add_command(calibrator_group, name="calibrate")
main.add_command(calibrator_group, name="calibrator")
main.add_command(validation_loop_group, name="validation-loop")
main.add_command(validation_loop_group, name="validate-loop")
main.add_command(model_router_group, name="router")
main.add_command(model_router_group, name="model-router")
main.add_command(compass_group, name="compass")
main.add_command(compass_group, name="harness-compass")
main.add_command(gradio_group, name="gradio")
main.add_command(gradio_group, name="gradio-app")
main.add_command(gemini_vercel_group, name="gemini-vercel")
main.add_command(gemini_vercel_group, name="streaming-chatbot")
main.add_command(gemini_vercel_group, name="gemini-chat")
main.add_command(pre_commit_security_group, name="pre-commit-security")
main.add_command(pre_commit_security_group, name="security-guard")
main.add_command(pre_commit_security_group, name="shift-left")
main.add_command(eval_group, name="eval")
main.add_command(eval_group, name="self-eval")
main.add_command(uncertainty_group, name="uncertainty")
main.add_command(uncertainty_group, name="uncertainty-guard")

# --- Register Standalone Commands ---
main.add_command(init_cli, name="init")
main.add_command(services_cli, name="services")
main.add_command(events_cli, name="events")
main.add_command(introspect_cli, name="introspect")
main.add_command(run_cli, name="run")
main.add_command(ui_cli, name="ui")
main.add_command(watch_cli, name="watch")
main.add_command(apply_cli, name="apply")
main.add_command(assess_compute_cli, name="assess-compute")
main.add_command(reflect_cli, name="reflect")

# --- Register Top-Level Aliases ---
main.add_command(creator_build, name="create")
main.add_command(creator_build, name="scaffold")
main.add_command(creator_validate, name="validate")
main.add_command(creator_archetypes, name="archetypes")


__all__ = [
    "_run_async",
    "main",
]


if __name__ == "__main__":
    main()
