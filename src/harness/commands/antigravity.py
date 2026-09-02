"""Antigravity CLI Commands — Headless inspection for proactor, policies, and telemetry."""

from __future__ import annotations

import json
import sys
from typing import Any
import click

from harness.commands._utils import _run_async
from plugins.agent_orchestration.antigravity_core_bridge.service import (
    AntigravityConnectionService,
)
from plugins.security_and_forensics.antigravity_policy_gate.service import (
    AntigravityPolicyService,
    Decision,
)
from plugins.agent_orchestration.antigravity_trigger_runtime.service import (
    AntigravityTriggerService,
)
from plugins.data_engineering.antigravity_otel_telemetry.service import (
    AntigravityTelemetryService,
)


@click.group("antigravity")
def antigravity_group() -> None:
    """Google Antigravity SDK & CLI headless inspection seams."""


@antigravity_group.command("status")
@click.option("--json-output", is_flag=True, help="Output status in JSON format")
def antigravity_status_cmd(json_output: bool) -> None:
    """Inspect Antigravity proactor and trigger runtime status."""
    conn = AntigravityConnectionService()
    trig = AntigravityTriggerService()
    trig.register_interval("pulse_10s", 10.0)

    status_data = {
        "connected": conn.is_connected,
        "proactor_channel": "127.0.0.1:4242",
        "registered_triggers": len(trig.list_triggers()),
        "trigger_details": [
            {"id": t.trigger_id, "type": t.trigger_type, "active": t.is_active}
            for t in trig.list_triggers()
        ],
    }

    if json_output:
        click.echo(json.dumps(status_data, indent=2))
        return

    click.echo("=" * 55)
    click.echo(" Google Antigravity Headless System Status")
    click.echo("=" * 55)
    click.echo(f" Proactor Connected : {status_data['connected']}")
    click.echo(f" Proactor Channel   : {status_data['proactor_channel']}")
    click.echo(f" Active Triggers    : {status_data['registered_triggers']}")
    for t in status_data["trigger_details"]:
        click.echo(f"   • {t['id']} [{t['type']}] (active: {t['active']})")


@antigravity_group.command("policy")
@click.option("--tool", default="run_command", help="Tool name to test")
@click.option("--cmd", default="echo hello", help="Command line argument to test")
@click.option("--json-output", is_flag=True, help="Output in JSON format")
def antigravity_policy_cmd(tool: str, cmd: str, json_output: bool) -> None:
    """Evaluate tool execution against Antigravity declarative policy gates."""
    policy = AntigravityPolicyService()
    policy.add_rule(
        tool_pattern=r"run_command|bash",
        decision=Decision.DENY,
        arg_patterns={"CommandLine": r"rm\s+-rf\s+/|del\s+/s\s+/q"},
        rationale="Catastrophic deletion commands blocked",
    )
    policy.add_rule(
        tool_pattern=r"run_command",
        decision=Decision.ASK_USER,
        arg_patterns={"CommandLine": r"git\s+push\s+--force"},
        rationale="Force push requires human confirmation",
    )

    decision, rationale = policy.evaluate(tool, {"CommandLine": cmd})
    result = {
        "tool": tool,
        "arguments": {"CommandLine": cmd},
        "decision": decision.value,
        "rationale": rationale,
    }

    if json_output:
        click.echo(json.dumps(result, indent=2))
        return

    click.echo(f"Policy Evaluation: [{decision.value}] — {rationale}")


@antigravity_group.command("telemetry")
@click.option("--mode", default="idle", help="UI mode: idle, tool, review")
@click.option("--json-output", is_flag=True, help="Output statusline JSON payload")
def antigravity_telemetry_cmd(mode: str, json_output: bool) -> None:
    """Generate Antigravity dynamic statusline IPC payload."""
    tel = AntigravityTelemetryService()
    tel.record_tokens(prompt_tokens=1420, completion_tokens=380)
    tel.start_span("agent_turn", span_id="span_001")
    payload = tel.export_statusline_payload(mode=mode)

    if json_output:
        click.echo(json.dumps(payload, indent=2))
        return

    click.echo("=" * 55)
    click.echo(" Antigravity Dynamic Statusline IPC Summary")
    click.echo("=" * 55)
    click.echo(f" Mode               : {payload['mode']}")
    click.echo(f" Prompt Tokens      : {payload['tokens']['prompt']:,}")
    click.echo(f" Completion Tokens  : {payload['tokens']['completion']:,}")
    click.echo(f" Total Tokens       : {payload['tokens']['total']:,}")
    click.echo(f" Context Window Fill: {payload['tokens']['context_fill_ratio'] * 100:.2f}%")
    click.echo(f" Active Spans       : {payload['active_spans_count']}")
