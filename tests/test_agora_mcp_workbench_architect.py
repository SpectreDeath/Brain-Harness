"""Top-level contract tests for AgoraWorkbenchEngine and domain re-exports (Rule 43, Rule 49)."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest

from harness.services import (
    AGORA_WORKBENCH_SERVICE_KEY,
    MAX_STREAMING_ENVELOPE_BYTES,
    MAX_TRANSFER_SIZE_BYTES,
    PARALLEL_COMPANION_TOOLS,
    STREAMING_TRANSFER_VERSION,
    AgoraWorkbenchEngine,
    AgoraWorkbenchProtocol,
    ConnectorRoutingDecision,
    DataLakeTransferReport,
    SidecarAuditReport,
    StateGraphPlanResult,
)


def test_constants_and_protocol_immutability_rule43() -> None:
    assert AGORA_WORKBENCH_SERVICE_KEY.name == "service.agora_mcp_workbench"
    assert MAX_TRANSFER_SIZE_BYTES == 256 * 1024 * 1024
    assert MAX_STREAMING_ENVELOPE_BYTES == 64 * 1024
    assert STREAMING_TRANSFER_VERSION == "2"
    assert PARALLEL_COMPANION_TOOLS == ("poll_batch", "collect_batch", "cancel_batch")
    assert isinstance(AgoraWorkbenchEngine(), AgoraWorkbenchProtocol)

    report = SidecarAuditReport(
        name="s1",
        valid=True,
        resolved_argv=("/bin/srv",),
        base_url="http://127.0.0.1:9000",
        health_url="http://127.0.0.1:9000/health",
        locked_host="127.0.0.1",
        locked_port=9000,
        env_override_attempted=False,
        loopback_bound=True,
    )
    with pytest.raises((AttributeError, TypeError)):
        report.valid = False  # type: ignore[misc]

    decision = ConnectorRoutingDecision(
        mode="dispatcher",
        allowed=False,
        selected_worker=None,
        suppressed_companions=(),
        rate_limited=False,
        affinity_rerouted=False,
        reason="no_healthy_workers",
    )
    with pytest.raises((AttributeError, TypeError)):
        decision.reason = "changed"  # type: ignore[misc]

    dl = DataLakeTransferReport(
        valid=True,
        effective_sources=("a",),
        cursor_rejected=False,
        masked_as_not_found=False,
        transfer_size_valid=True,
        envelope_valid=True,
    )
    with pytest.raises((AttributeError, TypeError)):
        dl.cursor_rejected = True  # type: ignore[misc]

    sg = StateGraphPlanResult(
        source_state="s.start",
        target_state="s.start",
        reachable=True,
        steps=(),
        bridges_used=(),
    )
    with pytest.raises((AttributeError, TypeError)):
        sg.source_state = "other"  # type: ignore[misc]


def test_sidecar_edge_cases() -> None:
    engine = AgoraWorkbenchEngine()
    bad = engine.audit_sidecar_config(
        name="dup",
        command=[],
        url_env_var="bad-var",
        port=70000,
        host="0.0.0.0",
        health_path="health",
        use_env_python=False,
        existing_names=["dup"],
    )
    assert bad.valid is False
    assert bad.loopback_bound is False
    assert "duplicate_sidecar_name:dup" in bad.violations
    assert "empty_command" in bad.violations
    assert "invalid_url_env_var:bad-var" in bad.violations
    assert "invalid_port:70000" in bad.violations
    assert "invalid_health_path:health" in bad.violations
    assert "non_loopback_host:0.0.0.0" in bad.violations


def test_state_graph_identity_and_invalid_bridge() -> None:
    engine = AgoraWorkbenchEngine()
    ident = engine.plan_state_graph_workflow(
        source_state="geo.loaded",
        target_state="geo.loaded",
        tools=[{"name": "clip", "server": "geo", "requires": ["geo.loaded"], "produces": ["geo.clipped"]}],
        bridges=[{"from_state": "missing.prod", "to_state": "geo.loaded"}],
    )
    assert ident.reachable is True
    assert ident.steps == ()
    assert ident.invalid_bridges == ("missing.prod->geo.loaded",)


def test_connector_gateway_blocks_rate_limit_and_weighted_rr() -> None:
    engine = AgoraWorkbenchEngine()
    blocked = engine.evaluate_connector_call(
        mode="gateway",
        code="parallel_execute(fn)",
        blocked_tools=["parallel_execute"],
    )
    assert blocked.allowed is False
    assert blocked.suppressed_companions == ("poll_batch", "collect_batch", "cancel_batch")
    assert blocked.reason == "blocked_tool:parallel_execute"

    limited = engine.evaluate_connector_call(
        mode="gateway",
        code="analyze()",
        calls_in_last_minute=60,
        max_calls_per_minute=60,
    )
    assert limited.allowed is False
    assert limited.rate_limited is True

    rr = engine.evaluate_connector_call(
        mode="dispatcher",
        workers=[{"name": "w1", "weight": 2}, {"name": "w2", "weight": 1}],
        healthy_workers=["w1", "w2"],
        strategy="round_robin",
        round_robin_index=1,
    )
    assert rr.allowed is True
    assert rr.selected_worker == "w1"

    fail_closed = engine.evaluate_connector_call(
        mode="dispatcher",
        workers=[{"name": "w2", "weight": 1}],
        healthy_workers=["w2"],
        session_affinity_worker="w1",
        worker_failure_policy="error",
    )
    assert fail_closed.allowed is False
    assert fail_closed.reason == "affinity_worker_unhealthy_error"


def test_datalake_and_streaming_bounds() -> None:
    engine = AgoraWorkbenchEngine()
    bad = engine.validate_datalake_and_transfer(
        policy_mode="homogeneous_source",
        has_per_artifact_enforcer=True,
        requested_sources=["s1"],
        permitted_sources=["s1"],
        target_source_permitted=False,
        size_bytes=MAX_TRANSFER_SIZE_BYTES + 1,
        transfer_version="1",
        envelope_bytes=MAX_STREAMING_ENVELOPE_BYTES + 1,
        has_duplicate_json_keys=True,
        correlation_id="bad space id",
    )
    assert bad.valid is False
    assert bad.masked_as_not_found is True
    assert bad.transfer_size_valid is False
    assert bad.envelope_valid is False
    assert "homogeneous_source_forbids_enforcer" in bad.violations
    assert "target_source_masked_not_found" in bad.violations
    assert "unsupported_transfer_version:1" in bad.violations
    assert "duplicate_streaming_json_keys" in bad.violations
    assert "invalid_correlation_id" in bad.violations


def test_skill_cli_entrypoint() -> None:
    script = (
        Path(__file__).resolve().parents[1]
        / ".agents"
        / "skills"
        / "agora-mcp-workbench-architect"
        / "scripts"
        / "agora_workbench_engine.py"
    )
    proc = subprocess.run(
        [
            sys.executable,
            str(script),
            "validate-transfer",
            "--policy-mode",
            "homogeneous_source",
            "--requested-sources",
            "local-files",
            "--permitted-sources",
            "local-files",
            "--correlation-id",
            "corr-42",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(proc.stdout)
    assert payload["valid"] is True
    assert payload["effective_sources"] == ["local-files"]
