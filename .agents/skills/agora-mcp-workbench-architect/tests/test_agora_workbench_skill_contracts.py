"""Contract tests for agora-mcp-workbench-architect skill and CLI engine (Rule 43, Rule 57)."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[4]
_HARNESS_SRC = _REPO_ROOT / "src"
if str(_HARNESS_SRC) not in sys.path:
    sys.path.insert(0, str(_HARNESS_SRC))

from harness.services.agora_workbench import (  # noqa: E402
    AgoraWorkbenchEngine,
    ConnectorRoutingDecision,
    DataLakeTransferReport,
    SidecarAuditReport,
    StateGraphPlanResult,
)

_SCRIPT_PATH = (
    _REPO_ROOT / ".agents" / "skills" / "agora-mcp-workbench-architect" / "scripts" / "agora_workbench_engine.py"
)


def test_frozen_slotted_immutability_rule43() -> None:
    report = SidecarAuditReport(
        name="chem-model",
        valid=True,
        resolved_argv=("/opt/venv/bin/python", "-m", "model_srv"),
        base_url="http://127.0.0.1:8100",
        health_url="http://127.0.0.1:8100/health",
        locked_host="127.0.0.1",
        locked_port=8100,
        env_override_attempted=False,
        loopback_bound=True,
    )
    with pytest.raises((AttributeError, TypeError)):
        report.locked_port = 9999  # type: ignore[misc]

    plan = StateGraphPlanResult(
        source_state="a",
        target_state="b",
        reachable=True,
        steps=({"tool": "t", "server": "s", "from_state": "a", "to_state": "b"},),
        bridges_used=(),
    )
    with pytest.raises((AttributeError, TypeError)):
        plan.reachable = False  # type: ignore[misc]

    decision = ConnectorRoutingDecision(
        mode="gateway",
        allowed=True,
        selected_worker=None,
        suppressed_companions=(),
        rate_limited=False,
        affinity_rerouted=False,
        reason="gateway_allowed",
    )
    with pytest.raises((AttributeError, TypeError)):
        decision.allowed = False  # type: ignore[misc]

    transfer = DataLakeTransferReport(
        valid=True,
        effective_sources=("local",),
        cursor_rejected=False,
        masked_as_not_found=False,
        transfer_size_valid=True,
        envelope_valid=True,
    )
    with pytest.raises((AttributeError, TypeError)):
        transfer.valid = False  # type: ignore[misc]


def test_audit_sidecar_env_lock_and_python_resolution() -> None:
    engine = AgoraWorkbenchEngine()
    res = engine.audit_sidecar_config(
        name="retrochimera",
        command=["-m", "retrochimera.serve"],
        url_env_var="RETRO_URL",
        port=8765,
        env_overrides={"SIDECAR_HOST": "0.0.0.0", "SIDECAR_PORT": "9999"},
    )
    assert res.valid is True
    assert res.env_override_attempted is True
    assert res.locked_host == "127.0.0.1"
    assert res.locked_port == 8765
    assert res.resolved_argv == ("/opt/venv/bin/python", "-m", "retrochimera.serve")


def test_plan_state_graph_with_bridge_and_duplicate_skills() -> None:
    engine = AgoraWorkbenchEngine()
    res = engine.plan_state_graph_workflow(
        source_state="chem.smiles_parsed",
        target_state="battery.electrolyte_configured",
        tools=[
            {
                "name": "predict_redox",
                "server": "chemistry",
                "requires": ["chem.smiles_parsed"],
                "produces": ["chem.redox_predicted"],
            },
            {
                "name": "setup_cell",
                "server": "ezbattery",
                "requires": ["ezbattery.electrolyte_ready"],
                "produces": ["battery.electrolyte_configured"],
            },
        ],
        bridges=[
            {"from_state": "chem.redox_predicted", "to_state": "ezbattery.electrolyte_ready"},
        ],
        skills=[
            {"name": "shared-helper", "upstream": "chemistry", "states": ["chem.smiles_parsed"]},
            {"name": "shared-helper", "upstream": "ezbattery", "states": ["ezbattery.electrolyte_ready"]},
        ],
    )
    assert res.reachable is True
    assert res.bridges_used == ("bridge:chem.redox_predicted->ezbattery.electrolyte_ready",)
    assert res.duplicate_skills == ("shared-helper",)
    assert set(res.inferred_domains) == {"battery", "chem", "ezbattery"}


def test_evaluate_gateway_cascade_and_dispatcher_affinity() -> None:
    engine = AgoraWorkbenchEngine()
    gw = engine.evaluate_connector_call(
        mode="gateway",
        code="run_safe_tool()",
        blocked_tools=["parallel_execute"],
        allowed_tools=["run_safe_tool"],
        calls_in_last_minute=5,
        max_calls_per_minute=10,
    )
    assert gw.allowed is True
    assert gw.suppressed_companions == ("poll_batch", "collect_batch", "cancel_batch")

    disp = engine.evaluate_connector_call(
        mode="dispatcher",
        workers=[{"name": "w1", "weight": 1, "active_calls": 3}, {"name": "w2", "weight": 2, "active_calls": 1}],
        healthy_workers=["w2"],
        strategy="least_loaded",
        session_affinity_worker="w1",
        worker_failure_policy="reroute",
    )
    assert disp.allowed is True
    assert disp.affinity_rerouted is True
    assert disp.selected_worker == "w2"


def test_validate_datalake_cursor_and_streaming_transfer() -> None:
    engine = AgoraWorkbenchEngine()
    res = engine.validate_datalake_and_transfer(
        policy_mode="per_artifact",
        has_per_artifact_enforcer=True,
        requested_sources=["src-a", "src-b"],
        permitted_sources=["src-a"],
        has_cursor=True,
        correlation_id="tx-01",
    )
    assert res.valid is False
    assert res.cursor_rejected is True
    assert "cursor_scope_mismatch" in res.violations


def test_cli_subcommands() -> None:
    proc = subprocess.run(
        [
            sys.executable,
            str(_SCRIPT_PATH),
            "audit-sidecar",
            "--name",
            "model-sidecar",
            "--cmd-json",
            '["-m", "srv"]',
            "--url-env-var",
            "MODEL_URL",
            "--port",
            "8200",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    data = json.loads(proc.stdout)
    assert data["valid"] is True
    assert data["locked_port"] == 8200
    assert data["resolved_argv"] == ["/opt/venv/bin/python", "-m", "srv"]
